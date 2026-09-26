# Plan: compute the SAFE model in chunks (issue 07)

This plan is for the change in [issue 07](issue.md). The implementation also measures
the memory and the time. These measurements replace the expected values in issue 07.

## Goal

`calc_pns` must compute the SAFE model on chunks of the sequence. The peak memory must
be the returned arrays and one chunk. The results must be the same as the results for
the whole sequence.

## Terms

| Term | Meaning |
|---|---|
| Sample | One value on the gradient raster (`grad_raster_time`, usually 10 µs). |
| Chunk | A set of consecutive samples. The plan uses 10⁵ samples (1 s at 10 µs). |
| Filter state | The last output of one low-pass filter. Each axis has 3 filters. |
| Gradient state | The last gradient sample of each axis. `np.diff` needs it. |
| Whole-sequence result | The output of `calc_pns` on `pns-lfilter`. This branch has the recursion of issue 06. |
| Peak memory | The peak of `tracemalloc.get_traced_memory()` during `calculate_pns`. |
| Main agent | The Claude session that runs the plan. It uses the `opus` model. |

## Repositories and paths

| Item | Value |
|---|---|
| pypulseq checkout | `/Users/dylan/dev/pypulseq` |
| Base branch | `pns-lfilter` (`e476200`, the fix of issue 06). It is `master` (`f2c582b`) and one commit. |
| New branch | `pns-chunked`, from `pns-lfilter` |
| Worktree | `/Users/dylan/dev/pypulseq/.worktrees/pns-chunked` |
| Tracking repository | `/Users/dylan/dev/pypulseq-issues` |
| Example of issue 07 | `07-pns-chunked-memory/repro.py` |
| Test command | `.venv/bin/python -m pytest <test files>` in the worktree |
| Check command | `.venv/bin/pre-commit run --all-files` and `.venv/bin/python -m pytest` |
| Parallel tests | Do not use `pytest -n`. Tests in `test_sequence.py` then fail at random, also on `master`. |

## Decisions for the user

Make these decisions before Phase 0 starts. Each decision has a recommendation.

| # | Decision | Recommendation |
|---|---|---|
| D1 | What happens to `pns-chunked` after the upstream PR of issue 06 merges? | Rebase it on `upstream/master`: `git rebase --onto upstream/master pns-lfilter pns-chunked`. |
| D2 | Is the chunk size an argument of `calculate_pns`? | No. Use a module constant, `_PNS_CHUNK_SAMPLES = 100_000`. The arguments of `calculate_pns` do not change. |
| D3 | How equal must the chunked result be? | Bit for bit (`assert_array_equal`). If a test fails, find the cause first. Then accept `rtol=1e-12` only if the cause is float order. |
| D4 | How many upstream PRs? | Two: PR A (the chunk function) and PR B (`calc_pns`). The maintainers can ask for one PR. Then squash them. |
| D5 | Does the test suite check the peak memory? | No. The validation in Phase 3 measures it. A memory test can fail on other platforms. |
| D6 | When do the PRs open upstream? | After the PR of issue 06 merges. Before that, push the branch to the fork only. |

## Interface contract

Phase 1 and Phase 2 agents work at the same time. They use this contract. Do not
change the contract without the main agent.

Add one public function to `src/pypulseq/utils/safe_pns_prediction.py`:

```python
def safe_gwf_to_pns_chunk(gwf, dt, hw, state=None):
    # gwf:   (n, 3) array in T/m. The samples are on the raster dt. No padding.
    # dt:    the raster in s.
    # hw:    the hardware, as for safe_gwf_to_pns.
    # state: None for the first chunk. Else the state that the last call returned.
    # Returns (pns, state). pns is (n, 3), in percent, as safe_gwf_to_pns gives it.
```

The state is a `SimpleNamespace` with two fields:

- `g_last`: a `(3,)` array. It is the gradient state. The first chunk uses zeros.
- `zi`: a `(3, 3)` array. Row = axis (x, y, z). Column = filter (tau1, tau2, tau3). The
  first chunk uses zeros.

