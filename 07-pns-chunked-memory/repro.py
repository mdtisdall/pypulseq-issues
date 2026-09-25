"""calculate_pns keeps arrays of the whole sequence: its peak memory is about four times
the arrays it returns. Pieces with time_range are not a workaround: each piece starts the
filters from zero, and the gradient at its start counts as a step from zero."""

import tracemalloc

import numpy as np
import pypulseq as pp
from pypulseq.utils.safe_pns_prediction import safe_example_hw

system = pp.Opts(max_grad=28, grad_unit='mT/m', max_slew=150, slew_unit='T/m/s')
grads = [pp.make_trapezoid(channel, area=1000, system=system) for channel in 'xyz']
delay = pp.make_delay(10e-3)
hw = safe_example_hw()


def make_seq(duration):  # a trapezoid on each axis every 10 ms
    seq = pp.Sequence(system)
    for _ in range(round(duration / 10e-3)):
        seq.add_block(*grads, delay)
    return seq


# Peak memory of calculate_pns, and the size of the arrays that it returns.
for duration in (15, 30, 60, 120):
    seq = make_seq(duration)
    tracemalloc.start()
    ok, pns_norm, pns_comp, t = seq.calculate_pns(hw, do_plots=False)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    returned = pns_norm.nbytes + pns_comp.nbytes + t.nbytes
    print(f'{duration} s, {t.size} samples: peak {peak / 1e9:.2f} GB, returned {returned / 1e9:.2f} GB')

# A piece that starts on the flat top of the trapezoids at 0.5 s.
seq = make_seq(1)
_, pns_norm, _, t = seq.calculate_pns(hw, do_plots=False)
_, piece, _, t_piece = seq.calculate_pns(hw, do_plots=False, time_range=[0.5002, 1.0])
i = np.searchsorted(t, t_piece[0])
print(f'at {t_piece[0] * 1e3:.3f} ms: {piece[0]:.3f} from the piece, {pns_norm[i]:.3f} from the whole sequence')
