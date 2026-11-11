# Proposal

## Why

SpaceFox helps a child follow rocket launches from an everyday Garmin watch:
current time and useful fitness data remain readable alongside the next launch,
its rocket and its location on Earth. The existing browser mockup demonstrates
the layout, but live updates and a maintainable visual catalog are still missing.

## What Changes

- Define a Forerunner 165 watch face with four configurable fitness fields, a
  local countdown, a model-specific rocket image and a launch-site globe/map.
  Use the accepted full-screen flat map with gradual fading and no clock tile:
  rocket/company and mission purpose above time, countdown adjacent to time,
  four large fields in 2×2, country/site below the fields and a large left rocket.
- Calculate the countdown entirely on the watch from its current clock and the
  cached UTC launch time, including after sleep and without connectivity.
- Refresh the schedule hourly by default and every fifteen minutes from two hours
  before a known launch through thirty minutes after its unconfirmed time.
  Unknown times use hourly checks; five-minute polling is an optional setting.
  Use the paired phone and a small personal static HTTPS feed. GitHub Actions
  runs a deterministic updater and publishes it with GitHub Pages; no AWS account,
  always-running backend, custom phone app or per-refresh LLM call is required.
  Polling and publisher/CDN delays affect how soon a change is learned, not the
  countdown's local progression; the longer update delay is an explicit trade-off.
  Retain cached information without inventing launch certainty or a confirmed liftoff.
- Keep the compact design from the latest answer: no permanent update timestamp;
  amber countdown for a reschedule and an independent dotted underline for stale data,
  with service-status badges removed from the face.
- Add a short ignition/ascent animation while the display is active; allow it to
  be disabled and stop it when the watch face sleeps. Add a separate sparse AMOLED
  AOD scene; the full-screen map is the active composition, not an AOD promise.
- Make site coordinates, rocket mappings, images and animation frames versioned
  static data/assets so they can be added or corrected without editing watch-face
  layout code. Preserve provider-validation age across file/CDN re-fetches.
- Require worldwide public orbital and civil suborbital/scientific coverage of
  countries/territories, configurations, launch organizations and pad-level sites.
  Bind paginated source inventories and official supplements to distinct metadata,
  artwork, marks and geographic-view acceptance; the initial sample pack does not
  establish completeness. See `evidence/global-catalog/` and `docs/GLOBAL_CATALOG.md`.
- Supply an MIT agent setup guide for another family's own GitHub feed, including
  URL configuration, quotas, schedule disablement, recovery and actual readback.
- Define native development/personal PRG/Store IQ, preserved signing identity,
  truthful free publication, platform eligibility and privacy/rights checks.
  Separate code releases from content updates; qualify FR165 API 5.2, response
  bounds, AOD, cache migrations and 90-day wire compatibility.
- Keep publisher active/pending state and request reservations in a dedicated
  feed-state branch with monotonic/CAS recovery and complete Pages artifacts;
  a public CDN response is not the authoritative recovery ledger.
- Consume the shared 36-language catalog, qualify native text/fonts/RTL on FR165
  and distribute original SpaceFox work under MIT with free official downloads.
  The completed resource/license foundation is tracked separately in
  `../localize-free-distribution/`; native support is not established by its preview.
- Preserve the current mockup and explicitly audit demonstrated versus missing
  behavior. This repository-creation increment authors the specification and
  setup only; native implementation remains in the implementation tasks.

## Capabilities

### New Capabilities

- `watchface`: readable time/fitness/launch display, geographic view, compact
  exceptional-state indicators and active-display animation.
- `launch-schedule`: automatic schedule refresh, launch identity/selection,
  countdown timing, reschedules, uncertainty, source freshness and reproducible
  personal static-feed publication.
- `visual-catalog`: maintainable, versioned site/rocket metadata and visual assets
  with validation, offline fallback and atomic update activation.
- `release-lifecycle`: qualified builds, signing, personal installation, free Store
  distribution and compatible/recoverable code-versus-content updates.

### Modified Capabilities

None; this is a new repository with no existing main specifications.

## Impact

Planned owners are a Monkey C watch face, a scheduled provider-to-static-feed
updater, a GitHub Pages publication workflow and a versioned catalog/asset pipeline.
The backend service in the initial design is replaced by this personal feed.
The existing sample visuals cover Falcon 9, Falcon Heavy, Electron, Ariane 62 and
Ariane 64 plus a generic fallback. The required production catalog is global;
all known current configurations require specific or explicitly reviewed shared
visuals before full artwork acceptance. Launch Library 2 API 2.3.0 is the checked
provider baseline, supplemented from official sources; its coverage and rate limits must be
preserved in product claims. The current increment updates the specification and
agent instructions only. Enabling scheduled workflows/Pages, paid hosting, SDK
installation and native implementation are separate implementation work. The
MIT source/specification remains published in the existing GitHub repository.
The final source-based review is in `evidence/final-review/`; intended-user
routine platform review and native/device/Store evidence remain explicit release work.
The adult owner publishes from their own Garmin account. The owner has confirmed
both relevant age conditions for this instance; no age clarification remains open.
Exact private ages are not retained. The reusable audience-review contract remains.
