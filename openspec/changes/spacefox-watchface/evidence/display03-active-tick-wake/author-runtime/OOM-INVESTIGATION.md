# Ordinary watchface out-of-memory observation — OPEN

The unmodified submitted signed 0.1.10 program admitted the actual hosted
Vulcan/Cape launch into its own fresh simulator storage. Without clearing
that storage, a production-identity/key diagnostic watchface observer compiled
from the candidate 0.1.12 native source (ID `40597c44`, FR165 Music, ordinary
watchface heap 126784 bytes) reopened the launch and rendered its marker and
countdown before optional reload. The observer wraps actual framework callbacks
and selects English or Russian through an isolated application property; its
entry point and logging are diagnostic, not an exported release artifact.

`candidate.log` records warm English startup and wake; `russian.log` records the
Russian restart, LOW, a manually delivered SDK Temporal Event, wake, and an
uncaught `Out Of Memory Error` after the reload and several active updates. No
stack symbol was reported. This is a failed instrumented ordinary-heap integration, regardless
of the 10/10 separate SDK unit table; it does not by itself establish an
uninstrumented app failure. The failure point in a particular owner is
not yet established. The simulator runtime and ini were restored byte-for-byte;
original temporal registration remains unverified. The four PNGs are SDK screen
captures before the failure, not physical images.

Competing hypotheses: (1) the extra derived-outline bitmap, retained scanline or
its construction increases the live decoder peak; (2) the additional local
outline/resource references or other wake/restore retained state consume the
ordinary app heap before decoding; (3) observer logging/entry overhead or an
existing scene-delivery failure, unrelated to the new outline, explains the
failure. The current trace cannot distinguish them. The next experiment will
measure used memory at actual lifecycle and decoder boundaries and compare a
source-identical observer against a diagnostic-only variant that suppresses
outline work, retaining same real hosted input and app heap. Neither variant is
release evidence or grounds to claim a physical cause.

The signed 0.1.10 Music program then survived the same LOW / manually delivered
SDK Temporal Event / HIGH sequence and displayed the real downloaded Vulcan
rocket and flag. Its actual simulator storage was retained and copied into two
separate ordinary-watchface diagnostic runs. With only step-level diagnostic
logging added, the candidate failed on its first role-0 map decode step after
heap samples 111544 and 115960 bytes. A control using the predecessor decoder
without the new outline derivation also failed at the same boundary, after
111008 and 115424 bytes. Both use the original 126784-byte watchface limit,
Russian application language, the same production UUID/key and the same
retained seed. These reproduce the ordinary-watchface failure but do not alone
prove whether the additional instrumentation contributes. They refute an
explanation in which the outline-derivation implementation alone is necessary.
The failed task-owned simulator states are retained privately at
`/Users/jekamas/.codex/tmp/spacefox-display03-author/memory-run/`; the original
simulator state was restored. Next, test whether the currently loaded bundled
LOW map consumes the missing foreground headroom by removing only that optional
load in a diagnostic variant; do not ship a variant that omits the LOW map.

A further diagnostic suppressed both bundled LOW bitmap loads without changing
the candidate decoder, using the same copied real seed and Russian diagnostic
observer. It still failed at the first map decode step, with 111224 and 115640
bytes at the corresponding samples. This is evidence against the one loaded
LOW bitmap being the sole pressure source; the diagnostic intentionally lacks a
LOW map and is not a candidate. Next compare the actual 0.1.10 source, same
Russian language, observer and seed, to separate language/observer overhead
from newly retained state. The original signed 0.1.10 success above was English.

## Matched allocation and uninstrumented controls

The matched source-0.1.10 Russian observer survived decoding and had 87320 B
before packet binding and 102136 B after renderer preparation. The candidate
observer had 92816 B and 111024 B at the same boundaries and failed. The
lookup-omission diagnostic (not a usable watchface) fell to 105408 B after
renderer preparation but failed after its pending build was canceled and
restarted. Suppressing bitmap loading alone fell only to 110776 B and still
failed. Replacing persistent object/resource lookup with packed coordinates
and a lazy selected-resource function brought the candidate to 105792 B; the
first decoder step then reached a distinct `Unexpected Type Error` at chunk
validation. Paging the outline method and representing its previous scanline as
bytes reached later shards but the observed diagnostic still OOMed. The
`heap-owners-*.log` files retain these separate runs with only the private
observer tag removed; full task-owned inputs and logs remain under
`/Users/jekamas/.codex/tmp/spacefox-display03-author/`.

A separate direct production-UUID/key build of the plain app, without the
observer subclass, ran for 90 seconds on the real source-0.1.10-produced warm
cache in English. The SDK showed the accepted Vulcan rocket, US flag and Cape
point. After manually triggering a Temporal Event, selecting LOW, triggering a
second Temporal Event and selecting HIGH, the active scene and countdown
returned. An uninstrumented Russian run survived 65 seconds and the LOW/event/
HIGH sequence with the same scene. Its seed was the state actually produced by
the Russian diagnostic, including its application language property, rather
than a pristine 0.1.10-only seed. Neither run measures first-frame latency or
proves physical behavior. The diagnostic OOM is real in its observed ordinary
heap but cannot be described as an uninstrumented production-app failure;
observer allocations materially affect the outcome. Both plain runs restored
all 636 simulator files and the ini exactly; temporal registration remains
unverified. The current uninstrumented run is not a final source-bound release
qualification.

A targeted job observer found that a second reload had no incoming feed, while
the accepted visual batch serial advanced from 1 to 2 and canceled the pending
build. Identity equality is being checked before deciding whether this is a
safe duplicate; serial difference alone does not establish identical content.

The identity trace shows the second no-incoming-feed reload had the same URL,
selection digest `77d4b3173b019ee84b7eb751e81ccb7a47edfba560a54166bfb47f441e8b7b37`,
and transfer digest `3e4b028f9bfdf0355c3a801bbb1ef452511c15bdcd877be23a74b667ddcc8cb4`
as the first, even though the batch serial advanced 1→2. The production
candidate now preserves the existing job only when the admitted namespace and
both immutable digests match; changed or absent identities still cancel. This
is a coalescing hypothesis until the source-bound native test and repeated
actual framework witness complete. The trace does not show that the owner's
physical device experienced this sequence.

The SDK same-job test passed for an unchanged namespace and both immutable
digests, and canceled on a changed digest. An actual framework replay of the
same seed observed serial 1→2 with a pending build, no incoming feed and no
cancel after the change. The instrumented replay still ran out of memory while
reading a later shard; that retained margin failure remains distinct from the
plain app runs and does not establish the owner's physical cause.

During a later diagnostic, a task-launched extra simulator was discovered
writing the restored original storage. That diagnostic is not counted as READY
evidence. The simulator was closed, its altered/created files quarantined, and
the affected files restored from the pre-existing independently recorded copy.
All 636 file hashes and simulator.ini then matched the original manifest; the
lane was released and the original temporal registration remains unverified.
