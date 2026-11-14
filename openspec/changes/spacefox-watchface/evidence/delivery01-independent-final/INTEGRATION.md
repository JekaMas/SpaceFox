# Public-main integration checkpoint

The public `4cb6f75f` cache/refresh and documentation changes are combined with
DELIVERY01. The published 0.1.8 test prerelease remains immutable and is the
predecessor of this 0.1.9 candidate. Its receipt and IQ hashes are documented in
`release/HANDOFF.md` and `release/signing-identity.json`. It was not submitted
to Garmin; the owner observed 0.1.6 on the physical watch after a power cycle.
The physical delivery and the remaining broader task 3.2 obligations are NOT DONE.

The integrated SDK 9.3 test-key source is 0.1.9/d04c16ef. Its DELIVERY01 unit
suite passes 9/9; the actual-parser identity case passes 1/1. Six selected native
cache, minute-refresh, latch, replay and transfer cases pass individually (6/6),
and the typed-operator/marker case passes 1/1. Their exact probes, fixture bytes,
build hashes and raw logs are in `integration-native/`. SDK tests report launcher
exit 1 even for a complete PASS table. The public cache proof is replayed against
its exact reconstructed public-main baseline; it is not replaced by these tests.

The first integrated retained-scene observer and an instrumented observer reached
full visual activation but produced no probe ticks after a background update.
An attempted current-attempt control still had a temporal event fire before the
foreground setup; a scheduler-reset control ticked but lost access to the retained
cache. Both controls and their raw logs are in `observer-diagnostics/`. A probe-only
re-arm after the actual background callback then observed a duplicate callback
retain the in-progress build, a full READY scene, malformed candidate rejection,
and restoration of that same scene. No production timer change is inferred; the
exact cause of the earlier missing ticks remains unknown.

The current-source simulator mode observer uses the same probe-only re-arm and
records READY → LOW → HIGH with the same launch, bitmap and renderer. Its LOW
interval excludes logged decoder/network activity; uninstrumented calls are not
covered. All simulator runs are test-key/isolated-namespace observations, not
production-signature or physical-watch proof. The post-start SDK-managed file
has a different hash than the compiled and pre-launch-copied PRG; its transform
is unknown and no equivalence to a production IQ member is asserted.

The official client observation in `install-client-observation.json` records an
unversioned install POST and a versioned compatibility GET. It does not identify
the selected server version or establish physical causality.

The fresh integrated natural run admitted the feed and registered its pending
asset event for UTC 1794693480; the simulator dispatched it at 1794693480. The
matching batch was fetched before the optional decoder started, then a full scene
became READY. A duplicate callback retained the in-progress build, and deliberate
malformed staging retained and restored the accepted scene. The sampled foreground
high was 113512 of 126784 bytes, not an allocator peak. The current-source log,
compiled probe and exact launch bindings are `native-cold-final.*`.

The SDK was stopped and the pre-run 636-file runtime snapshot and simulator.ini
were restored byte for byte. The original temporal registration remains unverified.
The authoritative post-restart physical gate is `physical-current-gate-019.json`.
