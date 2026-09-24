# Oversampled arbitrary gradients break in a Sequence: get_block, check_timing, waveforms, write and read

## Summary

`make_arbitrary_grad(..., oversampling=True)` makes a correct event. After `add_block`,
the `Sequence` handles it wrongly in three places:

1. `get_block` returns the event with twice its `shape_dur`. So `check_timing` reports
   `BLOCK_DURATION_MISMATCH` for a valid block, and `write()` warns about a timing error.
2. `waveforms()` leaves out the event's `first` and `last` points. `get_gradients`,
   `calculate_pns` and the k-space calculation all use `waveforms()`.
3. `write()` and `read()` fail with `KeyError: -1` in `remove_duplicates`, with their
   default `remove_duplicates=True`. With `remove_duplicates=False`, `write()` works, and
   MATLAB Pulseq reads the file correctly.

These are three separate causes, each with a one-line or short fix (below). They could be
split into separate issues or PRs.

## Versions

- pypulseq 1.5.0.post1, and master at f2c582b (2026-08-28): same results.
- For comparison: MATLAB Pulseq at c746912 (2026-09-17), run in GNU Octave 11.3.0.

## Minimal example

"Oversampled" here means `oversampling=True`. That is oversampling by a factor of 2, the
only factor that pypulseq and MATLAB Pulseq support: one sample every
`grad_raster_time / 2`, at `t = k * grad_raster_time / 2` for `k = 1 ... n`, with `n` odd,
`first` at `t = 0` and `last` at `t = (n + 1) * grad_raster_time / 2`. `make_arbitrary_grad`
sets `shape_dur = (n + 1) * grad_raster_time / 2`.

The example is a half sine of 21 samples, 0.47 mT/m high, far inside the limits, made
with `make_arbitrary_grad`. So `shape_dur` is 110 µs.

```python
import numpy as np
import pypulseq as pp

system = pp.Opts()
n = 21  # oversampling=True needs an odd number of samples, one every grad_raster_time/2
waveform = 20e3 * np.sin(np.pi * np.arange(1, n + 1) / (n + 1))  # Hz/m, well within limits
g = pp.make_arbitrary_grad('x', waveform, first=0, last=0, oversampling=True, system=system)

seq = pp.Sequence(system)
seq.add_block(g)
print('make_arbitrary_grad shape_dur:', g.shape_dur)  # 1.1e-04: (n + 1) * grad_raster_time / 2
print('block duration:               ', seq.block_durations[1])  # 1.1e-04

# 1. get_block gives twice the shape_dur.
print('get_block shape_dur:          ', seq.get_block(1).gx.shape_dur)  # expected 1.1e-04

# 2. waveforms() leaves out `first` at t = 0 and `last` at t = shape_dur.
t = seq.waveforms()[0][0]
print('waveforms() time range:       ', t[0], t[-1])  # expected 0.0 1.1e-04

# 3. write() and read() fail in Sequence.remove_duplicates.
try:
    seq.write('oversampled.seq')
    print('write(): ok')
except KeyError as err:
    print('write():', repr(err))
seq.write('oversampled.seq', remove_duplicates=False)  # writes time shape ID -1
try:
    pp.Sequence(system).read('oversampled.seq')
    print('read(): ok')
except KeyError as err:
    print('read(): ', repr(err))
```

Output (1.5.0.post1 and master):

```
make_arbitrary_grad shape_dur: 0.00011
block duration:                0.00011
get_block shape_dur:           0.00022
waveforms() time range:        5e-06 0.000105
write(): KeyError(-1)
read():  KeyError(np.float64(-1.0))
```

Both `write()` calls also warn `UserWarning: write(): 1 timing errors found in the
sequence`: `seq.check_timing()` gives `BLOCK_DURATION_MISMATCH` for block 1, 220 µs of
content in a 110 µs block.

Expected: `get_block shape_dur` 0.00011, `waveforms()` time range 0.0 to 0.00011, and
`write()` and `read()` without errors.

## Causes and suggested fixes

### 1. `get_block`: `shape_dur` without the factor 1/2

