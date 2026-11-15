# Text-transport composition — diagnostic checkpoint

Source is base 454945f7 plus selective 18305ba2 producer and test hunks.
`prepare_content` retains the root branch's registry eligibility and
`catalogReview` result. No public code, prototype or deployment was changed.

Initial process `tests.log.gz` ran the six new `PhoneTextTransportTest` cases,
which individually printed `ok`, then reported FAIL for the first publication
and integer-discriminator cases with the pre-handoff test module. The parent
process was interrupted (exit 130) after the reviewed test edits were applied;
unittest therefore did not print failure tracebacks or complete the run. It is
not a suite pass and does not establish the exact failing assertion.

Hypothesis: the initial test module rewrites only `feed.json` or a logical
closure, leaving the new byte-identical sidecar stale, or compares old delivery
without the new files. The independently reviewed 18305ba2 test changes
construct consistent aliases while retaining the policy/identity negative
assertions, and add an explicit pre-alias → protected-retained-alias witness.
A focused re-run of the modified tests is the discriminator; any failure must
be diagnosed from its complete traceback, not attributed to this hypothesis
without evidence. The same-run six new successes have unchanged code and tests,
but the interrupted suite itself is not a passing receipt.

`current-integrity.log` completed with one failure: selected-only versus four
record output differed only in mutable `feed.json.txt`, whose content correctly
mirrors the different accepted-record count. The assertion originally excluded
only `feed.json`; it now excludes both mutable root names, independently asserts
each alias is byte-identical to its own root, and retains exact equality for
all immutable closure bytes. The malformed feed test also now regenerates aliases
for each modified root, ensuring the intended parser/policy error cannot be
masked by sidecar mismatch; the corrupt-raster candidate still exercises actual
pinned-object rejection. Both affected cases are being re-run.
`current-integrity-recheck.log` then completed both affected cases successfully
(exit 0). `quota-origin.log` independently covers shared quota exhaustion and
old HTTP 200 source age (exit 0). `catalog.log` covers content-only preparation,
reported upcoming catalog gaps, and per-record age through local readback
(exit 0). `publisher-recheck.log` covers three affected publisher cases (exit 0).
`phone.log` has seven passing cases, but two later assertion-only edits were made:
`catalog-review.log` re-executes the affected transport-only case, while
`delivery-bounds-r2.log` re-executes the exact byte/file-bound case. Other phone
case production, assertions, fixtures and toolchain were unchanged.
`http-304-429.log` re-executes the affected local Git/loopback provider
sequence: due 200, no early call, 304 retains record validation epoch, 429
persists the 600-second backoff and prevents an early call. Exit 0; this does
not establish watch callback, paired-phone or hosted network behavior.
`source-closure.log.gz` is the raw exact tracked source-closure witness at
HEAD `aecbc86c`, exit 0. It materialized all 756 catalog inputs from the sparse
runtime seed, checked exact bytes and imports/CLI help, and rejected the controlled
corrupt input without replacement. This is local source integrity, not hosted
execution or a physical-device acceptance claim.
