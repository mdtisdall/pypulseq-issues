% The gradient between two gradient events that are more than one gradient raster
% apart, when an event starts or ends at a non-zero value below the setBlock limit.

sys = mr.opts();
a = 0.5 * sys.maxSlew * sys.gradRasterTime;  % below the limit of the setBlock checks

ramp_and_hold = mr.makeExtendedTrapezoid('x', 'times', [0 100e-6 200e-6], 'amplitudes', [0 a a], 'system', sys);
ramp_down = mr.makeExtendedTrapezoid('x', 'times', [0 100e-6], 'amplitudes', [a 0], 'system', sys);
ramp_down_delayed = ramp_down;
ramp_down_delayed.delay = 100e-6;

% Case 1: the second gradient starts at a after a delay of 100 us.
delayed = mr.Sequence(sys);
delayed.addBlock(ramp_and_hold);
delayed.addBlock(ramp_down_delayed);

% Case 2: the first gradient ends at a 100 us before the end of its block.
early_end = mr.Sequence(sys);
early_end.addBlock(ramp_and_hold, mr.makeDelay(300e-6));
early_end.addBlock(ramp_down);

names = {'delay', 'early end'};
seqs = {delayed, early_end};
for k = 1:2
    w = seqs{k}.waveforms_and_times();
    gx = w{1};
    fprintf('%s: addBlock accepted it; a = %.1f Hz/m; the gap is 200 to 300 us\n', names{k}, a);
    fprintf('  waveforms_and_times() gx times (us): %s\n', mat2str(round(gx(1, :) * 1e9) / 1e3));
    fprintf('  waveforms_and_times() gx values:     %s\n', mat2str(round(gx(2, :) * 10) / 10));
    fprintf('  values at 205, 250, 295 us:           %s\n', ...
        mat2str(round(interp1(gx(1, :), gx(2, :), [205e-6 250e-6 295e-6], 'linear', 0) * 10) / 10));
end
