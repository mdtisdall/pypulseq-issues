"""calculate_pns is slow for long sequences: safe_tau_lowpass convolves with a kernel of
up to about 11,000 taps. The same filter is a first-order recursion (scipy.signal.lfilter)."""

import resource
import sys
import time

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
t2 = time.perf_counter()
difference = np.max(np.abs(y_recursion - y_pypulseq)) / np.max(np.abs(y_pypulseq))
print(f'safe_tau_lowpass: {t1 - t0:.3f} s')
print(f'lfilter:          {t2 - t1:.3f} s')
print(f'largest difference / peak: {difference:.1e}')

# calculate_pns for a 60 s sequence: a trapezoid on each axis every 10 ms.
system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
seq = pp.Sequence(system)
for _ in range(6000):
    seq.add_block(*grads, delay)

t0 = time.perf_counter()
ok, pns_norm, _, _ = seq.calculate_pns(safe_example_hw(), do_plots=False)
t1 = time.perf_counter()
peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
peak_rss *= 1 if sys.platform == 'darwin' else 1024  # bytes on macOS, KiB on Linux
print(f'calculate_pns, {seq.duration()[0]:.0f} s sequence: {t1 - t0:.1f} s, peak {pns_norm.max():.4f}')
print(f'peak RSS of the process: {peak_rss / 1e9:.2f} GB')
