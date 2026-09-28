# Reduce the time and memory of calculate_pns for long sequences

**Is your feature request related to a problem? Please describe.**

On an Apple M1 Max, `Sequence.calculate_pns` takes about 40 s and 1 GB of memory for each
minute of sequence, so a PNS check of a real protocol takes minutes and several GB. There
are two causes:

1. Almost all of the time is in `safe_tau_lowpass`. `safe_pns_model` calls it three
   times for each axis, one time for each time constant. It filters with `np.convolve`
   and the kernel `(1 - alpha)^k`, cut where the kernel is below `eps = 1e-16`. On the
   10 µs gradient raster, the kernels of `safe_example_hw()` have 128 to 11,071 taps, so
   the filter costs up to 11,071 multiply-adds for each sample.
2. `calc_pns` computes each step of the model on the whole sequence at one time. It keeps
   arrays of the sampled gradients, their padded copies and differences, the filter
   outputs and the PNS values: about 170 bytes for each sample. The arrays that it
   returns (`pns_norm`, `pns_comp` and `t`) are 40 bytes for each sample. The rest is
   temporary.

The example filters 2 × 10⁶ random samples with the longest time constant (3 ms), with
`safe_tau_lowpass` and with the recursion below. Then it runs `calculate_pns` on a 60 s
sequence (a trapezoid on each axis every 10 ms), and measures the time and the peak
memory. Last, it computes the PNS of a piece of a 1 s sequence with `time_range`, from a
time on the flat top of a trapezoid:

```python
import time
import tracemalloc

import numpy as np
import pypulseq as pp
from pypulseq.utils.safe_pns_prediction import safe_example_hw, safe_tau_lowpass
from scipy.signal import lfilter

# One filter, 20 s of samples on the 10 us raster, with the longest time constant of
# safe_example_hw(). safe_pns_model gives tau and dt to safe_tau_lowpass in ms.
dt, tau = 0.01, 3.0
alpha = dt / (tau + dt)
x = np.random.default_rng(0).normal(size=2_000_000)
t0 = time.perf_counter()
y_pypulseq = safe_tau_lowpass(x, tau, dt)
t1 = time.perf_counter()
y_recursion = lfilter([alpha], [1.0, alpha - 1.0], x)
difference = np.max(np.abs(y_recursion - y_pypulseq)) / np.max(np.abs(y_pypulseq))
print(f'safe_tau_lowpass: {t1 - t0:.3f} s, largest difference from the recursion / peak: {difference:.1e}')

# calculate_pns for a 60 s sequence: a trapezoid on each axis every 10 ms.
system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
hw = safe_example_hw()


def make_seq(duration):
    seq = pp.Sequence(system)
    for _ in range(round(duration / 10e-3)):
        seq.add_block(*grads, delay)
    return seq


seq = make_seq(60)
t0 = time.perf_counter()
ok, pns_norm, pns_comp, t = seq.calculate_pns(hw, do_plots=False)
t1 = time.perf_counter()
tracemalloc.start()
seq.calculate_pns(hw, do_plots=False)
peak = tracemalloc.get_traced_memory()[1]
tracemalloc.stop()
returned = pns_norm.nbytes + pns_comp.nbytes + t.nbytes
print(f'calculate_pns, 60 s: {t1 - t0:.1f} s, peak of pns_norm {pns_norm.max():.4f}')
print(f'peak memory {peak / 1e9:.2f} GB, returned arrays {returned / 1e9:.2f} GB')

# A piece of a 1 s sequence with time_range, from the flat top of the trapezoids at 0.5 s.
seq = make_seq(1)
_, pns_norm, _, t = seq.calculate_pns(hw, do_plots=False)
_, piece, _, t_piece = seq.calculate_pns(hw, do_plots=False, time_range=[0.5002, 1.0])
i = np.searchsorted(t, t_piece[0])
print(f'at {t_piece[0] * 1e3:.3f} ms: {piece[0]:.3f} from the piece, {pns_norm[i]:.3f} from the whole sequence')
```

Results on an Apple M1 Max:

