# pypulseq-issues

Draft issue reports for [pypulseq](https://github.com/pulseq/pypulseq), each with a
minimal example and a tested fix. A draft is submitted to pypulseq by hand; the table
records where it went. A fix branch, in the fork
[mdtisdall/pypulseq](https://github.com/mdtisdall/pypulseq), holds the fix and a regression
test for the PR that follows the issue.

| # | Issue | Status | Fix branch | Upstream |
|---|---|---|---|---|
| 01 | [`make_arbitrary_grad(oversampling=True)` checks the slew rate 4× too leniently](01-oversampled-slew-check/issue.md) | submitted | [`fix-oversampled-slew-check`](https://github.com/mdtisdall/pypulseq/tree/fix-oversampled-slew-check) | [#421](https://github.com/pulseq/pypulseq/issues/421) |
| 02 | [Oversampled arbitrary gradients break in a Sequence: `get_block`, `check_timing`, `waveforms`, `write` and `read`](02-oversampled-sequence/issue.md) | draft | — | — |

## Layout

Each issue has its own folder:

- `issue.md`: the report, ready to paste into a GitHub issue. After submission, the
  text as submitted.
- `repro.py`: the minimal example of the report.
- `fix.diff`: the suggested fix, against pypulseq master. Apply it in a pypulseq
  checkout with `git apply <path>/fix.diff`.

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

`02-oversampled-sequence/repro.py` writes `oversampled.seq` in the current folder
(ignored by git).

## Versions used

- pypulseq 1.5.0.post1, and master at `f2c582b` (2026-08-28).
- For comparison with MATLAB Pulseq: `pulseq/pulseq` at `c746912` (2026-09-17), run in
  GNU Octave 11.3.0.

The reports come from a comparison of the gradient slew computations in pypulseq and
MATLAB Pulseq (September 2026).
