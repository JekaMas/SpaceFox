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

#### Scenario: Validate language resources
- **WHEN** a contributor validates the catalog
- **THEN** all 36 complete locales pass and missing keys, duplicate identifiers,
  changed placeholders or invalid directions fail with the affected locale named
- **AND** draft status does not assert linguistic or native device acceptance

### Requirement: Predictable preview language selection

The preview SHALL offer every catalog locale, select a recognized saved choice
before browser preferences, and use English for unsupported inputs. Changing
language MUST preserve launch, projection, schedule and fitness selections.
Arabic and Hebrew MUST use RTL text while clock/countdown and the physical
Earth/rocket/information order remain stable.

#### Scenario: Resolve a preview language
- **WHEN** the preview receives a saved locale or browser language preferences
- **THEN** it selects the first supported choice, including Chinese script/region
  matching, or English when none match
- **AND** language changes update visible and accessible labels without resetting
  the selected data; RTL text does not mirror the geographic projection
