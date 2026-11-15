#!/usr/bin/env python3
"""Run an existing local diagnostic with probe-only NativeMetrics injection.

The immutable original runtime helper remains available for its historical
source-bound receipts. This adapter does not run the SDK unless the selected
explicit diagnostic does so.
"""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: run_instrumented_probe.py <repository diagnostic.py> [args...]')
    target = (ROOT / sys.argv[1]).resolve()
    allowed = (ROOT / 'tools', ROOT / 'tests/native_scene_diagnostics')
    if target.suffix != '.py' or not target.is_file() or not any(target.is_relative_to(p) for p in allowed):
        raise SystemExit('diagnostic must be a Python file in tools or tests/native_scene_diagnostics')
    import tools
    from tools import native_probe_metrics_runtime as runtime
    sys.modules['tools.native_full_visual_runtime'] = runtime
    tools.native_full_visual_runtime = runtime
    sys.argv = [str(target), *sys.argv[2:]]
    runpy.run_path(str(target), run_name='__main__')


if __name__ == '__main__':
    main()
