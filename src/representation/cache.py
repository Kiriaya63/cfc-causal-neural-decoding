"""Rebuildable chunked LFP caches with protocol and source fingerprints."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.signal import oaconvolve

from data.align_session import AlignedSession
from data.load_lfp import open_lfp_memmap

from .config import DEFAULT_CONFIG, RepresentationConfig
from .filters import (
    PhysioFilterDesign,
    WaveformFilterDesign,
    causal_role_physio_from_waveforms,
    design_physio_filters,
    design_waveform_filter,
)
from .provenance import (
    anatomy_provenance_conflicts,
    default_anatomy_conflict_registry,
    role_channel_mapping,
    unique_feature_source_channels,
)


HASH_CHUNK_BYTES = 8 * 1024 * 1024


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=256)
def _sha256_for_unchanged_stat(
    path_text: str, size: int, mtime_ns: int
) -> str:
    """Hash content once per process for one observed immutable file state."""

    del size, mtime_ns
    return _sha256_file(path_text)


def file_content_fingerprint(path: str | Path) -> dict[str, object]:
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": _sha256_for_unchanged_stat(
            str(resolved), stat.st_size, stat.st_mtime_ns
        ),
    }


def representation_implementation_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _source_signature(session: AlignedSession) -> dict:
    metadata = session.metadata
    paths = [
        metadata.eeg_path,
        metadata.session_dir / f"{metadata.basename}.xml",
        metadata.session_dir / f"{metadata.basename}_BasicMetaData.mat",
        metadata.session_dir / f"{metadata.basename}_ChannelAnatomy.csv",
    ]
    conflict_registry = default_anatomy_conflict_registry()
    if conflict_registry.is_file():
        paths.append(conflict_registry)
    return {str(Path(path).resolve()): file_content_fingerprint(path) for path in paths}


def representation_cache_identity(config: RepresentationConfig) -> str:
    payload = f"{config.protocol_hash}:{representation_implementation_hash()}"
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def session_cache_dir(
    cache_root: str | Path, session: AlignedSession, config: RepresentationConfig
) -> Path:
    return Path(cache_root) / representation_cache_identity(config)[:16] / session.metadata.basename


def describe_cache_artifact(path: str | Path) -> dict[str, object]:
    resolved = Path(path)
    array = np.load(resolved, mmap_mode="r")
    descriptor = {
        "file_size_bytes": resolved.stat().st_size,
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "sha256": _sha256_file(resolved),
    }
    del array
    return descriptor


def cache_artifacts_match(directory: str | Path, metadata: dict) -> bool:
    root = Path(directory)
    expected = metadata.get("cache_artifacts")
    if not isinstance(expected, dict):
        return False
    try:
        for filename in ("lfp_waveform_50hz.npy", "lfp_physio_50hz.npy"):
            if expected.get(filename) != describe_cache_artifact(root / filename):
                return False
    except (OSError, ValueError, EOFError):
        return False
    return True


def _metadata_matches(
    path: Path,
    session: AlignedSession,
    config: RepresentationConfig,
    source_signature: dict,
) -> tuple[bool, dict | None]:
    if not path.is_file():
        return False, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, None
    matches = (
        payload.get("protocol_hash") == config.protocol_hash
        and payload.get("implementation_hash") == representation_implementation_hash()
        and payload.get("source_signature") == source_signature
    )
    return matches, payload


def ensure_lfp_cache(
    session: AlignedSession,
    cache_root: str | Path,
    config: RepresentationConfig = DEFAULT_CONFIG,
) -> tuple[Path, dict]:
    """Build or validate one session cache without loading the full EEG into RAM."""
    if session.metadata.lfp_sample_rate_hz != config.input_lfp_rate_hz:
        raise ValueError(
            f"Expected {config.input_lfp_rate_hz} Hz LFP, got "
            f"{session.metadata.lfp_sample_rate_hz:g} Hz."
        )
    directory = session_cache_dir(cache_root, session, config)
    metadata_path = directory / "cache_metadata.json"
    waveform_path = directory / "lfp_waveform_50hz.npy"
    physio_path = directory / "lfp_physio_50hz.npy"
    source_signature = _source_signature(session)
    metadata_matches, cached_metadata = _metadata_matches(
        metadata_path, session, config, source_signature
    )
    if metadata_matches and cached_metadata is not None and cache_artifacts_match(
        directory, cached_metadata
    ):
        return directory, cached_metadata

    directory.mkdir(parents=True, exist_ok=True)
    waveform_design = design_waveform_filter(config)
    physio_design = design_physio_filters(waveform_design, config)
    raw = open_lfp_memmap(
        session.metadata, expected_duration_s=session.report.common_end_s
    )
    role_mapping = role_channel_mapping(session.metadata)
    feature_channels = unique_feature_source_channels(role_mapping)
    indices = tuple(
        session.metadata.python_channel_index(channel) for channel in feature_channels
    )
    channel_to_column = {channel: index for index, channel in enumerate(feature_channels)}
    good_eeg_channel = int(role_mapping["good_eeg"]["physical_channel_one_based"])
    factor = config.decimation_factor
    n_observations = raw.shape[0] // factor
    waveform = np.lib.format.open_memmap(
        waveform_path, mode="w+", dtype=np.float32, shape=(n_observations, 1)
    )
    role_waveform_path = directory / ".role_waveforms_building.npy"
    role_waveforms = np.lib.format.open_memmap(
        role_waveform_path,
        mode="w+",
        dtype=np.float32,
        shape=(n_observations, len(feature_channels)),
    )
    write_position = 0
    chunk_size = config.cache_chunk_raw_frames
    if chunk_size % factor:
        raise ValueError("cache_chunk_raw_frames must be divisible by decimation factor.")
    usable_raw_stop = n_observations * factor
    for start in range(0, usable_raw_stop, chunk_size):
        stop = min(start + chunk_size, usable_raw_stop)
        history = min(waveform_design.numtaps - 1, start)
        extended_start = start - history
        values = np.asarray(raw[extended_start:stop, indices], dtype=np.float64)
        filtered = oaconvolve(
            values, waveform_design.taps[:, None], mode="full", axes=0
        )
        first = (factor - 1 - start) % factor
        global_indices = np.arange(start + first, stop, factor, dtype=np.int64)
        selected = filtered[global_indices - extended_start]
        role_waveforms[write_position : write_position + len(selected)] = selected
        waveform[write_position : write_position + len(selected), 0] = selected[
            :, channel_to_column[good_eeg_channel]
        ]
        write_position += len(selected)
    if write_position != n_observations:
        raise AssertionError("Chunked decimation produced an unexpected observation count.")
    waveform.flush()
    del raw

    role_waveforms.flush()
    channel_waveforms = {
        channel: np.asarray(role_waveforms[:, column], dtype=np.float64)
        for channel, column in channel_to_column.items()
    }
    waveforms_by_role = {
        role: channel_waveforms[int(item["physical_channel_one_based"])]
        for role, item in role_mapping.items()
        if role in {"good_eeg", "theta", "spindle"}
    }
    physio_values = causal_role_physio_from_waveforms(
        waveforms_by_role, physio_design, config
    )
    physio = np.lib.format.open_memmap(
        physio_path,
        mode="w+",
        dtype=np.float32,
        shape=physio_values.shape,
    )
    physio[:] = physio_values
    physio.flush()
    finite_waveform = bool(np.all(np.isfinite(waveform)))
    finite_physio = bool(np.all(np.isfinite(physio)))
    del channel_waveforms, waveforms_by_role, role_waveforms
    role_waveform_path.unlink(missing_ok=True)
    del physio_values, physio, waveform
    if not finite_waveform or not finite_physio:
        raise ValueError("Cached LFP representation contains non-finite values.")

    metadata = {
        "protocol_version": config.protocol_version,
        "protocol_hash": config.protocol_hash,
        "implementation_hash": representation_implementation_hash(),
        "source_signature": source_signature,
        "session_id": session.metadata.basename,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "input_lfp_rate_hz": config.input_lfp_rate_hz,
        "observation_rate_hz": config.observation_rate_hz,
        "observation_interval_s": config.observation_interval_s,
        "raw_complete_frame_count": session.lfp_info.n_timepoints,
        "observation_count": n_observations,
        "unrepresented_raw_tail_frames": session.lfp_info.n_timepoints
        - n_observations * factor,
        "unrepresented_tail_s": (
            session.lfp_info.n_timepoints - n_observations * factor
        )
        / config.input_lfp_rate_hz,
        "channel_roles": ["good_eeg"],
        "channels_one_based": [good_eeg_channel],
        "channel_anatomy": [session.metadata.anatomy_for_channel(good_eeg_channel)],
        "role_channel_mapping": role_mapping,
        "physical_feature_channels_loaded_one_based": list(feature_channels),
        "physical_feature_channel_reads_deduplicated": True,
        "role_sharing_present": len(
            {int(item["physical_channel_one_based"]) for item in role_mapping.values()}
        ) < len(role_mapping),
        "physio_feature_source_roles": dict(config.physio_feature_source_roles),
        "anatomy_provenance_conflicts": list(
            anatomy_provenance_conflicts(session.metadata.basename)
        ),
        "anatomy_provenance_conflict": bool(
            anatomy_provenance_conflicts(session.metadata.basename)
        ),
        "lfp_value_unit": config.lfp_value_unit,
        "waveform_shape": [n_observations, 1],
        "physio_shape": [n_observations, len(physio_design.names)],
        "physio_feature_order": list(physio_design.names),
        "waveform_first_valid_step": waveform_design.first_valid_observation_step,
        "waveform_first_valid_right_edge_s": (
            waveform_design.first_valid_observation_step + 1
        )
        / config.observation_rate_hz,
        "physio_first_valid_step": physio_design.first_valid_observation_step,
        "physio_first_valid_right_edge_s": (
            physio_design.first_valid_observation_step + 1
        )
        / config.observation_rate_hz,
        "waveform_fir": {
            "numtaps": waveform_design.numtaps,
            "beta": waveform_design.beta,
            "group_delay_input_samples": waveform_design.group_delay_input_samples,
            "group_delay_s": waveform_design.group_delay_s,
            "full_history_warmup_input_samples": waveform_design.full_history_warmup_input_samples,
            "full_history_warmup_s": waveform_design.full_history_warmup_s,
            "stopband_attenuation_db": waveform_design.stopband_attenuation_db,
            "passband_min_db": waveform_design.passband_min_db,
            "passband_max_db": waveform_design.passband_max_db,
            "coefficient_sha256": waveform_design.coefficient_sha256,
        },
        "physio_filters": {
            "family": config.physio_filter_family,
            "order": config.physio_filter_order,
            "settling_relative_threshold": config.iir_settling_relative_threshold,
            "settling_steps_by_band": dict(
                zip(physio_design.names, physio_design.settling_steps)
            ),
            "power_window_steps": physio_design.power_window_steps,
            "power_window_s": config.physio_power_window_s,
            "log1p": config.physio_log1p,
        },
        "finite_waveform": finite_waveform,
        "finite_physio": finite_physio,
        "normalization_statistics_fit": False,
    }
    metadata["cache_artifacts"] = {
        waveform_path.name: describe_cache_artifact(waveform_path),
        physio_path.name: describe_cache_artifact(physio_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return directory, metadata


def open_cached_lfp(cache_directory: str | Path) -> tuple[np.ndarray, np.ndarray, dict]:
    directory = Path(cache_directory)
    metadata = json.loads((directory / "cache_metadata.json").read_text(encoding="utf-8"))
    if not cache_artifacts_match(directory, metadata):
        raise ValueError(f"Cached representation failed integrity validation: {directory}")
    waveform = np.load(directory / "lfp_waveform_50hz.npy", mmap_mode="r")
    physio = np.load(directory / "lfp_physio_50hz.npy", mmap_mode="r")
    return waveform, physio, metadata
