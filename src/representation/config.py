"""Frozen, data-independent Milestone 4 representation configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class RepresentationConfig:
    protocol_version: str = "m4-v1.1.0"
    decision_rate_hz: int = 1
    observation_rate_hz: int = 50
    input_lfp_rate_hz: int = 1250
    waveform_passband_edge_hz: float = 20.0
    waveform_stopband_edge_hz: float = 25.0
    waveform_stopband_attenuation_db: float = 60.0
    waveform_cutoff_hz: float = 22.5
    waveform_design: str = "kaiser_window_fir"
    waveform_decimation_phase: str = "last_input_sample_before_observation_right_edge"
    physio_filter_family: str = "butterworth_sos"
    physio_filter_order: int = 4
    physio_bands_hz: tuple[tuple[str, float, float], ...] = (
        ("delta", 0.5, 4.0),
        ("theta", 4.0, 10.0),
        ("sigma", 10.0, 16.0),
        ("broadband", 0.5, 20.0),
    )
    physio_feature_source_roles: tuple[tuple[str, str], ...] = (
        ("delta", "good_eeg"),
        ("theta", "theta"),
        ("sigma", "spindle"),
        ("broadband", "good_eeg"),
    )
    physio_power_window_s: float = 2.0
    physio_log1p: bool = True
    iir_settling_relative_threshold: float = 1e-4
    iir_settling_search_s: float = 60.0
    lfp_value_unit: str = "ADC_count"
    spike_population_unit: str = "spikes_per_second_per_stable_unit"
    normalization_fit_stage: str = "M5_training_animals_only"
    cache_chunk_raw_frames: int = 250_000

    @property
    def observation_interval_s(self) -> float:
        return 1.0 / self.observation_rate_hz

    @property
    def decimation_factor(self) -> int:
        if self.input_lfp_rate_hz % self.observation_rate_hz:
            raise ValueError("Input and observation rates require integer decimation.")
        return self.input_lfp_rate_hz // self.observation_rate_hz

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def protocol_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


DEFAULT_CONFIG = RepresentationConfig()
