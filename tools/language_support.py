"""Release language-quality scope; inventory and manifest admission stay separate."""
import json
from pathlib import Path
try:
    from tools.native_language_policy import software_locales
except ModuleNotFoundError:
    from native_language_policy import software_locales

ROOT = Path(__file__).resolve().parents[1]


def language_qualification_status(root=ROOT):
    """Use the same source-bound software proof as runtime and manifest admission.

    Human translation and physical-device reviews remain separate observations;
    manual booleans cannot enable a locale or satisfy this software gate.
    """
    root = Path(root)
    catalog = json.loads((root / 'locales/catalog.json').read_text())
    policy = catalog['supportPolicy']
    if policy.get('schemaVersion') != 1:
        raise ValueError('unsupported language support policy')
    rows = catalog['locales']
    ids = [row['id'] for row in rows]
    primary = policy['primaryLocales']
    if (not isinstance(primary, list) or not 4 <= len(primary) <= 5
            or any(not isinstance(locale, str) for locale in primary)
            or len(set(primary)) != len(primary) or not set(primary) <= set(ids)
            or 'en' not in primary or policy.get('otherCatalogLocales') != 'best-effort'):
        raise ValueError('invalid primary/best-effort catalog partition')
    if policy.get('displayCorpus') != {
            'pastStartUtc': '2021-11-13T00:00:00Z',
            'future': 'all published future launches; paginate to next=null',
            'ui': 'actual application and menu text',
            'inventedDisplayText': False}:
        raise ValueError('finite real display corpus policy must remain explicit')
    if policy.get('qualificationCriteria') != ['finiteCorpusGlyphLayoutReview']:
        raise ValueError('language qualification criteria must remain explicit')
    if policy.get('separateEvidenceCriteria') != ['nativeSpeakerReview', 'physicalDeviceReview']:
        raise ValueError('separate evidence criteria must remain explicit')
    qualified = software_locales(root, catalog)
    missing = {locale: ['finiteCorpusSoftwareReview'] for locale in primary
               if locale not in qualified}
    return {'contractRevision': policy['contractRevision'], 'primaryLocales': primary,
            'bestEffortLocales': [locale for locale in ids if locale not in primary],
            'qualifiedSoftwareLocales': qualified,
            'missingPrimaryQualification': missing, 'languageQualityReady': not missing,
            'externalReviewStatus': {'nativeSpeakerReview': 'unobserved',
                                     'physicalDeviceReview': 'unobserved'},
            'proofBoundary': 'Source-bound finite software admission only; no native-speaker, phone or physical-device rendering claim.'}



if __name__ == '__main__':
    print(json.dumps(language_qualification_status(), indent=2))
