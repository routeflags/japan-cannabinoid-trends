# Storage reader fixtures — synthetic

Every file in this directory is **synthetic** (invented shapes, no real
collected records).  Two reasons:

- the recorded JSON shapes whose real files live outside the repository
  (pages / checkpoints) have invented companions here;
- a real YouTube dataset export cannot be committed at all (third-party video
  metadata; AGENTS.md redistribution rules), so the CSV reader contract uses
  `dataset_export_synthetic.csv`, whose rows are labelled `synthetic-*` and
  point at `example.invalid`.

The synthetic CSV is LF-terminated and BOM-free for readable diffs; the
encoding edge cases the reader fixes (UTF-8 BOM, CRLF records, embedded
newlines in quoted fields, blank physical lines) are constructed inside
`tests/storage/test_csv_reader.py`, not stored as invisible bytes here.
