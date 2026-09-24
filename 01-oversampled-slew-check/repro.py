"""make_arbitrary_grad(oversampling=True) checks the slew rate 4x too leniently."""

import numpy as np
import pypulseq as pp

system = pp.Opts(max_slew=100, slew_unit='T/m/s')
dt = system.grad_raster_time  # 10 us

# oversampling=True: a sample every dt/2 (oversampling by a factor of 2), an odd
# number of samples. A triangle that rises by 3.5 * max_slew * dt/2 per sample, so
# every segment is at 350 % of max_slew.
step = 3.5 * system.max_slew * dt / 2
waveform = step * np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1])

# the triangle starts and ends at 0
g = pp.make_arbitrary_grad('x', waveform, first=0, last=0, oversampling=True, system=system)
print('350 %: accepted (expected: ValueError, slew rate violation)')

# The slope of each segment of the event, from its own tt, waveform, first and last.
t = np.concatenate([[0], g.tt, [g.shape_dur]])
amp = np.concatenate([[g.first], g.waveform, [g.last]])
print(f'largest segment slope: {np.max(np.abs(np.diff(amp) / np.diff(t))) / system.max_slew:.2f} x max_slew')

# The check only fails above 4 x max_slew, and then reports a quarter of the slope.
try:
    pp.make_arbitrary_grad('x', waveform * 4.1 / 3.5, first=0, last=0, oversampling=True, system=system)
except ValueError as err:
    print(f'410 %: {err}')
