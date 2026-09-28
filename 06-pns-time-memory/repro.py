"""calculate_pns is slow and uses much memory for long sequences. safe_tau_lowpass convolves
with a kernel of up to about 11,000 taps, and calc_pns keeps arrays of the whole sequence."""

import time
import tracemalloc

import numpy as np
import pypulseq as pp
from pypulseq.utils.safe_pns_prediction import safe_example_hw, safe_tau_lowpass
from scipy.signal import lfilter

# One filter, 20 s of samples on the 10 us raster, with the longest time constant of
# safe_example_hw(). safe_pns_model gives tau and dt to safe_tau_lowpass in ms.
dt, tau = 0.01, 3.0
alpha = dt / (tau + dt)
x = np.random.default_rng(0).normal(size=2_000_000)
t0 = time.perf_counter()
y_pypulseq = safe_tau_lowpass(x, tau, dt)
t1 = time.perf_counter()
y_recursion = lfilter([alpha], [1.0, alpha - 1.0], x)
difference = np.max(np.abs(y_recursion - y_pypulseq)) / np.max(np.abs(y_pypulseq))
print(f'safe_tau_lowpass: {t1 - t0:.3f} s, largest difference from the recursion / peak: {difference:.1e}')

# calculate_pns for a 60 s sequence: a trapezoid on each axis every 10 ms.
system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
hw = safe_example_hw()


def make_seq(duration):
    seq = pp.Sequence(system)
    for _ in range(round(duration / 10e-3)):
        seq.add_block(*grads, delay)
    return seq


seq = make_seq(60)
t0 = time.perf_counter()
ok, pns_norm, pns_comp, t = seq.calculate_pns(hw, do_plots=False)
t1 = time.perf_counter()
tracemalloc.start()
seq.calculate_pns(hw, do_plots=False)
peak = tracemalloc.get_traced_memory()[1]
tracemalloc.stop()
returned = pns_norm.nbytes + pns_comp.nbytes + t.nbytes
print(f'calculate_pns, 60 s: {t1 - t0:.1f} s, peak of pns_norm {pns_norm.max():.4f}')
print(f'peak memory {peak / 1e9:.2f} GB, returned arrays {returned / 1e9:.2f} GB')

# A piece of a 1 s sequence with time_range, from the flat top of the trapezoids at 0.5 s.
seq = make_seq(1)
_, pns_norm, _, t = seq.calculate_pns(hw, do_plots=False)
_, piece, _, t_piece = seq.calculate_pns(hw, do_plots=False, time_range=[0.5002, 1.0])
i = np.searchsorted(t, t_piece[0])
print(f'at {t_piece[0] * 1e3:.3f} ms: {piece[0]:.3f} from the piece, {pns_norm[i]:.3f} from the whole sequence')
