"""Integration tests for the manifest-driven Milestone 3 audit."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import (  # noqa: E402
    audit_manifest,
    load_session_manifest,
    write_audit_reports,
)


MANIFEST = PROJECT_ROOT / "config" / "fcx1_milestone3_sessions.csv"


class MultiSessionAuditIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = load_session_manifest(MANIFEST)
        cls.results = audit_manifest(cls.entries)

    def test_manifest_discovers_five_requested_sessions(self) -> None:
        self.assertEqual(len(self.entries), 5)
        self.assertEqual(
            {entry.session_id for entry in self.entries},
            {
                "BWRat17_121712",
                "BWRat18_020513",
                "BWRat19_032513",
                "BWRat20_101013",
                "Splinter_020915",
            },
        )
        for entry in self.entries:
            self.assertEqual(entry.availability, entry.local_path.is_dir())

    def test_qc_schema_and_label_arithmetic_are_uniform(self) -> None:
        self.assertEqual(len(self.results), len(self.entries))
        schema = set(self.results[0].to_dict())
        for result in self.results:
            self.assertEqual(set(result.to_dict()), schema)
            self.assertNotEqual(result.qc_status, "FAIL")
            self.assertTrue(result.sleep_annotations_valid)
            self.assertGreater(len(result.metadata_recording_intervals_s), 0)
            self.assertGreater(len(result.lfp_support_intervals_s), 0)
            self.assertGreater(len(result.good_sleep_intervals_s), 0)
            self.assertGreater(len(result.candidate_analysis_intervals_s), 0)
            self.assertTrue(result.label_coverage_arithmetic_valid)
            self.assertEqual(
                result.wake_seconds
                + result.nrem_seconds
                + result.rem_seconds
                + result.ignore_seconds,
                result.full_1s_bin_count,
            )

    def test_invalid_annotations_are_masked_and_causal_checks_pass(self) -> None:
        for result in self.results:
            self.assertTrue(result.invalid_annotations_masked)
            self.assertTrue(result.core_alignment_valid)
            self.assertTrue(result.causal_sample_valid)
            self.assertEqual(result.causal_contexts_checked_s, (5, 10, 30))
            self.assertTrue(
                all(count > 0 for count in result.causal_sample_counts_by_context.values())
            )

    def test_aggregate_and_individual_report_counts_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_dir = Path(directory) / "reports"
            notes_path = Path(directory) / "milestone3_dataset_audit.md"
            write_audit_reports(
                self.results, report_dir, dataset_notes_path=notes_path
            )
            with (report_dir / "fcx1_session_qc.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as stream:
                rows = list(csv.DictReader(stream))
            json_paths = sorted((report_dir / "sessions").glob("*_qc.json"))
            self.assertEqual(len(rows), len(self.results))
            self.assertEqual(len(json_paths), len(self.results))
            self.assertEqual(
                {row["session_id"] for row in rows},
                {result.session_id for result in self.results},
            )
            for path in json_paths:
                self.assertIn(json.loads(path.read_text(encoding="utf-8"))["session_id"], {
                    result.session_id for result in self.results
                })
            self.assertTrue(notes_path.is_file())


if __name__ == "__main__":
    unittest.main()
