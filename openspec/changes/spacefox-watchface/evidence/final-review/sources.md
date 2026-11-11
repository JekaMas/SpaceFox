# Final review: primary source ledger

Checked 2026-11-11. These are source-based platform observations and SpaceFox design
inferences, not device/Store observations. No LL2 inventory re-fetch was performed;
the dated839-record audit remains unchanged. Sources can change before release.

| ID | Primary source | Observation used / proof limit |
| --- | --- | --- |
| G01 | [Compatible devices](https://developer.garmin.com/connect-iq/compatible-devices/) | FR165 and Music list390×390 AMOLED, API 5.2; qualify each declared product, not just the latest SDK |
| G02 | [Device reference](https://developer.garmin.com/connect-iq/device-reference/) | Screen/icon/color properties;65536 colors is not a memory allowance |
| G03 | [Getting started](https://developer.garmin.com/connect-iq/connect-iq-basics/getting-started/) | Official SDK/Monkey C tooling and4096-bit RSA developer key; retain same key for updates |
| G04 | [Your first app](https://developer.garmin.com/connect-iq/connect-iq-basics/your-first-app/) | Device-targeted PRG and GARMIN/APPS; actual Mac USB/MTP route still unobserved |
| G05 | [VS Code extension](https://developer.garmin.com/connect-iq/reference-guides/visual-studio-code-extension/) | Build for Device versus Export Project; current tooling version must be pinned later |
| G06 | [Submit an app](https://developer.garmin.com/connect-iq/submit-an-app/) | Supported products, IQ export, metadata and Garmin review; pending owner preview is not public distribution |
| G07 | [Manifest and permissions](https://developer.garmin.com/connect-iq/articles/core-topics/Manifest_and_Permissions.html) | Type/UUID/products/minApiLevel/languages/permissions; permission table conflicts with G17 for SensorHistory watchface availability |
| G08 | [Watch-face UX](https://developer.garmin.com/connect-iq/articles/user-experience-guidelines/Watch_Faces.html) | AMOLED minute updates,10-percent lit-pixel limit and applicable burn-in constraints; restrained sparse AOD is our design response |
| G09 | [WatchFace API](https://developer.garmin.com/connect-iq/api-docs/Toybox/WatchUi/WatchFace.html) | Required initial view, active/sleep callbacks and timers; MIP onPartialUpdate list does not qualify FR165 |
| G10 | [Backgrounding](https://developer.garmin.com/connect-iq/articles/core-topics/Backgrounding.html) | Limited memory and30-second service lifetime; background may terminate |
| G11 | [Background API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Background.html) | Temporal minimum and approximately8KiB exit-data ceiling; tiny revision notification is our choice |
| G12 | [Background FAQ](https://developer.garmin.com/connect-iq/connect-iq-faq/how-do-i-create-a-connect-iq-background-service/) | Watchface communication in background, parser buffers plus dictionary; not a modern FR165 memory benchmark |
| G13 | [Communications API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Communications.html) | JSON response path; octet-stream ByteArray appears at6.0.3, not baseline 5.2. Plain-text exists but a manual codec is not qualified |
| G14 | [Storage API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Application/Storage.html) | Per-value32KB and target-dependent total/types; latest generic BitmapReference listing is not proof of FR165 persistence |
| G15 | [Resources](https://developer.garmin.com/connect-iq/articles/core-topics/Resources.html) | Scoped/background resources and loading on demand; shipping all preview resources is unnecessary |
| G16 | [SensorHistory API](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html) | Recent bounded history and permission; actual field samples/target availability remain native evidence |
| G17 | [App Types](https://developer.garmin.com/connect-iq/articles/connect-iq-basics/App_Types.html) | Allows SensorHistory for watchface, conflicting with G07 table; do not invent a resolved device verdict |
| G18 | [Cryptography](https://developer.garmin.com/connect-iq/api-docs/Toybox/Cryptography.html) | SHA-256 API exists before5.2; canonical encoding, target/background availability and cost still need qualification |
| G19 | [Full review guidelines](https://developer.garmin.com/connect-iq/articles/app-review-guidelines/Overview.html) | Available text datedOct13,2021: developer responsibility, performance, rights, privacy, truthful dependencies/support and under13 restriction. Recheck before native use/release |
| G20 | [SDK agreement](https://developer.garmin.com/downloads/connect-iq/sdks/agreement.html) | Garmin account/distribution terms and ownership/privacy requirements; not MIT and not legal clearance |
| G21 | [Publishing to the Store](https://developer.garmin.com/connect-iq/articles/core-topics/Publishing_to_the_Store.html) | Export/review/pending behavior. No review-time SLA is promised by SpaceFox |
| G22 | [Beta apps](https://developer.garmin.com/connect-iq/articles/core-topics/Beta_Apps.html) | Alternate UUID and owner-only visibility; not a shared beta or proven production migration |
| H01 | [GitHub schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) | Default branch, possible delay/drop, off-hour scheduling and60-day public-inactivity disablement |
| H02 | [Custom Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) | Build/upload/deploy artifact, Pages permissions and environment; complete artifact assembly is SpaceFox's responsibility |
| H03 | [Concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) | Serial execution/pending behavior does not prove logical event order; CAS/generation recovery is our design |
| H04 | [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) | Standard public runners free, storage limits separate; no promise of unlimited/permanent free hosting |
| H05 | [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) | Static hosting limits/rate limits; custom Actions exception to10-build/hour soft limit |
| L01 | [TheSpaceDevs FAQ](https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md) | Anonymous15calls/hour and cached distribution recommendation; does not license arbitrary linked artwork or prove worldwide accuracy |

The public Garmin wrapper `/connect-iq/app-review-guidelines/` returned navigation
without body. Gatsby page metadata identified `app-review-guidelines/Overview.html`;
the linked official article was read directly over HTTPS. The browser search tool
could not open that direct article, but ordinary HTTP retrieval succeeded. The same
method read Publishing_to_the_Store and Beta_Apps. No community forum statement is
used as a platform requirement. No agreements were accepted or accounts created.

SpaceFox choices, not Garmin/GitHub mandates:60/15-minute polling,3h/45min stale
limits, JSON-geometry qualification baseline, feed-state Git ledger,64KiB current
ledger,8KiB feed,1MiB site,1-day artifact retention and 90-day major-transition support.
They require implementation/measurement; changing them requires explicit contract
reconciliation, not silently claiming they are platform defaults.
