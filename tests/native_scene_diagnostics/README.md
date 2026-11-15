# Current scene diagnostic sources

These are the generators, UI drivers and captured A/B current-format inputs used for a bounded Linux SDK 9.3 / FR165 simulator investigation. B is a technical mutation of A, not an asserted new launch or surveyed site. These diagnostics bypass normal release admission and do not establish phone, watch, firmware, physical storage or peak RAM behavior. They do not include Garmin SDK files, a development key, the original simulator image, or the retained private run logs. A fresh execution is a new observation; compiling or examining a saved log is not simulator execution.

`linux_probe.py` intentionally substitutes the historical public source commit 854a5a30 in its diagnostic build metadata, because the original mount had no Git metadata. That string is historical and does not establish the identity of a new checkout. Compare the generated `productionSources` and `productionResources` hashes with the actual checkout and record its Git revision and dirty state. Any changed production, probe, resource, profile, fixture, command or runtime input requires a new assessment. The copied scripts and fixtures are the retained original bytes; some UUIDs and the invalid fixture URL are intentionally fixed to let the diagnostic stages share their own store.

## Isolated preparation and example

Requires an already available official Linux SDK 9.3.0-2026-10-20-95888f262 and FR165 profile, an existing amd64 Docker image containing Python 3, Java 11, Xvfb and the simulator's OS libraries, and a caller-owned development key. No installation, network, published ports or host simulator is required. Use a fresh private task directory and container; the fixed UUIDs must never share another run's simulator storage. Copy the SDK/profile into `$SCENE_TASK/garmin`, preserving `Sdks/...`, `Devices/fr165` and required `Fonts`; set the other variables to absolute existing paths. Copy this directory's contents to the task directory. The scripts expect those exact `/task` mount paths.

```sh
cp -R "$SCENE_PUBLIC/tests/native_scene_diagnostics/." "$SCENE_TASK/"
docker run -d --name "$SCENE_CONTAINER" --network none --platform linux/amd64 \
  -v "$SCENE_TASK:/task" -v "$SCENE_PUBLIC:/task/source:ro" \
  -v "$SCENE_KEY:/test-key/spacefox-development.der:ro" "$SCENE_IMAGE" sleep infinity
docker exec "$SCENE_CONTAINER" sh -c 'mkdir -p /root/.Garmin && ln -s /task/garmin /root/.Garmin/ConnectIQ'
docker exec -d "$SCENE_CONTAINER" sh -c 'Xvfb :97 -screen 0 1200x1200x24 > /task/xvfb.log 2>&1'
docker exec -d -e DISPLAY=:97 "$SCENE_CONTAINER" sh -c '/task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/simulator > /task/simulator.log 2>&1'
docker exec "$SCENE_CONTAINER" python3 /task/build_batch_age.py
docker exec -e DISPLAY=:97 "$SCENE_CONTAINER" /task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/monkeydo /task/output/batch-source-age/CT2.prg fr165
```

Record the build JSON, raw output and exit code. The batch completion marker must report the selected object count, zero optional GETs and unchanged source validation age. A timeout is only a completed observation when its explicit completion marker occurred first; preserve the timeout. Do not call this controlled callback a live phone/network test.

Other `build_*.py` files generate the named `output/<group>` packages and their precise Monkey C source/resources and build JSON. `build_feed_controls.py`, `build_grammar.py`, `build_late.py` and `build_unresolved.py` create test-framework packages: run their generated package with `monkeydo <package> fr165 -t`, and require the complete named PASS table, even when the framework launcher exits 1. `build_callback.py`, `build_realview.py`, `build_fallback.py`, `build_race.py`, `build_raster_fault.py`, and `build_map_only.py` create ordinary packages; run the generated `.prg` with `monkeydo <package> fr165` and retain completion markers and exit codes. Refer to each generator and generated build JSON for package names and checks; the generator itself is not an execution receipt.

`build_phases.py` creates the A/B stage program. Launch once with monkeydo; stop and restart the isolated simulator, then use `RunInstalled.java` with the generated application UUID and SDK shell to open the installed program without pushing; repeat to advance B and its reopen. Capture installed PRG, DAT and IDX before/after each stop/reopen and the process identity; never repush. Compile inside the container with `javac -cp /task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/monkeybrains.jar /task/RunInstalled.java`, then run `java -cp /task:/task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/monkeybrains.jar RunInstalled <uuid> /task/garmin/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/shell` with `DISPLAY=:97`; pass the UUID printed by the builder. `build_lifecycle.py` and `build_ru.py` create seed and observe pairs with the same generated UUID: run the seed test first, then the observer. `build_ru_draw_io.py` and `build_ru_draw_hide.py` use the fixed CR1 UUID and require its A seed. The `drive_*.py` scripts operate only on the isolated Xvfb display with its documented 1200×1200 geometry, after an in-flight build marker; inspect their exact click coordinates and callback markers. Capture the simulator view using `capture_x.py`. UI automation is sensitive to window geometry and requires manual inspection if controls differ.

