"""Dataset-wide regression tests for positive-infinity support provenance."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.io import savemat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import (  # noqa: E402
    CausalSessionDataset,
    build_state_timeline,
    derive_session_time_support,
    inspect_lfp_file,
    load_aligned_session,
)
from data.interval_support import normalise_official_time_pairs  # noqa: E402


DEFAULT_JENN_SESSION = Path(
    r"F:\CfC-Sleep\crcns-downloader\fcx-1\data\20140528_565um"
)
JENN_SESSION = Path(os.environ.get("FCX1_JENN_SESSION_DIR", DEFAULT_JENN_SESSION))


def _synthetic_metadata(
    directory: Path,
    recording_intervals: np.ndarray,
    good_sleep_intervals: np.ndarray,
    *,
    corrupt_byte_count: int = 0,
) -> SimpleNamespace:
    basename = "synthetic"
    n_channels = 2
    lfp_hz = 10.0
    n_timepoints = 100
    eeg_path = directory / f"{basename}.eeg"
    eeg_path.write_bytes(b"\x00" * (n_timepoints * n_channels * 2 + corrupt_byte_count))
    savemat(
        directory / f"{basename}_GoodSleepInterval.mat",
        {"GoodSleepInterval": {"timePairFormat": good_sleep_intervals}},
    )
    recording = normalise_official_time_pairs(
        recording_intervals, field_name="RecordingFileIntervals"
    )
    return SimpleNamespace(
        session_dir=directory,
        basename=basename,
        eeg_path=eeg_path,
        n_channels=n_channels,
        lfp_sample_rate_hz=lfp_hz,
        recording_intervals_s=recording,
        duration_s=float(np.max(recording[:, 1])),
    )


class OpenEndedTimeSupportUnitTest(unittest.TestCase):
    def test_open_end_resolves_to_lfp_while_raw_inf_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = _synthetic_metadata(
                Path(directory),
                np.asarray([[0.0, np.inf]]),
                np.asarray([[0.0, np.inf]]),
            )
            support, lfp = derive_session_time_support(metadata)
            strict_info = inspect_lfp_file(metadata)
            self.assertEqual(lfp.duration_s, 10.0)
            self.assertEqual(strict_info.duration_s, lfp.duration_s)
            self.assertTrue(np.isposinf(support.raw_metadata_recording_intervals_s[0, 1]))
            self.assertTrue(np.isposinf(support.raw_good_sleep_intervals_s[0, 1]))
            np.testing.assert_array_equal(
                support.resolved_metadata_constraint_s, np.asarray([[0.0, 10.0]])
            )
            np.testing.assert_array_equal(
                support.resolved_good_sleep_constraint_s, np.asarray([[0.0, 10.0]])
            )
            np.testing.assert_array_equal(
                support.candidate_analysis_intervals_s, np.asarray([[0.0, 10.0]])
            )
            self.assertEqual(
                support.support_resolution_method,
                "open_end_clipped_to_verified_lfp_support",
            )

    def test_spike_and_annotation_like_values_cannot_change_resolved_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = _synthetic_metadata(
                Path(directory),
                np.asarray([[0.0, np.inf]]),
                np.asarray([[0.0, np.inf]]),
            )
            metadata.last_spike_s = 2.0
            metadata.last_annotation_s = 3.0
            first, _ = derive_session_time_support(metadata)
            metadata.last_spike_s = 9.9
            metadata.last_annotation_s = 1.0
            second, _ = derive_session_time_support(metadata)
            self.assertEqual(first.analysis_end_s, 10.0)
            self.assertEqual(second.analysis_end_s, first.analysis_end_s)

    def test_non_divisible_eeg_cannot_resolve_open_end(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = _synthetic_metadata(
                Path(directory),
                np.asarray([[0.0, np.inf]]),
                np.asarray([[0.0, np.inf]]),
                corrupt_byte_count=1,
            )
            with self.assertRaisesRegex(ValueError, "complete 2-channel time point"):
                derive_session_time_support(metadata)

    def test_nan_negative_infinity_and_invalid_starts_remain_rejected(self) -> None:
        invalid = (
            np.asarray([[0.0, np.nan]]),
            np.asarray([[0.0, -np.inf]]),
            np.asarray([[np.inf, np.inf]]),
            np.asarray([[-np.inf, np.inf]]),
            np.asarray([[2.0, 1.0]]),
            np.asarray([[0.0, np.inf], [2.0, 3.0]]),
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalise_official_time_pairs(value, field_name="test")

    def test_finite_constraints_retain_finite_intersection_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = _synthetic_metadata(
                Path(directory),
                np.asarray([[0.0, 12.0]]),
                np.asarray([[0.0, 10.0]]),
            )
            support, _ = derive_session_time_support(metadata)
            np.testing.assert_array_equal(
                support.raw_metadata_recording_intervals_s,
                np.asarray([[0.0, 12.0]]),
            )
            np.testing.assert_array_equal(
                support.raw_good_sleep_intervals_s,
                np.asarray([[0.0, 10.0]]),
            )
            self.assertEqual(support.analysis_end_s, 10.0)
            self.assertEqual(
                support.support_resolution_method,
                "finite_constraints_intersected_with_verified_lfp_support",
            )

    @unittest.skipUnless(JENN_SESSION.is_dir(), f"Session not found: {JENN_SESSION}")
    def test_20140528_real_session_uses_common_open_end_rule(self) -> None:
        session = load_aligned_session(JENN_SESSION)
        support = session.time_support
        self.assertTrue(np.isposinf(support.raw_metadata_recording_intervals_s[0, 1]))
        self.assertTrue(np.isposinf(support.raw_good_sleep_intervals_s[0, 1]))
        self.assertAlmostEqual(support.analysis_end_s, 12395.736)
        self.assertAlmostEqual(support.analysis_end_s, session.lfp_info.duration_s)
        self.assertGreater(support.analysis_end_s, session.spikes.last_spike_s)
        self.assertTrue(session.report.core_alignment_valid)
        timeline = build_state_timeline(session)
        self.assertTrue(set(timeline.target_label).issubset({"WAKE", "NREM", "REM", "IGNORE"}))
        for width in (5, 10, 30):
            dataset = CausalSessionDataset(session, width)
            self.assertGreater(len(dataset), 0)
            sample = dataset.get_sample(len(dataset) - 1)
            self.assertLess(sample.lfp.time_s[-1], sample.index.decision_time_s)


if __name__ == "__main__":
    unittest.main()
