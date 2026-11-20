# Bounded comparison probes

These are diagnostic source files, not production alternatives. Both use an ordinary FR165M watchface manifest with SDK 9.3. For the palette comparison, compile the same `PaletteBench.mc.txt` and `watchface/resources/drawables/MapView0.png` twice, changing only the bitmap resource's `automaticPalette` XML attribute from false to true. Captures show only the sampled map area; the complete watchface's map/marker and partial-alpha behavior were not established. The two 97,196-byte PRGs and raw logs did not establish a graphics-pool benefit. The candidate was rejected.

`OutlineBench.mc.txt` times 40 changing countdown-like strings using nine direct draws versus rebuilding and blitting an outlined bitmap for every new string. The initial attempt invoked `getDc` on the resource reference and failed; the retained corrected file invokes `.get()` first. A single simulator timing is not a physical performance result. The bitmap candidate was rejected.
