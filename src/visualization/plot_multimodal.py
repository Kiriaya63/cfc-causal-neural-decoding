"""Plot aligned sleep state, LFP, and stable-spike sanity checks."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from scipy.signal import spectrogram

from data.align_session import AlignedSession
from data.load_lfp import load_lfp_window, open_lfp_memmap


STATE_COLORS = {
    "WAKE": "#E69F00",
    "SLEEP": "#56B4E9",
    "SWS packet": "#0072B2",
    "REM": "#CC79A7",
    "Microarousal": "#F0E442",
    "Wake interruption": "#D55E00",
}


def _overlapping_intervals(
    session: AlignedSession,
    field: str,
    start_s: float,
    stop_s: float,
) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    for start, stop in session.sleep_states.get(field, valid_only=True):
        clipped_start = max(float(start), start_s)
        clipped_stop = min(float(stop), stop_s)
        if clipped_stop > clipped_start:
            intervals.append((clipped_start, clipped_stop))
    return intervals


def _plot_state_timeline(
    ax: plt.Axes,
    session: AlignedSession,
    start_s: float,
    stop_s: float,
) -> None:
    broad = (
        ("WakeTimePairFormat", "WAKE"),
        ("SleepTimePairFormat", "SLEEP"),
    )
    fine = (
        ("SWSPacketTimePairFormat", "SWS packet"),
        ("REMTimePairFormat", "REM"),
        ("MATimePairFormat", "Microarousal"),
        ("WakeInterruptionTimePairFormat", "Wake interruption"),
    )
    for field, label in broad:
        bars = [(start, stop - start) for start, stop in _overlapping_intervals(
            session, field, start_s, stop_s
        )]
        if bars:
            ax.broken_barh(bars, (0.1, 0.8), facecolors=STATE_COLORS[label])
    for field, label in fine:
        bars = [(start, stop - start) for start, stop in _overlapping_intervals(
            session, field, start_s, stop_s
        )]
        if bars:
            ax.broken_barh(bars, (1.1, 0.8), facecolors=STATE_COLORS[label])
    ax.set_ylim(0, 2)
    ax.set_yticks((0.5, 1.5), labels=("Broad", "Substate"))
    ax.set_ylabel("State")
    ax.grid(axis="x", alpha=0.2)
    handles = [Patch(color=color, label=label) for label, color in STATE_COLORS.items()]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.55),
        ncol=3,
        frameon=False,
        fontsize=8,
    )


def _state_boundaries(
    session: AlignedSession, start_s: float, stop_s: float
) -> np.ndarray:
    fields = (
        "WakeTimePairFormat",
        "SleepTimePairFormat",
        "SWSPacketTimePairFormat",
        "REMTimePairFormat",
        "MATimePairFormat",
        "WakeInterruptionTimePairFormat",
    )
    values: set[float] = set()
    for field in fields:
        for start, stop in _overlapping_intervals(session, field, start_s, stop_s):
            if start_s < start < stop_s:
                values.add(start)
            if start_s < stop < stop_s:
                values.add(stop)
    return np.asarray(sorted(values), dtype=np.float64)


def plot_multimodal_window(
    session: AlignedSession,
    start_s: float,
    stop_s: float,
    output_path: str | Path,
    *,
    lfp_channel_one_based: int | None = None,
    spectrogram_channel_one_based: int | None = None,
) -> Path:
    """Plot a short raw-LFP/spectrogram/spike-raster window on one time axis."""

    if not session.report.core_alignment_valid:
        raise ValueError("Core alignment validation failed; refusing to plot.")
    meta = session.metadata
    lfp_channel = lfp_channel_one_based or meta.good_lfp_channel_one_based
    spectral_channel = spectrogram_channel_one_based or meta.theta_channel_one_based
    window = load_lfp_window(
        meta,
        start_s,
        stop_s,
        [lfp_channel, spectral_channel],
        support_end_s=session.report.common_end_s,
    )
    lfp_uv = window.microvolts[:, 0]
    spectral_uv = window.microvolts[:, 1]

    nperseg = int(round(2.0 * meta.lfp_sample_rate_hz))
    noverlap = int(round(1.5 * meta.lfp_sample_rate_hz))
    frequencies, relative_times, power = spectrogram(
        spectral_uv,
        fs=meta.lfp_sample_rate_hz,
        window="hann",
        nperseg=nperseg,
        noverlap=noverlap,
        detrend="constant",
        scaling="density",
        mode="psd",
    )
    frequency_mask = (frequencies >= 0.5) & (frequencies <= 30.0)
    power_db = 10.0 * np.log10(np.maximum(power[frequency_mask], np.finfo(float).tiny))

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(15, 10),
        sharex=True,
        gridspec_kw={"height_ratios": (0.8, 1.5, 2.0, 2.2)},
        constrained_layout=True,
    )
    _plot_state_timeline(axes[0], session, start_s, stop_s)

    plot_stride = max(1, int(round(meta.lfp_sample_rate_hz / 250.0)))
    axes[1].plot(
        window.time_s[::plot_stride],
        lfp_uv[::plot_stride],
        color="#222222",
        linewidth=0.45,
    )
    axes[1].set_ylabel(f"LFP ch {lfp_channel}\n(microvolts)")
    axes[1].grid(alpha=0.15)

    mesh = axes[2].pcolormesh(
        start_s + relative_times,
        frequencies[frequency_mask],
        power_db,
        shading="auto",
        cmap="magma",
    )
    axes[2].set_ylabel(f"Ch {spectral_channel}\nfrequency (Hz)")
    colorbar = fig.colorbar(mesh, ax=axes[2], pad=0.01)
    colorbar.set_label("PSD (dB microvolts^2/Hz)")

    trains = session.spikes.spikes_in_window(start_s, stop_s)
    axes[3].eventplot(
        trains,
        lineoffsets=np.arange(1, session.spikes.n_units + 1),
        linelengths=0.8,
        linewidths=0.35,
        colors="#111111",
    )
    axes[3].set_ylim(0.5, session.spikes.n_units + 0.5)
    axes[3].set_ylabel("Stable unit")
    axes[3].set_xlabel("Session time (s)")
    axes[3].grid(axis="x", alpha=0.15)

    for boundary in _state_boundaries(session, start_s, stop_s):
        for ax in axes[1:]:
            ax.axvline(boundary, color="#666666", linestyle="--", linewidth=0.6)
    axes[0].set_xlim(start_s, stop_s)
    fig.suptitle(
        f"{meta.basename}: multimodal alignment ({start_s:g}-{stop_s:g} s)",
        fontsize=14,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def _stream_lfp_episode_summary(
    session: AlignedSession,
    start_s: float,
    stop_s: float,
    rms_channel_one_based: int,
    spectral_channel_one_based: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read one- and two-second chunks; never materialize the full episode."""

    meta = session.metadata
    fs = int(round(meta.lfp_sample_rate_hz))
    mmap = open_lfp_memmap(meta)
    rms_channel = meta.python_channel_index(rms_channel_one_based)
    spectral_channel = meta.python_channel_index(spectral_channel_one_based)

    one_second_edges = np.arange(start_s, stop_s + 1.0, 1.0)
    if one_second_edges[-1] > stop_s + 1e-9:
        one_second_edges = one_second_edges[:-1]
    rms_times: list[float] = []
    rms_uv: list[float] = []
    for left, right in zip(one_second_edges[:-1], one_second_edges[1:]):
        i0 = int(round(left * fs))
        i1 = int(round(right * fs))
        values = np.asarray(mmap[i0:i1, rms_channel], dtype=np.float64)
        values = values * meta.volts_per_count * 1e6
        values -= values.mean()
        rms_times.append((left + right) / 2.0)
        rms_uv.append(float(np.sqrt(np.mean(values * values))))

    segment_s = 2.0
    n_segment_samples = int(round(segment_s * fs))
    fft_window = np.hanning(n_segment_samples)
    fft_scale = fs * np.sum(fft_window * fft_window)
    frequencies = np.fft.rfftfreq(n_segment_samples, d=1.0 / fs)
    frequency_mask = (frequencies >= 0.5) & (frequencies <= 30.0)
    spectral_times: list[float] = []
    spectra: list[np.ndarray] = []
    left = start_s
    while left + segment_s <= stop_s + 1e-9:
        right = left + segment_s
        i0 = int(round(left * fs))
        i1 = i0 + n_segment_samples
        values = np.asarray(mmap[i0:i1, spectral_channel], dtype=np.float64)
        values = values * meta.volts_per_count * 1e6
        values -= values.mean()
        transform = np.fft.rfft(values * fft_window)
        psd = np.abs(transform) ** 2 / fft_scale
        if psd.size > 2:
            psd[1:-1] *= 2.0
        spectra.append(psd[frequency_mask])
        spectral_times.append((left + right) / 2.0)
        left = right

    power_db = 10.0 * np.log10(
        np.maximum(np.asarray(spectra, dtype=np.float64).T, np.finfo(float).tiny)
    )
    return (
        np.asarray(rms_times),
        np.asarray(rms_uv),
        np.asarray(spectral_times),
        frequencies[frequency_mask],
        power_db,
    )


