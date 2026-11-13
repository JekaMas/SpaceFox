# Native transport, cache and declarative renderer

This document retains the original bounded transport/cache observations. Public
feed-v1, optional profile and visual-v2 default statements below describe their
historical source; they are superseded by the sole current schema3/SFR1M
`/feed.json` contract in [NATIVE_MOTION_V3](NATIVE_MOTION_V3.md). Internal staging/
header version labels are not additional public wire majors. Current integrity,
source age, quota, atomic activation/reopen and resource bounds remain required;
retained historical receipts do not qualify the current implementation by themselves.

This increment extends the accepted native04/full face without changing its fonts,
icons, marker, map resources or layout. Native source is in `watchface/source/`.
The background service makes read-only HTTPS requests through Garmin's
`Communications.makeWebRequest`; the app never uploads health or location data.
`SensorHistory` remains the existing read-only fitness source. No GPS or raw
sensor activation is added. The FR165 target is API5.2; minimum API is now5.1
because the bounded parser/admission/decoder classes use the official `:extendedCode`
paging annotation. String comparison, sorting and display synchronization need5.0;
redraw, clock and drawing remain resident. The actual target remainsFR1655.2.
No older-firmware compatibility is inferred from compilation.

`FeedBaseUrl` is a personal HTTPS base URL with an empty default. Blank/invalid
configuration has no temporal fetch and starts at No Schedule, with actual Garmin
fitness values or unavailable dashes. A configured URL is a separate cache
namespace including its complete path. Data enters the scene only through the
validated persistent cache. The clock and countdown use local/UTC clock samples;
redraw does not fetch or read storage. The four independent fitness slots and
animation/AOD stop behavior are preserved.

## Feed admission and ordering

The watch requests `feed.json` as API3 plain-text response. The actual SDK JSON
experiment kept the latter duplicate key, which cannot prove strict wire admission.
An actual temporal request showed that TEXT_PLAIN returns application/json bytes
as a String on this pinned profile. The service checks raw decoded UTF8<=8192 and its SHA256 before durable provisional staging. It does not admit a source head or parse the full feed schema in background. The foreground parser checks depth<=8, nodes<=5000, container entries<=4096, duplicate keys, integer lexical form and trailing input before constructing `NativeFeed`. These work bounds exceed the possible typed entries in an8192-byte feed; there is no16-row dictionary or512-character feed-string cap. Feed bytes must be canonical compact JSON with sorted keys and minimal escapes;
raw Unicode is preserved. Generic SFV parsing also accepts Unicode/surrogate escapes. Small integers use Number; larger integers within signed64 use Long. Overflow integer tokens retain their exact decimal text in a distinct NativeIntegerLexeme type. Nonnegative source_status_id/source_precision_id metadata and positive refresh-policy values admit that type; UTC, indices, geometry and bounded schema counts retain exact Number/Long checks. Canonical serialization emits the original numeric token without quoting or floating conversion. Policy ordering and poll-interval equality are checked against the original exact integers before calculation projection.
No Toybox.Json, String.split/join, octet-stream response or executable data is used.
Transfer allocation precedes the parser; source byte admission alone is not a heap
measurement. Unit-runner heap observations are explicitly separate from ordinary
watch-face/background experiments.

The closed feed schema validates kinds/IDs, required nulls, integer UTC, timing
precision, policy, selected scope, dictionary references and semantic canonical
SHA256 of the embedded selected dictionary. Unverified source-position decimal
text is preserved as metadata and never becomes a qualified map point. Current
producer metadata does not carry qualified visuals; generic/no-point is deliberate.
The source country code and location name produce a short footer; original pad
and country names remain available and provide the explicit missing-field fallback.
No ID/name switch invents countries, locations or artwork.

The current draft feed-v1 requires `publisher` with instance (64 lower-case hex),
positive generation and signed `selectionValidatedUtc`, nullable only for never
qualified legacy state. Null qualification cannot activate or erase a cache.
The first accepted instance is pinned for that base URL; a different instance at
the same URL is rejected. Changing the feed URL establishes another namespace.
Reboot and switching away/back retain a per-URL monotonic publisher head.
At most eight namespaces can be pinned; identities are never network-evicted.
Intentional replacement at the same URL requires an
explicit app-data reset; an HTTP reply cannot request that reset.

