"""waveforms() leaves out the first and last points of an oversampled arbitrary gradient."""

import numpy as np
import pypulseq as pp

system = pp.Opts(max_slew=100, slew_unit='T/m/s')
dt = system.grad_raster_time  # 10 us

step = 0.9 * system.max_slew * dt / 2  # 90 % of max_slew over half a raster
waveform = step * np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1])

# the triangle starts and ends at 0
g = pp.make_arbitrary_grad('x', waveform, first=0, last=0, oversampling=True, system=system)

seq = pp.Sequence(system)
seq.add_block(g)

# The x gradient as (time, amplitude) points.
t, amp = seq.waveforms()[0]
print('number of points:', len(t))  # expected 19: first, 17 samples, last
print('first point:     ', t[0], amp[0])  # expected 0.0 0.0: `first` at t = 0
print('last point:      ', t[-1], amp[-1])  # expected 9e-05 0.0: `last` at t = shape_dur
