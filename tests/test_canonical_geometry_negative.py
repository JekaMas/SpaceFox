"""Focused negative witness for the retained qualified-model geometry probe."""
import importlib.util
from pathlib import Path

_PROBE = (Path(__file__).resolve().parents[1] / 'openspec/changes/spacefox-watchface/'
          'evidence/remaining-art/r2/independent-v1/probe_cli_rejected_geometry.py')
_spec = importlib.util.spec_from_file_location('spacefox_retained_geometry_probe', _PROBE)
_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_probe)


class CanonicalGeometryNegative(_probe.RejectedGeometryCLI):
    def test_unsupported_geometry_refuses_without_mutation(self):
        self._qualified_model_and_rights(positive_only=False)


class CanonicalGeometryPositive(_probe.RejectedGeometryCLI):
    def test_qualified_selection_reopens_and_reuses_objects(self):
        self._qualified_model_and_rights(positive_only=True)