Older generations reject, and same-generation conflicting documents reject,
including empty selections. Exact accepted replay does no provisional or admission write; the network attempt timestamp still writes once. A newer generation
preserves the true origin validation epoch: generation, retrieval, catalog update,
304 or an old200 never confer source freshness. Each selected launch also retains
its own source-validation UTC. A newer global selection can legitimately select
an older record; its older per-record age remains visible. Reschedule is per-ID
and latches for any same-ID timing change, including earlier targets and exact-to-unknown. Countdown zero remains
Awaiting Update. Default polling is3600s,900s in inclusive T-7200..T+1800,
optional configured fast>=300s. A slept-through near-window threshold remains
stale after return to hourly; a successful newer source validation clears the
record's stale latch only when its actual age permits it.

Temporal events are clamped against `getLastTemporalEventTime()+300`. Startup and
background exits arm the next source due or near-window transition (entry T−7200 and first normal second T+1801). A temporal wake checks due status; it does not itself authorize a source GET. The background
entry arms an hourly fallback before staging or network work so interruption does
not consume the only future event. An attempt is persisted before requesting.
A configured cache reuses its local schedule while requests fail. No timer counts
elapsed seconds and no redraw fetches data.

## Persistent activation and cache bounds

The service stages untrusted raw bytes behind a v2 provisional pointer. Each of at most16 positions has two512-character physical slots; unchanged exact chunks are reused, changed chunks are read back, and the pointer is written last. A failed stage preserves the prior pending pointer. This stage never changes accepted source age, publisher floor, active context or recovery. Background.exit sends only a small provisional descriptor. All provisional writes count separately from accepted-cache promotion writes.

AppBase.onBackgroundData processes this descriptor automatically while the face is active or always-on. Initial/onShow also processes an interrupted pending stage. Full raw/schema/catalog/ISO/source/order validation and atomic accepted promotion occur there, outside redraw. This explicit phase split replaced a full-background parser that produced actual NETWORK_RESPONSE_OUT_OF_MEMORY(-403) at8192 bytes; the red build/log is retained. Unit-runner memory is not the ordinary service quota.

An unprocessed pending feed temporarily releases reconstructible SceneRenderer
resources during synchronous foreground admission. The accepted packet, context
and optional bitmap remain resident. A finally block prepares/rebinds the renderer
before reload returns, including rejection and thrown plan-storage errors. Parsed
optional geometry is released after rasterization. Redraw gains no storage,
network or resource-reconstruction work from this maintenance boundary.

A changed feed URL releases the renderer before reconstructing that namespace's
cached raw feed. It clears the prior host's in-memory packet/context/bitmap and
replaces the cache owner before loading, because those objects belong to the old
namespace. The same finally block rebuilds the renderer for the new context or
empty fallback. Durable accepted data and per-URL publisher floors are retained;
no cross-host image or metadata is merged. Same-host pending admission still
retains its old working packet/context/bitmap during validation and rejection.

Feed data uses three slots, preserving active and recovery while writing a third.
Each slot contains at most16 string chunks of512 Unicode characters /2048 UTF8
bytes, followed by a v2 header. Restart reassembles into a bounded ByteArray and
converts UTF8 once, then revalidates the complete raw feed and embedded catalog.
The separately sealed v6 commit marker binds namespace, slot, raw/content hashes,
instance/generation, validation and local status. Header/readback precedes activation.
Source-validation-only admission writes the publisher-head/recovery/commit metadata and reuses accepted content chunks. Its preceding provisional stage may still write changed source-metadata chunks: the current8192-byte control changes three chunks plus the pointer (four writes), followed by one attempt write, three promotion writes and one processed acknowledgement. Those provisional writes are not described as metadata-only persistence. Startup reconstructs the latest source metadata using raw mutable-field witnesses, runs full validation, and streams the inverse hash against the unchanged durable original raw. A resealed projection is only a consistency witness; it cannot bypass full raw/schema/catalog validation. A per-URL publisher head is persisted before commitment;
interruption can preserve the prior display, but cannot reset the admission floor
by switching URLs. Unsupported/corrupt/incomplete raw data cannot become active;
restart tries active then recovery. A lost acknowledgement can recover old or fully
committed new state. Actual Storage plus explicit read/write fault boundaries are
qualified separately from undocumented physical power-loss atomicity.

