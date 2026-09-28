"""add_block stores an RF event with use='other' as undefined ('u')."""

import os
import tempfile

import numpy as np
import pypulseq as pp

system = pp.Opts()

# 'other' is one of the supported uses, so make_block_pulse accepts it.
print('supported uses:', pp.supported_labels_rf_use.get_supported_rf_uses())
rf = pp.make_block_pulse(np.pi / 2, duration=1e-3, use='other', system=system)
print('event use:', rf.use)  # other

seq = pp.Sequence(system)
seq.add_block(rf)

# The RF library keeps the use as one letter.
print('library letter:', seq.rf_library.type[1], '(expected: o)')
print('get_block use:', seq.get_block(1).rf.use, '(expected: other)')

# The letter is written to the .seq file, so the use is lost there too.
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, 'other.seq')
    seq.write(path)
    read_back = pp.Sequence(system)
    read_back.read(path)
    print('after write and read:', read_back.get_block(1).rf.use, '(expected: other)')
