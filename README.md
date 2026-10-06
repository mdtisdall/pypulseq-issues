# pypulseq-issues

Draft issue reports for [pypulseq](https://github.com/pulseq/pypulseq), each with a
minimal example and a tested fix, and notes for [MATLAB Pulseq](https://github.com/pulseq/pulseq)
(`pulseq/pulseq`) on questions, and on bugs to fix there first. A draft is submitted by hand;
the table records where it went. A fix branch, in the fork
[mdtisdall/pypulseq](https://github.com/mdtisdall/pypulseq) (for 10a,
[mdtisdall/pulseq](https://github.com/mdtisdall/pulseq)), holds the fix and a regression
test for the PR that follows the issue.

| # | Issue | Status | Fix branch | Upstream |
|---|---|---|---|---|
| 01 | [`make_arbitrary_grad(oversampling=True)` checks the slew rate 4× too leniently](01-oversampled-slew-check/issue.md) | PR open | [`fix-oversampled-slew-check`](https://github.com/mdtisdall/pypulseq/tree/fix-oversampled-slew-check) | issue [#421](https://github.com/pulseq/pypulseq/issues/421), PR [#422](https://github.com/pulseq/pypulseq/pull/422) |
| 02 | [`get_block` returns oversampled arbitrary gradients with twice their `shape_dur`](02-oversampled-get-block/issue.md) | PR open | [`fix-oversampled-get-block`](https://github.com/mdtisdall/pypulseq/tree/fix-oversampled-get-block) | issue [#423](https://github.com/pulseq/pypulseq/issues/423), PR [#424](https://github.com/pulseq/pypulseq/pull/424) |
| 03 | [`waveforms()` leaves out the first and last points of oversampled arbitrary gradients](03-oversampled-waveforms/issue.md) | draft | — | — |
| 04 | [`write()` and `read()` fail with `KeyError: -1` for oversampled arbitrary gradients](04-oversampled-remove-duplicates/issue.md) | draft | — | — |
| 05 | [Note for `pulseq/pulseq`: area of an oversampled arbitrary gradient counts only the raster-centre samples](05-oversampled-area/issue.md) | draft | — | — |
| 06 | [Reduce the time and memory of `calculate_pns` for long sequences](06-pns-time-memory/issue.md) | draft | [`pns-chunked`](https://github.com/mdtisdall/pypulseq/tree/pns-chunked) | — |
| 07 | Compute the SAFE model of `calculate_pns` in chunks ([plan](07-pns-chunked-memory/plan.md)) | merged into 06 | — | — |
| 08 | [`add_block` stores an RF event with `use='other'` as undefined](08-rf-use-other/issue.md) | draft | — | — |
| 09 | [`read()` stores the `[SIGNATURE]` hash as a float when the hex digest looks like a number](09-signature-hash-as-number/issue.md) ([plan](09-signature-hash-as-number/plan.md)) | draft | [`fix-signature-hash-as-number`](https://github.com/mdtisdall/pypulseq/tree/fix-signature-hash-as-number) | — |
| 10a | [For `pulseq/pulseq`: `signatureFile` is `'Text'` after `read`, but `'text'` after `write`](10a-signature-file-case/issue.md) | PR open | [`fix-signature-file-case`](https://github.com/mdtisdall/pulseq/tree/fix-signature-file-case) | issue [pulseq/pulseq#295](https://github.com/pulseq/pulseq/issues/295), PR [pulseq/pulseq#296](https://github.com/pulseq/pulseq/pull/296) |
| 10b | [`read` sets `signature_file` to `'Text'`, but `write` sets `'text'`](10b-signature-file-case/issue.md) | PR open | [`fix-signature-file-case`](https://github.com/mdtisdall/pypulseq/tree/fix-signature-file-case) | issue [#427](https://github.com/pulseq/pypulseq/issues/427), PR [#428](https://github.com/pulseq/pypulseq/pull/428) |
| 11a | [For `pulseq/pulseq`: `signatureValue` is kept after `addBlock`, and after `read` of a file with no `[SIGNATURE]`](11a-stale-signature/issue.md) | draft | — | — |
| 11b | [`Sequence` keeps the `[SIGNATURE]` hash of a file after `add_block` and after `read` of an unsigned file](11b-stale-signature/issue.md) | draft, after 11a | — | — |

## Layout

Each issue has its own folder:

- `issue.md`: the report, ready to paste into a GitHub issue. After submission, the
  text as submitted.
- `repro.py`: the minimal example of the report.
- `fix.diff`: the suggested fix, against pypulseq master. Apply it in a pypulseq
  checkout with `git apply <path>/fix.diff`.
- `pr.md`, where there is one: the PR description, ready to paste, with its title in
  the first line.
- `plan.md`, where there is one: the plan of the implementation of the fix.

07 is merged into 06. Its folder keeps `plan.md`, the plan of the implementation, and
`chunk_tradeoff.py`, which measures the time and the memory of `calculate_pns` for chunk
sizes on one computer. `chunk_tradeoff_m1max.txt` is its output on an Apple M1 Max. A note
for `pulseq/pulseq` has `repro.m` (MATLAB) as its example. 05 also has `repro.py`, the
same example in pypulseq, and no `fix.diff`. 10a and 10b, and 11a and 11b, are each the
same bug in MATLAB Pulseq and in pypulseq: the "a" issue is submitted first, and the "b"
issue refers to it. The `fix.diff` of 10a, with
a test, is against `pulseq/pulseq` at `c746912` and applies in a `pulseq/pulseq` checkout.

## Running an example

With [uv](https://docs.astral.sh/uv/), from this folder. The released version:

```bash
uv run --no-project --with pypulseq==1.5.0.post1 python 01-oversampled-slew-check/repro.py
```

pypulseq master at the commit that the reports name:

```bash
uv run --no-project --with "pypulseq @ git+https://github.com/pulseq/pypulseq@f2c582bae13145b8ac71958726bc8b5a14bd1cfd" python 01-oversampled-slew-check/repro.py
```

A pypulseq checkout with a `fix.diff` applied:

```bash
uv run --no-project --with-editable <pypulseq checkout> python 01-oversampled-slew-check/repro.py
```

`04-oversampled-remove-duplicates/repro.py` writes `oversampled.seq` in the current folder
(ignored by git).

## Versions used

- pypulseq 1.5.0.post1, and master at `f2c582b` (2026-08-28).
- For comparison with MATLAB Pulseq: `pulseq/pulseq` at `c746912` (2026-09-17), run in
  GNU Octave 11.3.0.
- For comparison with the MATLAB SAFE model (06):
  `filip-szczepankiewicz/safe_pns_prediction` at `0774e80`.

Reports 01 to 05 come from a comparison of the gradient slew computations in pypulseq and
MATLAB Pulseq (September 2026). Reports 06 and 07 come from the work on the PNS card of
[pulseq-reports](https://github.com/mdtisdall/pulseq-reports) for long sequences
(September 2026). Report 09 comes from the work on the sequence signature in the result
matrix of [pulseq-checks](https://github.com/mdtisdall/pulseq-checks) (October 2026).
Report 11 comes from the work on
[pulseq-analysis](https://github.com/mdtisdall/pulseq-analysis), which refuses a sequence
with no `[SIGNATURE]` hash (October 2026).