The optional `selection.json` envelope is a small native contract, not the global
publisher catalog. It binds schema1, catalogDigest, launchId, modelId, full semantic
sha256, canvas, animation and ordered RAW-byte shard references. Each reference
requires `path:"objects/<sha256>.json"`, matching raw UTF8 SHA256 and decodedBytes.
Formatting-equivalent files require their own correct raw reference; the full
semantic visual digest may stay unchanged. A private semantic-to-raw override is
not accepted. The earlier violating experiment is retained as a red control. The current provider
pipeline does not yet emit this envelope; that integration remains open. Schedule
metadata commits and exits first. A later>=5minute event may request selection and
stage missing immutable `objects/<sha256>.json` shards. Failed optional requests
back off hourly. Existing digest-validated objects are reused. The feed currently does not pin the optional full asset digest; same-ID/catalog
old-image rollback is an explicit remaining bridge boundary. A changed launch,
model, catalog, host, missing object or mixed shard set cannot reuse an old visual
under a new identity.

The content cache reserves an indexed object before writing its raw bytes. At
most96 objects /393216 decoded bytes are charged, including interrupted writes.
Eviction removes only unreferenced objects and protects active, recovery and
current staging closures. If all space is protected, staging rejects while the
active visual remains usable. Garmin serialized overhead, per-value limits and
total device quota require separate actual measurements; decoded-byte bounds are
not represented as serialized size or graphics RAM.

## SFV1 and redraw

The accepted producer's fixed SFV array, RGB24 palette, packedXY pool and op0
polygons are implemented. The producer still supports4096-byte shards /65536-byte
logical assets /4096 vertices /512 commands /4096 references. This native increment
admits a smaller measured profile: total decoded raw shards<=512 bytes, at most4
shards, pooled vertices<=32, commands<=16, references<=64 and polygon vertices<=16.
Larger accepted producer assets are unsupported here and preserve generic/old-active
fallback. These limits do not change the producer contract or close full visual tasks.
Schema/version, integer units/canvas, palette order, first-use unique pool, references,
nonzero simple polygons, animation and complete ordered semantic digest are checked.
Canonical hashing uses typed semantic JSON in128-character UTF8/ByteArray chunks.
The independent literal digest is
`461f4b86f4735f69acea89bf6c9aedf7a36e30c6705e1553e6d1a03a91755099`.
Decoded fragments from successful semantic activation are reused to rasterize;
there is no second parse/hash during bitmap construction. Raw background staging
is provisional. Foreground activation is attempted outside redraw on actual high-power onExitSleep or an actual display-mode change to HIGH. Schedule context appears first through onBackgroundData. AppBase.onDisplayModeChanged/System.getDisplayMode initialize and synchronize actual HIGH/LOW/OFF state; animation remains admitted only by the real onExitSleep lifecycle.
Ar62's actual high-power parsing watchdog is retained. Required larger rockets,
marks and world layers need bounded activation steps/packed data in a later unit.

The foreground prepares one transparent54x124 bitmap with aspect-preserving fit
inside the existing rocket frame. It reads/validates shards on first actual high-power wake after context replacement,
then keeps the bitmap. Redraw uses that bitmap and finite affine transforms only;
no storage, transfer, full catalog load or geometry reconstruction occurs there.
Animation remains bounded by actual watch-face high-power lifecycle and stops in
AOD, when disabled, on hide and on context replacement. A settings change may
reprepare existing scene resources; redraw does not.

## Evidence and limits

