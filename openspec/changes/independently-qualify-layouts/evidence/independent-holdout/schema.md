# Independent round-two holdout schema

This file describes the interface only. It contains no scenario IDs, data values,
seeds or content hashes. The inputs and oracle remain sealed until the parent
freezes its final candidate IDs and source fingerprints.

```ts
interface Holdout {
  schemaVersion: 1;
  synthetic: true;
  scenes: Scene[]; // 24 localized scenes
}

interface Label {
  full: string;
  displayLabel: string;
}

interface Scene {
  id: string;
  language: 'ru' | 'en';
  status: 'scheduled' | 'changed' | 'stale' | 'both' | 'tbd';
  flags: {
    rescheduled: boolean;
    stale: boolean;
    timeKnown: boolean;
  };
  clock: string; // legal 24-hour HH:MM
  fixture: {
    rocket: Label;
    operator: Label;
    purpose: Label;
    site: Label; // one explicitly supplied country/place display label
    point: [number, number] | null; // longitude, latitude
    model: 'falcon' | 'electron' | 'ariane' | 'generic';
  };
  countdown: {
    seconds: number | null;
    displayLabel: string;
  };
  fields: Array<{
    role: 'steps' | 'energy' | 'heart' | 'stress' | 'calories' | 'battery';
    value: number | null;
    displayLabel: string;
  }>; // exactly four, order is the physical slot order
}
```

All Label values are already localized for their scene. The implementation must
show the source-provided displayLabel in full and retain full separately. An
explicit supplied short displayLabel is allowed; additional implicit shortening
or replacement by aria-label is not full on-screen preservation.

Flags are the semantic authority for the independent exclamation and cloud-off
indicators. Status is a convenience category; unknown time does not by itself
prove a reschedule or prevent stale data. A missing numeric field has value null
and an explicitly supplied unavailable displayLabel. No fictitious replacement
number is allowed. A null point means no geographic marker, while site text stays.

The declared fully readable class is rocket <=20 graphemes, operator/purpose
<=32, and site.displayLabel <=28 in each language. This is a test-claim boundary,
not permission to reject longer real input. The local holdout intentionally uses
NFC Latin/Cyrillic strings without combining sequences or emoji, so its code-point
lengths equal its grapheme counts. Full site originals may exceed their supplied
short display labels.
