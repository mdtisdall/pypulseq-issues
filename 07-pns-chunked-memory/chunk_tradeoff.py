"""Time and peak memory of calculate_pns for different chunk sizes, on this computer.

Needs pypulseq from the branch pns-chunked (calc_pns with _PNS_CHUNK_SAMPLES). For each
chunk size, the time is the best of 3 runs and the peak memory is from a separate run with
tracemalloc. A linear fit of the time to the number of chunks gives the cost of one chunk
and of one sample. Their ratio is the chunk size below which the chunks add much time."""

import importlib
import platform
import subprocess
import sys
import time
import tracemalloc

import numpy as np
import pypulseq as pp
import scipy
from pypulseq.utils.safe_pns_prediction import safe_example_hw

calc_pns_module = importlib.import_module('pypulseq.Sequence.calc_pns')
if not hasattr(calc_pns_module, '_PNS_CHUNK_SAMPLES'):
    sys.exit('This pypulseq has no _PNS_CHUNK_SAMPLES. Install pypulseq from the branch pns-chunked.')


def cpu_name():
    if sys.platform == 'darwin':
        return subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip()
    if sys.platform.startswith('linux'):
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('model name'):
                    return line.split(':', 1)[1].strip()
    return platform.processor()


print(f'CPU: {cpu_name()} ({platform.machine()})')
print(f'OS: {platform.platform()}')
print(f'Python {platform.python_version()}, NumPy {np.__version__}, SciPy {scipy.__version__}')
print(f'pypulseq: {pp.__file__}, default chunk {calc_pns_module._PNS_CHUNK_SAMPLES:,} samples')

# 60 s: a trapezoid on each axis every 10 ms.
system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
seq = pp.Sequence(system)
for _ in range(6000):
    seq.add_block(*grads, delay)
hw = safe_example_hw()

# A first call, so that all rows use the same cached gradient data.
_, reference, _, t = seq.calculate_pns(hw, do_plots=False)
n = t.size

print(f'\n60 s sequence, {n:,} samples')
print(f'{"chunk":>10} {"chunks":>7} {"time s":>7} {"peak GB":>8} {"above returned MB":>18} {"same result":>12}')
rows = []
for chunk in [300, 1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000, n]:
    calc_pns_module._PNS_CHUNK_SAMPLES = chunk
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        seq.calculate_pns(hw, do_plots=False)
        times.append(time.perf_counter() - t0)
    tracemalloc.start()
    _, pns_norm, pns_comp, t = seq.calculate_pns(hw, do_plots=False)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    returned = pns_norm.nbytes + pns_comp.nbytes + t.nbytes
    chunks = -(-n // chunk)
    same = np.array_equal(pns_norm, reference)
    rows.append((chunks, min(times)))
    print(f'{chunk:>10,} {chunks:>7,} {min(times):>7.3f} {peak / 1e9:>8.3f} {(peak - returned) / 1e6:>18.1f} {same!s:>12}')

per_chunk, total_per_sample = np.polyfit([r[0] for r in rows], [r[1] for r in rows], 1)
per_sample = total_per_sample / n
print(f'\nFit: {per_chunk * 1e6:.0f} us for each chunk, {per_sample * 1e9:.0f} ns for each sample.')
print(f'Ratio: {per_chunk / per_sample:,.0f} samples. Chunks of this size double the time.')
