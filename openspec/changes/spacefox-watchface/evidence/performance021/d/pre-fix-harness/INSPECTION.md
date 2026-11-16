# Read-only helper inspection

A separate read-only inspection identified these defects in the archived helpers, before repair:

1. The 120-second observation deadline starts before PRG installation, so it does not provide 120 seconds after the binary gate. The binary gate does not itself witness the first application callback.
2. Sampling or capture-complete can trigger cleanup while a UI action is outstanding; the helper has no token-bound ready/claim/release lease. Clock readiness is an unbounded stale-file wait.
3. Window ID discovery has no timeout; the sampling loop checks launcher but not simulator liveness; foreground state is not verified.
4. Existing output directories can retain stale signal files. Captures have variable command duration plus two seconds, not a fixed two-second sampling frequency. No automatic image readability or scene classifier is implemented.
5. The implicit `current` and `fix` aliases name specific intermediate PRGs, not the latest source. Exact input PRG and debug identities must be tied to compiler input receipts before interpreting timing.
6. The mounted-device lane and all three `-a` transfers are the proved fixture recipe. A restart without that mapping is a known invalid identity setup. Diagnostic simulator time is not stock wall time.

The archived pre-fix helper SHA-256 values are: timing-lane.py `21400bc1be186bb839add4abb16f01c6c0bbb66257caf6ac23d5475ea34d5ec3`; controlled.py `f796784e8566dc9f74df142b9ab9c476e02340dba0f0137d7dabadce51328121`; mounted-lane.py `14698cd34069ddcaeb9ea54cc33898b98d4add2ad5e9201346d007dea3753cb7`. Retain the prior observations as harness-bounded reds; do not assert a product cause from them.