The function must obey these rules:

1. Compute `dgdt = np.diff(np.vstack([g_last, gwf]), axis=0) / dt`.
2. For each filter, use `scipy.signal.lfilter([alpha], [1.0, alpha - 1.0], x, zi=z)`.
3. Compute `alpha` with the same expression as `safe_tau_lowpass`. Use `dt * 1000` as the
   raster in ms.
4. Compute `stim1`, `stim2`, `stim3` and `stim` with the same expressions and the same
   order as `safe_pns_model`.
5. Call `safe_hw_check(hw)` only when `state` is None.
6. Do not change `safe_tau_lowpass`, `safe_pns_model` or `safe_gwf_to_pns`.

The invariant: split `gwf` into chunks of any sizes. Call the function on each chunk in
order. Concatenate the outputs. The result must equal the rows of
`safe_gwf_to_pns(gwf, rf, dt, hw)[0]` that `calc_pns` keeps. `calc_pns` keeps the rows
where `~np.isfinite(res.rf[1:])`, with `rf = np.nan * np.ones(n)`.

The invariant is true because of these facts:

- The zero padding before the sequence keeps the filter states at zero.
- The first kept row uses the difference from a zero sample.
- `calc_pns` removes the rows of the padding after the sequence.

## Phases

Each phase is one group of commits on `pns-chunked`. Phases 1 and 2 are one PR each.
Phase 0 and Phase 3 are not PRs.

### Phase 0: prepare the branch and the baseline (no PR)

| Task | Sub-task | Owner | Tier |
|---|---|---|---|
| 0.1 Prepare the branch | 0.1.1 Fetch `origin` and `upstream`. Make sure that `pns-lfilter` equals `origin/pns-lfilter`. | main | T3 |
| | 0.1.2 Make sure that the parent of `pns-lfilter` equals `upstream/master`. If not, stop and tell the user. | main | T3 |
| | 0.1.3 Create the worktree and the branch `pns-chunked` from `pns-lfilter`. | main | T3 |
| | 0.1.4 Create `.venv` in the worktree. Install `-e '.[test]'`. | main | T3 |
| | 0.1.5 Run the check command. Record the result. | main | T3 |
| 0.2 Measure the baseline | 0.2.1 Run `repro.py` of issue 07 in the worktree. Record the peak memory for each duration. | sub-agent | T1 |
| | 0.2.2 Record the time of `calculate_pns` for the 60 s sequence, 3 runs. | sub-agent | T1 |
| 0.3 Find the memory users | 0.3.1 Take a `tracemalloc` snapshot at the peak for the 60 s sequence. | sub-agent | T2 |
| | 0.3.2 List the 10 largest allocations, by source line. | sub-agent | T2 |
| | 0.3.3 Report the memory of `get_gradients` and `waveforms` alone. | sub-agent | T2 |

Only the main agent installs dependencies. Tasks 0.2 and 0.3 write only to the
scratchpad directory. They do not change files in the worktree.

Task 0.3 answers one question: does the peak come from the sample arrays? If
`get_gradients` uses a large part of the peak, stop. Tell the user. The plan then needs
a change.

### Phase 1: PR A, the chunk function

PR title: "Add safe_gwf_to_pns_chunk to compute the SAFE model on chunks".

| Task | Sub-task | Owner | Tier |
|---|---|---|---|
| 1.1 Write the function | 1.1.1 Add `safe_gwf_to_pns_chunk` as the contract gives it. | sub-agent A | T2 |
| | 1.1.2 Add a comment block in the style of the other functions in the file. | sub-agent A | T2 |
| 1.2 Write the tests | 1.2.1 Test the invariant with `safe_example_gwf()` and chunk sizes 1, 7, 1000 and all samples. | sub-agent B | T2 |
| | 1.2.2 Test the invariant with the time constants of `safe_example_hw()` multiplied by 2. | sub-agent B | T2 |
| | 1.2.3 Test that `state=None` gives the same result as a zero state. | sub-agent B | T2 |
| | 1.2.4 Test that the function does not change its inputs. | sub-agent B | T2 |
| 1.3 Review and commit | 1.3.1 Read the two diffs. | main | T3 |
| | 1.3.2 Run the check command. | main | T3 |
| | 1.3.3 Commit. Push to the fork only (decision D6). | main | T3 |