def plot_wake_sleep_episode(
    session: AlignedSession,
    output_path: str | Path,
    *,
    episode_index: int = 0,
) -> Path:
    """Plot a complete official WAKE->SLEEP pair using chunked LFP summaries."""

    if not session.report.core_alignment_valid:
        raise ValueError("Core alignment validation failed; refusing to plot.")
    episodes = session.sleep_states.wake_sleep_episodes_s
    if not 0 <= episode_index < episodes.shape[0]:
        raise IndexError(
            f"episode_index={episode_index} is outside 0..{episodes.shape[0] - 1}."
        )
    wake, sleep = episodes[episode_index]
    start_s = float(wake[0])
    stop_s = float(sleep[1])
    meta = session.metadata
    rms_times, rms_uv, spectral_times, frequencies, power_db = (
        _stream_lfp_episode_summary(
            session,
            start_s,
            stop_s,
            meta.good_lfp_channel_one_based,
            meta.theta_channel_one_based,
        )
    )

    spike_edges = np.arange(start_s, stop_s + 1.0, 1.0)
    all_spikes = np.concatenate(session.spikes.spikes_in_window(start_s, stop_s))
    population_counts, _ = np.histogram(all_spikes, bins=spike_edges)
    population_rate = population_counts / session.spikes.n_units
    population_times = (spike_edges[:-1] + spike_edges[1:]) / 2.0

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(16, 10),
        sharex=True,
        gridspec_kw={"height_ratios": (0.9, 1.3, 2.4, 1.5)},
        constrained_layout=True,
    )
    _plot_state_timeline(axes[0], session, start_s, stop_s)
    axes[1].plot(rms_times, rms_uv, color="#222222", linewidth=0.6)
    axes[1].set_ylabel(
        f"ACC ch {meta.good_lfp_channel_one_based}\n1-s RMS (microvolts)"
    )
    axes[1].grid(alpha=0.15)

    mesh = axes[2].pcolormesh(
        spectral_times,
        frequencies,
        power_db,
        shading="auto",
        cmap="magma",
    )
    axes[2].set_ylabel(
        f"dHipp ch {meta.theta_channel_one_based}\nfrequency (Hz)"
    )
    colorbar = fig.colorbar(mesh, ax=axes[2], pad=0.01)
    colorbar.set_label("2-s PSD (dB microvolts^2/Hz)")

    axes[3].plot(population_times, population_rate, color="#009E73", linewidth=0.7)
    axes[3].set_ylabel("Mean population\nrate (spikes/s/unit)")
    axes[3].set_xlabel("Session time (s)")
    axes[3].grid(alpha=0.15)
    for ax in axes[1:]:
        ax.axvline(float(wake[1]), color="#D55E00", linestyle="--", linewidth=1.0)
    axes[0].set_xlim(start_s, stop_s)
    fig.suptitle(
        f"{meta.basename}: complete official WAKE->SLEEP episode "
        f"({start_s:g}-{stop_s:g} s)",
        fontsize=14,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path
