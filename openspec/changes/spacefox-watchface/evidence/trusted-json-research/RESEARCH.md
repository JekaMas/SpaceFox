# Trusted-schema JSON experiment

The following investigation checkpoints are chronological. Final author status
is in `AUTHOR.md`; independent corrections and final proof boundaries are in
`PEER.md`. Earlier incomplete/failed experiments remain incomplete/failed at
their recorded boundary, not current final claims.

Baseline: public 0.2.2 source d1cbce712d8f877ed02419577ef4c5dd561fc1ac. User authorizes removing historical integrity, provenance, repeated parsing and recovery contracts where unnecessary; retain usable default feed, local clock/countdown and uncertainty, core facts before optional art, atomic offline snapshot after interrupted save, LOW/map/point/rocket/four fields and autonomous scheduled publishing. Old receipts are historical, not new requirements. This research changes no running publisher or deployed feed until coordinated delivery.

Garmin's [Communications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Communications.html) supports JSON response since API 1.3 with `application/json`, text response since 3.0 with `text/plain`, and background context. The current `.txt` request uses text/plain; response format and actual hosting content type must both change for native JSON. [Monkey C](https://developer.garmin.com/connect-iq/reference-guides/monkey-c-reference/) documents arrays and objects as more space-efficient than dictionary hash tables and reference-counted memory. [Storage](https://developer.garmin.com/connect-iq/api-docs/Toybox/Application/Storage.html) supports arrays/dictionaries and limits values to 32 KiB; it does not document atomicity across multiple keys. [Background services](https://developer.garmin.com/connect-iq/articles/core-topics/Backgrounding.html) use a smaller heap, may be terminated and have a 30-second lifetime. No precise watchdog margin or atomic write theorem is inferred from these documents.

Candidate set: existing schema text and complete admission; built-in JSON with compact object; built-in JSON with positional fixed-schema arrays; preprojected small core snapshot and independent optional assets; binary only if a compatible implementation demonstrably improves end-to-end results. Compare equal captured launch facts and same lifecycle; JSON byte count alone is not a speed result. Count only observed CPU/wall, sampled heap (not peak), storage operations and fact readiness with their actual boundaries. A single durable slot write plus commit-pointer publication may protect previous accepted data when an interrupted update leaves the first slot intact; test actual storage behavior and interruption rather than assuming cross-key atomicity.

Initial real fixture `tests/fixtures/fr165-runtime-20261116/feed.txt` is 5,660 bytes and its selected catalog is required by the current admission path. The live server currently returns both `/feed.json` as `application/json` and `/feed.json.txt` as `text/plain`, both 5,660 bytes at this observation. The executable `compare.py` preserves current launch display fields and the captured upcoming rows for an exploratory projection, and compares object vs positional JSON. It produces 3,974 vs 2,988 bytes; Python median parse/field extraction was 0.0237 vs 0.0180 vs 0.0147 ms for original/object/array on this host. These timings are parse-and-selection only and not watch, HTTP, admission, storage or visual results; the projections are not yet implemented product formats. Raw individual samples are in `host-results.json`.

A first isolated SDK compile failed to locate the copied device profile because Java uses its own user-home; a second correctly found it but the mounted SDK was read-only. Both original logs are private task-lane setup failures. The SDK was copied into the isolated lane before continuing; no foreign SDK files or processes are touched.

Current 0.2.2 source, SDK 9.3 Linux simulator FR165M, captured 5,660-byte feed and 27 real objects: the existing `b1MeasureCapturedCallbacks` test passed after the isolated compiler setup. `stageMs=7`, `beginMs=1`, largest batch scan callback 18 ms, largest object put 3 ms, and synchronous test-helper admission 494 ms on this host; see `sdk-baseline.log`. The test downloads all 27 locally substituted objects before manually pumping admission. This is not HTTP wall time, natural time-to-facts, a physical watchdog margin or a peak-memory sample. It gives a real current-source reference for selecting a next experiment, not a like-for-like candidate result.

