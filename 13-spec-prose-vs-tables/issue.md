# Specification: the prose of five sections disagrees with their tables and examples

https://github.com/pulseq/pulseq/blob/c7469123c2f381f065986e6cc3a7d09730ed16ef/doc/specification.pdf

The specification (version 1.5.3, draft) gives the layout of each event section three
ways: a sentence with the number of fields, a line with the names of the fields, and a
table with each field. Each section also has an example. In five places the prose
disagrees with the table and the example. The tables and the examples agree with each
other, and with the files that MATLAB Pulseq writes, so only the prose is wrong.

1. **RF (section 2.8.1, page 10).** The prose says that each RF event is "a single line
   containing seven numbers", and the line under it has eight fields:

   ```
   <id> <amp> <mag_id> <phase_id> <time_id> <delay> <freq> <phase>
   ```

   The table has twelve fields: it adds `<center>`, `<freq_ppm>`, `<phase_ppm>` and
   `<use>`, and calls the last two offsets `<freq_off>` and `<phase_off>`. The example has
   twelve fields, with `<center>` before `<delay>`:

   ```
   1 550 1 2 0 1000 100 0.000 0.0000 0.000 0.000 e
   ```

   Read with the line of the prose, this example has a delay of 1000 µs and a frequency
   offset of 100 Hz. The text under the example says that the center is at 1000 µs and the
   delay is 100 µs, as the table gives. In version 1.4.1 the count was wrong too: "seven
   numbers", with eight fields.

2. **Gradients (section 2.8.2, page 12).** The prose says that each arbitrary gradient is
   "specified by four numbers", and the line under it has seven fields:

   ```
   <id> <amp> <first> <last> <shape_id> <time_id> <delay>
   ```

   The table and the example (`1 790127 0 -550073 6 0 980`) have seven fields too. In
   version 1.4.1 the prose also said "four numbers", with five fields.

3. **ADC (section 2.8.3, page 14).** The prose says that each ADC event is "specified by
   six numbers", and the line under it, the table and the example
   (`1 512 5000 0 0.000 0.000 0.000 0.000 0`) have nine fields. Six was right in version
   1.4.1; version 1.5.0 added `<freq_ppm>`, `<phase_ppm>` and `<phase_shape_id>`.

4. **The extension header (section 2.8.4, page 16).** The table gives the type of
   `<STRING_ID>` as "integer text". The description calls it a text ID, the interpreter
   must recognize an extension only by it, and every example has a word
   (`extension TRIGGERS 1`, `extension DELAYS 2`, `extension ROTATIONS 1`,
   `extension RF_SHIMS 4`). The type is text.

5. **Soft Delay Extension (section 2.8.4, page 18).** The second paragraph starts "Label
   extension can be used in conjunction with pure delay blocks". The paragraph and its
   example (`extension DELAYS 2`) are about the soft delay extension, and the label
   extension (LABELSET and LABELINC) has no relation to delay blocks. It should say "Soft
   delay extension".

A suggested change: give the correct count in items 1 to 3, or remove the count and refer
to the line of fields; make the line of item 1 the twelve fields of the table, in the
order of the table; give the type of `<STRING_ID>` as text; and change "Label extension"
to "Soft delay extension" in item 5.

This matters to a reader that is written from the specification. Item 1 is the one with an
effect on values: a reader that follows the line of the prose puts the center in the delay.

Versions: `doc/specification.pdf` of MATLAB Pulseq (`pulseq/pulseq`) at c746912
(2026-09-17), version 1.5.3 (draft). This file has not changed since 2090dbc (2026-05-27).
Version 1.4.1 for comparison: the same file at 50436ab.

This was identified by Claude, but I've reviewed the specification myself and the finding
appears to be correct based on my review.
