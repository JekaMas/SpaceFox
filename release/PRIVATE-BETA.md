# SpaceFox private beta

The owner-only Garmin beta uses `private-beta.json` as its persistent application identity and Store title, SpaceFox Beta. It is a separate app from production, so settings and update identity are separate. The on-watch name remains SpaceFox. Version 0.1.3 uses the same nine device profiles, runtime, resources, language admission and feed as this source baseline.

From a clean committed checkout, build with the existing owner-only production RSA4096 key outside the repository:

```sh
python3 -B tools/build_private_beta.py --key /external/protected/developer.der --output /external/new-beta-output
```

The output is a signed local candidate; this command does not submit, install or publish it. Inspect `release.json` and the generated manifest before any Store upload. Garmin acceptance, phone sync and physical device operation require separate observation.
