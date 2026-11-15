"""Qualify the 0.1.15 reminder delta over the retained 0.1.14 language proof."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def validate(root, catalog):
    from tools.native_display03_probe import inputs
    from tools.generate_native_version import validate as validate_version
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def read(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('invalid reminder qualification path')
        raw = (root / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('reminder qualification input changed: ' + str(path))
        return raw
    record = json.loads(read(proof['reminder015Proof']))
    prior = json.loads(read(record['priorCatalog']))
    oldproof = prior['supportPolicy']['softwareQualificationProof']
    if {k: v for k, v in proof.items() if k != 'reminder015Proof'} != oldproof:
        raise ValueError('prior qualification proof changed')
    reconstructed = json.loads(json.dumps(catalog))
    reconstructed['supportPolicy']['softwareQualificationProof'] = oldproof
    if reconstructed != prior or record['scope'] != 'launch-reminders-0.1.15':
        raise ValueError('unqualified locale catalog change')
    old = json.loads(read(oldproof['version14Proof']))['nativeInputs']
    current = inputs(root)
    if current != record['nativeInputs']:
        raise ValueError('reminder native input closure changed')
    delta = sorted(k for k in old.keys() | current.keys() if old.get(k) != current.get(k))
    expected_delta = {
        'watchface/manifest.xml', 'watchface/toolchain-lock.json',
        'watchface/resources/settings/properties.xml', 'watchface/resources/settings/settings.xml',
        'watchface/resources/strings/strings.xml', 'watchface/resources-rus/strings/strings.xml',
        'watchface/resources-deu/strings/strings.xml', 'watchface/resources-fre/strings/strings.xml',
        'watchface/resources-spa/strings/strings.xml', 'watchface/source/FeedService.mc',
        'watchface/source/LaunchReminder.mc', 'watchface/source/LaunchReminderForeground.mc',
        'watchface/source/NativeFeed.mc', 'watchface/source/NativeForegroundApp.mc',
        'watchface/source/NativeJson.mc', 'watchface/source/SettingsMenu.mc',
        'watchface/source/SettingsMenuText.mc', 'watchface/source/SpaceFoxApp.mc',
        'watchface/source/generated/NativeVersion.mc',
    }
    if delta != record['delta'] or set(delta) != expected_delta:
        raise ValueError('reminder source delta changed')
    if set(record['newNativePaths']) != {'watchface/source/LaunchReminder.mc', 'watchface/source/LaunchReminderForeground.mc'}:
        raise ValueError('reminder added-source set changed')
    if not {x for x in expected_delta if x in old} <= set(record['priorSnapshots']):
        raise ValueError('prior reminder snapshots incomplete')
    for name, item in record['priorSnapshots'].items():
        raw = read(item)
        if name in old and hashlib.sha256(raw).hexdigest() != old[name]:
            raise ValueError('prior source snapshot mismatch: ' + name)
    low = json.loads(read(oldproof['lowMapDeltaProof']))
    profile = record['priorSnapshots']['tools/spacefox/native_profile.py']
    if profile['sha256'] != low['supportInputs']['tools/spacefox/native_profile.py']:
        raise ValueError('predecessor profile snapshot does not match retained LOW proof')
    validate_version(root)
    log = read(record['nativeLog']).decode()
    names = ('settingsPositive', 'cadencePositive', 'cadenceNegative', 'quietPositive',
             'quietNegative', 'identityPositive', 'identityNegative', 'schedulerPositive',
             'schedulerNegative', 'equivalencePositive', 'equivalenceNegative', 'sharedRegistration', 'snapshotWrites')
    if parse_output(log, record['rawExit'], names)['status'] != 'passed':
        raise ValueError('reminder SDK framework observation incomplete')
    if 'SHARED_REGISTRATION feed=300 reminder=900' not in log:
        raise ValueError('shared background scheduler observation missing')
    for item in record['observations'].values():
        read(item)
    previous_visual = json.loads(read(record['observations']['locale-015/prepared-inputs.json']))['nativeInputs']
    visual_delta = {k for k in previous_visual.keys() | current.keys() if previous_visual.get(k) != current.get(k)}
    if visual_delta != {'watchface/source/LaunchReminderForeground.mc', 'watchface/source/generated/NativeVersion.mc',
                        'watchface/source/LaunchReminder.mc', 'watchface/source/NativeFeed.mc'}:
        raise ValueError('visual reuse source delta changed')
    old_reminder = read(record['observations']['menu/pre-peer-reminder.mc.txt'])
    old_feed = read(record['observations']['menu/pre-peer-native-feed.mc.txt'])
    for name, raw in (('watchface/source/LaunchReminder.mc', old_reminder),
                      ('watchface/source/NativeFeed.mc', old_feed)):
        if hashlib.sha256(raw).hexdigest() != previous_visual[name]:
            raise ValueError('visual peer baseline differs: ' + name)
    # NativeFeed's peer edit is confined to the reminder-only projection.
    def outside_projection(raw):
        before, tail = raw.split(b'    function reminderProjection(){', 1)
        _, after = tail.split(b'    function hashRaw(text)', 1)
        return before, after
    if outside_projection(old_feed) != outside_projection((root / 'watchface/source/NativeFeed.mc').read_bytes()):
        raise ValueError('visual feed change extends beyond reminder projection')
    old_helper = read(record['observations']['menu/pre-dedup-foreground.mc.txt'])
    old_version = read(record['observations']['menu/pre-dedup-version.mc.txt'])
    if hashlib.sha256(old_helper).hexdigest() != previous_visual['watchface/source/LaunchReminderForeground.mc'] or hashlib.sha256(old_version).hexdigest() != previous_visual['watchface/source/generated/NativeVersion.mc']:
        raise ValueError('visual reuse source snapshot differs')
    # The menu host calls SettingsMenu.root, never the foreground cache publisher.
    # Version ID is not displayed; BUILD remains unchanged.
    for lang in ('en', 'ru'):
        host = read(record['observations']['menu/Host-' + lang + '.mc.txt'])
        if b'SettingsMenu.root(self)' not in host or b'Foreground' in host:
            raise ValueError('menu host observation boundary changed')
    old_build = old_version.decode().split('const ID = ')[0]
    new_build = (root / 'watchface/source/generated/NativeVersion.mc').read_text().split('const ID = ')[0]
    if old_build != new_build:
        raise ValueError('visual BUILD version changed')
    seed = read(record['observations']['peer-storage-reopen/seed.log']).decode()
    reopen = read(record['observations']['peer-storage-reopen/reopen.log']).decode()
    if 'REOPEN_SEED stored=true calls=0' not in seed or 'push=false' not in reopen or 'REOPEN_OBSERVED persisted=true calls=0 duplicateSuppressed=true' not in reopen:
        raise ValueError('SDK storage reopen observation missing')
    binding = json.loads(read(record['observations']['native-reminder-tests/peer-stable-binding.json']))
    for name, expected in binding['inputs'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
            raise ValueError('reminder SDK source binding changed: ' + name)
    if hashlib.sha256(log.encode()).hexdigest() != binding['logSha256']:
        raise ValueError('reminder SDK log binding changed')
    menu_log = read(record['observations']['current-menu/run.log']).decode()
    if parse_output(menu_log, 1, ('currentMenuSettings',))['status'] != 'passed':
        raise ValueError('current production menu observation incomplete')
    glyph = json.loads(read(record['glyphs']))
    if glyph['font_sha256'] != '31d218ca177e4c2191134f9c14fb43027f8a38622476db14038fd8ff186f875e':
        raise ValueError('retained settings font changed')
    allowed = set()
    for part in glyph['fontconfig_charset'].split():
        lo, *hi = part.split('-')
        allowed.update(range(int(lo, 16), int(hi[0], 16) + 1 if hi else int(lo, 16) + 1))
    text = (root / 'watchface/source/SettingsMenuText.mc').read_text()
    expected_labels = ['Launch reminders', 'Quiet/unknown: off', 'Сигналы пуска',
                       'Сон/нет данных: выкл.', 'Start-Hinweise', 'Ruhe/unbekannt: aus',
                       'Alerte lancement', 'Sommeil/inconnu : non', 'Avisos de cohete',
                       'Sueño/desconocido: no', 'Off', 'On', 'Выкл.', 'Вкл.', 'Aus', 'Ein',
                       'Désactivés', 'Activés', 'Desactivados', 'Activados']
    if record['newLabels'] != expected_labels:
        raise ValueError('primary menu label inventory changed')
    for label in record['newLabels']:
        if label not in text or not {ord(c) for c in label} <= allowed:
            raise ValueError('new menu label missing or not covered: ' + label)
    widths = read(record['observations']['menu/primary-widths-raw.txt']).decode().splitlines()
    expected_pairs = list(zip(record['newLabels'][0:10:2], record['newLabels'][1:10:2]))
    if len(widths) != len(expected_pairs):
        raise ValueError('primary menu width observations incomplete')
    for row, (title, subtitle) in zip(widths, expected_pairs):
        fields = row.split('|')
        if len(fields) != 4 or fields[0] != title or fields[2] != subtitle:
            raise ValueError('primary menu width source mismatch')
        title_width, subtitle_width = float(fields[1]), float(fields[3])
        if not 0 < title_width <= 319.375 or not 0 < subtitle_width <= 303.256:
            raise ValueError('primary menu width exceeds observed reference')
    # Restore predecessor bytes, including removal of newly added native owners.
    # Prior evidence is validated under its own source, never relabeled as 0.1.15.
    with tempfile.TemporaryDirectory(prefix='spacefox-reminder-prior-') as tmp:
        target = Path(tmp)
        for folder in ('watchface', 'locales', 'tools', 'tests'):
            shutil.copytree(root / folder, target / folder,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'assets', 'catalog', 'schemas'):
            (target / folder).symlink_to(root / folder, target_is_directory=True)
        for name in record['newNativePaths']:
            (target / name).unlink()
        for name, item in record['priorSnapshots'].items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(read(item))
        (target / 'locales/catalog.json').write_bytes(read(record['priorCatalog']))
        code = ('import json;from pathlib import Path;from tools.native_version14_qualification import validate;'
                'p=Path.cwd();c=json.loads((p/"locales/catalog.json").read_text());'
                'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=target,
                                env={'PATH': str(Path(sys.executable).parent)+':/usr/bin:/bin',
                                     'PYTHONPATH': str(target), 'PYTHONDONTWRITEBYTECODE': '1'},
                                capture_output=True, text=True, timeout=300)
        if result.returncode:
            raise ValueError('prior 0.1.14 proof failed: ' + result.stderr[-3000:])
    return catalog['supportPolicy']['softwareQualifiedLocales']
