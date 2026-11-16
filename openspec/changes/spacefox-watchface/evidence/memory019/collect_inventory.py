"""Inventory a fixed Git tree; never treat inventory as semantic review."""
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

BASE = "943f320c33b253b913eb8276d1c09b65d51a6c8a"
ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent


def classify(path: str) -> tuple[str, str]:
    suffix = Path(path).suffix.lower()
    if path.startswith("openspec/") and "/evidence/" in path:
        return "historical-evidence", "RETAINED_ARTIFACT_NOT_CURRENT_CODE"
    if path.startswith("watchface/source/") and suffix == ".mc":
        return "native-runtime", "PENDING_FULL_READ"
    if path.startswith("watchface/") and "test" in path.split("/")[1]:
        return "native-tests", "PENDING_TEST_BOUNDARY_REVIEW"
    if path.startswith("watchface/resources"):
        return "native-resources", "PENDING_RESOURCE_ANALYSIS"
    if path.startswith("tools/spacefox/") and suffix == ".py":
        return "publisher-package", "PENDING_FULL_READ"
    if path.startswith("deploy/cloudflare-schedule/") or path.startswith(".github/workflows/"):
        return "scheduler-workflows", "PENDING_FULL_READ"
    if path.startswith("tools/") and suffix in {".py", ".sh", ".js", ".mjs", ".java"}:
        return "engineering-tools", "PENDING_FULL_READ"
    if path.startswith("tests/"):
        return "host-tests-fixtures", "PENDING_TEST_BOUNDARY_REVIEW"
    if path.startswith("prototype/"):
        return "browser-prototype-research", "PENDING_PROTOTYPE_DISPOSITION"
    if path.startswith(("assets/", "corpus/", "locales/", "catalog/", "schemas/")):
        return "catalog-assets-data", "PENDING_DATA_ANALYSIS"
    if suffix in {".py", ".mc", ".sh", ".js", ".mjs", ".ts"}:
        return "other-executable", "PENDING_FULL_READ"
    return "documentation-build-metadata", "PENDING_DISPOSITION"


def main() -> None:
    raw = subprocess.run(
        ["git", "ls-tree", "-rlz", "--full-tree", BASE],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    prior_path = OUT / "FILE-INVENTORY.csv"
    prior = {r["path"]: r for r in csv.DictReader(prior_path.open())} if prior_path.exists() else {}
    rows = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        head, name = entry.split(b"\t", 1)
        mode, kind, blob, size = head.decode().split()
        path = name.decode("utf-8")
        group, state = classify(path)
        old = prior.get(path)
        if old and old["git_blob"] == blob:
            state = old["review_state"]
        rows.append({"path": path, "package": group, "object_type": kind,
                     "mode": mode, "git_blob": blob,
                     "bytes": int(size) if size != "-" else 0,
                     "review_state": state, "audit_note": old["audit_note"] if old and old["git_blob"] == blob else ""})
    assert rows and len({r["path"] for r in rows}) == len(rows)
    with (OUT / "FILE-INVENTORY.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(r["package"] for r in rows)
    sizes = Counter()
    for row in rows:
        sizes[row["package"]] += row["bytes"]
    result = {"base": BASE, "tracked_files": len(rows),
              "tracked_bytes": sum(r["bytes"] for r in rows),
              "packages": [{"package": k, "files": counts[k], "bytes": sizes[k]}
                           for k in sorted(counts)],
              "proof_boundary": "Git tree inventory only; not semantic review or RAM"}
    (OUT / "INVENTORY-SUMMARY.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
