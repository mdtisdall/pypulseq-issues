# `Sequence` keeps the `[SIGNATURE]` hash of a file after `add_block` and after `read` of an unsigned file

**Describe the bug**

The three signature fields of a `Sequence` are set in `__init__`, by `write` and by
`read`:

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/sequence.py#L92-L94

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/sequence.py#L1866-L1868

https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/read_seq.py#L94-L100

Nothing else changes them. So the hash of a file stays on the object after the object no
longer holds that file:

1. After `add_block` (or `set_block`), the object has blocks that are not in the file, and
   `signature_value` is still the hash of the file.
2. `read` makes new event libraries and a new block table, but it does not reset the
   signature fields:

   https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/read_seq.py#L47-L64

   So when a file with no `[SIGNATURE]` section is read into an object that read a signed
   file before, `signature_value` is the hash of the earlier file.

A caller that uses `signature_value` to know whether a sequence came from a signed file,
or to identify the file, gets a wrong answer in both cases.

pypulseq follows MATLAB Pulseq here, which has the same behaviour in `read` and `setBlock`
(its `readBinary` already resets the three fields). I reported that as pulseq/pulseq#XXX.

**To Reproduce**

```python
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
```

Output (pypulseq master at `f2c582b`):

```
after read of the signed file:     signature_value = 'a4e2bcddd205a1b51ae6dc2bceae2f67'
after add_block:                   signature_value = 'a4e2bcddd205a1b51ae6dc2bceae2f67'
after read of the unsigned file:   signature_value = 'a4e2bcddd205a1b51ae6dc2bceae2f67'
unsigned file into a new Sequence: signature_value = ''
```

**Expected behavior**

- After `read`, the signature fields are those of the file that was read: empty for a file
  with no `[SIGNATURE]` section, as for a new `Sequence`.
- After `add_block` or `set_block`, the signature fields are empty, because the object no
  longer holds the file that the hash is of. A new hash comes from `write`.

**Suggested fix**

At the start of `read`, next to the new event libraries, set `signature_type`,
`signature_file` and `signature_value` to `''`, as `__init__` does. In `add_block` and
`set_block`, set the same three fields to `''`.
