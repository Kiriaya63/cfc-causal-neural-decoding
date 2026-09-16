"""Unified 50-Hz multimodal sample contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np

from data.align_session import AlignedSession
from data.build_state_labels import build_state_timeline
from data.causal_windows import CausalIndexRow, build_causal_sample_index

from .cache import ensure_lfp_cache, open_cached_lfp
from .config import DEFAULT_CONFIG, RepresentationConfig
from .spikes import represent_spikes


MODALITY_ORDER = ("lfp_waveform", "lfp_physio", "spike_population", "spike_set")


@dataclass(frozen=True)
class MultimodalRepresentationSample:
    session_id: str
    decision_time_s: float
    target_label: str
    target_interval_s: np.ndarray
    observation_intervals_s: np.ndarray
    observation_right_edges_s: np.ndarray
    lfp_waveform_50hz: np.ndarray
    lfp_waveform_mask: np.ndarray
    lfp_physio_50hz: np.ndarray
    lfp_physio_mask: np.ndarray
    lfp_channel_roles: tuple[str, ...]
    lfp_channels_one_based: np.ndarray
    lfp_channel_anatomy_provenance: tuple[str | None, ...]
    lfp_channel_role_mask: np.ndarray
    lfp_role_channel_mapping_provenance: dict[str, dict[str, object]]
    lfp_physio_feature_order: tuple[str, ...]
    lfp_physio_feature_source_roles: dict[str, str]
    anatomy_provenance_conflicts: tuple[dict[str, str], ...]
    spike_population_count_50hz: np.ndarray
    spike_population_rate_50hz: np.ndarray
    spike_set_counts_50hz: np.ndarray
    neuron_mask: np.ndarray
    local_unit_number_one_based: np.ndarray
    local_unit_shank_one_based: np.ndarray
    local_unit_cell_index_within_shank: np.ndarray
    modality_mask: np.ndarray
    causal_validity_mask: np.ndarray
    context_length_s: int
    protocol_version: str
    protocol_hash: str


class RepresentationSessionDataset:
    """Random-access causal samples backed by a rebuildable session LFP cache."""

    def __init__(
        self,
        session: AlignedSession,
        context_length_s: int,
        cache_root: str | Path,
        config: RepresentationConfig = DEFAULT_CONFIG,
    ) -> None:
        if context_length_s not in (5, 10, 30):
            raise ValueError("M4 context_length_s must be one of 5, 10, or 30.")
        self.session = session
        self.config = config
        self.context_length_s = context_length_s
        self.cache_directory, self.cache_metadata = ensure_lfp_cache(
            session, cache_root, config
        )
        self.waveform, self.physio, _ = open_cached_lfp(self.cache_directory)
        timeline = build_state_timeline(session)
        index = build_causal_sample_index(
            timeline, session.metadata.basename, context_length_s
        )
        self.m2_valid_rows = tuple(row for row in index.rows if row.valid)
        self.rows = tuple(row for row in self.m2_valid_rows if self._row_is_valid(row))
        self.invalid_rows = tuple(
            row for row in self.m2_valid_rows if not self._row_is_valid(row)
        )

    def _observation_bounds(self, row: CausalIndexRow) -> tuple[int, int]:
        start = int(round(row.context_start_s * self.config.observation_rate_hz))
        stop = int(round(row.decision_time_s * self.config.observation_rate_hz))
        if stop - start != self.context_length_s * self.config.observation_rate_hz:
            raise ValueError("Causal interval does not map exactly to the 50-Hz grid.")
        return start, stop

    def _row_is_valid(self, row: CausalIndexRow) -> bool:
        start, stop = self._observation_bounds(row)
        return (
            start >= self.cache_metadata["physio_first_valid_step"]
            and stop <= self.cache_metadata["observation_count"]
        )

    def __len__(self) -> int:
        return len(self.rows)

    def get_sample(self, index: int) -> MultimodalRepresentationSample:
        return self.sample_for_row(self.rows[index])

    def sample_for_row(self, row: CausalIndexRow) -> MultimodalRepresentationSample:
        start, stop = self._observation_bounds(row)
        absolute_steps = np.arange(start, stop, dtype=np.int64)
        starts = absolute_steps.astype(np.float64) / self.config.observation_rate_hz
        stops = (absolute_steps + 1).astype(np.float64) / self.config.observation_rate_hz
        intervals = np.column_stack((starts, stops))
        waveform = np.asarray(self.waveform[start:stop], dtype=np.float32).copy()
        physio_3d = np.asarray(self.physio[start:stop], dtype=np.float32).copy()
        physio = physio_3d.reshape(len(absolute_steps), -1)
        wave_valid = absolute_steps >= self.cache_metadata["waveform_first_valid_step"]
        phys_valid = absolute_steps >= self.cache_metadata["physio_first_valid_step"]
        wave_mask = np.repeat(wave_valid[:, None], waveform.shape[1], axis=1)
        phys_mask = np.repeat(phys_valid[:, None], physio.shape[1], axis=1)
        spike = represent_spikes(self.session.spikes, starts, stops)
        modality_mask = np.ones(len(MODALITY_ORDER), dtype=bool)
        causal_mask = np.column_stack(
            (wave_valid, phys_valid, np.ones(len(starts), bool), np.ones(len(starts), bool))
        )
        role_channels = np.asarray(self.cache_metadata["channels_one_based"], dtype=np.int64)
        role_mask = np.ones(len(role_channels), dtype=bool)
        target_interval = np.asarray([row.target_start_s, row.target_stop_s])
        unit_number = np.arange(1, self.session.spikes.n_units + 1, dtype=np.int64)
        for array in (
            target_interval, intervals, stops, waveform, physio, wave_mask, phys_mask,
            role_channels, role_mask, modality_mask, causal_mask, unit_number,
        ):
            array.setflags(write=False)
        if intervals.size and (
            intervals[0, 0] != row.context_start_s
            or intervals[-1, 1] != row.decision_time_s
            or np.any(intervals[:, 1] > row.decision_time_s)
        ):
            raise AssertionError("Observation bins violate the strict causal interval.")
        return MultimodalRepresentationSample(
            session_id=self.session.metadata.basename,
            decision_time_s=row.decision_time_s,
            target_label=row.target_label,
            target_interval_s=target_interval,
            observation_intervals_s=intervals,
            observation_right_edges_s=stops,
            lfp_waveform_50hz=waveform,
            lfp_waveform_mask=wave_mask,
            lfp_physio_50hz=physio,
            lfp_physio_mask=phys_mask,
            lfp_channel_roles=tuple(self.cache_metadata["channel_roles"]),
            lfp_channels_one_based=role_channels,
            lfp_channel_anatomy_provenance=tuple(self.cache_metadata["channel_anatomy"]),
            lfp_channel_role_mask=role_mask,
            lfp_role_channel_mapping_provenance=self.cache_metadata["role_channel_mapping"],
            lfp_physio_feature_order=tuple(self.cache_metadata["physio_feature_order"]),
            lfp_physio_feature_source_roles=self.cache_metadata["physio_feature_source_roles"],
            anatomy_provenance_conflicts=tuple(
                self.cache_metadata["anatomy_provenance_conflicts"]
            ),
            spike_population_count_50hz=spike.population_count,
            spike_population_rate_50hz=spike.population_mean_firing_rate_hz,
            spike_set_counts_50hz=spike.counts_by_unit,
            neuron_mask=spike.neuron_mask,
            local_unit_number_one_based=unit_number,
            local_unit_shank_one_based=self.session.spikes.shank_one_based,
            local_unit_cell_index_within_shank=self.session.spikes.cell_index_within_shank,
            modality_mask=modality_mask,
            causal_validity_mask=causal_mask,
            context_length_s=self.context_length_s,
            protocol_version=self.config.protocol_version,
            protocol_hash=self.config.protocol_hash,
        )
