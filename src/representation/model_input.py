"""Strict model-facing whitelist for future M5/M6 adapters."""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np

from .samples import MultimodalRepresentationSample


@dataclass(frozen=True)
class ModelInput:
    observation_delta_t_s: np.ndarray
    lfp_waveform_50hz: np.ndarray
    lfp_waveform_mask: np.ndarray
    lfp_physio_50hz: np.ndarray
    lfp_physio_mask: np.ndarray
    spike_population_rate_50hz: np.ndarray
    spike_set_counts_50hz: np.ndarray
    neuron_mask: np.ndarray
    modality_mask: np.ndarray
    causal_validity_mask: np.ndarray


MODEL_INPUT_FIELD_WHITELIST = tuple(field.name for field in fields(ModelInput))


def _observation_delta_t_s(sample: MultimodalRepresentationSample) -> np.ndarray:
    """Derive relative elapsed observation time without exposing session position."""

    intervals = np.asarray(sample.observation_intervals_s, dtype=np.float64)
    right_edges = np.asarray(sample.observation_right_edges_s, dtype=np.float64)
    if intervals.ndim != 2 or intervals.shape[1] != 2:
        raise ValueError("observation_intervals_s must have shape [T,2].")
    if right_edges.ndim != 1 or right_edges.shape[0] != intervals.shape[0]:
        raise ValueError("observation_right_edges_s must have shape [T].")
    if not np.all(np.isfinite(intervals)) or not np.all(np.isfinite(right_edges)):
        raise ValueError("Observation timing must be finite.")
    if not np.array_equal(right_edges, intervals[:, 1]):
        raise ValueError("Observation right edges disagree with interval stops.")
    if right_edges.size == 0:
        delta_t = np.empty(0, dtype=np.float64)
    else:
        delta_t = np.concatenate(
            ([intervals[0, 1] - intervals[0, 0]], np.diff(right_edges))
        )
        # Remove floating cancellation from large absolute session times so it
        # cannot encode session position. Nanosecond precision is far finer
        # than the current 20-ms grid and remains suitable for future irregular
        # observation intervals.
        delta_t = np.round(delta_t, decimals=9)
    if np.any(delta_t <= 0):
        raise ValueError("Observation elapsed times must be strictly positive.")
    delta_t.setflags(write=False)
    return delta_t


def to_model_input(sample: MultimodalRepresentationSample) -> ModelInput:
    """Expose relative timing and observations, dropping absolute time/provenance."""

    return ModelInput(
        observation_delta_t_s=_observation_delta_t_s(sample),
        lfp_waveform_50hz=sample.lfp_waveform_50hz,
        lfp_waveform_mask=sample.lfp_waveform_mask,
        lfp_physio_50hz=sample.lfp_physio_50hz,
        lfp_physio_mask=sample.lfp_physio_mask,
        spike_population_rate_50hz=sample.spike_population_rate_50hz,
        spike_set_counts_50hz=sample.spike_set_counts_50hz,
        neuron_mask=sample.neuron_mask,
        modality_mask=sample.modality_mask,
        causal_validity_mask=sample.causal_validity_mask,
    )
