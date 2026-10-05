# Plan: read the [SIGNATURE] values as text (issue 09)

This plan is for the fix of [issue 09](issue.md). It makes a fix branch in the fork with
the change of `fix.diff` and a regression test. It checks the same commit on
pypulseq 1.5.0.post1 and on our branch from it, `pulseq-reports-pin`. It also prepares
the PR description and updates the tracking repository.

## Goal

After `Sequence.read`, `signature_value` must be the text of the `Hash` line and
`signature_type` must be the text of the `Type` line, for each digest. The values of
`[DEFINITIONS]` must not change: a number there is still a float or an array.

The fix and its tests must also pass on `v1.5.0.post1` and on `pulseq-reports-pin`.
We use `pulseq-reports-pin`: it is `v1.5.0.post1` with our local fixes.

## Terms

| Term | Meaning |
|---|---|
| Float-like digest | An MD5 hex digest that `float()` accepts: 32 decimal digits, or decimal digits with one `e` inside. About 1 in 850,000 digests. |
| Normal digest | A digest with one or more of the letters `a`-`f` other than one `e` between digits. `float()` refuses it. |
| Main agent | The Claude session that runs the plan. It uses the `opus` model. |

## Repositories and paths

| Item | Value |
|---|---|
| pypulseq checkout | `/Users/dylan/dev/pypulseq` |
| Base | `upstream/master` (`f2c582b`, 2026-08-28). `origin/master` (the fork) is the same commit. |
| New branch | `fix-signature-hash-as-number`, from `upstream/master`. The name follows `fix-oversampled-slew-check` and `fix-oversampled-get-block`. |
| Worktree | `/Users/dylan/dev/pypulseq/.worktrees/fix-signature-hash-as-number` |
| Tracking repository | `/Users/dylan/dev/pypulseq-issues` |
| Changed source file | `src/pypulseq/Sequence/read_seq.py` (the `[SIGNATURE]` branch of `read`, and `__read_definitions`) |
| Test file | `tests/test_sequence.py` (decision D2) |
| Test command | `.venv/bin/python -m pytest tests/test_sequence.py -k "test_read_signature_as_text or test_writeread_signature"` in the worktree. Do not use `-k signature`: it also selects `TestSequence::test_writeread_no_signature`, which fails when it runs without the other tests of its class. |
| Check command | `.venv/bin/pre-commit run --all-files` and `.venv/bin/python -m pytest` |
| Parallel tests | Do not use `pytest -n`. Tests in `test_sequence.py` then fail at random, also on `master`. |
| Release tag | `v1.5.0.post1` |
| Our branch | `pulseq-reports-pin` (`a74ab06`, also on `origin`). It is `v1.5.0.post1` and 4 commits: the 2 commits of issue 06, the fix of issue 02 (`get_block`), and #359 (no infinite loop for a file without a signature). |
| Check worktrees | `/Users/dylan/dev/pypulseq/.worktrees/signature-on-1.5.0.post1` (detached at `v1.5.0.post1`) and `/Users/dylan/dev/pypulseq/.worktrees/signature-on-pin` (branch `pulseq-reports-pin-signature`, from `pulseq-reports-pin`) |
| Check command on 1.5.0.post1 | `.venv/bin/python -m pytest -W ignore::pytest.PytestRemovedIn10Warning` only. The lint of the change is checked on the fix branch. Without `-W`, pytest 9.1 stops at collection: `tests/test_calc_duration.py` at the tag gives a generator to `parametrize`. |