| | master [f2c582b](https://github.com/pulseq/pypulseq/commit/f2c582bae13145b8ac71958726bc8b5a14bd1cfd) | with the recursion | with the recursion and the chunks |
|---|---|---|---|
| `safe_tau_lowpass`, 2 × 10⁶ samples | 4.49 s | 0.009 s | 0.009 s |
| largest difference / peak | 1.6e-15 | 0 | 0 |
| `calculate_pns`, 60 s sequence | 41.9 s | 0.7 s | 0.6 s |
| peak of `pns_norm` | 1.2032 | 1.2032 | 1.2032 |
| peak memory | 1.01 GB | 1.01 GB | 0.25 GB |
| returned arrays | 0.24 GB | 0.24 GB | 0.24 GB |

The piece gives 2.220 at 500.205 ms, and the whole sequence gives 1.108.

**Describe the solution you'd like**

Two changes, in one PR. The arguments and the results of `calculate_pns` do not change,
and pypulseq has no new public names.

1. Compute the filter as a recursion. The filter is the first-order recursion
   `y[i] = alpha * x[i] + (1 - alpha) * y[i - 1]`, with `y = 0` before the first sample.
   This is the loop of the
   [original MATLAB code](https://github.com/filip-szczepankiewicz/safe_pns_prediction/blob/0774e805ff6df9f81b36bb727519a6e696a4a000/safe_pns_model.m#L71-L77),
   which the Python port
   [replaced with a convolution](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/utils/safe_pns_prediction.py#L279-L286)
   "to get rid of for loop in original code". `scipy.signal.lfilter` runs the same
   recursion in compiled code, at O(1) for each sample:

   ```diff
   +from scipy.signal import lfilter
    ...
   -def safe_tau_lowpass(dgdt, tau, dt, eps=1e-16):
   +def safe_tau_lowpass(dgdt, tau, dt, eps=1e-16):  # noqa: ARG001
    ...
        alpha = dt / (tau + dt)
   -
   -    # Calculate number of elements in filter to reach desired accuracy (eps)
   -    n = min(round(np.log(eps) / np.log(1 - alpha)), dgdt.shape[0])
   -    filt = (1 - alpha) ** np.arange(n)
   -
   -    # Implements lowpass filter using convolution to get rid of for loop in original code
   -    return alpha * np.convolve(dgdt, filt)[: dgdt.shape[0]]
   +    return lfilter([alpha], [1.0, alpha - 1.0], dgdt)
   ```

   The values differ from the convolution only by float rounding and by the cut of the
   kernel: at most 1.6e-15 of the peak in the example. `eps` has no effect after the
   change. It stays so that callers do not break.

2. Compute the model in chunks. A private function,
   `_safe_gwf_to_pns_chunk(gwf, dt, hw, state=None)`, computes the model on one chunk of
   the waveform with `lfilter(..., zi=zi)`. It returns the PNS of the chunk and the
   state for the next chunk: the last gradient sample, and the final state of each of
   the nine filters. `calc_pns` then computes the model on chunks of 30,000 samples
   (0.3 s on the 10 µs raster):

   ```python
   _PNS_CHUNK_SAMPLES = 30_000
   ...
   n = t.shape[0]
   pns_comp = np.empty((n, 3))
   pns_norm = np.empty(n)
   state = None
   for start in range(0, n, _PNS_CHUNK_SAMPLES):
       stop = min(start + _PNS_CHUNK_SAMPLES, n)
       gw = np.zeros((stop - start, ng))
       for i in range(ng):
           if gw_pp[i] is not None:
               gw[:, i] = gw_pp[i](t[start:stop])
       pns_chunk, state = _safe_gwf_to_pns_chunk(gw / obj.system.gamma, obj.grad_raster_time, hardware, state)
       pns_comp[start:stop] = 0.01 * pns_chunk
       pns_norm[start:stop] = np.sqrt((pns_comp[start:stop] ** 2).sum(axis=1))
   ok = bool(np.all(pns_norm < 1))
   ```

   The result is the same as for the whole sequence, bit for bit. The zero padding
   before the sequence is the same as a zero initial state of the filters, and
   `calc_pns` removes the padding after the sequence from its result. The peak memory is
   the returned arrays and one chunk.

   Each chunk costs about 80 µs and each sample about 87 ns on an Apple M1 Max. So
   smaller chunks add time (about 9 % at 10,000 samples) without less memory, and larger
   chunks add memory (0.43 GB at 10⁶ samples) without less time.

   `ok` now uses `np.all` instead of the builtin `all`, which reads `pns_norm < 1` one
   sample at a time when the sequence passes. For a 60 s sequence that passes (a
   trapezoid on x every 10 ms), `calculate_pns` takes 0.41 s instead of 0.45 s.

**Describe alternatives you've considered**

- `scipy.signal.sosfilt`: the SciPy documentation prefers it to `lfilter` "for most
  filtering tasks", because high-order filters in second-order sections have fewer
  numerical problems. This filter is first order: `tf2sos` gives one section with the
  same coefficients, and `sosfilt` gives the same values as `lfilter`, bit for bit, for
  each time constant of `safe_example_hw()`. It takes about two times as long.
- `scipy.signal.fftconvolve` with the same cut kernel: O(n log n) instead of O(n), and
  the kernel stays.
- The loop of the MATLAB code in Python: slow in Python.
- A new dependency, for example Numba: not necessary, because SciPy has `lfilter`.
- Pieces with `time_range`, by the user: each piece starts the filters from zero, and
  the gradient at the start of the piece counts as a step from zero. In the example,
  this gives 2.220 instead of 1.108, a false failure.
- `float32` arrays: half of the memory, but it still increases with the duration, and
  the values change.
- An argument that returns only `ok` and the peak of `pns_norm`: with chunks, the
  memory would then not depend on the duration. This changes what `calculate_pns`
  returns, so it could be a later option.

**Additional context**

This improvement was identified and test case generated by Claude, but I've reviewed the
code myself and the change appears to be correct based on my review.

The open PR #385 moves `utils/safe_pns_prediction.py` to `safety/pns/safe_pns.py`, and
adds a `model` argument to `calc_pns`. This change applies in the same way to the moved
file and to the `'safe'` model.

Versions: macOS 26.6.2, Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1; pypulseq 1.5.0.post1,
and master at
[f2c582b](https://github.com/pulseq/pypulseq/commit/f2c582bae13145b8ac71958726bc8b5a14bd1cfd)
(2026-08-28). `safe_pns_prediction.py` and `calc_pns.py` are the same in both. For
comparison: `filip-szczepankiewicz/safe_pns_prediction` at
[0774e80](https://github.com/filip-szczepankiewicz/safe_pns_prediction/commit/0774e805ff6df9f81b36bb727519a6e696a4a000).

I have this change on a branch, with tests, and I am happy to open a PR. Are there any
concerns about the suggested change, or about the size of the chunks?
