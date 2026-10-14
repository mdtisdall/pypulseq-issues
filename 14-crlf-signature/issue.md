# Signature: for a file with CRLF line ends, the scanner's reader hashes other bytes than the specification says

https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/src/ExternalSequence.cpp#L1750-L1800

Section 2.4 of the specification (version 1.5.3, draft) says how to verify the
`[SIGNATURE]` hash: "The new line character preceding the keyword [SIGNATURE] is part of the
signature and needs to be stripped away for the signature verification." MATLAB's `write`
says the same in the comment that it writes above the hash. So the hashed bytes are the bytes
of the file before the `\n` that comes before `[SIGNATURE]`.

The reader of the interpreter (`ExternalSequence::buildFileIndex`, lines 1750-1800 at
`c746912`) does something else. It hashes each line with its line end. It holds back an empty
line (`"\n"` or `"\r\n"`), and drops it when the next line is `[SIGNATURE]`. So it hashes the
bytes before the whole line end of the empty line before `[SIGNATURE]`.

For a file with LF line ends, the two rules hash the same bytes: MATLAB writes `\n\n[SIGNATURE]`
after the last section, and both rules stop after the first `\n`. For a file with CRLF line
ends they differ by one byte:

```
... 2\r\n\r\n[SIGNATURE]\r\n
           ^ the specification's rule stops here (it keeps the \r)
       ^ the reader's rule stops here (it drops the empty line \r\n)
```

MATLAB writes files with `fopen(filename, 'w')`, so it writes LF on every platform. A file
with CRLF line ends comes from a tool that converts the file after it was written (an editor,
or a Git checkout with `core.autocrlf`). Such a conversion changes the hashed bytes anyway, so
a converted MATLAB file fails both checks. The difference matters for a writer that writes CRLF
and hashes what it writes: the specification and the interpreter then disagree on whether the
signature is valid.

Tested with the reader at `c746912` (`load`, then `isSignatureCheckSucceeded`), on a valid
1.5.1 file whose line ends were changed to CRLF and whose hash was then set with each rule:

| Hash computed over | Hash | `isSignatureCheckSucceeded` |
|---|---|---|
| the bytes before the `\n` that precedes `[SIGNATURE]` (the specification) | `e06b91d84d3fba7303a915e068320754` | false |
| the bytes before the empty line `\r\n` (the reader) | `f29fa772d7baf2ca58d083e4f4cd1f18` | true |

Other readers differ too. KomaMRI.jl (`KomaMRIFiles/src/Sequence/pulseq/Signature.jl`,
`signature_payload_candidates`, at `f58d6c8`) accepts the hash of any of three byte strings:
the bytes before `[SIGNATURE]` without their last line-end byte (the specification's rule), the
bytes before `[SIGNATURE]`, and those bytes without any line-end byte at their end. For the CRLF
file above these are `... 2\r\n\r`, `... 2\r\n\r\n` and `... 2`. None of them is the reader's
`... 2\r\n`, so KomaMRI.jl rejects the hash that the interpreter accepts.

Suggested change: say in section 2.4 which bytes are hashed when the line ends are CRLF. The
reader's rule is the one that decides on the scanner, so the specification could state it: the
hash covers the file up to the end of the last line before the empty line that precedes
`[SIGNATURE]`, and that empty line (`\n` or `\r\n`) is not part of it.
