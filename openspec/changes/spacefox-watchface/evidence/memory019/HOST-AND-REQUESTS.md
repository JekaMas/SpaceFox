# Publisher, scheduler and host resource audit

Scope: exact main943f320c, no network/provider/deploy activity performed. Per-module dispositions are in SOURCE-REVIEW.json; all431 non-historical Python sources have a syntax-tree resource-call index in PYTHON-RESOURCE-SCAN.json. Resource-path review is not a claim that every pure geometry/validation line was manually re-reviewed.

## Offline measurements

HOST-MEASUREMENT.json and measure_host.py preserve one retained real Starship launch, fixed source Date1794551192 and current product owners. Python3.14.7/macOS and existing local Node/librsvg were used, with cProfile+tracemalloc; these add overhead and timings are not a clean Ubuntu CI benchmark. No provider, Gitremote or hosted service was called. Numeric memory below is Python tracked allocation, not application-on-watch heap.

| Phase | Time with instrumentation | Python current at end | Python phase peak | Child processes |
|---|---:|---:|---:|---|
| Build full catalog |20.744s|70,480,459B|89,442,188B|0|
| Build selected artifact |46.527s|71,254,776B|88,002,236B|1Node +6rsvg|
| Validate same immutable artifact once |5.448s|71,399,266B|74,378,246B|3rsvg|

Artifact:106files /606,276bytes. Process high-water RSS reached390,365,184bytes; it includes instrumentation/allocator effects and excludes child RSS. It is not live Python object size or a device measurement. Catalog build called stable_id814,031times. Selected build revalidated the catalog16times; canonical encoder reached about3million calls. Repeated-artifact validation re-rasterized3roles. These are direct call counts, not an assumed optimization benefit.

## External request ownership and envelopes

| Route | Authority/cadence | Bound / cleanup | Cost caveat |
|---|---|---|---|
| Watch→staticPages | FeedService only;acceptednormal3600s/near900s default,firstfailure300s,pending5min |Serial GET,<=44starts,eventstart22scheck;feed8KiB,obj4KiBadmitted |Post-deliverysizecheck;noETag;foregroundneverpolls |
| Actions→LL2upcoming/detail |LL2Client.request→Publisher.reserve,shared15attempts/rollinghour |512KiBresponse,20sprocess/10ssocket,noautoresend;upcomingdefault2pages+2details |List/detailrecordobjects andbase64IPC overlap;429Retry-After only |
| Actions→LL2metadata |CatalogRefresh reserve_catalog yields todue schedule |2MiBpage,1-4requests/command,<=1024pages,20krows,64MiBrawcorpus |Parsedcurrent/previous/staging +deepcopies exceedraw-bytecapinRAM |
| Actions→GitHubAPI |Pagesrepo_call;status/OIDC/runfinality |64KiBAPI/32KiBOIDC,20sworker,serialpoll<=60,5sdefaultdelay |TransientPOST outcomeuncertain→noautomaticPOSTretry |
| Actions→staticPagesreadback |Site.observe onrecover andprePOST |Root8KiB,allimmutablefiles exact,rootrecheck;<=512files/1MiBunion |OnePythonprocessperHTTPfile;fullclosurecostoneveryrecover evennotdue |
| Actions→Gitstate/source |GitState.load/_context/write |CAS+anchor+sourcefence,temporarybaregitfinallyclosed |NoGitcommandtimeout,fullhistoryfetch/no-depth eachnewstore,perfilecat-file+show |
| Cloudflare→GitHubdispatch |4cron ticks/hour |OnePOST/10s/noRetry |Samecron alsoinActions;potential8workflowstarts/hour,not8providerpolls |
| CIprerequisites |installerperjob |Pinned2.3MBdebhash;EXITdeletesdownload;aptupdate/install |Repeatedinfiveisolatedjobs;outerjobtimeout,notcurltotaldeadline |

## Findings and proposed order

**HOST-01 / moderate / STATIC+NEW MEASUREMENT:** `catalog.dependency_closure:937-957` deepcopies the entire catalog before selecting rows, and `graphics.build_pack:642-711` returns another full catalog deepcopy even for a single asset. Full validation also repeats at nested helper boundaries. The measured current build performed16whole catalog validations. Use a validated immutable catalog context with a source digest and selected-row-only copies; never cache a mutable caller dictionary by object identity alone. Verify the same exact bytes/digests/rejection behavior, and measure one full build after repair.

