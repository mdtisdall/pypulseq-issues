fix: make `read` set `signatureFile` to `'text'`, as `write` does

Closes #295

`read` sets `signatureFile` to `'Text'`, while `write` sets `'text'`, the value that `Sequence.m` documents. This changes `read` to `'text'` as well.

- `matlab/+mr/@Sequence/read.m`: `'Text'` -> `'text'`.
- `tests/testTextSignature.m`: new, the text-format counterpart of `testBinarySignature.m`. It writes and reads a .seq file, compares the signature fields after `write` and after `read`, and verifies the file signature.

This bug was identified and the test was generated using Claude, but I have reviewed the code and it seems correct to me. Happy to remove the test if it seems like overkill given the standards of this project (Claude does tend to over-suggest tests).
