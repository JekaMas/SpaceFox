## Watchdog repair

- [x] Record physical crash evidence and identify candidate release debug mapping, with binary identity boundary.
- [x] Measure the hash/admission path on the captured feed and implement bounded work without weakening validation.
- [x] Run affected integrity and actual SDK/runtime checks, preserving existing valid results.
- [x] Self-review and build a labeled diagnostic candidate after software green.
- [x] Independent peer review and repair; software diagnostic gate green, root judgment separate (see evidence/PEER.md).
- [ ] Physical FR165 cold start, reopen and ordinary use for at least 15 minutes (device acceptance).

- [x] Prepare the 0.1.20 signed release from public main and reconcile its version-bound evidence; publication and physical verification remain separate.
- [x] Independently review and repair the 0.1.20 release guard and signed payload binding; root owns publication (see evidence/release-020/PEER.md).
