# Reduce the time and memory of `calculate_pns` for long sequences

Closes #XXX

`safe_tau_lowpass` now computes the SAFE low-pass filter as the first-order recursion of the original MATLAB code, with `scipy.signal.lfilter`, instead of a convolution with a kernel of up to about 11,000 taps. `calc_pns` now computes the model on chunks of 30,000 samples and carries the filter state from one chunk to the next, so it no longer keeps arrays of the whole sequence. For a 60 s sequence, `calculate_pns` takes 0.6 s instead of 42 s, and its peak memory is 0.25 GB instead of 1.01 GB. The arguments and the results of `calculate_pns` do not change, and pypulseq has no new public names.

- compute `safe_tau_lowpass` with `lfilter` in `utils/safe_pns_prediction.py`; `eps` stays, but has no effect
- add the private `_safe_gwf_to_pns_chunk` to `utils/safe_pns_prediction.py`: the SAFE model on one chunk, which returns the last gradient sample and the state of the nine filters for the next chunk
- compute `calc_pns` in chunks of `_PNS_CHUNK_SAMPLES = 30_000` samples in `Sequence/calc_pns.py`, and compute `ok` with `np.all`
- add `tests/test_safe_pns_prediction.py`: the recursion equals the convolution for each time constant of `safe_example_hw()`, and the concatenated chunks equal `safe_gwf_to_pns` bit for bit, for chunk sizes from 1 sample to the whole waveform
- add `tests/test_calc_pns.py`: `calculate_pns` equals the whole-sequence computation bit for bit for several sequences, with and without `time_range`, and with chunk ends on gradient ramps

One edge case changes: for a `time_range` with no samples and a hardware description with missing fields, `calc_pns` now returns empty arrays instead of raising an error.

This improvement was identified and the tests were generated using Claude, but I have reviewed the code and it seems correct to me.
