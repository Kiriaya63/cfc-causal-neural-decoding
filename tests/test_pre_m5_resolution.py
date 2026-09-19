"""Focused regressions for the approved pre-M5 representation resolution."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from representation import (
    CACHE_ARRAY_IMPLEMENTATION_FILES,
    DEFAULT_CONFIG,
    MODEL_INPUT_SCHEMA_VERSION,
    MODEL_INPUT_FIELD_WHITELIST,
    anatomy_provenance_conflicts,
    cache_artifacts_match,
    causal_physio_from_waveform,
    causal_role_physio_from_waveforms,
    causal_waveform_from_array,
    design_physio_filters,
    design_waveform_filter,
    ensure_lfp_cache,
    model_input_schema_hash,
    open_cached_lfp,
    representation_cache_identity,
    role_channel_mapping,
    to_model_input,
)
import representation.model_input as model_input_module
from unittest.mock import patch


class SyntheticMetadata:
    def __init__(self, root: Path, channels: tuple[int, int, int, int], raw: np.ndarray):
        self.session_dir = root
        self.basename = root.name
        self.lfp_sample_rate_hz = 1250.0
        self.n_channels = raw.shape[1]
        self.n_bits = 16
        self.duration_s = raw.shape[0] / self.lfp_sample_rate_hz
        self.recording_intervals_s = np.array([[0.0, self.duration_s]])
        self.good_lfp_channel_one_based = channels[0]
        self.theta_channel_one_based = channels[1]
        self.spindle_channel_one_based = channels[2]
        self.up_state_channel_one_based = channels[3]
        self.eeg_path = root / f"{self.basename}.eeg"
        raw.astype("<i2").tofile(self.eeg_path)
        for suffix, payload in (
            (".xml", b"<parameters/>"),
            ("_BasicMetaData.mat", b"synthetic metadata"),
            ("_ChannelAnatomy.csv", b"1,ctx\n"),
        ):
            (root / f"{self.basename}{suffix}").write_bytes(payload)

    def python_channel_index(self, channel_one_based: int) -> int:
        return channel_one_based - 1

    def anatomy_for_channel(self, channel_one_based: int) -> str:
        return f"region_{channel_one_based}"


def synthetic_session(root: Path, channels: tuple[int, int, int, int], raw: np.ndarray):
    metadata = SyntheticMetadata(root, channels, raw)
    return SimpleNamespace(
        metadata=metadata,
        report=SimpleNamespace(common_end_s=metadata.duration_s),
        lfp_info=SimpleNamespace(n_timepoints=raw.shape[0]),
    )


class PreM5ResolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.waveform_design = design_waveform_filter()
        cls.physio_design = design_physio_filters(cls.waveform_design)

    def test_shared_good_theta_has_one_waveform_and_deduplicated_read(self):
        raw = np.arange(2500, dtype=np.int16)[:, None]
        with tempfile.TemporaryDirectory() as tmp:
            session_dir = Path(tmp) / "shared"
            session_dir.mkdir()
            session = synthetic_session(session_dir, (1, 1, 1, 1), raw)
            directory, metadata = ensure_lfp_cache(session, Path(tmp) / "cache")
            waveform, physio, _ = open_cached_lfp(directory)
            self.assertEqual(waveform.shape, (100, 1))
            self.assertEqual(physio.shape, (100, 4))
            self.assertEqual(metadata["physical_feature_channels_loaded_one_based"], [1])
            self.assertTrue(metadata["physical_feature_channel_reads_deduplicated"])
            del waveform, physio

    def test_distinct_theta_still_keeps_good_eeg_only_waveform(self):
        raw = np.column_stack(
            (np.arange(2500), np.arange(2500) * 2, np.arange(2500) * -1)
        ).astype(np.int16)
        with tempfile.TemporaryDirectory() as tmp:
            session_dir = Path(tmp) / "distinct"
            session_dir.mkdir()
            session = synthetic_session(session_dir, (1, 2, 3, 1), raw)
            directory, _ = ensure_lfp_cache(session, Path(tmp) / "cache")
            waveform, _, _ = open_cached_lfp(directory)
            expected = causal_waveform_from_array(raw[:, 0], self.waveform_design)
            np.testing.assert_array_equal(waveform[:, 0], expected[:, 0].astype(np.float32))
            del waveform

    def test_feature_sources_are_theta_and_spindle_roles(self):
        rng = np.random.default_rng(7)
        roles = {
            "good_eeg": rng.normal(size=800),
            "theta": rng.normal(size=800),
            "spindle": rng.normal(size=800),
        }
        actual = causal_role_physio_from_waveforms(roles, self.physio_design)
        for band, name in enumerate(self.physio_design.names):
            source = dict(DEFAULT_CONFIG.physio_feature_source_roles)[name]
            expected = causal_physio_from_waveform(
                roles[source], self.physio_design
            )[:, 0, band]
            np.testing.assert_allclose(actual[:, band], expected, rtol=0, atol=0)
        self.assertEqual(dict(DEFAULT_CONFIG.physio_feature_source_roles)["theta"], "theta")
        self.assertEqual(dict(DEFAULT_CONFIG.physio_feature_source_roles)["sigma"], "spindle")

    def test_shared_physical_signal_can_supply_distinct_features(self):
        signal = np.sin(np.arange(800) / 17.0)
        actual = causal_role_physio_from_waveforms(
            {"good_eeg": signal, "theta": signal, "spindle": signal},
            self.physio_design,
        )
        self.assertEqual(actual.shape, (800, 4))
        self.assertTrue(np.all(np.isfinite(actual)))

    def test_role_mapping_preserves_source_and_indexing_provenance(self):
        metadata = SimpleNamespace(
            good_lfp_channel_one_based=5,
            theta_channel_one_based=7,
            spindle_channel_one_based=5,
            up_state_channel_one_based=9,
            python_channel_index=lambda channel: channel - 1,
            anatomy_for_channel=lambda channel: f"r{channel}",
        )
        mapping = role_channel_mapping(metadata)
        self.assertEqual(mapping["good_eeg"]["source_field"], "goodeegchannel")
        self.assertEqual(mapping["theta"]["physical_channel_one_based"], 7)
        self.assertEqual(mapping["theta"]["numpy_column_zero_based"], 6)
        self.assertEqual(mapping["spindle"]["physical_channel_one_based"], 5)
        self.assertEqual(mapping["up_state"]["physical_channel_one_based"], 9)

    def test_model_input_whitelist_excludes_provenance_and_identity(self):
        prohibited = {
            "animal_id", "session_id", "filename", "path", "physical_channel_id",
            "anatomy", "local_unit_id", "recording_condition", "role_channel_mapping",
            "lfp_channels_one_based", "local_unit_shank_one_based",
            "observation_intervals_s", "observation_right_edges_s", "decision_time_s",
            "context_start_s",
        }
        self.assertFalse(prohibited & set(MODEL_INPUT_FIELD_WHITELIST))
        self.assertIn("observation_delta_t_s", MODEL_INPUT_FIELD_WHITELIST)
        self.assertIn("neuron_mask", MODEL_INPUT_FIELD_WHITELIST)
        self.assertIn("causal_validity_mask", MODEL_INPUT_FIELD_WHITELIST)

    @staticmethod
    def _model_sample_at(start_s: float, steps: int = 5):
        starts = start_s + np.arange(steps, dtype=np.float64) * 0.02
        stops = starts + 0.02
        return SimpleNamespace(
            observation_intervals_s=np.column_stack((starts, stops)),
            observation_right_edges_s=stops,
            lfp_waveform_50hz=np.zeros((steps, 1), dtype=np.float32),
            lfp_waveform_mask=np.ones((steps, 1), dtype=bool),
            lfp_physio_50hz=np.zeros((steps, 4), dtype=np.float32),
            lfp_physio_mask=np.ones((steps, 4), dtype=bool),
            spike_population_rate_50hz=np.zeros((steps, 1), dtype=np.float32),
            spike_set_counts_50hz=np.zeros((steps, 2), dtype=np.int64),
            neuron_mask=np.ones(2, dtype=bool),
            modality_mask=np.ones(4, dtype=bool),
            causal_validity_mask=np.ones((steps, 4), dtype=bool),
        )

    def test_model_delta_t_is_invariant_to_absolute_session_time(self):
        early = to_model_input(self._model_sample_at(5.0))
        late = to_model_input(self._model_sample_at(12345.0))
        np.testing.assert_array_equal(
            early.observation_delta_t_s, late.observation_delta_t_s
        )

    def test_model_input_has_no_absolute_time_or_provenance_fields(self):
        prohibited = {
            "observation_intervals_s", "observation_right_edges_s",
            "decision_time_s", "context_start_s", "session_id", "animal_id",
            "target_interval_s", "target_label", "protocol_hash",
        }
        model_input = to_model_input(self._model_sample_at(300.0))
        self.assertFalse(prohibited & set(vars(model_input)))
        self.assertEqual(set(vars(model_input)), set(MODEL_INPUT_FIELD_WHITELIST))

    def test_regular_50hz_model_delta_t_is_20ms_every_step(self):
        model_input = to_model_input(self._model_sample_at(9876.0, steps=1500))
        np.testing.assert_array_equal(
            model_input.observation_delta_t_s,
            np.full(1500, 0.02, dtype=np.float64),
        )

    def test_model_delta_t_rejects_invalid_timing(self):
        sample = self._model_sample_at(10.0)
        mismatched = SimpleNamespace(**vars(sample))
        mismatched.observation_right_edges_s = sample.observation_right_edges_s.copy()
        mismatched.observation_right_edges_s[2] += 0.001
        with self.assertRaisesRegex(ValueError, "disagree"):
            to_model_input(mismatched)

        nonmonotonic = SimpleNamespace(**vars(sample))
        intervals = sample.observation_intervals_s.copy()
        intervals[2, 1] = intervals[1, 1]
        nonmonotonic.observation_intervals_s = intervals
        nonmonotonic.observation_right_edges_s = intervals[:, 1].copy()
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            to_model_input(nonmonotonic)

    def test_cache_hash_scope_excludes_model_adapter(self):
        names = set(CACHE_ARRAY_IMPLEMENTATION_FILES)
        self.assertNotIn("src/representation/model_input.py", names)
        self.assertNotIn("src/representation/samples.py", names)
        self.assertTrue(
            {
                "src/representation/cache.py",
                "src/representation/config.py",
                "src/representation/filters.py",
                "src/representation/provenance.py",
                "src/data/load_lfp.py",
                "src/data/load_metadata.py",
                "src/data/time_support.py",
            }.issubset(names)
        )

    def test_model_input_schema_has_independent_versioned_hash(self):
        current = model_input_schema_hash()
        self.assertEqual(MODEL_INPUT_SCHEMA_VERSION, "m4-model-input-v1.0.0")
        with patch.object(
            model_input_module,
            "MODEL_INPUT_SCHEMA_VERSION",
            "m4-model-input-v1.0.1",
        ):
            self.assertNotEqual(current, model_input_schema_hash())

    def test_cache_detects_readable_content_corruption(self):
        raw = np.arange(2500, dtype=np.int16)[:, None]
        with tempfile.TemporaryDirectory() as tmp:
            session_dir = Path(tmp) / "corrupt"
            session_dir.mkdir()
            session = synthetic_session(session_dir, (1, 1, 1, 1), raw)
            directory, metadata = ensure_lfp_cache(session, Path(tmp) / "cache")
            path = directory / "lfp_waveform_50hz.npy"
            array = np.load(path, mmap_mode="r+")
            array[0, 0] += 1
            array.flush()
            del array
            self.assertFalse(cache_artifacts_match(directory, metadata))
            _, rebuilt = ensure_lfp_cache(session, Path(tmp) / "cache")
            self.assertTrue(cache_artifacts_match(directory, rebuilt))

    def test_representation_config_changes_cache_identity(self):
        changed = replace(DEFAULT_CONFIG, waveform_cutoff_hz=21.5)
        self.assertNotEqual(DEFAULT_CONFIG.protocol_hash, changed.protocol_hash)
        self.assertNotEqual(
            representation_cache_identity(DEFAULT_CONFIG),
            representation_cache_identity(changed),
        )

    def test_templeton_conflict_is_provenance_only(self):
        conflicts = anatomy_provenance_conflicts("Templeton_032415")
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["claim_a"], "OFC")
        self.assertEqual(conflicts[0]["claim_b"], "mPFC")
        self.assertEqual(conflicts[0]["exclude_session"], "false")
        self.assertFalse(any("anatomy" in field for field in MODEL_INPUT_FIELD_WHITELIST))


if __name__ == "__main__":
    unittest.main()