A separate FR165M SDK resource/storage experiment used the same three actual launch rows, first projecting 17 display fields. The object JSON was 1,489 bytes; positional JSON was 907 bytes. On this test host, loading each compiled JSON resource, writing a value and pointer, reading the value and creating one `SceneContext` sampled 0/2/1 ms for object and 0/0/1 ms for array respectively; app `usedMemory` before and after resource load was 88,824/91,808 and 88,824/90,512 bytes. These are individual sampled values, not peaks. Source, inputs, compile and test logs are in `sdk-candidate/`. The fixture is an exploratory partial projection, not a production-equivalence proof: it simplifies precision and omits some scheduling/visual information, and resource loading substitutes for network JSON parsing. It does not justify claiming 494 ms versus 1 ms end-to-end, nor silently dropping those fields. Before using a projection, it must preserve exact/minute/coarse semantics, future selection, asset references and actual background delivery.

A preliminary native two-slot owner and full 22-field projection were separately exercised with the captured coarse and exact launches. The SDK test first failed because `Test.assertEqual` distinguished numeric object types for equal 550 values; the retained first failure and corrected numeric comparison are separate. The corrected test passes an injected failure of the commit-pointer write (old slot remains selected), restores the same coarse launch, then saves/restores the exact launch with 550 seconds, eligible reminder and point. This is an injected storage adapter and directly called native owner, not real background/network/restart proof. Full real coarse snapshot is 2,526 UTF-8 bytes including policy and asset references; no watch cutover has yet been proven.

A crucial API constraint surfaced while wiring the network response: Garmin documents `Communications.ContentType` as Dictionary/String/iterator/ByteArray, not a root Array. The wire wraps the positional snapshot in one `{"data": [...]}` object. Earlier array-root experiments are resource-only and cannot establish an accepted HTTP callback shape. The wrapper adds nine UTF-8 bytes; native network delivery remains to be observed.

The first host integration run retained at the private task lane passed seven cases and failed two old transport assertions because the new `watch.json` is an additional derived root. The original log is retained; the assertions are being updated to explicitly require that root and its unchanged source validation age, while retaining exact checks for existing artifact bytes and sidecars.

