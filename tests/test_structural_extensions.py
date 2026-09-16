"""Approved dataset-wide structural rules; synthetic fixtures, no ID branches."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import tempfile
import unittest
import numpy as np
from scipy.io import savemat, loadmat
from test_open_ended_time_support import _synthetic_metadata
from data.interval_support import normalise_official_time_pairs, resolve_constraint_to_lfp
from data.time_support import derive_session_time_support
from data.load_lfp import inspect_lfp_file, open_lfp_memmap
from data.load_spikes import load_stable_spikes
from data.bin_spikes import bin_stable_spikes


class StructuralExtensionsTest(unittest.TestCase):
    def test_empty_row_preserves_raw_and_contributes_empty_set(self):
        raw = np.array([[0., 5.], [5., 5.], [5., 10.]])
        with tempfile.TemporaryDirectory() as tmp:
            m = _synthetic_metadata(Path(tmp), raw, raw)
            support, _ = derive_session_time_support(m)
            np.testing.assert_array_equal(support.raw_metadata_recording_intervals_s, raw)
            np.testing.assert_array_equal(support.raw_good_sleep_intervals_s, raw)
            np.testing.assert_array_equal(support.candidate_analysis_intervals_s, [[0., 10.]])
            self.assertEqual(sum(f.code == 'zero_duration_provenance' for f in support.findings), 2)

    def test_reversed_nonfinite_malformed_and_illegal_order_remain_fatal(self):
        for raw in ([[2.,1.]], [[0.,np.nan]], [[0.,-np.inf]], [[np.inf,np.inf]],
                    [[0.,4.],[3.,5.]], [[2.,2.],[0.,3.]], [[0.,1.,2.]]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalise_official_time_pairs(raw, field_name='fixture')

    def test_empty_rows_cannot_create_support_or_hide_overlap(self):
        empty = normalise_official_time_pairs([[2.,2.]], field_name='fixture')
        with self.assertRaises(ValueError):
            resolve_constraint_to_lfp(empty, 10., field_name='fixture')
        with self.assertRaises(ValueError):
            normalise_official_time_pairs([[0.,8.],[4.,4.],[6.,10.]], field_name='fixture')

    def test_exact_frames_keep_old_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = _synthetic_metadata(Path(tmp), np.array([[0.,10.]]), np.array([[0.,10.]]))
            info = inspect_lfp_file(m)
            self.assertFalse(info.incomplete_tail_verified)
            self.assertEqual((info.n_timepoints, info.remainder_bytes, info.duration_s), (100,0,10.))
            self.assertEqual(open_lfp_memmap(m).shape, (100,2))

    def test_subframe_tail_is_guarded_readonly_prefix_and_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = _synthetic_metadata(Path(tmp), np.array([[0.,10.05]]), np.array([[0.,10.05]]), corrupt_byte_count=2)
            before = m.eeg_path.read_bytes()
            support, info = derive_session_time_support(m)
            self.assertTrue(info.incomplete_tail_verified)
            self.assertEqual(info.remainder_bytes,2)
            self.assertEqual(info.n_timepoints,100)
            self.assertEqual(info.official_end_s,10.05)
            self.assertAlmostEqual(info.endpoint_difference_s, .05)
            self.assertEqual(support.analysis_end_s,10.)
            self.assertEqual(support.support_resolution_method,'complete_frame_prefix_with_incomplete_tail')
            self.assertTrue(any(f.code == support.support_resolution_method for f in support.findings))
            mapped = open_lfp_memmap(m, expected_duration_s=10.)
            self.assertEqual(mapped.shape,(100,2))
            self.assertFalse(mapped.flags.writeable)
            del mapped
            self.assertEqual(before,m.eeg_path.read_bytes())

    def test_subframe_inconsistent_end_remains_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = _synthetic_metadata(Path(tmp), np.array([[0.,12.]]), np.array([[0.,12.]]), corrupt_byte_count=1)
            with self.assertRaises(ValueError): derive_session_time_support(m)

    def test_subframe_open_end_requires_independent_finite_official_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = _synthetic_metadata(Path(tmp), np.array([[0.,np.inf]]), np.array([[0.,np.inf]]), corrupt_byte_count=1)
            m.last_spike_s = m.last_annotation_s = 10.
            with self.assertRaises(ValueError): derive_session_time_support(m)
            savemat(Path(tmp)/'synthetic_GoodSleepInterval.mat', {'GoodSleepInterval':{'timePairFormat':[[0.,10.05]]}})
            s, i = derive_session_time_support(m)
            self.assertEqual(i.official_endpoint_source,'GoodSleepInterval.timePairFormat')
            self.assertTrue(np.isposinf(s.raw_metadata_recording_intervals_s[0,1]))

    def test_subframe_invalid_geometry_remains_fatal(self):
        for field, value in [('n_channels',0),('lfp_sample_rate_hz',0),('lfp_sample_rate_hz',np.nan),('n_bits',32)]:
            with self.subTest(field=field,value=value), tempfile.TemporaryDirectory() as tmp:
                m = _synthetic_metadata(Path(tmp),np.array([[0.,10.05]]),np.array([[0.,10.05]]),corrupt_byte_count=2)
                setattr(m,field,value)
                with self.assertRaises((ValueError,AssertionError)): derive_session_time_support(m)

    def _spikes(self, tmp, values):
        path=Path(tmp)/'fixture_SStable.mat'
        cells=np.empty((1,1),dtype=object); cells[0,0]=np.asarray(values)
        savemat(path,{'S_CellFormat':cells,'shank':[[1]],'cellIx':[[1]],'numgoodcells':[[1]]})
        return SimpleNamespace(stable_spikes_path=path,duration_s=3.,acquisition_sample_rate_hz=1250.)

    def test_off_declared_grid_raw_seconds_are_binned_half_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            values=np.array([.00005, .99995, 1., 1.00005, 1.99995, 2.])
            m=self._spikes(tmp,values)
            before=m.stable_spikes_path.read_bytes()
            spikes=load_stable_spikes(m)
            counts=bin_stable_spikes(spikes,np.array([0.,1.]),np.array([1.,2.]))
            np.testing.assert_array_equal(counts.counts[:,0],[2,3])
            self.assertEqual(counts.excluded_spike_count,1)
            self.assertTrue(spikes.clock_diagnostics['declared_grid_mismatch'])
            self.assertEqual(spikes.clock_diagnostics['observed_event_clock_hz'],20000.)
            self.assertEqual(m.acquisition_sample_rate_hz,1250.)
            self.assertEqual(spikes.timestamps_s[0].tobytes(),values.tobytes())
            self.assertEqual(before,m.stable_spikes_path.read_bytes())

    def test_arbitrary_sorted_seconds_do_not_require_any_candidate_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            values=np.array([np.sqrt(2)/10, np.pi/10, .999999999999, 1.000000000001])
            m=self._spikes(tmp,values); s=load_stable_spikes(m)
            self.assertIsNone(s.clock_diagnostics['observed_event_clock_hz'])
            self.assertEqual(s.timestamps_s[0].tobytes(),values.tobytes())
            np.testing.assert_array_equal(bin_stable_spikes(s,np.array([0.,1.]),np.array([1.,2.])).counts[:,0],[3,1])

    def test_invalid_spike_timestamps_remain_fatal(self):
        for values in ([np.nan],[np.inf],[-.1],[1.,.2],np.array([[.1,.2],[.3,.4]]),np.array([1+2j])):
            with self.subTest(values=values), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError): load_stable_spikes(self._spikes(tmp,values))

    def test_declared_grid_agreement_remains_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=load_stable_spikes(self._spikes(tmp,[.0008, .0016, 1.]))
            self.assertFalse(s.clock_diagnostics['declared_grid_mismatch'])
            self.assertEqual(s.clock_diagnostics['declared_off_grid_count'],0)


if __name__ == '__main__': unittest.main()
