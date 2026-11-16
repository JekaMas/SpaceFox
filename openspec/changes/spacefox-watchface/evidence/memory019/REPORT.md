# SpaceFox resource audit — final report

Completed on 2026-11-16 for the static/offline scope below. No product optimization has been applied by this analysis. Physical and graphics measurements listed below remain open.

Source: public main `943f320c33b253b913eb8276d1c09b65d51a6c8a`; released native source `8ca1b7a63e51692d173bedec762dc6d6cbcd8e1c`, version **0.1.18 / 256680ec**. Branch: `audit/memory-requests019-20261116`.

## Results that matter most

1. **The watch has little measured application-memory margin.** The retained production-identity, release-flag simulator runs observed peaks of 122.0 KiB on FR165 Music and 122.4 KiB on FR965 against a displayed 123.8 KiB limit. Approximate margin is **1.8 / 1.4 KiB**. This is a capacity risk; this audit did not reproduce a new OOM. The references, flags and exact original measurements are in [NATIVE.md](NATIVE.md).
2. **A host geography cache retains about 61 MiB.** One actual pinned corpus occupies 63,975,174 tracked Python bytes after dropping the caller reference. Clearing the LRU in that diagnostic process reduced tracked allocation to 8,615 bytes. This proves cache retention and release in CPython; it does not prove a native leak or that RSS immediately returns to the OS. See [CACHE-RELEASE-MEASUREMENT.json](CACHE-RELEASE-MEASUREMENT.json).
3. **The native object scanner repeats significant work.** For the retained real 17-object batch, 50,005 unique bytes cause **153 prefix object verifications / 527,343 hashed bytes**, before catalog/index/put/final-closure overhead. This is a static operation count, not a watch CPU-duration measurement. See [BATCH-COST.json](BATCH-COST.json).
4. **Publisher validation repeats expensive derivation.** The offline selected build called full catalog validation 16 times. Revalidating an unchanged artifact spawned three rasterizer children and took 5.448 seconds with instrumentation. Building the catalog and artifact took 20.744 and 46.527 seconds respectively. These macOS/Python 3.14 timings include profiler overhead; they are not Ubuntu CI timings. See [HOST-MEASUREMENT.json](HOST-MEASUREMENT.json).
5. **Several advertised bounds need careful interpretation.** The watch's 22-second check limits new request starts, not an already running asynchronous request. Immutable-object byte limits do not cover the complete persistent store. PNG/source size does not measure graphics-pool allocation. Steady redraw is network/storage-free, but cold layout and launch rollover can load local resources during their permitted frame. An unmatched map outline also needs about390 decoder row callbacks at the nominal50ms cadence; this is scene-readiness work, not a measured blocked wake.

## Coverage, file by file

[FILE-INVENTORY.csv](FILE-INVENTORY.csv) has one row for each of **18,772 base-tree files**, including its Git blob identity, bytes, package, review method and disposition. There are no pending or missing file dispositions. The audit does **not** call mechanical classification a manual code review.

| Package | Files | Review boundary |
|---|---:|---|
| Native runtime | 38 | Full source reads, ownership and allocation/release/request tracing |
| Publisher package | 19 | Resource-path source review plus per-function AST call index; pure validation/geometry lines not all manually re-reviewed |
| Scheduler/configuration | 4 | Workflow and Worker request/cadence/lifetime review |
| Native resources | 275 | Individual sizes, SHA, PNG dimensions, FNT and JSON metadata; load ownership traced |
| Engineering commands | 163 | Individual purpose/resource index; current CLI/build/release owners read; historical probes not executed |
| Browser research/prototypes | 127 | Script resource-site index and disposition outside the shipped runtime; selected lifetime owners read |
| Catalog/artwork/corpus/locales | 961 | Pinned finite source-data inventory and publisher loading boundaries |
| Native tests | 28 | Compile-path and proof-boundary inventory, outside the production source path |
| Host tests/fixtures | 1,242 | Per-file classification; Python resource/function index; selected proof readers inspected |
| Other executable helpers | 5 | Installer and preview/observer boundaries; excluded from production runtime as applicable |
| Documentation/build metadata | 274 | Non-executing input/configuration classification |
| Historical evidence | 15,636 | Preserved original evidence; not re-executed or manually re-reviewed |

431 non-historical Python files parsed successfully without execution. Their per-function allocation/I/O-related call sites and line numbers are in [PYTHON-RESOURCE-SCAN.json](PYTHON-RESOURCE-SCAN.json). This is a heuristic resource-call index, not Python alias resolution, a complete dynamic call graph or a new test result. The host test/fixture paths contain 1,112 `test_*` definitions; this number is not a test-run count.