[`Sequence/block.py`, lines 419-428](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/block.py#L419-L428),
the branch for time shape ID -1 (oversampling by a factor of 2):

```python
                    t_end = (len(g) + 1) * self.grad_raster_time
```

`make_arbitrary_grad` sets `(len(waveform) + 1) * 0.5 * system.grad_raster_time`, and
[MATLAB's `getBlock`](https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/matlab/%2Bmr/%40Sequence/Sequence.m#L1384-L1390)
has `t_end=(length(g)+1)/2*obj.gradRasterTime`.

```diff
-                    t_end = (len(g) + 1) * self.grad_raster_time
+                    t_end = (len(g) + 1) * 0.5 * self.grad_raster_time
```

### 2. `waveforms()`: an oversampled gradient is treated as an extended trapezoid

[`Sequence/sequence.py`, lines 1644-1677](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/sequence.py#L1644-L1677):
a gradient whose `tt` is not at the raster centres `(k + 0.5) * grad_raster_time` goes to
the "Extended trapezoid" branch, which uses only `tt` and `waveform`. An extended
trapezoid has its first and last points in `tt`; an oversampled gradient does not, so
`first` (t = 0) and `last` (t = shape_dur) are lost. The next event's samples are then
joined to this event's last sample, not to `last`.
[MATLAB's `waveforms_and_times`](https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/matlab/%2Bmr/%40Sequence/Sequence.m#L2023-L2032)
has a separate case for it: a first sample on the half raster means an oversampled
gradient, and it adds `[0 tt shape_dur]` and `[first waveform last]`.

```diff
-                        else:  # Extended trapezoid
+                        elif abs(tt_rast[0] - 1) < eps:  # Oversampled arbitrary gradient (first sample at half raster)
+                            out_len[j] += len(grad.tt) + 2
+                            shape_pieces[j].append(
+                                np.array(
+                                    [
+                                        curr_dur + grad.delay + np.concatenate(([0], grad.tt, [grad.shape_dur])),
+                                        np.concatenate(([grad.first], grad.waveform, [grad.last])),
+                                    ]
+                                )
+                            )
+                        else:  # Extended trapezoid
```

(`tt_rast` is `grad.tt / grad_raster_time + 0.5`, so the first sample of an oversampled
gradient, at half a raster, gives `tt_rast[0] == 1`. An extended trapezoid starts at
`tt[0] == 0`.) This fix needs fix 1, because it uses `grad.shape_dur`.

### 3. `remove_duplicates`: no mapping for time shape ID -1

[`Sequence/sequence.py`, line 1199](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/sequence.py#L1195-L1201):

```python
                new_data = (*data[0:3], mapping[data[3]], mapping[data[4]], data[5])
```

`data[4]` is the time shape ID. 0 (the regular raster) and -1 (the half raster, set in
`register_grad_event` for an oversampled gradient) are flags, not shape IDs. The shape
library's mapping has `0: 0` but no `-1`, so `write()` (which calls
`remove_duplicates()` by default) raises `KeyError: -1`. `read()` calls
`remove_duplicates(in_place=True)`
([`read_seq.py`, line 444](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/read_seq.py#L444))
and raises `KeyError: -1.0` for the same reason.

```diff
-                new_data = (*data[0:3], mapping[data[3]], mapping[data[4]], data[5])
+                # Time shape IDs 0 (regular raster) and -1 (half raster) are flags, not shapes
+                time_id = data[4] if data[4] <= 0 else mapping[data[4]]
+                new_data = (*data[0:3], mapping[data[3]], time_id, data[5])
```

## Tested

On master (f2c582b) with the three fixes:

- The example prints `get_block shape_dur: 0.00011`, `waveforms() time range: 0.0 0.00011`,
  `write(): ok` and `read(): ok`, with no timing warning. `check_timing()` passes.
- A round trip (`write`, then `read`) gives back the same `tt`, `first`, `last` and
  `shape_dur`, and the waveform within the file's precision (relative error 5e-10).
- `pytest tests` (run serially): 1262 passed and 2 failed, the same as without the
  fixes. The 2 failures are `test_sigpy.py::test_slr` and `test_sms`, because sigpy is
  not installed. No test in `tests/` makes an oversampled gradient.

A regression test could be the example above: `get_block` `shape_dur`, `check_timing()`,
the `waveforms()` end points, and a `write` / `read` round trip.

Related: `make_arbitrary_grad(oversampling=True)` also checks the slew rate 4× too
leniently (separate issue).
