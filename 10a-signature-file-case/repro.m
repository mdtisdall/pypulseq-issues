% signatureFile is 'text' after write, but 'Text' after read of the same file.

seq = mr.Sequence();
seq.addBlock(mr.makeDelay(1e-3));

fn = [tempname() '.seq'];
seq.write(fn);
fprintf('after write: signatureFile = ''%s''\n', seq.signatureFile);

seq2 = mr.Sequence();
seq2.read(fn);
fprintf('after read:  signatureFile = ''%s''\n', seq2.signatureFile);
delete(fn);

fprintf('strcmp(signatureFile, ''text''): %d after write, %d after read\n', ...
        strcmp(seq.signatureFile, 'text'), strcmp(seq2.signatureFile, 'text'));
