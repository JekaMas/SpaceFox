# Independent published-history verification

Outcome: **CLOSED / GREEN** for the bounded published test-release history unit.
Reviewed clean source `7769010359ca9f690cee76d22c7096195dd6d817`, including author
implementation `939a634e4a82b1baff2bf4f141b587f425792d66`. No material finding
or product/test repair was necessary. Root retains final judgment.

The review used SDD workflow and verification-design implementation review.
The worktree submodule was uninitialized; shared instructions were read from the
main checkout only after its HEAD matched the exact consumer pin
`f8e7ba481bf356600925e01936d7e9f3f1ac0084`. No install or workflow substitution.

## Inspected behavior and independent facts

- Read the preserved signing requirement/scenario, complete production admission
  path in `tools/release.py`, new pin/handoff, five history methods, custody methods,
  and exact changed graph/discovery selectors. The requirement statement and the
  sets of property/case IDs are unchanged. No property count increase or broad
  RL02.P1 completion is inferred from the narrower current executable witnesses.
- Independently hashed the frozen real original receipt, IQ and standalone PRG.
  The receipt matches `f38a42325101fd870ed9ae8470267827380eb7453df16b4261d3178f71ddb2f5`;
  IQ matches `b0126d9ed13cf186f2fc15be984231da06a562070f3aa2d3d5395c7bdefc037a`;
  PRG matches `aa0376f64da4b7a6d9ddcf253c034360c23b1157e2aee9a20953632356a3f788`.
  Extracted only public IQ manifest/SPKI bytes and checked actual version 0.1.0,
  production UUID and pinned SPKI digest. No private custody path was opened.
- The copied eight-asset anonymous-200 readback is byte-identical to the root
  publication receipt. This is retained historical readback, not a new network check.
- Existing `previous_release` requires clean completed receipt plus matching real
  IQ bytes; production `build_release` requires the pinned previous version/IQ;
  `validate_previous` requires UUID/SPKI preservation and strict version increase.
  The recorded original-receipt SHA is documentary; production does not impose
  byte-exact JSON identity. Current handoff/status explicitly explain that limit.
- Missing prior receipt, mismatched prior version and same/lower current version
  assertions reach these real guards. Higher-version success deliberately raises
  at `backup_status` before output/export, with upstream doubles stated in the
  test module and helper. This is sufficient for the requested metadata/admission
  unit and does not prove fresh signing, key access or export.
- Current verification/discovery and tests have no retired ProductionIdentityTest
  selectors. References inside immutable historical evidence remain historical.
  The retained disposable custody class is AST-identical to the original class.

## Evidence retained, with no redundant execution

The original observed five history methods and two real disposable OpenSSL custody
methods remain valid: source hashes match observations.json, with its custody EOF
whitespace repair explicitly recorded. None of their assertions, fixtures, owners,
dependencies, toolchain or contracts changed during this review. **Zero behavior
methods were rerun.** Original two-command, seven-method greens are retained.

The three original structural validation/query receipts match their recorded
SHA-256 values. Their graph/discovery inputs are unchanged by this report, so no
structural gate was rerun. RL02.P2 original eleven-case/two-command SDK/export
receipts and existing signed higher-version controls retain original proof limits;
release.py, build_watchface.py, ReleaseInspector.java, watchface/** and
test_release.py are unchanged by the author and this review.

`independent-inspection.json` records nineteen successful independent read-only
artifact/source/receipt checks. Its initial overbroad class-text comparison was
corrected to class-specific AST inspection; that reviewer-harness false result
is retained explicitly and was not a product or behavior-test failure.

No production restore, new signed package, native compiler/simulator, external
mutation, fresh HTTPS observation, physical device, phone, Garmin submission or
Store approval occurred. Candidate publication_ready/official_release remain
false; broad RL02.P1 and existing tasks7.1–7.3 remain open. This closure concerns
only the already-public binary history pin and its next-build admission policy.
