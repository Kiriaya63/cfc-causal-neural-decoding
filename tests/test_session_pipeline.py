"""Integration checks against the downloaded BWRat17_121712 session."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import (  # noqa: E402
    inspect_lfp_file,
    load_aligned_session,
    load_lfp_window,
    load_session_metadata,
    load_sleep_states,
    load_stable_spikes,
)


DEFAULT_SESSION = Path(
    r"F:\CfC-Sleep\crcns-downloader\fcx-1\data\BWRat17_121712"
)
SESSION_DIR = Path(os.environ.get("FCX1_SESSION_DIR", DEFAULT_SESSION))


@unittest.skipUnless(SESSION_DIR.is_dir(), f"Session not found: {SESSION_DIR}")
class BWRat17PipelineIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = load_session_metadata(SESSION_DIR)

    def test_metadata_cross_file_values(self) -> None:
        metadata = self.metadata
        self.assertEqual(metadata.basename, "BWRat17_121712")
        self.assertEqual(metadata.n_channels, 72)
        self.assertEqual(metadata.lfp_sample_rate_hz, 1250.0)
        self.assertEqual(metadata.acquisition_sample_rate_hz, 20000.0)
        self.assertAlmostEqual(metadata.duration_s, 6059.4)
        self.assertEqual(metadata.anatomy_for_channel(13), "ACC")
        self.assertEqual(metadata.anatomy_for_channel(65), "dhipp")

    def test_lfp_size_and_short_read(self) -> None:
        info = inspect_lfp_file(self.metadata)
        self.assertEqual(info.logical_shape, (7_574_250, 72))
        self.assertEqual(info.remainder_bytes, 0)
        self.assertAlmostEqual(info.duration_s, self.metadata.duration_s)
        window = load_lfp_window(self.metadata, 2428.0, 2433.0, [13, 65])
        self.assertEqual(window.counts.shape, (6250, 2))
        self.assertEqual(window.counts.dtype, np.dtype("<i2"))
        self.assertAlmostEqual(window.time_s[0], 2428.0)
        self.assertAlmostEqual(window.time_s[-1], 2432.9992)
        self.assertFalse(window.counts.flags.writeable)

    def test_stable_spikes(self) -> None:
        spikes = load_stable_spikes(self.metadata)
        self.assertEqual(spikes.n_units, 50)
        self.assertEqual(spikes.total_spikes, 345_203)
        self.assertAlmostEqual(spikes.first_spike_s, 0.04275)
        self.assertAlmostEqual(spikes.last_spike_s, 6059.355)

    def test_sleep_states_report_known_out_of_bounds_rows(self) -> None:
        states = load_sleep_states(self.metadata)
        self.assertEqual(states.wake_sleep_episodes_s.shape, (1, 2, 2))
        np.testing.assert_array_equal(
            states.wake_sleep_episodes_s[0],
            np.asarray([[5.0, 2431.0], [2431.0, 4009.0]]),
        )
        self.assertEqual(len(states.issues), 2)
        observed = {
            (issue.field, issue.start_s, issue.stop_s) for issue in states.issues
        }
        self.assertEqual(
            observed,
            {
                ("MATimePairFormat", 8145.0, 8155.0),
                ("WakeInterruptionTimePairFormat", 6801.0, 6890.0),
            },
        )
        self.assertEqual(states.get("MATimePairFormat").shape, (10, 2))
        self.assertEqual(
            states.get("MATimePairFormat", valid_only=True).shape, (9, 2)
        )

    def test_alignment_separates_core_validity_from_annotation_issues(self) -> None:
        report = load_aligned_session(SESSION_DIR).report
        self.assertTrue(report.core_alignment_valid)
        self.assertTrue(report.lfp_duration_matches_metadata)
        self.assertTrue(report.spikes_within_recording)
        self.assertTrue(report.wake_sleep_episodes_valid)
        self.assertFalse(report.all_sleep_rows_within_recording)
        self.assertEqual(report.sleep_interval_issue_count, 2)


if __name__ == "__main__":
    unittest.main()
