% Sequence keeps the [SIGNATURE] hash after addBlock, and after read of a file with no
% [SIGNATURE] section.

signed_fn = [tempname() '.seq'];
unsigned_fn = [tempname() '.seq'];

seq = mr.Sequence();
seq.addBlock(mr.makeTrapezoid('x', 'Area', 1000, 'Duration', 2e-3));
seq.write(signed_fn);
fprintf('after write:                       signatureValue = ''%s''\n', seq.signatureValue);

seq.addBlock(mr.makeDelay(1e-3));
fprintf('after addBlock:                    signatureValue = ''%s''\n', seq.signatureValue);

seq.write(unsigned_fn, false);  % no [SIGNATURE] section

seq2 = mr.Sequence();
seq2.read(signed_fn);
seq2.read(unsigned_fn);
fprintf('signed, then unsigned file read:   signatureValue = ''%s''\n', seq2.signatureValue);

seq3 = mr.Sequence();
seq3.read(unsigned_fn);
fprintf('unsigned file into a new Sequence: signatureValue = ''%s''\n', seq3.signatureValue);

delete(signed_fn);
delete(unsigned_fn);
