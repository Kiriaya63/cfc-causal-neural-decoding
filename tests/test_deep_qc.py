import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from data import load_session_manifest,load_aligned_session,build_state_timeline
from data.deep_qc import annotation_diagnostics,animal_summary,FIELDS

class DeepQCTest(unittest.TestCase):
    def test_pilot_conflicts_reconstruct_unchanged_ignore_bins(self):
        for entry in load_session_manifest(ROOT/'config/fcx1_milestone3_sessions.csv'):
            s=load_aligned_session(entry.local_path)
            t=build_state_timeline(s)
            before=t.target_label.copy()
            d=annotation_diagnostics(s,t)
            reconstructed=np.zeros(len(before),dtype=bool)
            for row in d['conflicts']:
                mask=(t.bin_start_s>=row['start_s']) & (t.bin_stop_s<=row['stop_s'])
                self.assertFalse(np.any(reconstructed & mask))
                reconstructed |= mask
                self.assertTrue(np.all(t.target_label[mask]=='IGNORE'))
                for label in row['type'].split('+'):
                    pairs=s.sleep_states.get(FIELDS[label],valid_only=True)
                    for a,b in zip(t.bin_start_s[mask],t.bin_stop_s[mask]):
                        self.assertTrue(np.any((pairs[:,0]<=a)&(pairs[:,1]>=b)))
            np.testing.assert_array_equal(reconstructed,t.invalid_reason=='conflicting_annotations')
            np.testing.assert_array_equal(before,t.target_label)
            self.assertEqual(sum(r['count'] for r in d['out_of_bounds_by_field']),len(s.sleep_states.issues))

    def test_animal_totals_do_not_sum_units_as_unique_neurons(self):
        base=dict(animal_id='A',core_alignment_valid=True,causal_sample_valid=True,qc_status='WARN',recording_duration_s=10.5,wake_seconds=3,nrem_seconds=4,rem_seconds=0,ignore_seconds=3)
        rows=animal_summary([SimpleNamespace(**base,stable_unit_count=n) for n in (20,30)])
        self.assertEqual(rows[0]['session_count'],2)
        self.assertEqual(rows[0]['effective_recording_duration_s'],21)
        self.assertEqual(rows[0]['stable_units_per_session'],[20,30])
        self.assertEqual(rows[0]['missing_core_classes'],['REM'])
        self.assertEqual(rows[0]['wake_seconds'],6)
