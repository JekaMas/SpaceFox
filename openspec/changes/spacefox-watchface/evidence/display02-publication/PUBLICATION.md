# SpaceFox 0.1.10 publication and delivery checkpoint

The accepted two-mode repair is merged into public `main` and tagged `v0.1.10`
at `ba1eada6`. The production-signed IQ is published in the
[GitHub prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.10).
All 19 release asset bodies were anonymously downloaded with HTTP 200; their
SHA-256 values match both the local files and GitHub digests. The final IQ and
embedded Music program identities are in [publication.json](publication.json).
The final source/snapshot comparison remains the accepted 1,392-input receipt;
these publication records change none of those signed inputs.

## Original Garmin listing: submitted

The prepared 0.1.9 form was cancelled before submission. The final 0.1.10 IQ was
uploaded to the original ordinary SpaceFox app, with its unchanged production
UUID, signing key and three permissions. Garmin verified the manifest/signature
and displayed ten supported products, including Forerunner 165 Music and FR965.
The upload was submitted. Readback shows **0.1.10 (Internal: 7), 4 MB, PENDING**.
The description, release notes and three actual signed-SDK screenshots were
saved. [Screenshot](garmin-version.png) records the saved version and notes.

The [original installation link](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3)
was reloaded in the authenticated publisher session and also displays 0.1.10
(Internal: 7). It is still publisher preview. Public approval and the phone's
rendered listing were not observed; the web readback does not establish either.
The separate Beta card was not used.

## Delivery request: accepted, version not identified

The existing paired Forerunner 165 Music was selected and the same app permissions
confirmed. Garmin's installation POST returned HTTP 200 with an empty response
body. Neither the request nor response identifies an app version. The sanitized
[network receipt](garmin-install-network.json) therefore proves only acceptance
of an unversioned installation request, not delivery of internal version 7.
No device serial, credentials, owner activity readings or raw photos are included.

Ivan Danilenko was sent the original link and an accurate 0.1.10 status through
Telegram, with one normal phone-sync request and a request to read the version
on the watch. The outgoing message is visible; it was not observed as read.
No reinstall, reset, cache clearing or repeated stock-face/reboot/account question
was performed or requested.

## Remaining acceptance

**The incident and goal are NOT DONE.** The last confirmed physical executable
is 0.1.6 after a normal full power cycle. Corrected 0.1.10 execution, a fresh
matching selected launch and visible point, and stable physical LOW/NOT_LOW
remain unobserved. Owner confirmation is pending. Upload, publisher preview,
GitHub file availability, SDK captures and the HTTP 200 queue cannot close this
gate. No new task/property group starts while this delivery unit remains open.

LOW retains Garmin's once-per-minute snapshot limit; active seconds use the
same UTC calculation. Current coverage is 189 fixed numeric catalog positions,
not a claim of universal future/mobile-event coverage. The bounded software and
signed runtime verdict is in [the root judgment](../display02/ROOT-JUDGMENT.md).
No behavior checks were rerun for this metadata-only publication checkpoint.
