# Supported and candidate watches

The released 0.1.18 package targets ten SDK profiles: Forerunner 165 and 165 Music, 170 and 170 Music, 570 42 mm, 70 and 965; Venu 3S and 4 41 mm; and vívoactive 6. Garmin Store review, physical installation, phone synchronization and actual device acceptance are separate from simulator and compiler results.

The source compatibility expansion below passed author software checks and awaits independent review. It is not a claim that the existing 0.1.18 Store package includes these candidates. Each product ID identifies an SDK profile; marketed aliases and part numbers are retained in the [complete installed-profile inventory](../openspec/changes/spacefox-watchface/evidence/devices020/inventory.json), not assumed to be one product per marketing name.

| SDK product ID | SDK display name | Display |
| --- | --- | --- |
| fr165 | Forerunner® 165 | 390 × 390 |
| fr165m | Forerunner® 165 Music | 390 × 390 |
| fr170 | Forerunner® 170 | 390 × 390 |
| fr170m | Forerunner® 170 Music | 390 × 390 |
| fr57042mm | Forerunner® 570 42mm | 390 × 390 |
| fr70 | Forerunner® 70 | 390 × 390 |
| venu3s | Venu® 3S | 390 × 390 |
| venu441mm | Venu® 4 41mm | 390 × 390 |
| vivoactive6 | vívoactive® 6 | 390 × 390 |
| fr965 | Forerunner® 965 | 454 × 454 |
| approachs7042mm | Approach® S70 42mm | 390 × 390 |
| approachs7047mm | Approach® S70 47mm | 454 × 454 |
| approachs7243mm | Approach® S72 43mm | 416 × 416 |
| approachs7247mm | Approach® S72 47mm | 454 × 454 |
| d2mach1 | D2™ Mach 1 | 416 × 416 |
| d2mach2 | D2™ Mach 2 | 454 × 454 |
| d2mach2pro | D2™ Mach 2 Pro | 454 × 454 |
| descentmk343mm | Descent™ Mk3 43mm / Mk3i 43mm | 390 × 390 |
| descentmk351mm | Descent™ Mk3i 51mm | 454 × 454 |
| epix2 | epix™ (Gen 2) / quatix® 7 Sapphire | 416 × 416 |
| epix2pro42mm | epix™ Pro (Gen 2) 42mm | 390 × 390 |
| epix2pro47mm | epix™ Pro (Gen 2) 47mm / quatix® 7 Pro | 416 × 416 |
| epix2pro51mm | epix™ Pro (Gen 2) 51mm / D2™ Mach 1 Pro / tactix® 7 – AMOLED Edition | 454 × 454 |
| fenix843mm | fēnix® 8 43mm | 416 × 416 |
| fenix847mm | fēnix® 8 47mm / 51mm / tactix® 8 47mm / 51mm / quatix® 8 47mm / 51mm | 454 × 454 |
| fenix8pro47mm | fēnix® 8 Pro 47mm / 51mm / MicroLED / quatix® 8 Pro 47mm / 51mm | 454 × 454 |
| fenix943mm | fēnix® 9 43mm | 416 × 416 |
| fenix947mm | fēnix® 9 47mm / 51mm | 454 × 454 |
| fenix9pro43mm | fēnix® 9 Pro 43mm | 416 × 416 |
| fenix9pro47mm | fēnix® 9 Pro 47mm | 454 × 454 |
| fenix9pro51mm | fēnix® 9 Pro 51mm | 466 × 466 |
| fenixe | fēnix® E | 416 × 416 |
| fr265 | Forerunner® 265 | 416 × 416 |
| fr265s | Forerunner® 265s | 360 × 360 |
| fr57047mm | Forerunner® 570 47mm | 454 × 454 |
| fr970 | Forerunner® 970 | 454 × 454 |
| marq2 | MARQ® (Gen 2) Athlete / Adventurer / Captain / Golfer / Carbon Edition / Commander - Carbon Edition | 390 × 390 |
| marq2aviator | MARQ® (Gen 2) Aviator | 390 × 390 |
| marq3 | MARQ® (Gen 3) Athlete / Adventurer / Aviator / Commander / Golfer / Diver | 454 × 454 |
| venu3 | Venu® 3 | 454 × 454 |
| venu445mm | Venu® 4 45mm / D2™ Air X15 | 454 × 454 |
| venux1 | Venu® X1 | 448 × 486 |

Venu X1 cached-feed simulator testing observed a 123.0 / 123.8 KiB app-heap peak: only 0.8 KiB headroom in that specific run. It does not establish physical-device or graphics-pool capacity, battery performance, or all workloads.

The inventory covers 178 device directories installed with the existing SDK profile set on 2026-11-16, not all marketed devices or future Garmin releases. Garmin’s dated compatible-device table has 180 rows; mechanical normalized-name comparison matched 178 and left Instinct 3 AMOLED 50mm and Instinct 3 Solar 45mm / 50mm without installed profiles. The [comparison and alias limits](../openspec/changes/spacefox-watchface/evidence/devices020/OFFICIAL-SCOPE.md) are recorded; neither missing row is qualified. It records every installed profile, all part numbers and explicit admission blockers, including watches with no watch-face app type. The proposed admission floor remains API 5.1 on every part, watch-face 128 KiB, background 64 KiB, graphics pool 2 MiB and storage 10 MiB. The actual device API must expose `getVectorFont`, and a qualified scalable font family must be present. These are current qualification thresholds; a lower value is not proof a device cannot run SpaceFox.

## Path to broader support

1. **Lower graphics pools and MIP.** First run the unchanged renderer with a captured feed and real decoded assets on FR955, fenix 7 / 8 Solar and Enduro 3 / 4 profiles. Their installed profiles report 1 MiB graphics pools; determine actual allocation, palette, color, active/AOD and legibility behavior before deciding whether a buffer or palette adaptation is needed. Admit only after targeted memory, active/LOW, five-language, settings and compile evidence; do not reduce fields or silently omit visuals.
2. **Older APIs and no scalable font.** Identify the precise missing APIs and glyph/size constraints, then implement an alternative only if it preserves the required features and readability. Requalify notifications, background, cache and all five primary languages; no silent minimum-API reduction.
3. **Smaller or unusual geometries and monochrome.** Measure the unchanged scene on actual device profiles first; qualify clipping, visual hierarchy, map/marker geometry, settings and both power states. Introduce a different composition only with explicit design acceptance.
4. **New and missing models.** Compare the current official compatible-device and device-reference lists against the local installed profile inventory; obtain new profiles through Garmin’s supported tooling only when authorized. For each new profile preserve the full compiler/simulator/runtime inputs and hashes, all part aliases and firmware/API versions; verify admission limits and vector method/face, compile the exact source with release-equivalent flags, test representative viewport/font family in English and Russian plus required primary-locale behavior, run cached-feed/asset memory checks where the resource boundary changes, and independently review. Update the manifest, lock and this inventory together. Compilation and SDK simulation do not establish physical device or Store delivery.

Use the exact model-specific PRG for an authorized USB test. An IQ is the Store export, not a phone-installable file.
