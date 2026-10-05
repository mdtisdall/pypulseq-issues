# Read the `[SIGNATURE]` values of a `.seq` file as text

Closes #XXX

`read` now reads the `[SIGNATURE]` section as text. Before, it used the reader of `[DEFINITIONS]`, which converts each value that `float()` accepts to a float, so an MD5 digest such as `9731349875117297474679317e925476` became `inf` or a rounded number. `[DEFINITIONS]` does not change.

- add the argument `numeric` (default `True`) to the private `__read_definitions` in `Sequence/read_seq.py`; the `[SIGNATURE]` branch gives `numeric=False`
- add `test_read_signature_as_text` to `tests/test_sequence.py`: `read` keeps four float-like digests and one normal digest as `str`
- add `test_writeread_signature`: after `read`, `signature_value` equals the value that `write` returned

This bug was identified and the test was generated using Claude, but I have reviewed the code and it seems correct to me.
