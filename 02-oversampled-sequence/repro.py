"""An oversampled arbitrary gradient does not survive a Sequence: get_block, waveforms,
write and read."""

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
