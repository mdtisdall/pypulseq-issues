% The area of an oversampled arbitrary gradient counts only the raster-centre samples.

sys = mr.opts('MaxSlew', 100, 'SlewUnit', 'T/m/s');
dt = sys.gradRasterTime;  % 10 us

step = 0.9 * sys.maxSlew * dt / 2;  % 90 % of maxSlew over half a raster
w = step * [1:9, 8:-1:1];           % 17 samples: centre, edge, centre, ..., centre

% the triangle starts and ends at 0
g = mr.makeArbitraryGrad('x', w, sys, 'oversampling', true, 'first', 0, 'last', 0);

w_all = g.waveform(:)';
e = [g.first, w_all(2:2:end), g.last];  % the gradient at the raster edges, t = 0, dt, ..., shape_dur

area_centre = g.area                                                     % sum(w_all(1:2:end)) * dt
area_edge = dt * (sum(e) - (e(1) + e(end)) / 2)                          % piecewise linear through the edge samples
area_all = trapz([0, g.tt(:)', g.shape_dur], [g.first, w_all, g.last])  % piecewise linear through all samples
