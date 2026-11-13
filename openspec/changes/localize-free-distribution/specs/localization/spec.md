# Spec Delta

## Purpose

Keep SpaceFox interface translations complete and selectable across the main
Connect IQ languages without confusing a draft resource with device qualification.

## ADDED Requirements

### Requirement: Complete language catalog

SpaceFox SHALL provide a single versioned catalog for all 36 Connect IQ language
identifiers documented on 2026-11-10. Every locale MUST have the same nonempty UI
keys and placeholders, a unique identifier, a text direction and a review status.
The resource validator MUST reject incomplete or inconsistent entries.

#### Scenario: Scope mandatory language qualification
- **WHEN** release language-quality readiness is assessed
- **THEN** all five primary modes require finite-real-corpus FR165 glyph/layout review;
  a missing software observation keeps that gate incomplete; human review is optional
  and physical product/release acceptance stays separate
- **AND** missing quality observations for the 31 retained best-effort modes do
  not block that gate; unsupported, duplicate or non-catalog primary IDs are rejected
- **AND** qualification flags and release manifest admission are not promoted by scope;
  actual source-bound finite-corpus software proof governs production/manifest admission
  through explicit softwareQualifiedLocales, independently of human/device flags
- **AND** translations, resources, selections and actual UI resources remain; invented display-string and normative Unicode
  edgecase qualification vectors are retired
- **AND** unbounded rare Unicode, arbitrary mixed-script provider names and perfect
  display outside primary modes are outside the quality target; input/grapheme
  integrity, common UI readability, 8192-byte and cache/memory guards remain required


#### Scenario: Validate language resources
- **WHEN** a contributor validates the catalog
- **THEN** all 36 complete locales pass and missing keys, duplicate identifiers,
  changed placeholders or invalid directions fail with the affected locale named
- **AND** draft status does not assert linguistic or native device acceptance

### Requirement: Predictable preview language selection

The preview SHALL offer every catalog locale, select a recognized saved choice
before browser preferences, and use English for unsupported inputs. Changing
language MUST preserve launch, schedule and fitness selections.
The fixed map, numeric countdown and physical scene order remain stable.

#### Scenario: Resolve a preview language
- **WHEN** the preview receives a saved locale or browser language preferences
- **THEN** it selects the first supported choice, including Chinese script/region
  matching, or English when none match
- **AND** language changes update visible and accessible labels without resetting
  the selected data; the fixed map and physical scene order remain unchanged

The native settings menu SHALL expose Auto (ID36) and only the five primary
choices (IDs0–4). All36 translation resources and internal IDs remain intact;
unqualified system selections use the existing English fallback.

Display testing SHALL use only launches since 2021-11-13T00:00:00Z, ALL published
future launches paginated until next=null, and actual UI/menu strings. Exact source
proofs and complete counts SHALL be retained; invented names and Unicode edgecase
expansion SHALL NOT qualify display coverage. Mutations of actual records MAY
exercise technical failures without fabricating display names.
