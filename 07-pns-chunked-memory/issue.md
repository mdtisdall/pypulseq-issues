# Reduce the memory of calculate_pns by computing the SAFE model in chunks

**Is your feature request related to a problem? Please describe.**

`Sequence.calculate_pns` computes each step of the SAFE model on the whole sequence at
one time. It keeps arrays of the sampled gradients, their padded copies and
differences, the outputs of the nine low-pass filters and the PNS values. The peak
memory is about 170 bytes for each sample on the gradient raster: about 1 GB for each
minute of gradient waveform on the 10 µs raster, so about 10 GB for a 10 min protocol.
The arrays that `calculate_pns` returns (`pns_norm`, `pns_comp` and `t`) are 40 bytes for
each sample. The rest is temporary.

The example measures the peak memory of `calculate_pns` with `tracemalloc` for
sequences of 60 s and 120 s (a trapezoid on each axis every 10 ms). Then it computes the
PNS of a piece of a 1 s sequence with `time_range`, from a time on the flat top of a
trapezoid:

```python
import tracemalloc

import numpy as np
import pypulseq as pp
from pypulseq.utils.safe_pns_prediction import safe_example_hw

system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
hw = safe_example_hw()


def make_seq(duration):  # a trapezoid on each axis every 10 ms
    seq = pp.Sequence(system)
    for _ in range(round(duration / 10e-3)):
        seq.add_block(*grads, delay)
    return seq


# Peak memory of calculate_pns, and the size of the arrays that it returns.
for duration in (60, 120):
    seq = make_seq(duration)
    tracemalloc.start()
    ok, pns_norm, pns_comp, t = seq.calculate_pns(hw, do_plots=False)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    returned = pns_norm.nbytes + pns_comp.nbytes + t.nbytes
    print(f'{duration} s, {t.size} samples: peak {peak / 1e9:.2f} GB, returned {returned / 1e9:.2f} GB')

# A piece that starts on the flat top of the trapezoids at 0.5 s.
seq = make_seq(1)
_, pns_norm, _, t = seq.calculate_pns(hw, do_plots=False)
_, piece, _, t_piece = seq.calculate_pns(hw, do_plots=False, time_range=[0.5002, 1.0])
i = np.searchsorted(t, t_piece[0])
print(f'at {t_piece[0] * 1e3:.3f} ms: {piece[0]:.3f} from the piece, {pns_norm[i]:.3f} from the whole sequence')
```

Results:

| Sequence | Samples | Peak memory | Peak memory with the change below | Returned arrays |
|---|---|---|---|---|
| 60 s | 5,999,103 | 1.02 GB | 0.26 GB | 0.24 GB |
| 120 s | 11,999,103 | 2.04 GB | 0.52 GB | 0.48 GB |

The piece gives 2.220 at 500.205 ms, and the whole sequence gives 1.108.

**Describe the solution you'd like**

Add `safe_gwf_to_pns_chunk(gwf, dt, hw, state=None)` to `safe_pns_prediction.py`. It
computes the model on one chunk of the waveform with `scipy.signal.lfilter(b, a, x,
zi=zi)`. It returns the PNS of the chunk and the state for the next chunk: the last
gradient sample, and the final state of each of the nine filters. This needs the
recursion of #XXX (compute the SAFE low-pass filter in calculate_pns as a recursion).

Then `calc_pns` computes the model on chunks of 30,000 samples (0.3 s on the 10 µs
raster), and writes each chunk into the arrays that it returns:

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
    pns_chunk, state = safe_gwf_to_pns_chunk(gw / obj.system.gamma, obj.grad_raster_time, hardware, state)
    pns_comp[start:stop] = 0.01 * pns_chunk
    pns_norm[start:stop] = np.sqrt((pns_comp[start:stop] ** 2).sum(axis=1))
```

The result is the same as for the whole sequence, bit for bit. The zero padding before
the sequence is the same as a zero initial state of the filters, and `calc_pns` removes
the padding after the sequence from its result. The tests compare the chunked result
with the whole-sequence computation for several sequences, with and without
`time_range`, and with chunk sizes that put the chunk ends on gradient ramps.

The peak memory is the returned arrays and one chunk: 0.26 GB instead of 1.02 GB for the
60 s sequence. The time does not change: about 0.6 s for the 60 s sequence on an Apple
M1 Max, with and without the chunks. The arguments and the results of `calculate_pns`
do not change. `safe_gwf_to_pns` and `safe_pns_model` stay for other callers.

The size of the chunks sets the balance between memory and time. For the 60 s sequence
on an Apple M1 Max (the best of 3 runs, in one process after a first call):

| Chunk (samples) | Chunks | Time | Peak memory |
|---|---|---|---|
| 1,000 | 6,000 | 1.01 s | 0.248 GB |
| 3,000 | 2,000 | 0.71 s | 0.248 GB |
| 10,000 | 600 | 0.57 s | 0.249 GB |
| 30,000 | 200 | 0.53 s | 0.250 GB |
| 100,000 | 60 | 0.53 s | 0.261 GB |
| 1,000,000 | 6 | 0.54 s | 0.426 GB |
| 5,999,103 (one chunk) | 1 | 0.53 s | 1.202 GB |

Each chunk costs about 80 µs (the loop, the sampling of the gradients and nine `lfilter`
calls), and each sample about 87 ns. So smaller chunks add time, about 9 % at 10,000
samples. They do not decrease the memory below the returned arrays (0.24 GB) and about
8 MB of other data. Chunks of 30,000 samples are within 2 MB of that minimum, at the
time of one chunk.

**Describe alternatives you've considered**

- Pieces with `time_range`, by the user: each piece starts the filters from zero, and
  the gradient at the start of the piece counts as a step from zero. In the example,
  this gives 2.220 instead of 1.108, a false failure. Pieces that overlap by a few
  times the longest time constant are close, but not exact.
- `float32` arrays: half of the memory, but it still increases with the duration, and
  the values change.
- An argument that returns only `ok` and the peak of `pns_norm`: with chunks, the
  memory would then not depend on the duration. This changes what `calculate_pns`
  returns, so it could be a later option.

**Additional context**

This improvement was identified and test case generated by Claude, but I've reviewed the
code myself and the change appears to be correct based on my review.

The results are with the change of #XXX, so that the example runs in seconds. The
memory is the same without it.

The open PR #385 adds a `model` argument to `calc_pns`. The chunks would apply to its
`'safe'` model.

Versions: macOS 26.6.2, Python 3.12.14, NumPy 2.5.3, SciPy 1.18.1; pypulseq master at
[f2c582b](https://github.com/pulseq/pypulseq/commit/f2c582bae13145b8ac71958726bc8b5a14bd1cfd)
(2026-08-28).

I am happy to open a PR with this change and its tests, or two PRs: one for
`safe_gwf_to_pns_chunk`, and one for `calc_pns`. Are there any concerns about the
suggested change, or about the size of the chunks?
