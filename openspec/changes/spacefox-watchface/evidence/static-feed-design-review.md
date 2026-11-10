# Personal static-feed specification review

2026-11-10. The owner explicitly selected **GitHub Actions + static files** in
response to the architecture choice. This revision updates specifications and the
MIT agent guide; it does not implement or enable the updater, cron, Pages or Garmin
app. The earlier planned always-running `service/` owner is superseded.

## Decision and scope

The family can use its existing GitHub repository/account. A scheduled ordinary
program fetches and normalizes launch data, and custom Actions/Pages deployment
serves bounded JSON plus immutable licensed visuals. Garmin Connect bridges the
watch's background HTTPS fetches. The watch computes the countdown locally.
An agent configures or repairs this path; periodic model inference is unnecessary.
The static URL contains public launch/catalog data, not the child's health data.

| Alternative | Assessment |
| --- | --- |
| Direct watch → provider | Avoids the publisher, but provider guidance favors caching and FR165 payload/memory/query limits are unqualified; not the selected default |
| Local agent/scheduler → static host | Can reuse the same program; depends on an awake connected computer and is an optional later runner |
| GitHub Actions → Pages | Selected; uses the existing GitHub account and no always-on personal machine/AWS; queue/CDN delays, quotas and occasional schedule recovery remain real limits |

Five-minute publishing and watch polling are independent. They can approach ten
minutes of polling delay before queue/deployment/CDN/network delays; this revision
does not promise immediate or five-minute end-to-end notification.

## Sources checked

These are primary documentation observations, not a live provider/deployment test:

- [Garmin Background API](https://developer.garmin.com/connect-iq/api-docs/Toybox/Background.html):
  temporal events cannot be scheduled less than five minutes apart.
- [Garmin background services](https://developer.garmin.com/connect-iq/articles/core-topics/Backgrounding.html):
  the background process has less memory, can be terminated and has a 30-second
  runtime limit. An 8-KiB feed is a proposed ceiling, not proven FR165 capacity.
- [Garmin Communications](https://developer.garmin.com/connect-iq/api-docs/Toybox/Communications.html):
  the phone can bridge internet requests; background communication is available.
  This is not evidence of our actual image persistence/transfer path.
- [The Space Devs FAQ](https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md)
  documents 15 calls/hour on the anonymous tier and recommends caching rather than
  direct client polling. The official
  [throttle endpoint](https://ll.thespacedevs.com/2.3.0/api-throttle/)
  exposes budget fields; another process/IP's observation is not our quota receipt.
- [GitHub schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule):
  five-minute minimum, default-branch execution, possible delays/dropped jobs and
  disablement after 60 days without repository activity. Running a cron is not
  assumed to reset that inactivity rule; recovery is explicit in the guide.
- [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits):
  Pages is available for public GitHub Free repositories. Its ten-build/hour soft
  limit excludes custom Actions publishing, hence the selected artifact route.
- [Custom Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages):
  deployment uses Pages/id-token permissions and a Pages environment; no incoming
  application server or provider token on the watch is needed.
- [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions):
  standard runners in public repositories are free; larger runners/storage require
  separate attention. The plan bounds artifact size/retention and authorizes no
  paid upgrade or permanent promise about platform terms.

## Contract review

- Stable identity/UTC precision, missing context, unknown coordinates/model
  fallback, zero without confirmed liftoff and separate status indicators remain.
- Failed runs retain the last working publication. Real unchanged provider
  validation may renew source age without creating or clearing a reschedule flag.
  Old file 200/304, catalog-only builds and missing retained records cannot renew
  that record's freshness. Unsupported/oversize/regressing feeds retain the cache.
- Immutable asset references plus watch validation handle CDN version skew;
  Pages publication is not assumed to be atomic across separate cached requests.
- A family's `FeedBaseUrl` is configurable; forks do not silently consume the
  author's feed or require the author's credentials. The same catalog/layout
  supports another host without a hardcoded list or source edit.
- The public guide distinguishes planned missing owners from a working installer,
  names first/second publication and physical watch readback, and explains quota,
  disabled scheduling, offline/stale behavior and asset correction/replacement.

The exact provider batch query, durable budget/retained-state handling and native
image/memory path remain implementation qualification in tasks 2.1/2.2/3.1–3.4;
the artifact does not fabricate a runnable command, successful setup or test ID.

## Verification and retained evidence

`openspec validate spacefox-watchface --strict --json` passed after the substantive
spec/design/proposal/task revision, with no issues. The prior structural receipt
was invalidated by the changed launch-schedule/visual-catalog contract. Its raw
new result is in `static-feed-strict.json`.

Prototype code, locale resources, real resolver/validators, their tests and the
completed `localize-free-distribution` specs were unchanged. Their six observed
behavior passes and browser checks were retained without rerunning. No current
native/service test is claimed; before semantic implementation the original
task 2.1 must author the new complete verification/discovery records.

The current scope has no active workflow file and does not alter Pages settings,
publish a data endpoint, install SDK/tools, create an automation or incur charges.
Only the MIT source/specification update is published to the existing repository.
