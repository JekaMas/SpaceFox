# Independent hosted-delivery review

Verdict: GREEN for the bounded local hosted-delivery unit at author commit
`9ab7ec3bfb609b58972cae5d7206cb5368e29627`. No finding required a source,
specification or test repair. This is an independent source and evidence review;
it is not a new behavioral test receipt or a hosted deployment observation.

- Compared every path and byte in the 279-file fixture to the captured Git tree
  `9675e0f0e42297e2399ae55f106f31dad67856ff`: path sets equal, zero byte
  mismatches. Fixture SHA-256 is
  `dcea174d89cf44cd728c2e171d9a083dd02940be3f5e38c9288fbf7ad7658d6f`.
  The retained first-failure log and closure observation bind the 274-path,
  864,544-byte union to the old 256-file refusal; the captured test would
  encounter that old guard before successful delivery.
- Each actual current snapshot is validated at 256 files and 1 MiB, including
  native text copies. For older accepted snapshots `with_text_transport`
  validates derived sidecars against the same limits before the previous feed
  roots are excluded. Thus at most two 256-file closures, including current
  roots and protected sidecars, fit the explicit 512-name ceiling. Complete
  delivery still checks 1 MiB and native feed validation retains 8192 bytes.
  The two amended specifications distinguish this union from the 256-file
  individual artifact bound.
- Both `prepare` and `accept_and_prepare` converge on `_prepare_document`;
  preflight uses authenticated active bytes plus the finalized candidate, with
  the same retained-root exclusions and current-name replacement as delivery,
  before `_save` persists pending. Existing pending recovery follows its exact
  journal and bytes; the change adds no discard, reconstruction or bypass.
  CAS, exact manifest authentication, finality and full readback remain in the
  delivery path. The receipt-bound parent fallback checks the original digest
  and rejects altered fallback bytes; no receipt is repinned.
- Reused the author's applicable green receipts in `targeted-tests.log`,
  `union-final-test.log`, `preflight-final-test.log`, `admission-binding.log`,
  and `recovery-tests.log`; no semantic inputs were changed here. Local 49 and
  50 replay receipts report simulated finality and full readback, no provider
  requests and unchanged source epoch/quota. They do not prove live delivery.

Remaining root gates: integrate, run the existing workflow serially to recover
and deploy 49, then run it again to project and deliver 50; inspect finality and
live complete closure and upcoming metadata after each. The first run alone is
not full success. Physical watch delivery remains unobserved.
