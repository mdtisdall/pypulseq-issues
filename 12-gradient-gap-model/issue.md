# `waveforms()` draws a line across a gap between two gradient events, where MATLAB Pulseq ramps to 0

**Describe the bug**

`Sequence.waveforms()` joins the points of all the gradient events of an axis, in play
order, and does nothing else at a gap between two events:

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/sequence.py#L1745-L1754

`get_gradients()` makes the piecewise-linear gradients from these points, so between two
events it gives the straight line from the last point of one event to the first point of
the next. `calculate_pns` and `calculate_gradient_spectrum` use `get_gradients()`:

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/calc_pns.py#L47

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/calc_grad_spectrum.py#L76

When both ends are 0 (a trapezoid, and most shapes), the line is 0 and there is no
problem. When an event starts or ends at a value that is not 0 next to a gap, the line is
not 0. That happens in two cases:

1. A gradient that starts at a value that is not 0, after a delay.
2. A gradient that ends at a value that is not 0, before the end of its block.

`add_block` refuses both cases, but only above `max_slew * grad_raster_time`:

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/block.py#L223-L225

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/block.py#L289-L294

The specification gives the same two rules, with no limit ("Gradients that start at
non-zero values must be aligned to the beginning of the block, meaning that the start
delay of such gradients must be 0", and a gradient that ends at a non-zero value must be
aligned to the end of the block):

https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/doc/specification.tex#L420

These rules have a purpose only when the gradient is 0 during a delay and after the end of
an event. Below the limit, `add_block` accepts the two cases, and `waveforms()` then gives
a line that is not 0 across the gap.

MATLAB Pulseq has the same limit in `setBlock`:

https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/matlab/+mr/@Sequence/Sequence.m#L1113-L1131

But its `waveforms_and_times()` does not draw a line across a gap of more than one gradient
raster time. It adds a ramp to 0 in half a raster time after the earlier event, and a ramp
from 0 in half a raster time before the later event, with a warning. A value of 1e-6 Hz/m
or less is set to 0 with no warning:

https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/matlab/+mr/@Sequence/Sequence.m#L2113-L2135

Thus, for the same sequence, the gradients of pypulseq and of MATLAB Pulseq are different
in the gap, and so are the values that `calculate_pns` and `calculate_gradient_spectrum`
calculate from them. In the example below, pypulseq has the constant value `a` for 100 us,
and MATLAB Pulseq has 0. Each step is at most `max_slew * grad_raster_time`, so the slew
of a MATLAB ramp of half a raster time is up to `2 * max_slew`.

**To Reproduce**

```python
import numpy as np
import pypulseq as pp

system = pp.Opts()
a = 0.5 * system.max_slew * system.grad_raster_time  # below the limit of the add_block checks


def ramp_and_hold():
    # 0 to a in 100 us, then a to 200 us: it ends at a.
    return pp.make_extended_trapezoid('x', times=[0, 100e-6, 200e-6], amplitudes=[0, a, a], system=system)


def ramp_down(delay):
    # a to 0 in 100 us, after `delay`: it starts at a.
    g = pp.make_extended_trapezoid('x', times=[0, 100e-6], amplitudes=[a, 0], system=system)
    g.delay = delay
    return g


# Case 1: the second gradient starts at a after a delay of 100 us.
delayed = pp.Sequence(system)
delayed.add_block(ramp_and_hold())
delayed.add_block(ramp_down(delay=100e-6))

# Case 2: the first gradient ends at a 100 us before the end of its block.
early_end = pp.Sequence(system)
early_end.add_block(ramp_and_hold(), pp.make_delay(300e-6))
early_end.add_block(ramp_down(delay=0))

for name, seq, gap in (('delay', delayed, (200e-6, 300e-6)), ('early end', early_end, (200e-6, 300e-6))):
    t, g = seq.waveforms()[0]
    gx = seq.get_gradients()[0]
    inside = np.array([205e-6, 250e-6, 295e-6])
    print(f'{name}: add_block accepted it; a = {a:.1f} Hz/m; the gap is {gap[0] * 1e6:.0f} to {gap[1] * 1e6:.0f} us')
    print(f'  waveforms() gx times (us): {np.round(t * 1e6, 3).tolist()}')
    print(f'  waveforms() gx values:     {np.round(g, 1).tolist()}')
    print(f'  get_gradients() at 205, 250, 295 us: {np.round(gx(inside), 1).tolist()}')
```

Output (pypulseq master at `f2c582b`):

```
delay: add_block accepted it; a = 36189.6 Hz/m; the gap is 200 to 300 us
  waveforms() gx times (us): [0.0, 100.0, 200.0, 300.0, 400.0]
  waveforms() gx values:     [0.0, 36189.6, 36189.6, 36189.6, 0.0]
  get_gradients() at 205, 250, 295 us: [36189.6, 36189.6, 36189.6]
early end: add_block accepted it; a = 36189.6 Hz/m; the gap is 200 to 300 us
  waveforms() gx times (us): [0.0, 100.0, 200.0, 300.0, 400.0]
  waveforms() gx values:     [0.0, 36189.6, 36189.6, 36189.6, 0.0]
  get_gradients() at 205, 250, 295 us: [36189.6, 36189.6, 36189.6]
```

The same sequences in MATLAB Pulseq at `c746912` (`repro.m` of this folder, in GNU Octave),
without the two warnings of each sequence ("forcing ramp-down from a non-zero gradient
sample on axis 1 at t=200 us", and "forcing ramp-up ... at t=300 us"):

```
delay: addBlock accepted it; a = 36189.6 Hz/m; the gap is 200 to 300 us
  waveforms_and_times() gx times (us): [0 100 200 205 295 300 400]
  waveforms_and_times() gx values:     [0 36189.6 36189.6 0 0 36189.6 0]
  values at 205, 250, 295 us:           [0 0 0]
early end: addBlock accepted it; a = 36189.6 Hz/m; the gap is 200 to 300 us
  waveforms_and_times() gx times (us): [0 100 200 205 295 300 400]
  waveforms_and_times() gx values:     [0 36189.6 36189.6 0 0 36189.6 0]
  values at 205, 250, 295 us:           [0 0 0]
```

**Expected behavior**

`waveforms()` gives the gradients of MATLAB Pulseq: across a gap of more than one gradient
raster time, a ramp to 0 in half a raster time after the earlier event and a ramp from 0
in half a raster time before the later event, with the same warning above 1e-6 Hz/m. Then
`get_gradients()`, `calculate_pns` and `calculate_gradient_spectrum` agree with MATLAB
Pulseq, and with the rules of `add_block` and of the specification.

**Suggested fix**

In `waveforms()`, before the pieces of an axis are joined, port the gap rule of
`waveforms_and_times()` of MATLAB Pulseq (the lines above): for each pair of consecutive
pieces with a gap of more than `grad_raster_time`, add the point
`(last time + grad_raster_time / 2, 0)` after the earlier piece when its last value is
above 1e-6 Hz/m (else set that value to 0), and the point
`(first time - grad_raster_time / 2, 0)` before the later piece when its first value is
above 1e-6 Hz/m (else set that value to 0).

A separate question, for both toolboxes: should `add_block` (`setBlock`) refuse these two
cases for any value that is not 0, as the specification says, and not only above
`max_slew * grad_raster_time`?
