"""Run the manifest-driven Milestone 3 fcx-1 dataset audit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import audit_manifest, load_session_manifest, write_audit_reports  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "config" / "fcx1_milestone3_sessions.csv",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "milestone3",
    )
    parser.add_argument(
        "--notes",
        type=Path,
        default=PROJECT_ROOT / "notes" / "milestone3_dataset_audit.md",
    )
    args = parser.parse_args()

    entries = load_session_manifest(args.manifest)
    results = audit_manifest(entries)
    write_audit_reports(results, args.report_dir, dataset_notes_path=args.notes)
    for result in results:
        print(
            f"{result.session_id}: {result.qc_status} "
            f"(core={result.core_alignment_valid}, causal={result.causal_sample_valid})"
        )
    if any(result.qc_status == "FAIL" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
