#!/usr/bin/env python3
"""Evaluate separately observed delivery and physical launch evidence.

This gate checks receipt consistency; it cannot authenticate photographs, vendor
claims, or prove that a submitted/queued package was installed by itself.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

CARD = '7ef095e4-72fe-44cd-bc39-8987b6ab49e3'

def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (AttributeError, ValueError, TypeError):
        return None

def evaluate(receipt, expected_build):
    problems = []
    if receipt.get('cardId') != CARD:
        problems.append('ordinary app identity is not established')
    artifact = receipt.get('releaseArtifact') or {}
    runtime_id = artifact.get('runtimeId')
    if not (artifact.get('version') == expected_build and isinstance(runtime_id, str) and
            re.fullmatch(r'[0-9a-f]{8}', runtime_id) and isinstance(artifact.get('sha256'), str) and
            re.fullmatch(r'[0-9a-f]{64}', artifact['sha256']) and
            artifact.get('sourceBindingEvidence')):
        problems.append('signed target build and runtime identity are not bound')
    public = receipt.get('public') or {}
    # A compatibility check, publisher preview, or queue acknowledgement is not
    # an observation of which version is available to the intended phone.
    installable = public.get('installable') or {}
    phone_installable = (installable.get('cardId') == CARD and
            installable.get('build') == expected_build and
            installable.get('evidence') and timestamp(installable.get('observedAtUtc')) and
            installable.get('method') in ('phone-version-list', 'version-bound-install'))
    watch = receipt.get('installedBuild') or {}
    watch_installed = (watch.get('build') == expected_build and watch.get('method') == 'watch-runtime' and
            runtime_id and watch.get('runtimeId') == runtime_id and
            watch.get('deviceRef') and watch.get('evidence') and timestamp(watch.get('observedAtUtc')))
    # Actual execution is stronger evidence of owner installation than a phone
    # listing; public approval remains a separate Store-release obligation.
    if not (phone_installable or watch_installed):
        problems.append('target build installability is not observed')
    if not watch_installed:
        problems.append('target build executing on the physical watch is not observed')
    launch = receipt.get('watchLaunch') or {}
    t = timestamp(launch.get('observedAtUtc'))
    validated = timestamp(launch.get('sourceValidatedUtc'))
    feed = timestamp(launch.get('feedObservedAtUtc'))
    if not (t and validated and feed and launch.get('watchEvidence') and launch.get('feedEvidence') and
            launch.get('watchLaunchId') and launch.get('watchLaunchId') == launch.get('feedLaunchId') and
            launch.get('watchBuild') == expected_build and launch.get('deviceRef') == watch.get('deviceRef') and
            watch.get('deviceRef') and timestamp(watch.get('observedAtUtc')) and
            0 <= (t - timestamp(watch.get('observedAtUtc'))).total_seconds() <= 3600 and
            0 <= (t - validated).total_seconds() <= 10800 and
            abs((t - feed).total_seconds()) <= 3600):
        problems.append('fresh matching launch on the physical watch is not observed')
    modes = receipt.get('watchModes') or {}
    events = modes.get('events') or []
    stamps = [timestamp(event.get('observedAtUtc')) for event in events]
    if not (modes.get('watchBuild') == expected_build and modes.get('deviceRef') == watch.get('deviceRef') and
            modes.get('launchId') == launch.get('watchLaunchId') and modes.get('evidence') and
            [event.get('mode') for event in events] == ['active', 'ambient', 'active'] and
            all(stamps) and stamps == sorted(stamps) and t and 0 <= (stamps[0] - t).total_seconds() <= 3600 and
            (stamps[-1] - stamps[0]).total_seconds() <= 3600 and
            all(event.get('coherentScene') is True for event in events)):
        problems.append('stable active and ambient transitions on the physical watch are not observed')
    return {'status': 'NOT DONE' if problems else 'DONE', 'failures': problems,
            'boundary': 'Receipt consistency only; evidence must be independently inspected.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--expected-build', required=True)
    args = parser.parse_args()
    result = evaluate(json.loads(args.receipt.read_text()), args.expected_build)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'DONE' else 1

if __name__ == '__main__':
    raise SystemExit(main())