The five vendored files are qualified at the caller/pin boundary, not through a fresh upstream implementation review. An exact-revision JetBrains semantic index was unavailable because login was required; direct source reads used the exact worktree. No other checkout's index was substituted.

## Memory ownership and release

[NATIVE.md](NATIVE.md) includes the app/view/callback ownership graph and the lifetime table for renderer, downloaded images, decoder, settings, locale resources, metrics, subscriptions and timers.

- Hiding the face or opening settings stops owned timers, cancels the decode job, unsubscribes selected fields and drops renderer/downloaded/mask/scale-canvas references.
- LOW stops active fitness sampling and decoding, skips repeated updates in the same minute, and retains enough scene state for fast wake. Retaining active bitmaps in LOW can trade memory for wake latency; dropping them blindly would reintroduce decode delays.
- Native SFR decoding uses a bounded shard, a 96-byte decode block and a previous scanline. Full rasters use graphics buffers; `.get()` retains a strong graphics-pool object. Completed decoding drops scanline, color, hash and drawing-context scratch state.
- A non-390 display uses a locked 390×390 16-bit logical canvas: nominal pixel storage is **304,200 bytes**, excluding overhead. That is separate from application-heap observations. The downloaded map, rocket, flag and optional outline add graphics-pool allocations whose exact peak is unmeasured.
- Monkey C uses reference counts. `pendingLoader` creates a persistent app↔view cycle. No growing sequence was observed; it needs a teardown-specific check before being labeled a leak. Timer and subscription callback roots have explicit stop paths. See the [Garmin language reference](https://developer.garmin.com/connect-iq/reference-guides/monkey-c-reference/).
- The host geography LRU is bounded to four keys but duplicates original coordinates and float working representations. Process exit releases it; operation-local clearing was measured separately. It is not an always-running service leak.

## External requests and expensive operations

[HOST-AND-REQUESTS.md](HOST-AND-REQUESTS.md) records request owners, authority, bounds, deadlines, cleanup and repeated work.

The watch only requests the static feed/object sidecars from its configured host. Countdown/redraw does not poll the launch provider. Source polling and metadata requests run in Actions, share the durable 15-attempt rolling-hour allowance, and preserve accepted source facts on failures. Production host HTTP uses killable worker deadlines. Optional operator-only readers use socket timeouts and have a weaker total-duration guarantee.

Both Actions cron and the Cloudflare clock can produce four triggers per hour. This can mean up to eight workflow starts per hour if both deliver; it does not mean eight permitted provider polls. The single writer group and durable cadence/quota prevent concurrent writers and duplicate source permission, but do not avoid all no-op clone/install/validation cost.

Full HTTPS readback checks every file and rechecks the root. It runs in several recovery phases. For illustration, the measured 106-file artifact requires 107 requests for one complete observation: initial root, 105 other files, final root. Actual hosted manifests were not fetched during this audit. At the configured maximum of 512 files, serial 20-second request deadlines can exceed job-level time limits; no current outage is inferred from this upper-bound calculation.

Git state opens a new temporary bare repository, fetches state/anchor history and validates artifact contents. Source and CAS checks are valuable; repeatedly re-rasterizing the same immutable content within one command is a separate cost. State/history growth is explicitly not lifetime-bounded. No authoritative history or accepted cache was modified in this audit.

## Ranked findings and proposed repair groups

All 27 IDs have source references and explanations in the three detailed reports. Priorities below rank future work; they are not new normative specification requirements or another development task list.

| Priority | IDs | Proposed unit and measurable verification |
|---|---|---|
| First | MEM-01, MEM-03, MEM-05 | Qualify app and graphics peaks together during actual release decoding plus active draw and real discovered custom fields. Increase the minimum measured app margin; proposed target ≥4 KiB improvement over the retained 1.4 KiB case. Measure native resource release separately. Preserve visuals and field support. |
| First | IO-01 | Keep a generation-bound scan cursor within one background event. Target linear prefix verification work for the same real batch; retain final complete digest/corruption validation and recovery pins. |
| First | HOST-01, HOST-03 | Remove whole-catalog copies from selected closures and reuse validation of the exact immutable artifact within one process. Target one source-pixel validation per exact identity instead of repeated rasterization; prove unchanged output bytes and all existing rejection behavior. Keep fresh remote/source/CAS fences. |
| Next | HOST-02, HOST-05 | Move heavy geography/renderer work after a genuinely due build decision. Target zero geography decode and zero Node/rsvg children in a no-op command. Release operation-local geography when no remaining owner needs it. Preserve autonomous scheduling and shared quota. |
| Next | HOST-04, HOST-06 | Reduce intermediate full reopens/readbacks, batch Git blob reads and add bounded Git execution. Preserve the required complete final observation and root-race checks; bounded parallel readback is an option. Measure request/process counts and elapsed time. |
| Next | CPU-01, CPU-02, CPU-04, PERF-01, MEM-02, MEM-04 | Event-local dictionary reuse, selected-field-only formatting, bounded layout reuse and packed map metadata. Compare cold frame and warm frame CPU separately. Do not trade the small heap margin for an unbounded cache or break the matching LOW map. |
| Later | IO-02, IO-03, CPU-03, LIFE-01 | Clarify deadline semantics and total-store accounting; avoid unnecessary cold settings allocation; qualify owner teardown. No arbitrary cache resets or loss of publisher floors. |
| Later | HOST-07, ASSET-01, ENG-01, ENG-02 | Pre-admission local reads, unused declared bitmap fonts, release source-scan costs and operator-only HTTP deadlines. Preserve signature/source guarantees and existing valid evidence. |
| Retire only with a dependency decision | CLEAN-01, CLEAN-02, WEB-01 | Initial 0.1.15 reminder-state upgrade, hardcoded 0.1.4 beta wrapper, old illustrative embed's global listener. These are specific legacy findings; do not infer all historical files can be deleted safely. |

No OOM fix, faster frame, reduced battery consumption, reduced request count or smaller release has been claimed as implemented.

## Tests, specification and evidence reconciliation

No product owner, test, fixture, compiler option or runtime contract changed. Existing valid product greens were retained; they were not rerun to make this audit look like new qualification.

| Existing evidence | What it establishes | What it does not establish |
|---|---|---|
| `fields018/peer-stock390`, `peer-stock454` release-flag observations | Actual release-identity finite steady/peak app memory and complete selected visuals on two simulator profiles | Exact graphics-pool peak, physical energy, all provider text/icons or long-run reclamation |
| `tests/test_native_cache_budget_whole.py` | Source-bound composition of original storage/heap experiments and current marker behavior; retained negative OOM witness | A fresh complete 0.1.18 resource-peak run |
| `watchface/display03-tests/MetricRoleTests.mc` and fields018 receipts | Selected sampling, subscription dedup/stop, LOW/OFF behavior and actual-ID selection | Physical sensor callback frequency, graphics allocations or every teardown byte |
| `tests/test_display04_operation_trace.py` and pixel readers | Exact source-bound operation/transform and mask evidence with explicit partial-reuse limits | Runtime energy, full watch timing or a new SDK execution from Python receipt checks |
| Current publisher/metadata tests and retained operational receipts | Quota, CAS, corruption/recovery and source-freshness behavior at their recorded owners | Present-day CI cost or a fresh live schedule observation |
| This audit's two offline host probes | One retained real launch's allocation/call counts and one pinned geography-cache release trace | Ubuntu CI benchmark, watch memory or publication acceptance |

Resource clauses reviewed include the 8 KiB feed; 4 KiB immutable object; 40-object/114,688-byte transfer; 256-file snapshot; 512-file/1 MiB protected delivery; foreground/background budgets and deadline; no network on redraw; and retained accepted state on failures. No caps were weakened. The 22-second request-start guard cannot itself prove the separate 30-second background-exit clause. Strong graphics locks must be measured apart from app heap. Broad old-record projection/initial reminder compatibility is recorded rather than silently called current-only cleanup.

## Remaining measurement limits

The following are **OPEN measurements**, not claimed passes: actual graphics-pool peak/freeing, native per-transition reclaimed bytes and long-run reference counts, physical battery consumption, physical wake/frame timing, real provider icon/text residency and Linux runner memory/cost. A controlled native probe and physical observation can close them in a subsequent authorized repair/qualification unit. Source inspection and this single host sample do not justify claiming that every resource behavior is measured.

The plan/progress journal is [AUDIT.md](AUDIT.md). The source file review ledger is [SOURCE-REVIEW.json](SOURCE-REVIEW.json); supporting tools are indexed in [TOOLS.md](TOOLS.md). Product source, schedules, caches and deployed services were left unchanged.
