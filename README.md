# pypulseq-issues

Draft issue reports for [pypulseq](https://github.com/pulseq/pypulseq), each with a
minimal example and a tested fix, and notes for [MATLAB Pulseq](https://github.com/pulseq/pulseq)
(`pulseq/pulseq`) on questions that are not pypulseq bugs. A draft is submitted by hand;
the table records where it went. A fix branch, in the fork
[mdtisdall/pypulseq](https://github.com/mdtisdall/pypulseq), holds the fix and a regression
test for the PR that follows the issue.

| # | Issue | Status | Fix branch | Upstream |
|---|---|---|---|---|
| 01 | [`make_arbitrary_grad(oversampling=True)` checks the slew rate 4× too leniently](01-oversampled-slew-check/issue.md) | PR open | [`fix-oversampled-slew-check`](https://github.com/mdtisdall/pypulseq/tree/fix-oversampled-slew-check) | issue [#421](https://github.com/pulseq/pypulseq/issues/421), PR [#422](https://github.com/pulseq/pypulseq/pull/422) |
| 02 | [`get_block` returns oversampled arbitrary gradients with twice their `shape_dur`](02-oversampled-get-block/issue.md) | PR open | [`fix-oversampled-get-block`](https://github.com/mdtisdall/pypulseq/tree/fix-oversampled-get-block) | issue [#423](https://github.com/pulseq/pypulseq/issues/423), PR [#424](https://github.com/pulseq/pypulseq/pull/424) |
| 03 | [`waveforms()` leaves out the first and last points of oversampled arbitrary gradients](03-oversampled-waveforms/issue.md) | draft | — | — |
| 04 | [`write()` and `read()` fail with `KeyError: -1` for oversampled arbitrary gradients](04-oversampled-remove-duplicates/issue.md) | draft | — | — |
| 05 | [Note for `pulseq/pulseq`: area of an oversampled arbitrary gradient counts only the raster-centre samples](05-oversampled-area/issue.md) | draft | — | — |
| 06 | [Compute the SAFE low-pass filter in `calculate_pns` as a recursion](06-pns-lowpass-recursion/issue.md) | draft | — | — |

## Layout

Each issue has its own folder:

- `issue.md`: the report, ready to paste into a GitHub issue. After submission, the
  text as submitted.
- `repro.py`: the minimal example of the report.
- `fix.diff`: the suggested fix, against pypulseq master. Apply it in a pypulseq
  checkout with `git apply <path>/fix.diff`.

A note for `pulseq/pulseq` has no `fix.diff`, and its example is `repro.m` (MATLAB), with
`repro.py` as the same example in pypulseq.

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
MATLAB Pulseq (September 2026). Report 06 comes from the work to make the PNS card of
[pulseq-reports](https://github.com/mdtisdall/pulseq-reports) fast for long sequences
(September 2026).
