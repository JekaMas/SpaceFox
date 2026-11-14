# SpaceFox private beta

The owner-only Garmin beta uses `private-beta.json` as its persistent application identity and Store title, SpaceFox Beta. It is a separate app from production, so settings and update identity are separate. The on-watch name remains SpaceFox. The local 0.1.4 candidate uses the same nine device profiles, runtime, resources, language admission and feed as this source baseline. Its previous published beta is 0.1.3; the candidate is not evidence of an upload or installation.

The current [SpaceFox Beta 0.1.3 listing](https://apps.garmin.com/apps/db2b9b57-0d38-4df5-ae04-8cfabc0b81c9) is owner-only. Sign in to Connect IQ on the phone with the same Garmin account that submitted the beta; another account cannot download this owner-only listing. The beta is a separate app identity from the ordinary SpaceFox listing and has separate settings and updates.

The owner selected the paired Forerunner 165 Music, accepted the requested permissions, and Garmin confirmed the beta is queued for the next device sync. Open Garmin Connect on the phone and sync the watch; once installation completes, select SpaceFox from the watch face menu. The queue confirmation does not establish that phone sync or physical installation completed.

From a clean committed checkout, build with the existing owner-only production RSA4096 key outside the repository:

```sh
python3 -B tools/build_private_beta.py --key /external/protected/developer.der --previous /external/previous-beta/release.json --output /external/new-beta-output
```

The output is a signed local candidate; this command does not submit, install or publish it. Inspect `release.json` and the generated manifest before any Store upload. The 0.1.3 beta submission and queue were accepted as described above; phone sync and physical device operation require separate observation.