**HOST-02 / moderate / STATIC+NEW MEASUREMENT:** `geographic_context:61-146` retains original points and `_line`float tuples, supplement coordinate arrays and duplicated float lines in an LRU(max4). This is bounded process-lifetime cache residency, not proven leak. Catalog building eagerly loads it from `catalog:1123-1127`, even before whether schedule polling is due. Cache release is separately measured in CACHE-RELEASE-MEASUREMENT.json; RSS high-water must not be called reclaimed/live. Prefer loading only for an actual asset build; keep one current corpus or explicit operation lifetime if safe.

**HOST-03 / high efficiency / STATIC+NEW MEASUREMENT:** `GitState.load:466-495`→`_files:521-538`→`validate_snapshot_artifact:185`→`native_motion.validate_artifact:352-545` repeats full source-pixel derivation on every state reopen. `_context`, `write`, `pending_files`, journal/delivery multiply those reopens within one command. Even unchanged offline validation spawned3rsvgchildren and took5.448s instrumented. Cache successful semantic validation *within one process* by exact Git commit/artifact/content digests AND renderer/source identity; retain current remote/source CAS checks. Separate authority refresh from revalidating unchanged immutable bytes. Do not remove publication readback or weaken corruption detection.

**HOST-04 / high efficiency / STATIC:** `cloud.Site.observe:434-468` reads all closure files serially for every recovery and prePOST. At configured512files and20s/request the theoretical bound exceeds outerjobtimeouts (512x20s;not an observed outage). Repeated job reopens also repeat Git/Pixels validation. Preserve the one required final complete exact readback, then reuse an authenticated exact receipt across unchanged intermediate phases with appropriate root/authority checks; or bounded parallel readback (small worker count and fullbytebudget). This needs concurrency/race tests, not merely faster happy-path screenshots.

**HOST-05 / moderate / STATIC:** both `.github/workflows/update-feed.yml:4-10` and `deploy/.../worker.mjs:2` wake4times/hour. Durable cadence/quota/concurrency prevent duplicate provider permissions, but duplicate workflow starts can still clone/install/validate. The workflow installs the renderer inprepare,arm,deploy,promote,metadata. Nativechart/geometry should be needed only when building or independently admitting changed content; early cheap no-op decision and reusable pinned prerequisite artifact/image can cut cost. Do not remove the independent timer without a fresh autonomous-delivery decision.

**HOST-06 / moderate long-term / STATIC:** `GitState` creates a new bare repo and fetches state+anchor without depth/history compaction. Archive/history is intentionally not lifetime-bounded. `measure()` itself materializes the complete reachable-object list and sizes. A single reservation can invoke at least4ls-remote and2fetch operations through_context/write/sourcefences, before otherGit/blob work. Add boundedGitdeadlines first, then a coherent process-local snapshot/batch-cat-file interface; history retention/compaction must preserve bootstrap and archive authority, not shallow-fetch blindly.

**HOST-07 / low / STATIC:** localcatalog/bridge/globalmap `_read/read_bytes` checks several byte caps after reading the full trusted pinned file; node/rsvgstdout checked after subprocess capture. Current repository pins bound legitimate input, so no remote attack or observedRAMfailure is asserted. For shared helpers that accept arbitrary paths, stat+limitedread gives clearer allocation bounds. Existing network workers already bound beforeparse and close/kill onerror.

## Retention and failure behavior that should be preserved

- HTTPresponse context managers close; subprocess.run(deadline) terminates the child on timeout. Base64 IPC creates copies but avoids keeping an unresolved workerthread and credentials in argv.
- GitState temporary directory is closed in cloud_feed finally; publisher-state/refresh/update entrypoints are reconciled separately in tools inventory.
- CatalogRefresh _save failure resets journal to durable authority and drops objects scratch; successful objects retained only for currentcache/stage/current+previous references within64MiBrawbudget.
- Frozen schedule values, immutable content-addressed bytes and `.txt` aliases share references in dictionaries; duplicate filenames are not automatically duplicate Python byte payloads. Disk/HTTP copies do add transfer/storage bytes.
- Bodyerror/304/assetonlybuild never manufactures fresh source validation or replaces accepted launch facts with an error.
