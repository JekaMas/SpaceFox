## Behavioral dependency graph

Initial view → first frame clock/date → deferred cache admission → verified facts → optional scene build → READY render. ACTIVE draw reads current UTC independently of build progress. LOW/OFF/hide cancels active work; HIGH resumes only after a frame. FeedService acquires staged text, catalog then immutable closure; foreground validates before admitting. Retained startup uses strict cache restoration and recovery; empty startup cannot assume a READY packet. The clock path must not depend on any of these optional edges.

## Investigation and boundaries

0.1.18 physical failure is real but unclassified. Obtain CIQ log or matching natural-path reproducer before attributing cause. Evaluate actual heap peak, graphics-pool lifetimes and work slice duration independently; allocation exceptions alone do not establish safety. Do not change normal visual design or source retention to obtain a green. Preserve prior scoped simulator evidence, and record newly invalidated boundaries.

## Cases before implementation

P2: empty, retained, bad cache and optional-failure first-frame paths (4). P3: pending decode advancing, delayed catch-up, LOW minute and return HIGH (4). P1/P7: cold provisional feed/catalog/asset staging, accepted cache reopen, failed replacement/recovery, pending decode LOW/HIGH, hide/reopen, OFF/HIGH, failure window 5–10s and 15-minute endurance (8). Include real memory and graphics peak observations and callback timings; neither a stub nor a seeded READY scene proves natural acquisition. Physical cold/reopen and 15 minutes remain independent acceptance.

## Watchdog repair under investigation

The isolated live SDK RED mapped the foreground background-data callback to current feed parsing and `recordIdentity` hashing. Stage strict admission as bounded event turns: validate the exact immutable provisional identity and catalog, parse, validate, compute each existing digest, then perform the existing atomic promotion. A paused/canceled generation must never promote stale work; newer provisional input must be rechecked. Keep accepted source age, publisher floor, raw bytes and recovery seal intact. Release optional render/decoded resources while parse state is resident, retain compact selected context for clock/facts, and measure actual heap/graphics overlap rather than assuming event separation itself provides headroom. LOW/OFF/hide must not start timers; pending work must safely resume or restart on HIGH after a clock frame. Existing synchronous cache consumers stay semantically equivalent and need directly affected transactional tests.

## Provider icon budget

A user complication's icon is optional and provider-controlled. Admit only a managed `Graphics.BitmapReference` with positive dimensions no larger than 96×96; retain normal scaled display for admitted icons. This bounds four full-color icon payloads to at most 147,456 bytes under the four-byte pixel estimate. A larger or unsupported icon uses a neutral marker; it does not change the selected field, value, unit or color. Null icon retains the existing absent-icon presentation. Width/height lookup and rendering remain guarded, and icon references remain evictable under the documented SDK graphics-pool contract. The limit is tied to the FR165 conditional working-set margin in `evidence/GRAPHICS-LEDGER.md`, not a claim about the undocumented native allocator or a universal physical memory guarantee.
