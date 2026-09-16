"""Representation provenance that is explicitly excluded from model features."""

from __future__ import annotations

import csv
from pathlib import Path


ROLE_SOURCE_FIELDS = {
    "good_eeg": "goodeegchannel",
    "theta": "Thetachannel",
    "spindle": "Spindlechannel",
    "up_state": "UPstatechannel",
}


def role_channel_mapping(metadata) -> dict[str, dict[str, object]]:
    channels = {
        "good_eeg": metadata.good_lfp_channel_one_based,
        "theta": metadata.theta_channel_one_based,
        "spindle": metadata.spindle_channel_one_based,
        "up_state": metadata.up_state_channel_one_based,
    }
    return {
        role: {
            "source_field": ROLE_SOURCE_FIELDS[role],
            "source_indexing": "MATLAB_1_based",
            "physical_channel_one_based": int(channel),
            "numpy_column_zero_based": metadata.python_channel_index(int(channel)),
            "anatomy_provenance": metadata.anatomy_for_channel(int(channel)),
        }
        for role, channel in channels.items()
    }


def unique_feature_source_channels(mapping: dict[str, dict[str, object]]) -> tuple[int, ...]:
    """Physical channels needed by existing features, preserving first-role order."""

    result: list[int] = []
    for role in ("good_eeg", "theta", "spindle"):
        channel = int(mapping[role]["physical_channel_one_based"])
        if channel not in result:
            result.append(channel)
    return tuple(result)


def default_anatomy_conflict_registry() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "fcx1_anatomy_provenance_conflicts.csv"


def anatomy_provenance_conflicts(
    session_id: str, registry_path: str | Path | None = None
) -> tuple[dict[str, str], ...]:
    path = default_anatomy_conflict_registry() if registry_path is None else Path(registry_path)
    if not path.is_file():
        return ()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = tuple(row for row in csv.DictReader(stream) if row["session_id"] == session_id)
    return rows
