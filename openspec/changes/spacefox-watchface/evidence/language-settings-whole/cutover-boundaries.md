# Fixed map and settings cutover boundaries

The owner's 2026-11-13 decision retires the 12/24-hour selection and system-preference transition, analog clock, field hiding/Off, optional top battery, optional animation, origin selection, globe/projection selection, dual-scene wire format and old-cache migration. These are retired, not passing cases. The `pre-cutover-graph.json` preserves their former graph context. Independent basic-scope review retires the17 WF05.P4 alternate-scene/switch cases outright; no replacement projection feature matrix remains. Existing fixed-map, field and lifecycle contracts retain their own basic assertions. The current contract is fixed `HH:mm`, four fixed slots with six roles, active-only short animation, model-origin flag, operator logo and one faded flat map. Date and number formatting follow the app locale when shown; there is no separate system date/number preference API claim.

The earlier public dual-scene artifact and namespace are historical. The tested new map-only artifact was built offline from the captured real launch and seeded into an isolated simulator namespace. It does not demonstrate public publication. A separate clean authority/bootstrap is needed; preserve rolling-hour quota reservations or wait the full window. No old-format parser or migration is supplied.

The rapid 100 ms cycling crash is retained in `pace-control/activation.log` as an unqualified stress observation. The first 1.5 s attempt timed out waiting for a scene after a simulator restart; reseeding the isolated current map-only namespace led to 26 successful diagnostic activations in `pace-control/reseeded.log`. Diagnostic mode is explicitly not production admission. The separate frozen normal activation has no diagnostic bypass. Simulator results are not native-speaker review, phone settings rendering, physical-device or battery-lifetime evidence.

The later basic-scope decision supersedes the 26-primary admission above: mandatory software modes are en, ru, de, fr and es; the other 31 catalog resources are best-effort. The single countdown is `HH:mm:ss` with accumulating hours, including local arithmetic to a validated nominal-minute target without upgrading source precision. Unknown/date/window without target is `--:--:--`; zero is `00:00:00` and is not a launch claim. Earlier 26-language and RTL observations are historical. Current finite proof is `basic-five-finite/`; five ordinary no-bypass activations are in `basic-five-activation/`. `basic-five-red/` retains the first UI attempt's stale background exception, the earlier clock test red, and the initial activation's malformed completion label; the clean UI retry and corrected label are separately observed. The corrected activation-only generator string changed no reconstructed UI/common probe bytes, and the qualification binding was revalidated without repeating those unchanged SDK observations.


Current map-only publication uses `refs/heads/feed-state-map-v3` and
`refs/tags/spacefox-state-bootstrap-map-v3`. There is no fallback reader or quota
import from the historical motion-v3 namespace. The coordinator must quiesce the
old writer, wait a full rolling hour from its last request, then run the existing
clean bootstrap against these absent new refs. Old Git refs and history remain.
Actual Ubuntu validation and public cutover are separate pending observations.
