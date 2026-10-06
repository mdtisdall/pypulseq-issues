% read stores the [SIGNATURE] hash as a double when the hex digest is a finite number.

% The value of 'Nonce' gives a file whose MD5 digest has only decimal digits. It was
% found by trying 'n-0', 'n-1', and so on. write signs the file itself, so the hash is
% correct for the file.
seq = mr.Sequence();
seq.addBlock(mr.makeDelay(1e-3));
seq.setDefinition('Nonce', 'n-8829771');

fn = [tempname() '.seq'];
seq.write(fn);
fprintf('after write: signatureValue = ''%s'' (%s)\n', seq.signatureValue, class(seq.signatureValue));

seq2 = mr.Sequence();
seq2.read(fn);
fprintf('after read:  signatureValue = %.17g (%s)\n', seq2.signatureValue, class(seq2.signatureValue));
delete(fn);

fprintf('isequal(signatureValue): %d (expected: 1)\n', isequal(seq.signatureValue, seq2.signatureValue));