Canonical evidence: `openspec/changes/spacefox-watchface/evidence/native-transport/round1/`.
The two accepted parent heads were actually merged; direct Git object/metadata
union is in `merge-preservation.json`. The WF06.P2 descriptor's nominal80px wording
was corrected from accepted resource metrics to83.3737px Barlow600; no font pixels
or resource files were changed for this erratum.

The original c600 actual emitted2151-byte fixture is retained and rejected for
activation because it lacks the required publisher envelope and sourced footer
fields. Native envelope/geometry literals are explicitly separate controlled
vectors. `producer-6956153-feed.json` is an exact2196-byte output of clean backend
source6956153 with unknown typed IDs and NZ/New Cosmodrome source fields. Its
SHA is83dcbff7fc76a042d1ceca5f7d4e3789c53f3e2022002b0aaf3f0acd8d0ea146.
Backend independent review/root acceptance and actual Pages/phone delivery are separate; this fixture is not a live-provider or published-feed claim. The producer695 ESA control uses actual catalog organization27 and its23 country dependencies (24 rows), a4096-character mission purpose and exactly8192 raw bytes. It is a controlled launch through immutable producer code, not a live ESA launch. Older padded-ISO8192 stress fixtures are diagnostic memory probes and are not producer-valid conformance inputs.

No whole task2.2/3.2/4.2/4.4/4.5, physical FR165, paired Garmin Connect phone,
qualified public HTTPS feed, all valid8192-byte wire shapes, global geometry/artwork, full languages, hardware
sleep/power-loss/battery, release signing, Store publication or update acceptance
is closed by this increment. Current simulator/network measurements and exact
remaining failures are recorded in the evidence packet, rather than inferred from
the successful direct native logic tests.


## Admission parity boundary

| Input | Producer695 / native candidate |
| --- | --- |
|24 actual ESA dictionary dependencies,600/4096-character purpose,8192 bytes | Producer emits/validates; ordinary current SDK transfer and foreground admission observed.24 is a sample, not a schema limit or worst-case capacity claim. |
| Long status253402300800 above UTC year9999 | Accepted as a non-UTC signed integer; UTC fields retain signed years0001..9999 bounds. |
| Status9223372036854775808 /500-digit status or precision ID /explicit null status | Independent R1 native repair admits nonnegative overflow metadata without precision loss and admits nullable status; raw bytes/digests survive source-only persistence and reopen. These samples do not prove every8KiB shape. |
| RefreshPolicy intervals/stale_cycles above signed64 | R2 validates exact positive integer bounds/order and poll equality before deriving arithmetic values. Policies with overflow tokens use min(value,315537897600) for calculation only, greater than every qualified UTC elapsed age; raw bytes retain original values. Native-width policies retain their existing v6 projection identity. Independent 500-digit/invalid-order/equality/reopen oracles are in independent-r2/. |
| Stable IDs / normalized source strings | No native256-ID or512-text cap. Full facts remain in durable raw; display strings are independently ellipsized. Capacity for every possible8192-byte ID arrangement is not established by the ESA sample. |
| Source timestamps | Full foreground schema validates source updated/validated ordering and exact/nominal/window/date coherence. R2 parses Python3.12 calendar/basic/ISO-week dates, reduced/basic/colon times, comma/dot fractions, single-character separators and fractional offsets against exact normalized UTC and source microseconds. Literal producer-valid positives/negatives are observed; this is not exhaustive grammar or future Python-runtime qualification. |
| Decimal-text-v1 position | Canonical decimal text is range-checked without binary rounding, including producer Decimal exponent limits; unverified positions never create points. |
| Corrupt/unsupported/malformed/old/conflicting input | Retains accepted context and age; raw provisional writes do not confer source admission. |

Garmin Storage serialization overhead and total device quota are not established by host JSON sizes or declared decoded-byte charges. Direct fault-store sequences qualify interruption semantics at explicit operations; they do not establish physical power-loss atomicity. The accepted producer caps and full visual tasks stay unchanged.

