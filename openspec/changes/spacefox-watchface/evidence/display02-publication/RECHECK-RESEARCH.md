# Delivery recheck and research — 15 November 2026

The same physical delivery incident remains **NOT DONE**. The earlier blocked
state reflected the absence of confirmed corrected execution on the watch, not a
proved root cause or an SDK build error. The next observation must distinguish
Store presentation, transfer and actual execution.

## Confirmed observations and channel boundaries

| Channel or observation | Version and boundary |
| --- | --- |
| Physical watch | Owner last confirmed **0.1.6** in SpaceFox settings after a stock-face round trip and full reboot. Corrected execution has not been observed. |
| Original ordinary Garmin app | The signed **0.1.10, Internal 7** was submitted; publisher preview shows **PENDING**. Public approval has not been observed. [Submission and versioned artifact receipt](PUBLICATION.md); [original listing](https://apps.garmin.com/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3); [publisher portal](https://apps-developer.garmin.com/ru-RU/apps/7ef095e4-72fe-44cd-bc39-8987b6ab49e3). |
| GitHub | Signed **0.1.11** is the latest [test prerelease](https://github.com/JekaMas/SpaceFox/releases/tag/v0.1.11-test.1), with model-specific PRGs; it has not been submitted to Garmin. [Installation](../../../../../release/INSTALLATION.md). |

The sanitized [authenticated server metadata observation](garmin-metadata-recheck.json) from 15 November identified the original
app as `betaApp=false`, `status=PENDING`, `latestExternalVersion=0.1.10`,
`latestInternalVersion=7`, `hasVersionPendingScan=false`, and
`downloadProtected=false`. These fields do not prove device delivery or public
approval. The accepted [installation request](garmin-install-network.json) was
unversioned and its empty response did not identify a selected version. The paired
FR165 Music's Garmin Connect page showed firmware 29.05 as latest, but exposed no
installed SpaceFox version. A recorded device download timestamp is later than
that request; its field semantics do not establish a particular app transfer,
synchronization or execution. Therefore the evidence does not support blaming a
lack of synchronization. Private device identifiers and timestamps are omitted.

Garmin's [submission guidance](https://developer.garmin.com/connect-iq/submit-an-app/)
permits the owner to preview and download for testing during approval; public
visibility awaits approval. Pending status alone is not proof that owner testing
is unavailable or that it caused this incident. Garmin staff described a general
review backlog due to submission volume in an [October 2026 reply](https://forums.garmin.com/developer/connect-iq/i/bug-reports/my-app-pac-man-under-review-for-6-days-almost-a-week?CommentId=ac882763-7793-4e9b-8390-9286b753a9c0);
that is context, not evidence this particular review is stuck or an ETA.

## Hosted feed observation

Root observed one GET of the public [text feed](https://jekamas.github.io/SpaceFox/feed.json.txt)
at 2026-11-15 05:00:57 UTC: HTTP 200, `text/plain; charset=utf-8`, 2,743
bytes. The [observed public body](hosted-feed-recheck.json) has publisher
generation 33 and selection and launch source validation at 04:24:51 UTC, about
36 minutes earlier, with `stale=false` and a 3,600-second normal interval. It
selected Vulcan VC6L / ULA / Amazon Leo (LV-01), Cape Canaveral SLC 41, with
T0 17:11:30 UTC on 15 November. The source content's own update time is 14
November; fresh validation does not mean the provider changed that content.
Root also observed successful serialized-feed workflow dispatches, including
the [04:52 UTC run](https://github.com/JekaMas/SpaceFox/actions/runs/43678604789).
This is a point-in-time hosted publisher observation, not proof of phone or
watch delivery, execution, or future freshness.

## Hypotheses and evidence needed

A stale Store presentation, update-selection or delivery mismatch is plausible,
but none is established for SpaceFox. Garmin's acknowledged [pending-update
report](https://forums.garmin.com/developer/connect-iq/i/bug-reports/ciq-store-thinks-app-is-up-to-date-but-it-s-not-after-app-is-updated-while-a-newer-update-is-pending)
describes an iOS author's old installed app while the Store reports no update.
A separate [Android/beta account](https://forums.garmin.com/developer/connect-iq/f/connect-iq-web-store/408195/apps-not-really-upgrading/1919867)
reports an apparently queued update or newer displayed version while the device
retains older code. Another [firsthand report](https://forums.garmin.com/developer/connect-iq/f/connect-iq-web-store/412136/users-not-being-able-to-update-app-to-latest-version-connect-iq-pushes-installs-old-versions)
describes a version/code mismatch. These are related reports, not confirmation
of this incident's cause or evidence that another version bump would fix it.

To close the Store gate, observe the phone's actual listing and update action, the
result of the chosen Store delivery route, and the version executing in SpaceFox
settings on the paired watch. Then observe the fresh matching launch and visible
point and stable physical LOW/NOT_LOW behavior, as required by the existing
[publication checkpoint](PUBLICATION.md). A request, displayed listing, generic
sync timestamp, simulator run or local PRG alone cannot supply these observations.

## Next discriminating steps

1. On Android, force-stop Connect IQ **without clearing storage or data**, reopen
   the original listing, record its displayed version and any update action, and
   perform a normal Connect IQ and Garmin Connect sync. Read the version actually
   executing in SpaceFox settings. This app restart is a proposed reversible
   diagnostic, not a verified workaround.
2. If it remains old, when the physical watch and computer are available, use
   Garmin Express's independent USB Store route and inspect **Items Ready to
   Install → View Details → Install**, then record the resulting on-watch version.
   Garmin's [official update guide](https://support.garmin.com/en-IN/?faq=apVl8M95hQ4WG7wzgKgeA8)
   also documents Connect IQ's **My Device → Updates → Update All**. Neither
   route has been performed as part of this recheck.
3. A model-specific [local PRG transfer](../../../../../release/INSTALLATION.md)
   can separately test that exact binary; it does not prove a Store update. Its
   effect on existing settings and cache is unknown. Do not substitute that result
   for Store acceptance.

Keep the original unversioned request and existing cache. Do not blindly
republish or bump the version, create another beta, repeatedly queue requests,
retest native regressions, or repeat completed face-switch, reboot, account or
firmware questions. A factual [draft for Garmin](GARMIN-REPORT-DRAFT.md) is
prepared but has not been sent. Garmin's [Bug Reports FAQ](https://forums.garmin.com/developer/connect-iq/w/wiki/5/bug-reports-faq)
requests new information on existing reports and explains that Acknowledged means
an internal ticket exists.

The signed release receipts retain their original compiled-source bounds. This
documentation recheck does not claim a current-tree exact pin match or require a
new binary.
