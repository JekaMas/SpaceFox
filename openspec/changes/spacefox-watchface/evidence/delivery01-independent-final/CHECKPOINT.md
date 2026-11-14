# Independent verification boundary

The physical delivery remains **NOT DONE**. The owner observed 0.1.6. No target
binary execution, fresh matching physical launch, or stable physical mode round trip was
observed. Neither a simulator nor a test-key installation establishes this.

The verifier found the former runtime identifier did not change when a German
resource changed; native resource directories are now included in the identity.
Against the author's source, `mode-red.log` shows an actual SDK assertion error
for an unknown mode callback. The changed source passes the callback trace and
ensures HIGH, LOW and OFF transitions are idempotent, with unknown values ignored.
The test checks actual view state and timer observations after every event.

`missing-assets-red.log` preserves a fresh source-bound SDK run where the normal
pending batch was decoded before its sidecars arrived and repeated reloads retried
that missing scene. The final source admits a matching completed batch, and only
a changed completion serial can retry a failed build. The normal pending asset
status remains waiting while its OS event is unconsumed. The final cold log records
HTTP 200, admitted metadata and the unchanged +300 registration across reloads,
without a premature decoder step.

The SDK unit log contains 9 passed, zero failed and zero errors; the actual-parser
identity log contains 1 passed, zero failed and zero errors. The SDK launcher exits
1 even when its framework reports passes. The retained-state runtime observer
shows a normal fallback during decoding, duplicate callback without cancellation,
full scene, malformed staging rejection and restoration of the same scene. The
sleep observer shows actual READY → LOW → HIGH callbacks with the same launch,
bitmap and renderer. LOW tracing excludes logged network and decoder calls in the
observed interval, not uninstrumented operations.

These runs use isolated test UUIDs and a test key. Compiler output, launch command,
pre-launch copied program, unique source-set owner and 0.1.8/65b7215d runtime
identity are recorded. The SDK-managed post-start file differs in bytes; the
transformation is unknown and no equivalence to a production IQ member is claimed.
The final natural run restored the simulator snapshot (636 files) and simulator.ini were restored byte for byte;
the original temporal registration was not inspected. Sampled memory is not an
allocator peak. Historical 4544aa8b receipts remain labeled with their own source.

The final fresh-state natural run registered the pending asset event for UTC
1794691769 and the SDK dispatched it at that time. The selected descriptor and
raster closure was fetched, the full visual became ready, and the deliberately
malformed subsequent response was rejected while the accepted scene survived.
No decoder step or unexpected rejection preceded the scheduled event and completed
batch. The sampled foreground high was 111816 of 126784 bytes, not an allocation
peak. The captured log and source/launch bindings are `native-cold-final.*`.

The first candidate export was rejected by the independent verifier because its
input snapshot omitted 60 of 225 required delivery-proof inputs. That export was
quarantined with `.rejected` suffixes and its discrepancy is recorded in
`export-inventory-red.json`. Release inventory now includes the complete delivery
proof closure; a host regression checks that inclusion. Native behavior receipts
remain valid because this change is confined to the release tool and host test.
