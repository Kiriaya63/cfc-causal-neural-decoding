"""Strictly causal model-ready representations built on the frozen data layer."""

from .config import DEFAULT_CONFIG, RepresentationConfig
from .filters import (
    PhysioFilterDesign,
    WaveformFilterDesign,
    causal_physio_from_waveform,
    causal_role_physio_from_waveforms,
    causal_waveform_from_array,
    design_physio_filters,
    design_waveform_filter,
)
from .spikes import (
    SpikeRepresentation,
    pad_variable_neuron_batch,
    population_rate_from_padded,
    represent_spikes,
)
from .cache import (
    CACHE_ARRAY_IMPLEMENTATION_FILES,
    cache_artifacts_match,
    describe_cache_artifact,
    ensure_lfp_cache,
    open_cached_lfp,
    representation_cache_identity,
    representation_implementation_hash,
)
from .samples import MODALITY_ORDER, MultimodalRepresentationSample, RepresentationSessionDataset
from .model_input import (
    MODEL_INPUT_DELTA_T_DECIMALS,
    MODEL_INPUT_FIELD_WHITELIST,
    MODEL_INPUT_SCHEMA_VERSION,
    MODEL_INPUT_TIME_SEMANTICS,
    ModelInput,
    model_input_schema_hash,
    to_model_input,
)
from .provenance import anatomy_provenance_conflicts, role_channel_mapping

__all__ = [
    "DEFAULT_CONFIG", "RepresentationConfig", "PhysioFilterDesign",
    "WaveformFilterDesign", "causal_physio_from_waveform",
    "causal_role_physio_from_waveforms",
    "causal_waveform_from_array", "design_physio_filters",
    "design_waveform_filter", "SpikeRepresentation",
    "pad_variable_neuron_batch", "population_rate_from_padded",
    "represent_spikes",
    "CACHE_ARRAY_IMPLEMENTATION_FILES", "cache_artifacts_match",
    "describe_cache_artifact", "ensure_lfp_cache",
    "open_cached_lfp", "representation_cache_identity",
    "representation_implementation_hash",
    "MODALITY_ORDER", "MultimodalRepresentationSample", "RepresentationSessionDataset",
    "MODEL_INPUT_DELTA_T_DECIMALS", "MODEL_INPUT_FIELD_WHITELIST",
    "MODEL_INPUT_SCHEMA_VERSION", "MODEL_INPUT_TIME_SEMANTICS", "ModelInput",
    "model_input_schema_hash", "to_model_input",
    "anatomy_provenance_conflicts", "role_channel_mapping",
]
