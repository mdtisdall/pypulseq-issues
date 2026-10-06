# The [SIGNATURE] fields of a Sequence keep the hash of a file after the object changes:
# after add_block, and after read() of a file with no [SIGNATURE] section into an object
# that read a signed file before.

import os
import re
import tempfile

import pypulseq as pp


def make_seq(area):
    seq = pp.Sequence()
    seq.add_block(pp.make_trapezoid('x', area=area, duration=2e-3))
    return seq


fd, signed_fn = tempfile.mkstemp(suffix='.seq')
os.close(fd)
fd, unsigned_fn = tempfile.mkstemp(suffix='.seq')
os.close(fd)

make_seq(1000).write(signed_fn)
make_seq(1500).write(unsigned_fn)
# The second file without its [SIGNATURE] section.
with open(unsigned_fn) as f:
    text = f.read()
with open(unsigned_fn, 'w') as f:
    f.write(re.sub(r'\n\[SIGNATURE\].*', '\n', text, flags=re.DOTALL))

seq = pp.Sequence()
seq.read(signed_fn)
print(f"after read of the signed file:     signature_value = '{seq.signature_value}'")

seq.add_block(pp.make_delay(1e-3))
print(f"after add_block:                   signature_value = '{seq.signature_value}'")

seq.read(unsigned_fn)
print(f"after read of the unsigned file:   signature_value = '{seq.signature_value}'")

fresh = pp.Sequence()
fresh.read(unsigned_fn)
print(f"unsigned file into a new Sequence: signature_value = '{fresh.signature_value}'")

os.remove(signed_fn)
os.remove(unsigned_fn)
