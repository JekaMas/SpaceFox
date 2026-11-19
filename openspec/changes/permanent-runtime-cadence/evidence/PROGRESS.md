# Current status

Base 161b61392206837f7c8425f4e56f961b201bdb5a. `tools/run_native_tests.py` selects ten clock tests only; it does not execute incident health, activity-menu, countdown lineage or STM suites. The existing GitHub motion workflow runs Python publisher tests and does not provision the Garmin SDK. `SpaceFoxView` separately owns minute field state, a 60-second fitness timer and a 1-second fallback clock timer in addition to display lifecycle; the new batch is open. Historical test receipts remain bounded to their original selectors and source. No device acceptance or new release claimed.

Author checks passed: ordinary runner 34/34 (17 per profile), final changed per-seed selector passed on both profiles, real FR165M simulator app observer and current five-primary qualification passed. NativeID 7fac46b5. Clean source-state/peer/release remain open; see AUTHOR.md for exact retained-source and physical limits.
