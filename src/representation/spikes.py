"""50-Hz population and variable-neuron spike representations."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from data.bin_spikes import bin_stable_spikes
from data.load_spikes import StableSpikes


@dataclass(frozen=True)
class SpikeRepresentation:
    counts_by_unit: np.ndarray
    population_count: np.ndarray
    population_mean_firing_rate_hz: np.ndarray
    neuron_mask: np.ndarray


def represent_spikes(
    spikes: StableSpikes, bin_start_s: np.ndarray, bin_stop_s: np.ndarray
) -> SpikeRepresentation:
    binned = bin_stable_spikes(spikes, bin_start_s, bin_stop_s)
    counts = binned.counts.copy()
    population_count = counts.sum(axis=1, keepdims=True, dtype=np.int64)
    rate = population_count.astype(np.float64) / (
        spikes.n_units * binned.bin_width_s
    )
    mask = np.ones(spikes.n_units, dtype=bool)
    for array in (counts, population_count, rate, mask):
        array.setflags(write=False)
    return SpikeRepresentation(counts, population_count, rate, mask)


def pad_variable_neuron_batch(
    counts: list[np.ndarray], masks: list[np.ndarray] | None = None
) -> tuple[np.ndarray, np.ndarray]:
    if not counts:
        raise ValueError("At least one variable-neuron tensor is required.")
    steps = counts[0].shape[0]
    if any(value.ndim != 2 or value.shape[0] != steps for value in counts):
        raise ValueError("All tensors must have shape [T, N] with the same T.")
    maximum = max(value.shape[1] for value in counts)
    padded = np.zeros((len(counts), steps, maximum), dtype=counts[0].dtype)
    neuron_mask = np.zeros((len(counts), maximum), dtype=bool)
    for index, value in enumerate(counts):
        n_units = value.shape[1]
        padded[index, :, :n_units] = value
        if masks is None:
            neuron_mask[index, :n_units] = True
        else:
            supplied = np.asarray(masks[index], dtype=bool)
            if supplied.shape != (n_units,):
                raise ValueError("Each neuron mask must match its local unit axis.")
            neuron_mask[index, :n_units] = supplied
    padded.setflags(write=False)
    neuron_mask.setflags(write=False)
    return padded, neuron_mask


def population_rate_from_padded(
    padded_counts: np.ndarray, neuron_mask: np.ndarray, bin_width_s: float
) -> np.ndarray:
    values = np.asarray(padded_counts)
    mask = np.asarray(neuron_mask, dtype=bool)
    if values.ndim != 3 or mask.shape != (values.shape[0], values.shape[2]):
        raise ValueError("Expected counts [B,T,N] and mask [B,N].")
    valid_units = mask.sum(axis=1)
    if np.any(valid_units == 0):
        raise ValueError("Every batch item needs at least one real neuron.")
    masked = np.where(mask[:, None, :], values, 0)
    return masked.sum(axis=2, keepdims=True) / (
        valid_units[:, None, None] * bin_width_s
    )