Files:

- Sub-agent A owns `src/pypulseq/utils/safe_pns_prediction.py`.
- Sub-agent B owns `tests/test_safe_pns_prediction.py`. This file comes from
  `pns-lfilter`. Sub-agent B adds tests and keeps the tests of issue 06.

### Phase 2: PR B, `calc_pns` in chunks

PR title: "Compute calculate_pns in chunks to reduce the peak memory".

| Task | Sub-task | Owner | Tier |
|---|---|---|---|
| 2.1 Write the characterization tests | 2.1.1 Copy the body of `calc_pns` on `pns-lfilter` into the test file as `whole_sequence_pns`. | sub-agent C | T1 |
| | 2.1.2 Write sequences: dense trapezoids (3 s), one axis only, a gap between gradients, an arbitrary gradient. | sub-agent C | T2 |
| | 2.1.3 Test that `calc_pns` equals `whole_sequence_pns` for each sequence: `ok`, `pns_norm`, `pns_comp` and `t`. | sub-agent C | T2 |
| | 2.1.4 Test with `time_range`. | sub-agent C | T2 |
| | 2.1.5 Test with a small chunk size (997 samples) through `monkeypatch`. Chunk ends then fall on gradient ramps. | sub-agent C | T2 |
| | 2.1.6 Test a sequence shorter than one chunk, and a sequence of exactly 2 chunks. | sub-agent C | T2 |
| 2.2 Write the implementation | 2.2.1 Call `get_gradients` one time. Keep `t` for the whole sequence. | sub-agent D | T2 |
| | 2.2.2 Allocate `pns_comp` and `pns_norm` for the whole sequence. | sub-agent D | T2 |
| | 2.2.3 For each chunk, sample the gradients, call `safe_gwf_to_pns_chunk` and write the rows. | sub-agent D | T2 |
| | 2.2.4 Keep `do_plots`, `time_range` and the `.asc` hardware path the same. | sub-agent D | T2 |
| | 2.2.5 Add the constant `_PNS_CHUNK_SAMPLES = 100_000` (decision D2). | sub-agent D | T2 |
| 2.3 Review and commit | 2.3.1 Read the two diffs. Compare `calc_pns` with the contract. | main | T3 |
| | 2.3.2 Run the check command. | main | T3 |
| | 2.3.3 Commit. Push to the fork only (decision D6). | main | T3 |

Files:

- Sub-agent C owns the new file `tests/test_calc_pns.py`.
- Sub-agent D owns `src/pypulseq/Sequence/calc_pns.py`.

Rules for sub-agent C:

- Write the tests before sub-agent D changes `calc_pns`. The tests must pass at the
  start, with the code of `pns-lfilter`.
- Do not change `whole_sequence_pns` after 2.1.1, except for imports.

Rules for sub-agent D:

- Do not change the arguments or the return values of `calc_pns`.
- Do not change the behavior of `time_range`. A range still starts from a zero state.
- Keep `ok` as a Python `bool`.

### Phase 3: validate issue 07 (no pypulseq PR)

| Task | Sub-task | Owner | Tier |
|---|---|---|---|
| 3.1 Measure the memory | 3.1.1 Run `repro.py` of issue 07 on `pns-chunked`. Record the peak memory for each duration. | sub-agent | T1 |
| | 3.1.2 Run the 60 s sequence with chunk sizes 10⁴, 10⁵ and 10⁶. Record the peak memory. | sub-agent | T1 |
| 3.2 Measure the time | 3.2.1 Record the time of `calculate_pns` for the 60 s sequence, 3 runs. | sub-agent | T1 |
| | 3.2.2 Compare with 0.2.2. | main | T3 |
| 3.3 Update the tracking repository | 3.3.1 Write `fix.diff`: `git diff pns-lfilter pns-chunked`. It applies after the `fix.diff` of issue 06. | main | T3 |
| | 3.3.2 Change the claims of issue 07 from expected values to measured values. | main | T3 |
| | 3.3.3 Add a code sketch of the chunk loop to the solution of issue 07. | main | T3 |
| | 3.3.4 Remove the 15 s and 30 s rows from the table of issue 07. | sub-agent | T1 |
| | 3.3.5 Set the fix branch of row 07 in `README.md`. Write that the `fix.diff` of 07 applies after the `fix.diff` of 06. | sub-agent | T1 |
| | 3.3.6 Show the changes to the user. Commit only after the user agrees. | main | T3 |

