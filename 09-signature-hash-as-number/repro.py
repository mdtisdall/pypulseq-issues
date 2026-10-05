"""read() stores the [SIGNATURE] hash as a float when the hex digest looks like a number."""

import os
import tempfile

import pypulseq as pp

# About 1 in 850,000 MD5 hex digests parse as a float: 32 decimal digits, or decimal
# digits with one 'e' inside. The value of 'Nonce' was found by a search over 'n-0',
# 'n-1', ... for a file whose digest is one of these. pypulseq writes the signature
# itself, so the hash is correct for the file. The value works while the text that
# write() gives does not change (pypulseq 1.5.0.post1 and master f2c582b).
seq = pp.Sequence()
seq.add_block(pp.make_delay(1e-3))
seq.set_definition('Nonce', 'n-14723')

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, 'signed.seq')
    written = seq.write(path)
    read_back = pp.Sequence()
    read_back.read(path)

print('written hash:', repr(written))
print('read hash:   ', repr(read_back.signature_value), f'({type(read_back.signature_value).__name__})')
print('equal:', read_back.signature_value == written, '(expected: True)')
