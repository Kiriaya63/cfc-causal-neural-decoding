"""Visual checks for strict labels and one past-only causal sample."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from data.build_state_labels import StateTimeline
from data.causal_dataset import CausalSample


LABEL_COLORS = {
    "WAKE": "#E69F00",
    "NREM": "#0072B2",
    "REM": "#CC79A7",
    "IGNORE": "#BDBDBD",
}
REASON_COLORS = {
    "valid": "#FFFFFF",
    "unlabeled": "#777777",
    "fine_state_gap": "#F0E442",
    "microarousal": "#009E73",
    "wake_interruption": "#D55E00",
    "conflicting_annotations": "#000000",
    "annotation_boundary_inside_bin": "#56B4E9",
}


def plot_causal_sample(sample: CausalSample, output_path: str | Path) -> Path:
    t = sample.index.decision_time_s
    future_display_s = 5.0
    fig, axes = plt.subplots(3, 1, figsize=(15, 8), sharex=True, constrained_layout=True)
    axes[0].axvspan(
        sample.index.context_start_s, t, color="#DDEEFF", label="input context [t-W,t)"
    )
    axes[0].axvspan(
        sample.index.target_start_s,
        sample.index.target_stop_s,
        color=LABEL_COLORS[sample.label],
        alpha=0.8,
        label=f"target [t-1,t): {sample.label}",
    )
    axes[0].axvspan(t, t + future_display_s, color="#EEEEEE", hatch="//", label="future: not accessed")
    axes[0].set_yticks([])
    axes[0].set_ylabel("Semantics")
    axes[0].legend(loc="upper left", ncol=3, fontsize=9)

    axes[1].plot(sample.lfp.time_s, sample.lfp.microvolts[:, 0], color="#222222", linewidth=0.45)
    axes[1].set_ylabel(f"LFP ch {sample.lfp.channels_one_based[0]}\n(microvolts)")
    axes[1].grid(alpha=0.15)

    population_counts = sample.spike_counts.sum(axis=1)
    axes[2].step(sample.spike_bin_stop_s, population_counts, where="pre", color="#009E73")
    axes[2].set_ylabel("Population spikes\nper 1-s bin")
    axes[2].set_xlabel("Session time (s)")
    axes[2].grid(alpha=0.15)
    for ax in axes:
        ax.axvline(t, color="#D55E00", linewidth=1.5, linestyle="--")
        ax.set_xlim(sample.index.context_start_s, t + future_display_s)
    fig.suptitle(
        f"{sample.index.session_id}: causal sample, W={t-sample.index.context_start_s:g} s, decision t={t:g} s"
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def plot_label_coverage(
    timeline: StateTimeline, session_id: str, output_path: str | Path
) -> Path:
    label_order = ("IGNORE", "WAKE", "NREM", "REM")
    label_codes = np.asarray([label_order.index(x) for x in timeline.target_label])
    reason_order = tuple(REASON_COLORS)
    reasons = np.where(timeline.valid_label, "valid", timeline.invalid_reason)
    reason_codes = np.asarray([reason_order.index(x) for x in reasons])
    label_cmap = matplotlib.colors.ListedColormap([LABEL_COLORS[x] for x in label_order])
    reason_cmap = matplotlib.colors.ListedColormap([REASON_COLORS[x] for x in reason_order])
    fig, axes = plt.subplots(2, 1, figsize=(16, 5), sharex=True, constrained_layout=True)
    extent = [timeline.bin_start_s[0], timeline.bin_stop_s[-1], 0, 1]
    axes[0].imshow(label_codes[np.newaxis], aspect="auto", interpolation="nearest", extent=extent, cmap=label_cmap, vmin=0, vmax=len(label_order)-1)
    axes[1].imshow(reason_codes[np.newaxis], aspect="auto", interpolation="nearest", extent=extent, cmap=reason_cmap, vmin=0, vmax=len(reason_order)-1)
    axes[0].set_yticks([]); axes[1].set_yticks([])
    axes[0].set_ylabel("Target"); axes[1].set_ylabel("Reason")
    axes[1].set_xlabel("Session time (s)")
    axes[0].legend(handles=[Patch(color=LABEL_COLORS[x], label=x) for x in label_order], loc="upper center", bbox_to_anchor=(0.5,1.45), ncol=4, frameon=False)
    axes[1].legend(handles=[Patch(color=REASON_COLORS[x], label=x) for x in reason_order], loc="upper center", bbox_to_anchor=(0.5,-0.45), ncol=4, frameon=False, fontsize=8)
    c = timeline.coverage
    fig.suptitle(f"{session_id}: strict 1-s label coverage | WAKE {c.wake_seconds}, NREM {c.nrem_seconds}, REM {c.rem_seconds}, IGNORE {c.ignore_seconds}; out-of-bounds rows={c.out_of_bounds_annotation_count}")
    output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180); plt.close(fig)
    return output_path