Reproduce the six controlled695 ESA fixtures without network calls using `python3 tools/reproduce_native_transport_fixtures.py --output build/native/producer-reproduction`. It extracts immutable695 producer code, runs it in an isolated temporary subprocess against the pinned local catalog inputs, records per-vector epochs and requires byte-identical agreement with the owned fixtures.


The earlier bounded-unit source eff0f4bf54e4be510dcf5ce515f0663018de3ce3 and its [round1 evidence](../openspec/changes/spacefox-watchface/evidence/native-transport/round1/RESULTS.md) remain unchanged historical receipts. The [independent R1 repair packet](../openspec/changes/spacefox-watchface/evidence/native-transport/independent-r1/REVIEW.md) records actual pre-fix refusal of the original wide-status fixture and explicit null, current28 compiled affected routines, and a separate ordinary126784B seeded8192-byte wide-status admission/reopen observation. The observer package excludes seed/raw fixture constants; it uses production startup/onShow full admission, with no network/BG/cadence claim. The raw test receipts retain dirty provenance and exact source hashes; a later clean freeze does not relabel those as clean executions or refresh old PNG pins. A DIFFERENT NEW verifier/root judgment is required after this repair; that historical R1 packet does not establish R2 policy/ISO support or whole task acceptance.

The [independent R2 repair packet](../openspec/changes/spacefox-watchface/evidence/native-transport/independent-r2/REVIEW.md) owns actual wide-policy/basic-ISO reds and current literal controls. Let D=253402300799−(−62135596800)=315537897599. For qualified elapsed age a∈[0,D], an interval>D can never become due, and floor(a/interval) is0. A positive stale-cycle count>D can never be reached because intervals are>=300. Saturation to D+1 therefore preserves these predicates without multiplication or floating conversion. Original exact ordering/equality must precede this projection. Native-width policies keep their old v6 representation to preserve accepted cache hashes; only previously unsupported overflow policies enter the normalized path. Primitive calculation projections, exact durable raw and source-only wire witnesses remain separate. Existing diagnostic v6 trust/migration and serialized storage quotas are not release-qualified.

The ISO oracle uses the prepared Python3.12 interpreter with immutable695 source. Python runtime behavior is an explicit input: the ambient Python3.14 rejects one reduced-hour fractional form accepted by3.12, so no unqualified future-interpreter grammar equivalence is claimed. Provider/runtime changes need their own source-pinned reconciliation. R2 still stops for a different new independent verifier and root judgment.

R2 source-time grammar is derived in [grammar/CONTRACT.md](../openspec/changes/spacefox-watchface/evidence/native-transport/independent-r2/grammar/CONTRACT.md), including global Z replacement before splitting dates, ISO-week ambiguity, unmarked basic fractions and Python3.12 local fraction tails. The actual compiled2594-row matrix and a separate full-feed NBSP/Cyrillic/non-BMP code-point/UTF8/raw-hash discriminator qualify these chosen grammar classes. They do not prove every possible string or every8192-byte feed arrangement.

Final R2 cold/reopen samples did not qualify warm admission with a resident optional bitmap. R3's plain production observer reproduced an ordinary-heap OOM at that boundary and repaired foreground renderer residency. The [R3 packet](../openspec/changes/spacefox-watchface/evidence/native-transport/independent-r3/REVIEW.md) records current true-bitmap8192 source-only promotion and invalid-feed preservation, sampled118880/126784B, plus plain mutable-source reopen105504B/0writes. Larger diagnostic-package OOMs remain retained, and phase samples are not exhaustive peaks. The current earlier-target full-content promotion was recovery without prior bitmap activation; a separate fixed full-content warm/bitmap control remains for the DIFFERENT NEW R4 and root judgment. The historical123176B warm receipt retains its older source boundary. No whole task, all-shape, hardware, storage-quota or full-visual acceptance follows.

The additive explicit wire3/SFR1 full-scene qualification profile, finite bounds,
code paging requirement and production activation gap are owned by
[NATIVE_RASTER_V3.md](NATIVE_RASTER_V3.md). The default producer remains visual-v2.
