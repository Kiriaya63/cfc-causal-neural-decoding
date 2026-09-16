"""Frozen-protocol full-release invariants; failures remain explicit observations."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from data import load_session_manifest, load_aligned_session, build_state_timeline, build_causal_sample_index
from run_milestone3b1 import preflight, _strict_causal_check

class FullReleaseInvariantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries=load_session_manifest(ROOT/'config/fcx1_milestone3b2_sessions.csv')
        cls.details=json.loads((ROOT/'reports/milestone3b2_2/session_details.json').read_text(encoding='utf-8'))

    def test_official_manifest_and_readable_cohort(self):
        self.assertEqual(len(self.entries),27)
        self.assertEqual(len({e.animal_id for e in self.entries}),11)
        with (ROOT/'reports/milestone3b/fcx1_animal_session_map.csv').open(encoding='utf-8-sig') as f:
            official={(r['session_id'],r['animal_id']) for r in csv.DictReader(f)}
        self.assertEqual({(e.session_id,e.animal_id) for e in self.entries},official)
        self.assertEqual(len({e.session_id for e in self.entries}),27)
        for e in self.entries: self.assertEqual(preflight(e.local_path,e.session_id),(True,[]))

    def test_frozen_processing_hashes_and_no_identity_branch(self):
        expected=json.loads((ROOT/'reports/milestone3b2_2/frozen_pipeline_sha256.json').read_text())
        identities={e.session_id for e in self.entries}|{e.animal_id for e in self.entries}
        for path in (ROOT/'src/data').glob('*.py'):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),expected[path.name])
            tree=ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,(ast.If,ast.IfExp)):
                    strings={n.value for n in ast.walk(node.test) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
                    self.assertFalse(strings & identities,path.name)

    def test_successful_sessions_have_valid_support_and_past_only_targets(self):
        for e in self.entries:
            q=self.details[e.session_id]['qc']
            if q['qc_status']=='FAIL': continue
            s=load_aligned_session(e.local_path); t=build_state_timeline(s)
            support=s.time_support
            self.assertTrue(s.report.core_alignment_valid)
            for a,b in support.candidate_analysis_intervals_s:
                self.assertTrue(0<=a<b<=s.lfp_info.duration_s+1e-9)
            np.testing.assert_array_equal(t.valid_label,t.target_label!='IGNORE')
            self.assertTrue(set(t.target_label).issubset({'WAKE','NREM','REM','IGNORE'}))
            self.assertTrue(np.all(~t.valid_label[t.invalid_reason=='conflicting_annotations']))
            for issue in s.sleep_states.issues: self.assertFalse(s.sleep_states.valid_masks[issue.field][issue.row_index])
            for w in (5,10,30):
                index=build_causal_sample_index(t,e.session_id,w)
                for r in index.rows:
                    self.assertEqual(r.context_start_s,r.decision_time_s-w)
                    self.assertEqual(r.context_stop_s,r.decision_time_s)
                    self.assertEqual(r.target_start_s,r.decision_time_s-1)
                    self.assertEqual(r.valid,r.target_label in {'WAKE','NREM','REM'})
                ok,n,error=_strict_causal_check(s,w)
                self.assertTrue(ok,error)
                self.assertEqual(n,q[f'causal_sample_count_{w}s'])

    def test_failures_remain_fail_with_reproducible_evidence(self):
        for e in self.entries:
            d=self.details[e.session_id]; q=d['qc']
            self.assertTrue(d['raw_evidence']['raw_unit_count_matches_cells'])
            if q['qc_status']!='FAIL': continue
            self.assertTrue(q['structural_issue'])
            self.assertIsNone(q['valid_supervision_fraction'])
            self.assertTrue(d['minimal_reproduction'])
            with self.assertRaises(Exception): load_aligned_session(e.local_path)

    def test_inventory_distinguishes_audited_from_qc_success(self):
        with (ROOT/'reports/milestone3b/full_release_inventory.csv').open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),len(self.entries))
        for r in rows:
            for field in ('downloaded','extracted','preflight_passed','audited'): self.assertEqual(r[field],'True')
            self.assertEqual(r['qc_status'],self.details[r['session_id']]['qc']['qc_status'])
            self.assertNotEqual(r['processing_status'],'missing_not_audited')

if __name__=='__main__': unittest.main()