Give the T1 sub-agents the exact text and the exact commands. They do not make
decisions.

## Parallel work

| Group | Work at the same time | Must wait for |
|---|---|---|
| G1 | 0.1 | Decisions D1 to D6 |
| G2 | 0.2 and 0.3 | G1 |
| G3 | 1.1, 1.2 and 2.1 | G2, and the result of 0.3 |
| G4 | 1.3 | G3 (1.1 and 1.2) |
| G5 | 2.2 | G4. Sub-agent D needs the real function to run the tests. |
| G6 | 2.3 | G5, and 2.1 |
| G7 | 3.1 | G6 |
| G8 | 3.2 | G7. Do not run a time measurement at the same time as other work. |
| G9 | 3.3 | G7 and G8 |

Notes:

- In G3, three sub-agents work at the same time. Each one owns a different file.
- Sub-agent D can start at G3 with the contract only. The main agent then must run the
  tests of 2.2 again after G4. The plan does not do this, because the gain is small.
- Time measurements (0.2.2 and 3.2.1) must run alone on the computer. Other processes
  change the time.
- Memory measurements can run at the same time as other work. `tracemalloc` counts only
  the allocations of its own process.

## Model tiers

| Tier | Model | Tasks in this plan |
|---|---|---|
| T1 | `haiku` | 0.2, 2.1.1, 3.1, 3.2.1, 3.3.4, 3.3.5 |
| T2 | `sonnet` | 0.3, 1.1, 1.2, 2.1.2 to 2.1.6, 2.2 |
| T3 | `opus` (main agent) | 0.1, 1.3, 2.3, 3.2.2, 3.3.1 to 3.3.3, 3.3.6 |

Rules for all sub-agents:

- Do not run git commands that write.
- Do not install dependencies.
- Change only the files that you own.
- Report the files that you changed, the tests that you ran and the results.

The main agent reads each diff before the checks. A report from a sub-agent is not
evidence.

## Risks

| Risk | Effect | Action |
|---|---|---|
| PR #385 moves `safe_pns_prediction.py` to `safety/pns/safe_pns.py`. | PR A and PR B do not apply. | Rebase after #385 merges. The functions do not change. |
| The PR of issue 06 changes in review. | `pns-chunked` has an old base. | Rebase it on the new `pns-lfilter`: `git rebase --onto pns-lfilter <old base> pns-chunked`. |
| `lfilter` with `zi` is not bit for bit equal to one call on all samples. | The tests of 1.2 fail. | Find the cause. Then apply decision D3. |
| `get_gradients` uses much memory for arbitrary gradients. | Chunks do not decrease the peak enough. | Task 0.3 finds this. Stop and tell the user. |
| `t`, `pns_norm` and `pns_comp` stay whole-sequence arrays. | The peak still increases with the duration, by 40 bytes for each sample. | Accept. Issue 07 lists an option for a later PR. |
| The loop over chunks adds time. | `calculate_pns` is slower. | Task 3.2 measures it. Accept an increase of 10 % or less. |

## Completion criteria

1. The check command passes on `pns-chunked`.
2. The chunked result equals the whole-sequence result for each test (decision D3).
3. The peak memory for the 60 s sequence is 0.30 GB or less. Issue 07 expects 0.26 GB.
4. The time for the 60 s sequence is at most 10 % more than in task 0.2.2.
5. Issue 07 gives measured values only. The user approved the changes.
