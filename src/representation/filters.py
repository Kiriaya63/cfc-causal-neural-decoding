"""Deterministic strictly causal LFP filters for the 50-Hz representation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from scipy.signal import butter, firwin, freqz, kaiserord, lfilter, sosfilt

from .config import DEFAULT_CONFIG, RepresentationConfig


@dataclass(frozen=True)
class WaveformFilterDesign:
    taps: np.ndarray
    beta: float
    numtaps: int
    group_delay_input_samples: float
    group_delay_s: float
    full_history_warmup_input_samples: int
    full_history_warmup_s: float
    first_valid_observation_step: int
    stopband_attenuation_db: float
    passband_min_db: float
    passband_max_db: float
    coefficient_sha256: str


@dataclass(frozen=True)
class PhysioFilterDesign:
    names: tuple[str, ...]
    sos: tuple[np.ndarray, ...]
    settling_steps: tuple[int, ...]
    power_window_steps: int
    first_valid_observation_step: int


def design_waveform_filter(
    config: RepresentationConfig = DEFAULT_CONFIG,
) -> WaveformFilterDesign:
    width = (config.waveform_stopband_edge_hz - config.waveform_passband_edge_hz) / (
        config.input_lfp_rate_hz / 2
    )
    numtaps, beta = kaiserord(config.waveform_stopband_attenuation_db, width)
    if numtaps % 2 == 0:
        numtaps += 1
    taps = firwin(
        numtaps,
        config.waveform_cutoff_hz,
        window=("kaiser", beta),
        fs=config.input_lfp_rate_hz,
        scale=True,
    ).astype(np.float64)
    frequencies, response = freqz(
        taps, worN=262_144, fs=config.input_lfp_rate_hz
    )
    stop = np.abs(response[frequencies >= config.waveform_stopband_edge_hz])
    passed = np.abs(response[frequencies <= config.waveform_passband_edge_hz])
    attenuation = float(-20 * np.log10(np.max(stop)))
    if attenuation + 1e-9 < config.waveform_stopband_attenuation_db:
        raise ValueError("Designed FIR does not meet the frozen stopband requirement.")
    factor = config.decimation_factor
    phase = factor - 1
    full_history = numtaps - 1
    first_valid = max(0, int(np.ceil((full_history - phase) / factor)))
    taps.setflags(write=False)
    return WaveformFilterDesign(
        taps=taps,
        beta=float(beta),
        numtaps=numtaps,
        group_delay_input_samples=(numtaps - 1) / 2,
        group_delay_s=(numtaps - 1) / (2 * config.input_lfp_rate_hz),
        full_history_warmup_input_samples=full_history,
        full_history_warmup_s=full_history / config.input_lfp_rate_hz,
        first_valid_observation_step=first_valid,
        stopband_attenuation_db=attenuation,
        passband_min_db=float(20 * np.log10(np.min(passed))),
        passband_max_db=float(20 * np.log10(np.max(passed))),
        coefficient_sha256=hashlib.sha256(taps.tobytes()).hexdigest(),
    )


def _settling_steps(sos: np.ndarray, config: RepresentationConfig) -> int:
    length = int(config.iir_settling_search_s * config.observation_rate_hz)
    impulse = np.zeros(length, dtype=np.float64)
    impulse[0] = 1.0
    response = np.abs(sosfilt(sos, impulse))
    threshold = float(np.max(response)) * config.iir_settling_relative_threshold
    suffix_max = np.maximum.accumulate(response[::-1])[::-1]
    candidates = np.flatnonzero(suffix_max <= threshold)
    if not candidates.size:
        raise ValueError("IIR settling criterion was not reached in the search interval.")
    return int(candidates[0])


def design_physio_filters(
    waveform: WaveformFilterDesign,
    config: RepresentationConfig = DEFAULT_CONFIG,
) -> PhysioFilterDesign:
    names, filters, settling = [], [], []
    for name, low_hz, high_hz in config.physio_bands_hz:
        sos = butter(
            config.physio_filter_order,
            (low_hz, high_hz),
            btype="bandpass",
            fs=config.observation_rate_hz,
            output="sos",
        ).astype(np.float64)
        names.append(name)
        filters.append(sos)
        settling.append(_settling_steps(sos, config))
        sos.setflags(write=False)
    power_steps = int(round(config.physio_power_window_s * config.observation_rate_hz))
    first_valid = (
        waveform.first_valid_observation_step + max(settling) + power_steps - 1
    )
    return PhysioFilterDesign(
        names=tuple(names),
        sos=tuple(filters),
        settling_steps=tuple(settling),
        power_window_steps=power_steps,
        first_valid_observation_step=first_valid,
    )


def causal_waveform_from_array(
    raw_lfp: np.ndarray,
    design: WaveformFilterDesign,
    config: RepresentationConfig = DEFAULT_CONFIG,
) -> np.ndarray:
    """Filter from session origin and sample at each 20-ms bin's last raw sample."""
    values = np.asarray(raw_lfp, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    filtered = lfilter(design.taps, [1.0], values, axis=0)
    n_observations = values.shape[0] // config.decimation_factor
    indices = (
        np.arange(n_observations, dtype=np.int64) * config.decimation_factor
        + config.decimation_factor
        - 1
    )
    return filtered[indices]


def causal_physio_from_waveform(
    waveform: np.ndarray,
    design: PhysioFilterDesign,
    config: RepresentationConfig = DEFAULT_CONFIG,
) -> np.ndarray:
    """Causal bandpass, square, and trailing two-second mean at 50 Hz."""
    values = np.asarray(waveform, dtype=np.float64)
    if values.ndim == 1:
        values = values[:, None]
    result = np.empty((values.shape[0], values.shape[1], len(design.names)))
    kernel = np.ones(design.power_window_steps) / design.power_window_steps
    for band, sos in enumerate(design.sos):
        band_signal = sosfilt(np.array(sos, copy=True), values, axis=0)
        power = lfilter(kernel, [1.0], band_signal * band_signal, axis=0)
        result[:, :, band] = np.log1p(power) if config.physio_log1p else power
    return result


def causal_role_physio_from_waveforms(
    waveforms_by_role: dict[str, np.ndarray],
    design: PhysioFilterDesign,
    config: RepresentationConfig = DEFAULT_CONFIG,
) -> np.ndarray:
    """Build one causal feature per band from its approved functional role."""

    source_roles = dict(config.physio_feature_source_roles)
    if set(source_roles) != set(design.names):
        raise ValueError("Every physiological feature needs exactly one source role.")
    lengths = {
        np.asarray(waveforms_by_role[role]).shape[0]
        for role in set(source_roles.values())
        if role in waveforms_by_role
    }
    missing = set(source_roles.values()) - set(waveforms_by_role)
    if missing:
        raise ValueError(f"Missing waveform source roles: {sorted(missing)}")
    if len(lengths) != 1:
        raise ValueError("All role waveforms must share one observation length.")

    n_steps = lengths.pop()
    result = np.empty((n_steps, len(design.names)), dtype=np.float64)
    kernel = np.ones(design.power_window_steps) / design.power_window_steps
    for band, (name, sos) in enumerate(zip(design.names, design.sos)):
        values = np.asarray(waveforms_by_role[source_roles[name]], dtype=np.float64)
        if values.ndim == 2:
            if values.shape[1] != 1:
                raise ValueError("Each functional role must resolve to one physical signal.")
            values = values[:, 0]
        if values.ndim != 1:
            raise ValueError("Each functional role waveform must be one-dimensional.")
        band_signal = sosfilt(np.array(sos, copy=True), values)
        power = lfilter(kernel, [1.0], band_signal * band_signal)
        result[:, band] = np.log1p(power) if config.physio_log1p else power
    return result
