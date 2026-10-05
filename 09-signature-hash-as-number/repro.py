"""read() stores the [SIGNATURE] hash as a float when the hex digest looks like a number."""

import hashlib
import os
import tempfile

import pypulseq as pp

# About 1 in 850,000 MD5 hex digests parse as a float: 32 decimal digits, or decimal
# digits with one 'e' inside (for example '123e45...'). To get such a file without
# editing it by hand, search for a definition value that gives one. pypulseq writes the
# signature itself, so the hash is correct for the file.


def is_float(text):
    try:
        float(text)
    except ValueError:
        return False
    return True


seq = pp.Sequence()
seq.add_block(pp.make_delay(1e-3))

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, 'signed.seq')

    # The text of the file up to [SIGNATURE] is the text of a write without a signature.
    seq.set_definition('Nonce', 'n-PLACEHOLDER')
    seq.write(path, create_signature=False)
    with open(path) as f:
        template = f.read()
    nonce = next(
        f'n-{k}'
        for k in range(100_000_000)
        if is_float(hashlib.md5(template.replace('n-PLACEHOLDER', f'n-{k}').encode()).hexdigest())
    )

    seq.set_definition('Nonce', nonce)
    written = seq.write(path)  # pypulseq writes the [SIGNATURE] section
    print('nonce:', nonce)
    print('written hash:', repr(written))
    with open(path) as f:
        print('file says:   ', [line for line in f if line.startswith('Hash ')][0].strip())

    read_back = pp.Sequence()
    read_back.read(path)
    print('read hash:   ', repr(read_back.signature_value), f'({type(read_back.signature_value).__name__})')
    print('equal:', read_back.signature_value == written, '(expected: True)')