Binary transport was considered and rejected for the core snapshot: the [official response enum](https://developer.garmin.com/connect-iq/api-docs/Toybox/Communications.html) lists octet-stream/ByteArray only from API 6.0.3, while this application supports API 5.1. `Lang.ByteArray` itself exists from API 3.0, but that does not make raw HTTP response transport available. No binary speed claim was made.

The selected design uses a top-level JSON object containing one positional snapshot, with selected and upcoming rows, source time/precision and independent visual references. Publisher-side projection eliminates the watch's repeated feed parsing and hashing. The spec now retires those prior on-watch feed-specific obligations while preserving the last complete snapshot on an interrupted pointer switch and retaining source precision, clock, queue, optional artwork and LOW behavior. The old proof artifacts remain historical. This design is in implementation, not yet self-GREEN.

Native communications experiments: a genuine simulator background event reached the local HTTP test server but returned -1001 because Garmin requires HTTPS. A self-signed local HTTPS attempt returned 404 without a completed server request; this is not yet a successful native JSON network observation and does not establish an application failure. The local server itself returned 200 to an independently trusted client. Logs remain in `sdk-candidate/` and private task lane. The foreground resource-only experiment remains distinct from this missing network boundary.

A genuine background event with a public HTTPS echo and the captured compact JSON exposed a real SDK difference: epoch values arrived as `Lang.Double`, so the first foreground implementation treated target/order as absent and displayed the next launch. `app-27.log` retains the wrong selected frame and exact number types. Snapshot storage now converts the fixed schema's integer fields to Long/Number once; `app-28.log` shows HTTP 200, 743 ms request-to-callback, background snapshot publication and the selected Taiyuan ID with point and target 1795042200 in a normal frame 788 ms after event start, sampled foreground usedMemory 92,248 bytes. The HTTPS echo includes its extra response envelope, so timing is not directly comparable to the prior manually pumped baseline. The source changed during this diagnostic compile in an unrelated failure-retry guard; it is a diagnosis, not an exact-final-source qualification. Physical, real phone transport and stable-source LOW/reopen remain unobserved.


## Independent primary-source technique comparison (2026-11-17)

The peer checked the official Garmin response enum, callback type, object store
and background documentation directly. JSON is available from API 1.3 and uses
`application/json`; octet-stream ByteArray response starts at 6.0.3. Storage
supports the chosen values but promises no cross-key transaction. The response
wrapper and one numeric conversion at the network boundary follow these platform
constraints; resource-load timing remains a separate observation.

| Technique and primary source | Relevant property | Decision for this runtime |
| --- | --- | --- |
| [RapidJSON SAX/direct custom structure](https://rapidjson.org/md_doc_sax.html#ParsingToCustomDataStructure) | Handler events can build the destination without a generic DOM; filtering can discard unwanted fields. | Publisher projection adopts the destination-first idea. A new Monkey C SAX parser would restore the code and per-token work intentionally removed; Garmin JSON already supplies objects. No C++ parser is imported. |
| [RapidJSON in-situ parsing](https://rapidjson.org/md_doc_dom.html#InSituParsing) | Decodes strings in a writable input buffer; retained values depend on that buffer's lifetime. | The Garmin callback offers parsed objects, not a writable JSON buffer. Porting this would require a custom text path and keep its input resident. No improvement is measured or claimed here. |
| [jsmn token slices](https://github.com/zserge/jsmn) | Tokens refer to ranges in the original JSON and support incremental/zero-copy processing. | Appropriate when the application already owns text and token scanning is cheap. Here it would reintroduce text acquisition, escaping, field lookup and buffer lifetime; no on-watch token port was selected. |
| [simdjson On-Demand and schema-based models](https://simdjson.org/api/3.0.0/md_doc_ondemand_design.html) | Contrasts DOM, events, compile-time schemas and lazy traversal; fixed field order removes context/key lookup work. | The fixed publisher schema uses positional rows and constructs the existing scene directly. SIMD/lazy C++ implementation results are not Monkey C measurements, and no generator or On-Demand framework is added. |
| [ArduinoJson filtering and chunks](https://arduinojson.org/v7/how-to/deserialize-a-very-large-document/) | Filtering limits retained fields; chunks limit simultaneous document residency. | Selected/upcoming facts are projected before transmission; optional visual chunks remain separate. JSON callback parsing itself is not claimed to be streaming or filtered by Garmin. |
| [Nanopb bounded schema generation](https://jpa.kapsi.fi/nanopb/docs/concepts.html) | Generated fixed-capacity fields or callbacks can bound variable data. | A binary schema adds a compiler/decoder and requires a compatible binary HTTP path. API 5.1 support and no demonstrated equal-workload win rule it out for this batch. |

These are technique comparisons from maintainers' documentation, not benchmarks
of those libraries on Garmin. The selected simplification removes a watch-side
parser/admission dependency and transmits only complete scene/scheduling values.
The actual wire comparison is 5,660 to 2,547 UTF-8 bytes for the same captured
selected/upcoming display projection, a reduction of 3,113 bytes (55.0%). It is a
wire-size result, not a CPU/heap/speed multiplier or total publisher/artwork
traffic reduction: the older feed and optional assets remain for their consumers. Full admitted baseline 494 ms,
partial-resource 1 ms and network echo 788 ms have different boundaries and must
not be divided into a speedup. No equal-boundary full end-to-end timing or peak
heap improvement has been demonstrated. The observed wins are smaller wire,
fewer required objects before facts, and deletion of the repeated on-watch
feed/chunk/hash/reparse owners, with local functionality checked separately.

Projection review maps all 22 row fields to the prior SceneContext projection:
identity/title/operator/site, source-qualified point, UTC/precision/date,
retention/order/source-age/policy, reschedule/stale/hold, display NET and reminder
eligibility. Selected catalog fallbacks and future-row source values remain;
terminal updates and independent transfer/selection/site/identity references are
carried beside the rows. Dictionary-key validation, source rehashing and old
sealed-feed recovery are intentionally retired, not silently passed. HTTPS,
known snapshot/version/row shape, runtime numeric normalization and bounded
optional visual reads remain the small implementation boundary.
