# Spec Delta

## Purpose

Make the rights to use and redistribute original SpaceFox work clear while
preserving the separate licenses and provenance of third-party components.

## ADDED Requirements

### Requirement: Explicit permissive distribution scope

Original SpaceFox code, specifications, translations and schematic artwork SHALL
use MIT. Distribution MUST retain its license and notices. Official SpaceFox
downloads SHALL be free, without activation fees, paid fields or subscriptions;
this policy MUST NOT restrict downstream MIT rights. Third-party components MUST
retain separate provenance and license scope, and product packages MUST exclude
development tooling without an established redistribution grant.

#### Scenario: Inspect a distribution inventory
- **WHEN** a contributor prepares SpaceFox for distribution
- **THEN** the inventory identifies original MIT work, separate component terms
  and excluded development tooling
- **AND** unknown-license rocket photos are excluded until their redistribution
  rights are established; API access does not grant image rights
