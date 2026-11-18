# Independent Pages pre-POST repair — GREEN

Reviewed host source: `1ab35d5823316cf6068d73662e4dd3a1a03b5a32`. Scope is only the cloud helper, focused test delta and retained Pages evidence. Native 0.2.12 / 335c4db7, signed IQ, art and Garmin submission are unchanged. No runtime repair was required by peer.

## Control-flow judgment

`tools/spacefox/cloud.py:306` authenticates completed run/attempt/source/repository/main/workflow identity and a unique matching completed deploy job/step before `_stale_prepost`. Empty Pages status or a failed job alone is insufficient. The new branch at :255 requires one structured immutable-file closure HTTP503 error and one exit2 inside the failed step's time bounds. Original stale-source refusal remains supported; arbitrary errors and ambiguous outcomes stay armed.

At :278 the original workflow must match exactly; :281 compares the original/current AST of the CLI main, deploy, HTTP/Pages operations, error producer, Site.observe/_get_before and Publisher._context. The reviewed workflow invokes deploy exactly once. Actual deploy (:670) observes the live closure before the sole Pages POST; its post-POST wait/cancel path cannot emit this Site closure error. The source mutation negative specifically adds an observe after POST and refuses. This is a bound preflight witness, not a generic HTTP503 classification.

`recover` (:644) applies only the existing Publisher observed/not_started transition after that witness. Publisher.deployment_event (:993) requires the exact armed intent and performs the existing state CAS. Recovery then still requires complete HTTPS observation/reconcile; it neither issues a POST nor promotes merely because the witness succeeded. A later new arm remains governed by the normal workflow. No manual journal reset, duplicate POST, finality bypass or native change was introduced.

## Retained and independent observations

Retained author `green.log`: five focused tests PASS, covering exact stale source; actual503 format; wrong status, duplicated error, changed workflow/post-POST source; recovery routing; missing workflow; wrong source/attempt, timestamps and cancellation. First RED and fixture-only missing-buildVersion error remain in their original files. No repeat of this already valid five-test suite was needed.

Peer inspected the retained full failed-workflow log at `/Users/jekamas/.codex/tmp/spacefox-release-0212-prep-20261118/original-pages-failure.log`: deploy command once, original checkout source4ee218f70a5e3a1e1a543deb32a950e969fca767, exact structured503/exit2; promote subsequently reports empty Pages status. The canonical excerpt is an excerpt, not a complete log.

`peer-control.log` records the new independent offline check using actual retained generation88 intent, deploy log and original source bytes from Git. Positive `_stale_prepost` PASS; duplicate error, post-POST observe mutation and altered workflow refuse. This check reconstructs step bounds from the retained log and uses a synthetic job ID; it does not pretend to replay authenticated run/job API metadata. No API, network, journal mutation, SDK, PBT, export or publication was executed by peer.

The author observed authenticated `never_started=True` for run44226344248/attempt1, recorded in `real-run-readonly.log`. Raw API run/job metadata and historical contents responses were not retained separately. This remains author-observed provenance, not independently reauthenticated remote proof. Current source guarding and offline original-source comparison were independently assessed; no contradictory runtime evidence was found.

## Handoff boundary

Bounded host repair GREEN. Root may judge and return delivery ownership to author for normal main integration and actual publisher recovery/deployment/HTTPS readback. Those live outcomes remain unobserved by this review; a continuing CDN503 may still block complete observation safely. No claim of physical watch, phone or new native/art qualification.
