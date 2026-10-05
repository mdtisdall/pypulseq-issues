Set `signature_file` to `'text'` in `read`, as `write` does

Closes #427

`read` set `signature_file` to `'Text'`, while `write` sets `'text'`. This changes `read` to `'text'`, as pulseq/pulseq#296 does for MATLAB Pulseq.

- set `signature_file = 'text'` in `Sequence/read_seq.py`
- check in `test_writeread` (`tests/test_sequence.py`) that `signature_type` and `signature_file` are the same after `write` and after `read`

This bug was identified and the test was generated using Claude, but I have reviewed the code and it seems correct to me.