On `v1.5.0.post1`, `read_seq.py` differs from `master` only in `__read_shapes` (#359).
On `pulseq-reports-pin`, `read_seq.py` is the same as on `master`. `fix.diff` applies to
both (checked with `git apply --check` on 2026-10-05). `tests/test_sequence.py` is
different on both: 103 lines on `v1.5.0.post1` and 46 lines on `pulseq-reports-pin`
are not the same as on `master`.

## Decisions for the user

Make these decisions before Phase 0 starts. Each decision has a recommendation.

| # | Decision | Recommendation |
|---|---|---|
| D1 | How does the reader keep the text? (a) An argument `numeric=True` on `__read_definitions`; the `[SIGNATURE]` branch gives `numeric=False`. (b) A new function `__read_signature`. | (a). It is the change that the issue proposes, and it is the smallest diff. It adds no public API: `__read_definitions` is private to the module. |
| D2 | Where does the test go? (a) A module-level function in `tests/test_sequence.py`, after `class TestSequence`. (b) A new file `tests/test_read_seq.py`. | (a). `test_sequence.py` has the write and read tests, also `test_writeread_no_signature`. A function outside the class does not run once for each sequence of `sequence_zoo`. |
| D3 | How does the test make a file with a float-like digest? (a) Write the file with `create_signature=False`, then append a `[SIGNATURE]` section in the format of `write_seq.py`. (b) Patch `hashlib.md5` so that `write` writes a chosen digest. (c) Search for a definition value, as the first version of `repro.py` did. | (a). It is fast and gives the same file each time. `read` does not check the hash, so a hash that is not the MD5 of the file is correct for this test. (b) depends on how `write_seq.py` calls `hashlib`. (c) needs about 850,000 MD5 calculations on average, and its value changes when the output of `write` changes (for example the version lines). |
| D4 | MATLAB Pulseq has the same pattern for 32-digit digests and small exponents. Does it get its own note for `pulseq/pulseq`, as issue 05 does? | Not in this plan. Issue 09 already names it in "Additional context". If you want a note, it is issue 10, with a `repro.m`. |
| D5 | The "Suggested fix" of `issue.md` names `fix.diff` and gives the test-suite result. The style of the issues is: self-contained, and no test-suite results (they are CI results for the PR). Issue 08 has the same two items. | Change issue 09 in Phase 3: put the diff of `src/` in the issue as a `diff` block, and remove the test-suite sentence. Keep the result of the example with the fix. Do the same for issue 08 in a separate task. |
| D6 | Who opens the issue and the PR upstream? | You. The main agent pushes the branch to the fork only and writes `pr.md`. The PR body has `Closes #N`; you set `N` after you submit the issue. |
| D7 | After the checks of Phase 2 pass, does the fix go on `pulseq-reports-pin`? | Yes, as the fix of issue 02 did (`8c089a1`). Task 2.2 cherry-picks the commit with `git cherry-pick -x` and keeps the message, as `8c089a1` does. Fast-forward `pulseq-reports-pin` to that commit. Push it to `origin` only after you agree. |

## Test cases

The test is parametrized on the digest. For each digest it checks that
`seq2.signature_value == digest`, that `type(seq2.signature_value) is str`, and that
`seq2.signature_type == 'md5'`.

| Digest | `float(digest)` | Why |
|---|---|---|
| `9731349875117297474679317e925476` | `inf` | The digest of the issue example. A large exponent. |
| `12345678901234567890123456789e12` | `1.2345678901234568e+40` | A small exponent: a finite, rounded float. MATLAB has this bug too. |
| `12345678901234567890123456789012` | `1.2345678901234567e+31` | 32 decimal digits: rounded. |
| `00000000000000000000000000000042` | `42.0` | Leading zeros: the text and the number differ most. |
| `d41d8cd98f00b204e9800998ecf8427e` | `ValueError` | A normal digest (the MD5 of the empty string). It passes before and after the fix. |

A second test writes a file with `create_signature=True`, reads it, and checks that
`signature_value` equals the value that `write` returned. No test in the suite checks
this now. It passes before and after the fix.

## Phases

The change is about 15 lines in one source file and one test file. Parallel work gives
no gain, so the main agent does all the tasks. There are no sub-agents.

### Phase 0: prepare the branch (no PR)

| Task | Sub-task |
|---|---|
| 0.1 Check the base | 0.1.1 Fetch `upstream` and `origin` in the pypulseq checkout. |
| | 0.1.2 If `upstream/master` is not `f2c582b`, look at `git log f2c582b..upstream/master -- src/pypulseq/Sequence/read_seq.py`. If the `[SIGNATURE]` branch or `__read_definitions` changed, stop and tell the user. |
| | 0.1.3 Look for open upstream PRs and issues about `read_seq.py` or the signature (`gh pr list -R pulseq/pypulseq` through `nix develop`, or the GitHub web pages). If one fixes the same bug, stop and tell the user. |
| 0.2 Make the worktree | 0.2.1 `git worktree add -b fix-signature-hash-as-number .worktrees/fix-signature-hash-as-number upstream/master` |
| | 0.2.2 Create `.venv` in the worktree. Install `-e '.[test]'` and `pre-commit`. |
| | 0.2.3 Run the check command. Record the result. The 2 tests of `tests/test_sigpy.py` fail when sigpy is not installed. |

### Phase 1: the fix and the test (one PR)

PR title: "Read the `[SIGNATURE]` values of a `.seq` file as text".

| Task | Sub-task |
|---|---|
| 1.1 Write the tests first | 1.1.1 Add the two tests of "Test cases" (decision D2, decision D3). Use `tmp_path`. |
| | 1.1.2 Run the test command on the unchanged code. The 4 float-like digests must fail; the normal digest and the round trip must pass. If not, find the cause before 1.2. |
| 1.2 Write the fix | 1.2.1 Apply `09-signature-hash-as-number/fix.diff` with `git apply`. If it does not apply, make the same change by hand (decision D1). |
| | 1.2.2 Correct the docstring of `__read_definitions` only where `fix.diff` changes it. Do not correct other typos in the file: they are a different change. |
| 1.3 Check and commit | 1.3.1 Run the test command. All cases must pass. |
| | 1.3.2 Run the check command. Compare with 0.2.3: the only difference must be the new tests. |
| | 1.3.3 Read the full diff against `upstream/master`. |
| | 1.3.4 Commit, in the style of the commits on `fix-oversampled-get-block`: a short subject, a body that says the cause and what the test checks, and `Closes #N` as the last line. |
| | 1.3.5 Push the branch to `origin` (the fork) only (decision D6). |

### Phase 2: check the fix on 1.5.0.post1 and on our branch (no PR)

Do the checks in the two check worktrees. Each worktree has its own `.venv`. Do not
change the fix branch in this phase. If the fix needs a change for 1.5.0.post1, stop
and tell the user: the upstream commit and our commit must stay the same change.

| Task | Sub-task |
|---|---|
| 2.1 Check on `v1.5.0.post1` | 2.1.1 `git worktree add --detach .worktrees/signature-on-1.5.0.post1 v1.5.0.post1`. Create `.venv` and install `-e '.[test]'`. |
| | 2.1.2 Run `.venv/bin/python -m pytest` before the change. Record the result. This is the baseline of the tag. |
| | 2.1.3 `git cherry-pick --no-commit fix-signature-hash-as-number`. If `tests/test_sequence.py` has a conflict, keep the tag's version of the file and add the two new tests at the end of it. `read_seq.py` must not have a conflict. |
| | 2.1.4 Run the test command. All cases must pass. |
| | 2.1.5 Run `.venv/bin/python -m pytest`. Compare with 2.1.2: the only difference must be the new tests. |
| | 2.1.6 Run `repro.py` with `uv run --no-project --with-editable <this worktree> python 09-signature-hash-as-number/repro.py`. It must print the hash as a `str` and `equal: True`. |
| | 2.1.7 Remove the worktree. Nothing in it is kept. |
| 2.2 Check on `pulseq-reports-pin` | 2.2.1 `git worktree add -b pulseq-reports-pin-signature .worktrees/signature-on-pin pulseq-reports-pin`. Create `.venv` and install `-e '.[test]'`. |
| | 2.2.2 Run `.venv/bin/python -m pytest` before the change. Record the result. |
| | 2.2.3 `git cherry-pick -x fix-signature-hash-as-number`. Resolve a conflict in `tests/test_sequence.py` as in 2.1.3. |
| | 2.2.4 Run the test command, `.venv/bin/python -m pytest` and `repro.py`, as in 2.1.4 to 2.1.6. Compare with 2.2.2. |
| | 2.2.5 Tell the user the results of 2.1 and 2.2. Apply decision D7 only after the user agrees: fast-forward `pulseq-reports-pin` to `pulseq-reports-pin-signature` and push it to `origin`. Then remove the worktree and the branch `pulseq-reports-pin-signature`. |

### Phase 3: update the tracking repository (no pypulseq PR)

Do this phase on a new docs branch of the tracking repository.

| Task | Sub-task |
|---|---|
| 3.1 Validate the example | 3.1.1 Run `repro.py` with `uv run --no-project --with-editable <fix worktree> python 09-signature-hash-as-number/repro.py`. It must print the hash as a `str` and `equal: True`. |
| 3.2 Update the files | 3.2.1 Write `fix.diff` again: `git diff upstream/master fix-signature-hash-as-number -- src`. The other `fix.diff` files do not include tests. If it differs from the current file, use the new one. |
| | 3.2.2 Write `pr.md` in the style of the PRs that close an issue: the title on the first line, `Closes #N`, one or two sentences, a short list of changes, no test results, and the Claude note at the end. |
| | 3.2.3 Change the "Suggested fix" of `issue.md` (decision D5). The "Desktop" section already says that the example gives the same output with 1.5.0.post1 and with `master`. Keep that sentence only if 2.1.6 confirms it with the fix. |
| | 3.2.4 In `README.md`, set the fix branch of row 09 to `fix-signature-hash-as-number`, with a link to the branch in the fork. |
| 3.3 Approve | 3.3.1 Show the changes to the user. Commit only after the user agrees. |

## Risks

| Risk | Effect | Action |
|---|---|---|
| Upstream changes `read_seq.py` before the PR merges. | `fix.diff` and the branch do not apply. | Task 0.1.2 finds this before the work. After the work, rebase the branch. |
| Code outside pypulseq uses `signature_value` as a float. | That code changes behavior. | Accept. A float digest is not useful, and for a normal digest the value is already a `str`. |
| A `Hash` line has spaces at the end. | The text has spaces. | `fix.diff` uses `.strip()`, as the text branch of `__read_definitions` does now. |
| A `[SIGNATURE]` section has a key with no value. | The value is `''`. | Accept. This is the behavior now. |
| `signature_file` is `'Text'` after `read` and `'text'` after `write`. | Not part of this bug. See "Signature file: 'Text' and 'text'" below. | Do not change it in this PR. |
| `tests/test_sequence.py` on `v1.5.0.post1` and `pulseq-reports-pin` differs from `master`. | The cherry-pick of the test has a conflict. | Tasks 2.1.3 and 2.2.3: keep the old file and add the two tests at the end. The tests use only `pp.Sequence`, `make_delay`, `write` and `read`, which are in 1.5.0.post1. |
| `v1.5.0.post1` does not have #359. `read` can loop forever on a file without a `[SIGNATURE]` section. | A test of the fix can hang on the tag. | The new tests always write a `[SIGNATURE]` section. If a test hangs on the tag, stop it and tell the user. `pulseq-reports-pin` has #359. |
| The tag needs older dependencies than the fix branch. | `pytest` gives other failures on the tag. | Tasks 2.1.2 and 2.2.2 record a baseline. Compare with the baseline, not with `master`. |

### Signature file: 'Text' and 'text'

`Sequence` has three signature attributes: `signature_type`, `signature_value` and
`signature_file`. `signature_file` tells which data the hash was computed on. MATLAB
Pulseq documents it in `Sequence.m` (line 67, `c746912`): "currently 'text' or 'bin'
(used file format of the save function)". `bin` is a binary file format that pypulseq
does not have.

The two functions that set the attribute give different case:

| Function | pypulseq | MATLAB Pulseq (`c746912`) |
|---|---|---|
| Constructor | `''` (`sequence.py`, line 93) | `''` (`Sequence.m`, line 125) |
| `write` | `'text'` (`sequence.py`, line 1867; line 1804 in 1.5.0.post1) | `'text'` (`write.m`, line 277) |
| `read` | `'Text'` (`read_seq.py`, line 100) | `'Text'` (`read.m`, line 92) |

So pypulseq copies MATLAB, and both have the difference. No code in pypulseq or in MATLAB
Pulseq reads the attribute: each tool only sets it. The effect is on code outside the
libraries: a test like `seq.signature_file == 'text'` is true after `write` and false
after `read` of the same file. The fix for this is one character (`'Text'` to `'text'`
in `read`), but the documented value comes from MATLAB. An issue for it must go to
`pulseq/pulseq` first, or to both repositories together. It is not part of issue 09,
because the hash is correct with either value.

## Completion criteria

1. The 4 tests with a float-like digest fail on `upstream/master` and pass on
   `fix-signature-hash-as-number`.
2. The check command gives the same result as in task 0.2.3, plus the new tests.
3. `repro.py` with the fix prints the hash as a `str` and `equal: True`, on the fix
   branch, on `v1.5.0.post1` and on `pulseq-reports-pin`.
4. On `v1.5.0.post1` and on `pulseq-reports-pin`, the commit applies with no change to
   `read_seq.py`, the new tests pass, and `pytest` gives the same result as the baseline,
   plus the new tests.
5. The branch is on the fork. `fix.diff`, `pr.md`, `issue.md` and `README.md` are
   up to date, and the user approved the changes.
6. `pulseq-reports-pin` has the fix only if the user agreed (decision D7).
