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
