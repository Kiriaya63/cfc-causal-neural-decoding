"""Regression coverage for the BWRat18 time-support discrepancy."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import (  # noqa: E402
    CausalSessionDataset,
    build_state_timeline,
    derive_session_time_support,
    load_aligned_session,
    load_session_metadata,
)


DEFAULT_SESSION = Path(
    r"F:\CfC-Sleep\crcns-downloader\fcx-1\data\BWRat18_020513"
)
SESSION_DIR = Path(os.environ.get("FCX1_BWRAT18_SESSION_DIR", DEFAULT_SESSION))


@unittest.skipUnless(SESSION_DIR.is_dir(), f"Session not found: {SESSION_DIR}")
class BWRat18TimeSupportRegressionTest(unittest.TestCase):
    def test_lfp_good_sleep_define_support_without_shortening_to_last_spike(self) -> None:
        metadata = load_session_metadata(SESSION_DIR)
        support, lfp_info = derive_session_time_support(metadata)

        np.testing.assert_array_equal(
            support.metadata_recording_intervals_s,
            np.asarray([[0.0, 973.9], [973.9, 9388.8]]),
        )
        np.testing.assert_array_equal(
            support.good_sleep_intervals_s, np.asarray([[0.0, 7591.0]])
        )
        self.assertAlmostEqual(metadata.duration_s, 9388.8)
        self.assertAlmostEqual(lfp_info.duration_s, 7591.0)
        self.assertAlmostEqual(support.analysis_end_s, 7591.0)
        self.assertTrue(support.duration_mismatch)
        self.assertEqual(
            [(finding.code, finding.field) for finding in support.findings],
            [
                (
                    "duration_mismatch",
                    "BasicMetaData.RecordingFileIntervals_vs_LFP",
                )
            ],
        )

        session = load_aligned_session(SESSION_DIR)
        report = session.report
        self.assertAlmostEqual(report.common_end_s, 7591.0)
        self.assertAlmostEqual(report.metadata_recording_end_s, 9388.8)
        self.assertFalse(report.lfp_duration_matches_metadata)
        self.assertTrue(report.lfp_duration_matches_analysis_support)
        self.assertTrue(report.spikes_within_recording)
        self.assertTrue(report.wake_sleep_episodes_valid)
        self.assertTrue(report.core_alignment_valid)
        self.assertAlmostEqual(session.spikes.last_spike_s, 7590.45115)
        self.assertGreater(report.common_end_s, session.spikes.last_spike_s)
        self.assertAlmostEqual(
            session.sleep_states.wake_sleep_episodes_s[-1, 1, 1], 7591.0
        )

        timeline = build_state_timeline(session)
        self.assertEqual(timeline.coverage.full_bin_count, 7591)
        dataset = CausalSessionDataset(session, context_length_s=5)
        sample = dataset.get_sample(len(dataset) - 1)
        self.assertLess(sample.lfp.time_s[-1], sample.index.decision_time_s)


if __name__ == "__main__":
    unittest.main()
