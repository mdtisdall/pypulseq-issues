"""write() and read() fail in Sequence.remove_duplicates for an oversampled arbitrary gradient."""

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
