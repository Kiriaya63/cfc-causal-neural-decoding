"""Causality, shape, variable-neuron, mask, and leakage tests for M4."""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data.load_spikes import StableSpikes
from representation import (
    DEFAULT_CONFIG,
    causal_physio_from_waveform,
    causal_waveform_from_array,
    design_physio_filters,
    design_waveform_filter,
    pad_variable_neuron_batch,
    population_rate_from_padded,
    represent_spikes,
)


def spikes(trains: list[np.ndarray]) -> StableSpikes:
    n_units = len(trains)
    frozen = []
    for train in trains:
        value = np.asarray(train, dtype=np.float64).copy()
        value.setflags(write=False)
        frozen.append(value)
    shank = np.ones(n_units, dtype=np.int64)
    cell = np.arange(1, n_units + 1, dtype=np.int64)
    shank.setflags(write=False); cell.setflags(write=False)
    return StableSpikes(Path("synthetic"), tuple(frozen), shank, cell, {})


class Milestone4RepresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.waveform = design_waveform_filter()
        cls.physio = design_physio_filters(cls.waveform)

    def test_filter_design_meets_frozen_specification(self):
        self.assertEqual(self.waveform.numtaps, 909)
        self.assertAlmostEqual(self.waveform.group_delay_s, .3632)
        self.assertAlmostEqual(self.waveform.full_history_warmup_s, .7264)
        self.assertGreaterEqual(self.waveform.stopband_attenuation_db, 60.)
        self.assertEqual(self.physio.names, ("delta","theta","sigma","broadband"))
        self.assertEqual(self.physio.power_window_steps, 100)
        self.assertEqual(self.physio.first_valid_observation_step, 542)

    def test_lfp_future_perturbation_cannot_change_current_waveform(self):
        rng = np.random.default_rng(123)
        raw = rng.normal(size=(5000, 2))
        changed = raw.copy(); changed[2500:] += rng.normal(0, 1e6, changed[2500:].shape)
        before = causal_waveform_from_array(raw, self.waveform)
        after = causal_waveform_from_array(changed, self.waveform)
        np.testing.assert_array_equal(before[:100], after[:100])

    def test_lfp_future_perturbation_cannot_change_current_physio(self):
        rng = np.random.default_rng(321)
        wave = rng.normal(size=(500,2))
        changed = wave.copy(); changed[250:] += 1e5
        before = causal_physio_from_waveform(wave, self.physio)
        after = causal_physio_from_waveform(changed, self.physio)
        np.testing.assert_array_equal(before[:250], after[:250])

    def test_filter_startup_is_explicit_and_conservative(self):
        self.assertGreater(self.waveform.first_valid_observation_step, 0)
        self.assertGreater(
            self.physio.first_valid_observation_step,
            self.waveform.first_valid_observation_step + self.physio.power_window_steps - 1,
        )

    def test_spike_half_open_boundary_and_future_perturbation(self):
        original = spikes([np.array([0., .019999, .02, .039999, .04])])
        starts = np.array([0.,.02]); stops=np.array([.02,.04])
        represented = represent_spikes(original, starts, stops)
        np.testing.assert_array_equal(represented.counts_by_unit[:,0], [2,2])
        changed = spikes([np.array([0., .019999, .02, .039999, .04, .041, 99.])])
        np.testing.assert_array_equal(
            represent_spikes(changed, starts, stops).counts_by_unit,
            represented.counts_by_unit,
        )

    def test_population_rate_definition(self):
        value = spikes([np.array([.001,.002]), np.array([.003])])
        represented = represent_spikes(value, np.array([0.]), np.array([.02]))
        self.assertEqual(represented.population_count[0,0], 3)
        self.assertEqual(represented.population_mean_firing_rate_hz[0,0], 75.)

    def test_variable_unit_range_needs_no_identity_branch(self):
        for n_units in (10, 36, 113):
            value = spikes([np.array([.001 + index * 1e-7]) for index in range(n_units)])
            represented = represent_spikes(value, np.array([0.]), np.array([.02]))
            self.assertEqual(represented.counts_by_unit.shape, (1,n_units))
            self.assertEqual(represented.neuron_mask.shape, (n_units,))

    def test_unit_permutation_is_equivariant_and_population_is_invariant(self):
        trains = [np.array([.001]),np.array([.002,.003]),np.array([])]
        original = represent_spikes(spikes(trains),np.array([0.]),np.array([.02]))
        permutation = np.array([2,0,1])
        permuted = represent_spikes(spikes([trains[i] for i in permutation]),np.array([0.]),np.array([.02]))
        np.testing.assert_array_equal(permuted.counts_by_unit,original.counts_by_unit[:,permutation])
        np.testing.assert_array_equal(permuted.population_count,original.population_count)
        np.testing.assert_array_equal(permuted.population_mean_firing_rate_hz,original.population_mean_firing_rate_hz)

    def test_padding_mask_excludes_padded_neurons(self):
        first=np.array([[1,0],[0,1]],dtype=np.int32)
        second=np.array([[0,1,2],[3,0,0]],dtype=np.int32)
        padded,mask=pad_variable_neuron_batch([first,second])
        baseline=population_rate_from_padded(padded,mask,.02)
        changed=padded.copy(); changed[0,:,2]=999999
        np.testing.assert_array_equal(population_rate_from_padded(changed,mask,.02),baseline)
        np.testing.assert_array_equal(padded[0,:,:2],first)

    def test_no_fitted_normalization_or_forbidden_filter_calls(self):
        source="\n".join(path.read_text(encoding="utf-8") for path in (ROOT/'src/representation').glob('*.py'))
        for forbidden in ('filtfilt(', 'resample(', 'resample_poly(', 'StandardScaler', '.fit('):
            self.assertNotIn(forbidden, source)
        self.assertEqual(DEFAULT_CONFIG.normalization_fit_stage,'M5_training_animals_only')

    def test_no_session_or_animal_specific_processing_branch(self):
        with (ROOT/'config/fcx1_milestone3b2_sessions.csv').open(encoding='utf-8-sig') as stream:
            rows=list(csv.DictReader(stream))
        identities={r['session_id'] for r in rows}|{r['animal_id'] for r in rows}
        for path in (ROOT/'src/representation').glob('*.py'):
            tree=ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,(ast.If,ast.IfExp,ast.Match)):
                    values={n.value for n in ast.walk(node) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
                    self.assertFalse(values & identities, f'{path}:{node.lineno}')

    @unittest.skipUnless((ROOT/'reports/milestone4/representation_shapes.json').is_file(), 'M4 full audit not built yet')
    def test_fullrelease_shapes_are_exact_for_every_session(self):
        shapes=json.loads((ROOT/'reports/milestone4/representation_shapes.json').read_text(encoding='utf-8'))
        self.assertEqual(len(shapes),27)
        for session, contexts in shapes.items():
            self.assertIsNotNone(contexts,session)
            for width in (5,10,30):
                item=contexts[str(width)]; steps=width*50
                self.assertEqual(item['steps'],steps)
                self.assertEqual(item['lfp_waveform'],[steps,1])
                self.assertEqual(item['lfp_physio'],[steps,4])
                self.assertEqual(item['spike_population_rate'],[steps,1])
                self.assertEqual(item['spike_set_counts'][0],steps)

    @unittest.skipUnless((ROOT/'reports/milestone4/global_summary.json').is_file(), 'M4 full audit not built yet')
    def test_fullrelease_audit_has_no_fail_or_leakage(self):
        summary=json.loads((ROOT/'reports/milestone4/global_summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['sessions'],27)
        self.assertEqual(summary['animals'],11)
        self.assertEqual(summary['status_counts']['FAIL'],0)
        self.assertFalse(summary['identity_specific_branches'])
        self.assertFalse(summary['normalization_statistics_fit'])
        self.assertFalse(summary['raw_preservation']['changed_files'])


if __name__ == '__main__': unittest.main()
