"""The area of an oversampled arbitrary gradient counts only the raster-centre samples.

pypulseq version of repro.m: make_arbitrary_grad and get_block compute the area with the
same formula as MATLAB Pulseq.
"""

import numpy as np
import pypulseq as pp

system = pp.Opts(max_slew=100, slew_unit='T/m/s')
dt = system.grad_raster_time  # 10 us

step = 0.9 * system.max_slew * dt / 2  # 90 % of max_slew over half a raster
waveform = step * np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5, 4, 3, 2, 1])

# the triangle starts and ends at 0
g = pp.make_arbitrary_grad('x', waveform, first=0, last=0, oversampling=True, system=system)

# the gradient at the raster edges, t = 0, dt, ..., shape_dur
e = np.concatenate([[g.first], g.waveform[1::2], [g.last]])

area_centre = g.area  # sum(waveform[0::2]) * dt
area_edge = dt * (e.sum() - (e[0] + e[-1]) / 2)  # piecewise linear through the edge samples
area_all = np.trapezoid(  # piecewise linear through all samples
    np.concatenate([[g.first], g.waveform, [g.last]]), np.concatenate([[0], g.tt, [g.shape_dur]])
)

print(f'area_centre: {area_centre:.4f}')
print(f'area_edge:   {area_edge:.4f}')
print(f'area_all:    {area_all:.4f}')
