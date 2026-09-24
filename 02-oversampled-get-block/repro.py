"""get_block returns an oversampled arbitrary gradient with twice its shape_dur."""

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
print('make_arbitrary_grad shape_dur:', g.shape_dur)  # 9e-05: (17 + 1) * dt / 2
print('block duration:               ', seq.block_durations[1])  # 9e-05
print('get_block shape_dur:          ', seq.get_block(1).gx.shape_dur)  # expected 9e-05

ok, errors = seq.check_timing()
print('check_timing:', ok, [(e.error_type, e.value, e.duration) for e in errors])  # expected True []
