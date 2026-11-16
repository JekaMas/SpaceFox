# Group C independent verification and repairs

Status: **GREEN at the local software boundary; root judgment pending.** Source
checkpoint `007c3a0d8f90fdefb7626633c6aaf51a0bf9bf30`; overall performance021
remains NOT DONE and D has not started.

## Findings and repairs

1. The C author added a second requirement `WF21` for the browser embed while
   that identity already belonged to native saved-field lifecycle. The new
   embed cases pointed to the old `WF21.P1` property, and four existing native
   cases had their implementation notes replaced by unrelated C notes.
   [PEER-GRAPH-FIRST-RED.txt](PEER-GRAPH-FIRST-RED.txt) records the exact
   collision and wrong owner before repair. The embed now has `WF24.P1`, its
   own scenario/property/requirement joins and both script dependencies; the
   four native cases are restored exactly to their pre-C JSON objects. The
   author `GRAPH.json` is a historical pre-repair observation: its embed IDs
   and assertion of native C ownership are superseded by
   [PEER-GRAPH-GREEN.txt](PEER-GRAPH-GREEN.txt). This checks global ID
   uniqueness and C plus native case-to-scenario/property/requirement/command,
   actual callable and source-hash joins; it is not the unavailable private
   full graph runner.
2. `docs/GEOGRAPHIC_CONTEXT.md` advertised the now-deleted CLI as an operator
   recipe. Marked its old study historical and removed the executable recipe;
   retained the source and measurement narrative. A fresh search of non-evidence
   files found the retired names only in removal/negative tests and historical
   qualification reconstruction. No current map or selected-pack route changed.

## Actual observations

- `python3 -B -m unittest -v tests.test_performance021_c tests.test_current_selected_metadata`:
  nine passed (14.918s), including real isolated Git and SDK file mutations,
  ten snapshot event classes, current eleven-metadata refusal classes, historical
  snapshot tamper, and authenticated author browser receipts. Browser receipt
  tests read the retained actual Chrome observations; this peer did not launch a
  new browser. The unchanged owner releases within its stipulated tick and on a
  disconnected global event. Pending resize/timeout callbacks can run before
  that tick; the requirement does not claim synchronous removal on detach.
- [PEER-FILES.txt](PEER-FILES.txt): independent real files with unchanged
  positives and refusal of same-length restored-mtime mutation, same-content
  rename, generated-selector mutation and added empty directory, with restored
  trees accepted. This exercises the real complete snapshot fence, not a compiler.
- `python3 -B -m unittest -v tests.test_performance021_proof`: ten historical
  receipt/current/prior source tamper and missing-input controls passed;
  [PEER-PROOF.txt](PEER-PROOF.txt). The current fully readdressed SFR1M
  jurisdiction/provenance/position/root refusal test passed in 8.348s;
  [PEER-CURRENT.txt](PEER-CURRENT.txt).
- `openspec validate spacefox-watchface --strict` passed after graph repair.
  Retained author real-Chrome and SDK observations remain valid because their
  production and test input bytes were unchanged. The corrected graph is not
  evidence of another native execution. The source/sparse proof remains at the
  author's 756-catalog/28-seed boundary; doc and graph edits are outside it.
- Clean checkpoint copied admission ran `python3 -B openspec/changes/spacefox-watchface/evidence/performance021/c/copy_admission.py`:
  [PEER-RELEASE.json](PEER-RELEASE.json) independently records all 6,671
  selected hashes, exactly en/ru/de/fr/es, and two fresh full fences with
  13,346 reads of 6,673 unique files and 968,628,754 bytes. Same-size,
  restored-mtime source mutation was refused. All selected byte hashes match
  the author's a9b2df23 receipt. This is copied source admission, not a
  fresh compiler, PRG/IQ build, signing, simulator or physical test.

The first peer copy attempt failed its final clean-tree guard because this peer
edited the documentation while the copy was running (`release source must be
clean, including untracked inputs`). That is a verification sequencing failure,
not a product defect. The documentation was committed before the successful
clean checkpoint above. Subsequent peer receipts, this record, task checkbox and
journal are disjoint from the recorded release inputs; no selected product or
test bytes changed after that checkpoint.

No profile speedup is claimed: author measured fewer reads and bytes but a
slower single toolchain elapsed sample. No external provider, production key,
Garmin device, phone, deployment, Store, or physical-power claim is made.
