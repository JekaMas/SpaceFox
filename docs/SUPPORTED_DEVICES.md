# Supported devices in the 0.1.2 candidate

The candidate targets these installed Garmin Connect IQ profiles:

- Forerunner 165, Forerunner 165 Music, Forerunner 170, Forerunner 170 Music, Forerunner 570 42mm and Forerunner 70
- Venu 3S and Venu 4 41mm
- vívoactive 6

The pinned profiles specify a 390 × 390 round AMOLED display, Connect IQ API 5.2 or newer, at least 128 KiB watch-face and 64 KiB background memory, at least 2 MiB graphics memory and 10 MiB application storage, and the RobotoRegular vector font used for the five language modes. Every profile is compiled by Garmin's SDK; the IQ inspector checks each exported part number and its signed program. A compiler or simulator result does not prove installation, all device firmware, actual memory use, battery behavior, phone synchronization or Store approval. Some metrics may be unavailable on a given device.

The following installed 390 × 390 AMOLED profiles were excluded because their simulator profiles did not declare the RobotoRegular vector font used by the present layout: Approach S50, Approach S70 42mm, Descent G2, Descent Mk3/Mk3i 43mm, epix Pro (Gen 2) 42mm, Instinct 3 AMOLED 45mm, Instinct Crossover AMOLED, MARQ (Gen 2), MARQ (Gen 2) Aviator, and vívoactive 5. This is a qualification boundary, not a claim that those devices cannot run the app. Profiles with other geometries, displays, insufficient limits, or older APIs are outside this candidate. Support for other models needs its own layout and runtime evidence.

For a USB test use the PRG named for the exact profile, for example `SpaceFox-fr165m.prg` for Forerunner 165 Music, where USB installation is supported. The IQ contains all listed profiles. Do not rename a different model's PRG and assume it is compatible. Physical installation remains unobserved.
