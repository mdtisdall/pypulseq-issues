"""write() after read() of a 1.4 file with an RF event fails with KeyError."""

import tempfile
from pathlib import Path

import pypulseq as pp

# A 1.4.1 file with one RF block pulse of 100 us. A 1.4 [RF] row has 8 fields: no center
# and no use.
SEQ_1_4_1 = """\
[VERSION]
major 1
minor 4
revision 1

[DEFINITIONS]
AdcRasterTime 1e-07
BlockDurationRaster 1e-05
GradientRasterTime 1e-05
RadiofrequencyRasterTime 1e-06

# NUM DUR RF GX GY GZ ADC EXT
[BLOCKS]
1 20 1 0 0 0 0 0

# id amp mag_id phase_id time_id delay freq phase
[RF]
1 1000 1 2 0 0 0 0

[SHAPES]

shape_id 1
num_samples 100
1
0
0
97

shape_id 2
num_samples 100
0
0
98

"""

with tempfile.TemporaryDirectory() as tmp:
    path_in = Path(tmp) / 'rf_v141.seq'
    path_in.write_text(SEQ_1_4_1)

    seq = pp.Sequence()
    seq.read(str(path_in))
    print('rf_library.type after read():', dict(seq.rf_library.type))
    print('use of the RF event:', seq.get_block(1).rf.use)

    try:
        seq.write(str(Path(tmp) / 'out.seq'))
        rf_rows = (Path(tmp) / 'out.seq').read_text().split('[RF]\n')[1].splitlines()
        print('write(): ok, [RF] row:', ' '.join(rf_rows[0].split()))
    except KeyError as err:
        print('write():', repr(err))
