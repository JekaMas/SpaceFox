# Safe interface — independent reconfirm24

This file contains no scene values, identities, hashes or generation seeds. Both independent packets use exactly the accepted round-two interface:

```ts
interface Label { full: string; displayLabel: string }
interface Packet {
  schemaVersion: 1;
  synthetic: true;
  scenes: Array<{
    id: string;
    language: 'ru' | 'en';
    status: 'scheduled' | 'changed' | 'stale' | 'both' | 'tbd';
    flags: { rescheduled: boolean; stale: boolean; timeKnown: boolean };
    clock: string;
    fixture: {
      rocket: Label; operator: Label; purpose: Label; site: Label;
      point: [number, number] | null;
      model: 'falcon' | 'electron' | 'ariane' | 'generic';
    };
    countdown: { seconds: number | null; displayLabel: string };
    fields: Array<{
      role: 'steps' | 'energy' | 'heart' | 'stress' | 'calories' | 'battery';
      value: number | null;
      displayLabel: string;
    }>;
  }>;
}
```

Each packet contains 24 scenes: twelve payloads × RU/EN. Each scene has exactly four immutable logical configured slots. A candidate must declare its logical-slot-to-position mapping before qualification; row-major and column-major routes are permitted feature grammars. Role/value identity is preserved under that explicit mapping. Labels are already localized and are the exact approved on-screen strings. A shorter producer-approved displayLabel may differ from full; the renderer may not shorten it further. Full source labels remain retained. Flags, not the convenience status category alone, control the independent indicators.

Full-reading class:

- rocket displayLabel ≤20 graphemes;
- operator and purpose displayLabel ≤32 graphemes each;
- site displayLabel ≤28 graphemes;
- valid 24-hour clock `HH:MM` with leading zero;
- countdown displayLabel ≤16 graphemes, including an unknown-time label; seconds are nonnegative integers when timeKnown, otherwise null;
- exactly four distinct configured roles per scene, drawn from the six-role set;
- fitness displayLabel ≤7 graphemes; integer steps/calories 0..99999, energy/stress/battery 0..100, heart 0..240, or null with the explicit visible unavailable marker `—`;
- a null point means no marker; source site text stays;
- finite geographic point ordered [longitude, latitude], with valid ranges.

All newly authored packet data is synthetic. Country names are existing real countries, with no fictional state claimed. Synthetic place labels and coordinate selections do not assert actual launch pads or real missions. These packets use NFC Latin/Cyrillic strings; their ordinary code-point lengths equal grapheme lengths. The class boundary is not permission to reject longer real production inputs. Repeated configured roles or larger production values remain accepted inputs with outside-benchmark diagnostics; this finite benchmark does not claim every such combination.

Screen values/oracle/IDs/hashes are released only after the 12-candidate shortlist and sources are frozen. Confirm values/oracle/IDs/hashes stay independently sealed until the top-five and sources are frozen. Confirmation is not a repair/training set.

The reviewer-added universal row-major assumption was clarified before any screening release. See slot-mapping-clarification.md; sealed scene values and oracle identities are unchanged.

This separate reconfirm24 belongs to the explicitly declared post-failed-confirmation increment. It is released only after the new second candidate/source freeze; the previous confirm24 is regression material. All numeric/text/field bounds remain unchanged.
