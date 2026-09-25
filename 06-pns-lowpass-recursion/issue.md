# calculate_pns is slow for long sequences: compute the SAFE low-pass filter as a recursion

**Is your feature request related to a problem? Please describe.**

On an Apple M1 Max, `Sequence.calculate_pns` takes about 40 s for each minute of
sequence, so a PNS check of a real protocol takes minutes. Almost all of the time is in
`safe_tau_lowpass`. `safe_pns_model` calls it three times for each axis, one time for
each time constant. It filters with `np.convolve` and the kernel `(1 - alpha)^k`, cut
where the kernel is below `eps = 1e-16`. On the 10 µs gradient raster, the kernels of
`safe_example_hw()` have 128 to 11,071 taps, so the filter costs up to 11,071
multiply-adds for each sample.

The example filters 2 × 10⁶ random samples with the longest time constant (3 ms), with
`safe_tau_lowpass` and with the recursion below. Then it runs `calculate_pns` on a 60 s
sequence (a trapezoid on each axis every 10 ms), and prints the times and the peak
memory:

```python
import resource
import sys
import time

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
t2 = time.perf_counter()
difference = np.max(np.abs(y_recursion - y_pypulseq)) / np.max(np.abs(y_pypulseq))
print(f'safe_tau_lowpass: {t1 - t0:.3f} s')
print(f'lfilter:          {t2 - t1:.3f} s')
print(f'largest difference / peak: {difference:.1e}')

# calculate_pns for a 60 s sequence: a trapezoid on each axis every 10 ms.
system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
seq = pp.Sequence(system)
for _ in range(6000):
    seq.add_block(*grads, delay)

t0 = time.perf_counter()
ok, pns_norm, _, _ = seq.calculate_pns(safe_example_hw(), do_plots=False)
t1 = time.perf_counter()
peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
peak_rss *= 1 if sys.platform == 'darwin' else 1024  # bytes on macOS, KiB on Linux
print(f'calculate_pns, {seq.duration()[0]:.0f} s sequence: {t1 - t0:.1f} s, peak {pns_norm.max():.4f}')
print(f'peak RSS of the process: {peak_rss / 1e9:.2f} GB')
```

Results on an Apple M1 Max:

| | 1.5.0.post1 | master [f2c582b](https://github.com/pulseq/pypulseq/commit/f2c582bae13145b8ac71958726bc8b5a14bd1cfd) | master with the change below |
|---|---|---|---|
| `safe_tau_lowpass`, 2 × 10⁶ samples | 4.48 s | 4.46 s | 0.009 s |
| `lfilter`, the same samples | 0.008 s | 0.008 s | 0.009 s |
| largest difference / peak | 1.6e-15 | 1.6e-15 | 0 |
| `calculate_pns`, 60 s sequence | 42.6 s | 42.0 s | 0.8 s |
| peak of `pns_norm` | 1.2032 | 1.2032 | 1.2032 |
| peak RSS of the process | 1.40 GB | 1.44 GB | 1.42 GB |

**Describe the solution you'd like**

The filter is the first-order recursion `y[i] = alpha * x[i] + (1 - alpha) * y[i - 1]`,
with `y = 0` before the first sample. This is the loop of the
[original MATLAB code](https://github.com/filip-szczepankiewicz/safe_pns_prediction/blob/0774e805ff6df9f81b36bb727519a6e696a4a000/safe_pns_model.m#L71-L77),
which the Python port
[replaced with a convolution](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/utils/safe_pns_prediction.py#L279-L286)
"to get rid of for loop in original code". `scipy.signal.lfilter` runs the same recursion
in compiled code, at O(1) for each sample. SciPy is already a dependency of pypulseq.

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

The name, the arguments and the result shape do not change. `eps` has no effect after
the change. It stays so that callers do not break. The values differ from the
convolution only by float rounding and by the cut of the kernel: at most 1.6e-15 of the
peak in the example. The whole test suite passes on master with the change.

**Describe alternatives you've considered**

- `scipy.signal.sosfilt`: the SciPy documentation prefers it to `lfilter` "for most
  filtering tasks", because high-order filters in second-order sections have fewer
  numerical problems. This filter is first order: `tf2sos` gives one section with the
  same coefficients, and `sosfilt` gives the same values as `lfilter`, bit for bit, for
  each time constant of `safe_example_hw()`. It takes about two times as long (0.015 s
  instead of 0.008 s for the 2 × 10⁶ samples).
- `scipy.signal.fftconvolve` with the same cut kernel: O(n log n) instead of O(n), and
  the kernel stays.
- The loop of the MATLAB code in Python: slow in Python.
- A new dependency, for example Numba: not necessary, because SciPy has `lfilter`.

**Additional context**

This improvement was identified and test case generated by Claude, but I've reviewed the
code myself and the change appears to be correct based on my review.

The change does not reduce the memory. `calc_pns` keeps arrays of the whole sequence
(the gradient samples, their differences, the padded copies and the PNS values): about
1.4 GB for the 60 s example. The model could also run on the sequence in chunks with
bounded memory, leveraging the fact that the recursion keeps one number of state for
each filter. That would be a larger change, and so is not considered here.

The open PR #385 moves `utils/safe_pns_prediction.py` to `safety/pns/safe_pns.py`, and
does not change `safe_tau_lowpass`. This change applies to the new file in the same way.

Versions: macOS 26.6.2, Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1; pypulseq 1.5.0.post1,
and master at
[f2c582b](https://github.com/pulseq/pypulseq/commit/f2c582bae13145b8ac71958726bc8b5a14bd1cfd)
(2026-08-28). `safe_pns_prediction.py` is the same in both. For comparison:
`filip-szczepankiewicz/safe_pns_prediction` at
[0774e80](https://github.com/filip-szczepankiewicz/safe_pns_prediction/commit/0774e805ff6df9f81b36bb727519a6e696a4a000).

I will open a PR with this change and a test that compares the recursion with the
convolution, for each time constant of `safe_example_hw()` and in `safe_gwf_to_pns` on
`safe_example_gwf()`.
