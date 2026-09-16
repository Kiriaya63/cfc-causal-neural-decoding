"""Structural regression tests for the 11-animal M3-B1 audit."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import (  # noqa: E402
    CausalSessionDataset,
    audit_manifest,
    build_state_timeline,
    load_aligned_session,
    load_session_manifest,
)


MANIFEST = PROJECT_ROOT / "config" / "fcx1_milestone3b1_sessions.csv"
REQUIRED_SUFFIXES = (
    "_BasicMetaData.mat",
    ".xml",
    "_ChannelAnatomy.csv",
    "_GoodSleepInterval.mat",
    "_WSRestrictedIntervals.mat",
    "_SStable.mat",
    ".eeg",
)


class Milestone3B1StructuralTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = load_session_manifest(MANIFEST)
        cls.results = audit_manifest(cls.entries)

    def test_manifest_has_11_unique_animals_and_readable_required_files(self) -> None:
        self.assertEqual(len(self.entries), 11)
        self.assertEqual(len({entry.session_id for entry in self.entries}), 11)
        self.assertEqual(len({entry.animal_id for entry in self.entries}), 11)
        for entry in self.entries:
            self.assertTrue(entry.availability)
            self.assertTrue(entry.local_path.is_dir())
            for suffix in REQUIRED_SUFFIXES:
                path = entry.local_path / f"{entry.session_id}{suffix}"
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 0, path)
                with path.open("rb") as stream:
                    self.assertTrue(stream.read(16), path)

    def test_common_pipeline_preserves_support_labels_and_invalid_masks(self) -> None:
        failures = {result.session_id: result for result in self.results if result.qc_status == "FAIL"}
        self.assertEqual(failures, {})

        by_id = {entry.session_id: entry for entry in self.entries}
        for result in self.results:
            session = load_aligned_session(by_id[result.session_id].local_path)
            support = session.time_support
            self.assertTrue(support.is_single_contiguous_interval)
            self.assertAlmostEqual(support.analysis_start_s, 0.0)
            self.assertGreaterEqual(support.analysis_start_s, support.lfp_support_intervals_s[0, 0])
            self.assertLessEqual(support.analysis_end_s, support.lfp_support_intervals_s[0, 1])
            timeline = build_state_timeline(session)
            self.assertTrue(set(timeline.target_label).issubset({"WAKE", "NREM", "REM", "IGNORE"}))
            np.testing.assert_array_equal(timeline.valid_label, timeline.target_label != "IGNORE")
            self.assertTrue(np.all(timeline.target_label[~timeline.valid_label] == "IGNORE"))
            for issue in session.sleep_states.issues:
                self.assertFalse(session.sleep_states.valid_masks[issue.field][issue.row_index])
            conflict = timeline.invalid_reason == "conflicting_annotations"
            self.assertTrue(np.all(~timeline.valid_label[conflict]))
            self.assertTrue(np.all(timeline.target_label[conflict] == "IGNORE"))

    def test_each_supported_session_has_strict_past_only_5_10_30s_samples(self) -> None:
        by_id = {entry.session_id: entry for entry in self.entries}
        for result in self.results:
            session = load_aligned_session(by_id[result.session_id].local_path)
            for width in (5, 10, 30):
                dataset = CausalSessionDataset(session, width)
                self.assertGreater(len(dataset), 0)
                for index in sorted({0, len(dataset) // 2, len(dataset) - 1}):
                    sample = dataset.get_sample(index)
                    row = sample.index
                    self.assertTrue(row.valid)
                    self.assertIn(row.target_label, {"WAKE", "NREM", "REM"})
                    self.assertTrue(math.isclose(row.context_start_s, row.decision_time_s - width))
                    self.assertTrue(math.isclose(row.context_stop_s, row.decision_time_s))
                    self.assertTrue(math.isclose(row.target_start_s, row.decision_time_s - 1.0))
                    self.assertTrue(math.isclose(row.target_stop_s, row.decision_time_s))
                    if sample.lfp.time_s.size:
                        self.assertLess(sample.lfp.time_s[-1], row.decision_time_s)
                    if sample.spike_bin_stop_s.size:
                        self.assertLessEqual(sample.spike_bin_stop_s[-1], row.decision_time_s)


if __name__ == "__main__":
    unittest.main()
