# signature_file is 'text' after write, but 'Text' after read of the same file.
# The same example as repro.m of 10a, in pypulseq.

import os
import tempfile

import pypulseq as pp

seq = pp.Sequence()
seq.add_block(pp.make_delay(1e-3))

fd, fn = tempfile.mkstemp(suffix='.seq')
os.close(fd)
seq.write(fn)
print(f"after write: signature_file = '{seq.signature_file}'")

seq2 = pp.Sequence()
seq2.read(fn)
print(f"after read:  signature_file = '{seq2.signature_file}'")
os.remove(fn)

print(
    f"signature_file == 'text': {seq.signature_file == 'text'} after write, "
    f"{seq2.signature_file == 'text'} after read"
)