The full-store sequence uses the same fixed CL1 UUID and URL: first seed A using `build_lifecycle.py`'s seed with that same UUID (adjust the generated identity in a new, explicitly recorded diagnostic revision), build and run `full-prefill`, `full-fill`, phase-split `full-reject` from `build_fullreject2.py`, `full-clean`, and `full-positive` in that order. Preserve every raw result, including failures; always run the owned-key cleanup after filling. A fresh replay with changed generators is not byte-identical to the retained observation. Do not reset foreign stores.

Remove only the uniquely named container and its owned diagnostic files when finished. No SDK, keys or simulator data should be committed. Pixel verification of the original screenshots and the private source-binding graph requires their retained evidence, which is not included here; this directory supplies their publishable executable sources and inputs, not those private receipts.

## Three distinct modes

`build_fresh_retained.py` generates a separate one-test package for source-only
freshness, stale-latch clearing, same-selection renderer-reference retention and
SDK Storage reopen in the same process. Run its `output/fresh-retained/CF2.prg` with `monkeydo
... fr165 -t` and require `freshRetainedScene PASS`; raw launcher exit 1 alone
does not establish success. Its injected clock and store are controlled, and the
retained renderer is a reference, not a decoded bitmap or process restart.
As with the other generators, independently compare the recorded source/resource
hashes to the intended checkout; the runner's substituted Git head is historical.

`build_batch_marker_fault.py` builds `output/batch-marker-fault/CF3.prg` for
the same framework launcher. It injects failures at the pending batch's two
begin and two completion marker writes, checks the accepted feed seal and retry,
and uses a technical empty transfer index solely to reach completion. It does
not establish that this artificial index is an admissible visual closure or
simulate physical power loss.

`build_core_fault_roles.py` builds `output/core-fault-roles/CF4.prg`. It records
the operations actually reached by a current A-to-B cache commit and interrupts
each one against a copying in-memory store, requiring reopened state to have an
exact old or new wire hash with its matching source-validation time. It does not
stand in for physical interruption, full-storage behavior or other update paths.

1. **Recorded-build source applicability:** `python3 -B tests/native_scene_diagnostics/verify_binding.py --public-root "$SCENE_PUBLIC"` compares the public production sources/resources, retained generated probe sources/resources, generators/drivers and A/B fixture bytes to the recorded build bindings. It does not inspect logs, run the simulator, or check an installed SDK. It requires the historical public base in the checkout ancestry. A mismatch or missing file invalidates the affected reuse; it is not repaired by updating a digest.
2. **Installed runtime comparison:** add `--sdk-root "$SCENE_SDK_COPY" --image "$SCENE_IMAGE"` to the preceding command. This compares the compiler, simulator, profile, API/font inputs and image ID to the historical runtime. It does not execute the SDK. A different runtime requires affected requalification. The archived SDK digest is provenance, not a fresh archive check.
3. **Fresh SDK replay:** run the isolated setup and relevant generator/package above, save new outputs and separately assess their actual outcomes. A fresh run is not verified by source applicability alone. The default host test suite does not install, invoke or require the SDK.

For retained screenshots supplied separately, `python3 -B tests/native_scene_diagnostics/verify_pixels.py --public-root "$SCENE_PUBLIC" --scene "$SCENE_SCREEN" --map "$SCENE_MAP_SCREEN"` checks their recorded hashes and fixed pixels. For newly captured screenshots, add `--new-captures`, which compares pixels without asserting the old screenshot hashes; the fixed 1200×1200 window origin must match. The raw reference is shared with the producer renderer, so this is not independent artwork accuracy. `python3 -B tests/native_scene_diagnostics/verify_draw_intervals.py --log "$SCENE_DRAW_LOG"` checks a supplied instrumented redraw log and its built-in negative controls. These commands consume supplied evidence; neither starts a simulator. The original screenshot and log receipts are retained separately and are not included here.
