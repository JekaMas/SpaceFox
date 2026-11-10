# Proposal

## Why

SpaceFox should be available without payment and useful to families in the main
Garmin interface languages. The Russian-only prototype and missing project
license currently make those intentions unclear.

## What Changes

- Add a shared catalog for all 36 Connect IQ language identifiers, with complete
  draft UI translations, language direction and an explicit review status.
- Let the browser prototype select a language, detect the browser preference and
  fall back to English, preserving the launch/fitness settings and compact layout.
- Apply MIT to original SpaceFox work, retain dependency notices, and document
  free official distribution without restricting downstream MIT permissions.
- Replace the exported preview's bundled Codex shell with an original, repeatable
  standalone page. Do not redistribute that service runtime as SpaceFox code.
- Keep native language/font/device qualification in the existing watch-face
  implementation plan. This change does not build or publish a Garmin app.

## Capabilities

### New Capabilities

- `localization`: complete language resources and deterministic preview language
  selection, with honest draft/native-support boundaries.
- `open-distribution`: permissive project licensing and explicit component scope
  for source and future free official releases.

### Modified Capabilities

None. The original `spacefox-watchface` change remains unarchived; its native
implementation will consume these resources and release policies.

## Impact

Adds `locales/`, preview localization/build code, license texts and documentation.
No SDK installation, paid service, live API access or external publication.
The pinned workflow is a separately owned submodule with no redistribution grant
asserted in its README; it is outside SpaceFox MIT and future product packages.
