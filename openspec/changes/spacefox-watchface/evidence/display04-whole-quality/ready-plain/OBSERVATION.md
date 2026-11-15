# Ordinary READY replay

An offline test-key seed staged the retained, source-qualified Vulcan/Cape feed
and its 19 immutable objects in a separate test UUID. The exact seeded DAT/IDX/
SET hashes are retained in `seed-manifest.json`; the original owned simulator
state is restored separately after the SDK lane. This feed is deliberately old:
its T+42h display is a stale-seed rendering/recovery witness, not current launch
selection or end-to-end delivery. No provider was contacted.

The unmodified `SpaceFoxApp` program identified in `build.json` ran on SDK 9.3
FR165 Music with the ordinary 126,784-byte app profile. The actual screen showed
its decoded Vulcan artwork, US site-country flag, source-qualified Cape point,
ACTIVE clock and automatic changing countdown. After simulator LOW and HIGH
transitions the map contour/point and then decoded artwork/flag remained visible.
The screenshots are simulator-generated values; they are not physical-watch
health, power, latency or firmware proof. The no-observer plain run had no
native error output through these captures; the runner was terminated after the
observation. Exact first-frame and decode-completion times, peak app heap,
graphics-pool use and per-element overlap remain separately unproven.

The earlier identical-seed plain program failed with a TypeError at the 4,028-byte
payload substring. Test-only instrumentation showed the substring returned null
with 3,704 bytes left in the ordinary heap. A later streamed candidate still
failed on the next shard read. The source now streams 128-character base64
blocks, retains one RGB row for checksum/contour, and releases the already
validated origin/root-format metadata before reading shard data. The distinct
failed raw programs and traces remain under `~/.codex/tmp/spacefox-display04-replay-*`
and `spacefox-display04-stream-diag*`; they are not relabeled as passes.

The SDK Memory viewer was also inspected on a separate live run of this same
plain program and seeded cache. At settled READY it displayed 105.8/123.8 kB,
peak 121.9 kB, 409 objects (peak 536), zero new resource allocations in the
last onUpdate, and one 60-second refreshFitness timer. In LOW it displayed
105.9/123.8 kB, the same peak, 411 objects, zero new resources and no timer;
after HIGH wake it showed 106.1/123.8 kB, 414 objects and one timer. Its
expanded graphics pool showed one 556-byte bitmap reference; this is not a
measurement of total graphics-pool use. A short profiler sample recorded 30
onUpdate calls averaging 9.85 ms. These rounded viewer readings are scoped to
this simulator run, do not establish peak decode-slice time or device latency,
and do not establish a resource plateau through replacement and reopen. A
Force onHide menu action left the timer displayed, but its dispatch was not
established; this observation does not prove either a leak or hide cleanup.
