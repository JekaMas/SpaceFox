# Proposal

## Why

SpaceFox helps a child follow rocket launches from an everyday Garmin watch:
current time and useful fitness data remain readable alongside the next launch,
its rocket and its location on Earth. The existing browser mockup demonstrates
the layout, but live updates and a maintainable visual catalog are still missing.

## What Changes

- Define a Forerunner 165 watch face with four configurable fitness fields, a
  local countdown, a model-specific rocket image and a launch-site globe/map.
  Use a compact Earth/rocket/information band with rocket, company and mission
  context on the right, and a larger country/site label below the countdown.
- Refresh the launch schedule through the paired phone, approximately every five
  minutes when available, retaining useful cached information without inventing
  launch certainty or a confirmed liftoff.
- Keep the compact design from the latest answer: no permanent update timestamp;
  a circled `!` plus amber countdown for a reschedule and a separate stale marker.
- Add a short ignition/ascent animation while the display is active; allow it to
  be disabled and stop it when the watch face sleeps.
- Make site coordinates, rocket mappings, images and animation frames versioned
  data so they can be added or corrected without editing watch-face layout code.
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
  countdown timing, reschedules, uncertainty and cached-data freshness.
- `visual-catalog`: maintainable, versioned site/rocket metadata and visual assets
  with validation, offline fallback and atomic update activation.

### Modified Capabilities

None; this is a new repository with no existing main specifications.

## Impact

Planned owners are a Monkey C watch face, a small cached data service and a
versioned catalog/asset pipeline. Initial visuals cover Falcon 9, Electron and
Ariane 6 (the Ariane 62 variant in the mockup), plus a clearly generic fallback.
Launch Library 2 is the proposed provider; its coverage and rate limits must be
preserved in product claims. Paid hosting, publication, SDK installation and a
completed native application are outside this specification/setup increment.
