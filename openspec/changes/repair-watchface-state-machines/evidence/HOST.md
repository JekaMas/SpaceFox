# Host observations

`publisher-first-red.log` is the original single minimized failing test against the real `_prepare_content` decision; substituted provider/update dependencies isolate the branch. The due/no-future case returned `content_pending` instead of reaching acquisition. The changed owner now applies the existing `_schedule_due` policy before taking the content-only branch. The targeted no-future regression and `ScheduleProducerTransportTest.test_current_content_only_prepare_preserves_source_age_without_provider` subsequently both passed (`Ran 2 tests`, `OK`); this uses a local authority fixture and is not a hosted deployment observation.

The retained 0.2.4 signed release receipt is the actual previous-release input. `predecessor-first-red.log` preserves the obsolete test expectation found while advancing that binding; `predecessor-green.log` records the two focused higher-version and wrong-signer cases after correction. No key material is included here.

`admission-green.log` records three focused current-release checks: repinned closure refusal, unreviewed native delta refusal, and matching independent-peer identity/changed-source binding. These ran after the author source commit, not against an uncommitted candidate.
