# read() stores the [SIGNATURE] hash as a float when the hex digest looks like a number

**Describe the bug**

`Sequence.read` reads the `[SIGNATURE]` section with `__read_definitions`, the reader of
`[DEFINITIONS]`. That function converts each value that `float()` accepts to a float. An
MD5 hex digest is text, but some digests are also valid floats: 32 decimal digits, or
decimal digits with one `e` inside (for example `9731349875117297474679317e925476`).
About 1 in 850,000 digests is one of these. For such a file, `seq.signature_value` is a
`numpy.float64`, not the hash: a rounded number, or `inf` when the exponent is large.
The hash text is lost, so the signature cannot be compared with the hash that `write`
returned, with the file, or with another file.

[`Sequence/read_seq.py`, lines 94-100](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/read_seq.py#L94-L100)
and
[lines 447-475](https://github.com/pulseq/pypulseq/blob/f2c582bae13145b8ac71958726bc8b5a14bd1cfd/src/pypulseq/Sequence/read_seq.py#L447-L475).

**To Reproduce**

The example does not edit a file by hand. It searches for a value of a definition that
gives a digest of this kind, and then `write` signs the file itself, so the hash is
correct for the file.

```python
import hashlib
import os
import tempfile

import pypulseq as pp


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
```

Output:

```
nonce: n-14723
written hash: '9731349875117297474679317e925476'
file says:    Hash 9731349875117297474679317e925476
read hash:    np.float64(inf) (float64)
equal: False (expected: True)
```

**Expected behavior**

`signature_value` is the text of the `Hash` line, `'9731349875117297474679317e925476'`,
for each digest. `signature_type` is the text of the `Type` line.

**Suggested fix**

Read the values of `[SIGNATURE]` as text. Add the argument `numeric=True` to
`__read_definitions`; the `[SIGNATURE]` branch gives `numeric=False`, and
`[DEFINITIONS]` does not change:

```diff
--- a/src/pypulseq/Sequence/read_seq.py
+++ b/src/pypulseq/Sequence/read_seq.py
@@ -92,7 +92,9 @@ def read(self, path: str, detect_rf_use: Union[bool, None] = None, remove_duplic
         elif section == '[SIGNATURE]':
-            temp_sign_defs = __read_definitions(input_file)
+            # The values are text: a hex digest can look like a number (for example
+            # '9731349875117297474679317e925476'), and a float loses it.
+            temp_sign_defs = __read_definitions(input_file, numeric=False)
             if 'Type' in temp_sign_defs:
@@ -444,7 +446,7 @@ def l2(s):
-def __read_definitions(input_file) -> Dict[str, str]:
+def __read_definitions(input_file, numeric: bool = True) -> Dict[str, str]:
@@ -452,6 +454,9 @@ def __read_definitions(input_file) -> Dict[str, str]:
     input_file : file object
         Sequence file.
+    numeric : bool, default=True
+        Convert the values that are numbers to floats. If False, each value is the text
+        after the key.
@@ -462,6 +467,10 @@ def __read_definitions(input_file) -> Dict[str, str]:
     while line != -1 and not (line == '' or line[0] == '#'):
         tok = line.split(' ')
+        if not numeric:
+            definitions[tok[0]] = line[len(tok[0]) + 1 :].strip()
+            line = __strip_line(input_file)
+            continue
         try:  # Try converting every element into a float
```

With this change, the example prints the hash as a `str` and `equal: True`.

**Desktop (please complete the following information):**
 - OS: macOS
 - OS Version: 26.6.2
 - `pypulseq` version: 1.5.0.post1, and master at f2c582b (2026-08-28). The code is the
   same in both, and the example gives the same output with both.
 - Python 3.12.14, NumPy 2.5.3.

**Additional context**

MATLAB Pulseq has the same pattern:
[`readDefinitions` in `read.m`](https://github.com/pulseq/pulseq/blob/c746912/matlab/%2Bmr/%40Sequence/read.m#L452-L469)
uses `str2double` and keeps the text only when the number is not finite, and the
`[SIGNATURE]` branch
([lines 85-93](https://github.com/pulseq/pulseq/blob/c746912/matlab/%2Bmr/%40Sequence/read.m#L85-L93))
calls it. So in MATLAB a digest of 32 decimal digits, or with a small exponent, becomes a
`double`; the example digest above (exponent 925476) stays text there.

This bug was identified and test case generated by Claude, but I've reviewed the code
myself and the error appears to be a correct finding based on my review.
