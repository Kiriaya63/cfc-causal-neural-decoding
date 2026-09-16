"""Causality and strict-label tests for Milestone 2."""
from __future__ import annotations
import tempfile, sys, unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from data import CausalSessionDataset, StableSpikes, bin_stable_spikes, build_state_timeline, load_aligned_session, load_lfp_window  # noqa:E402

SESSION=Path(r"F:\CfC-Sleep\crcns-downloader\fcx-1\data\BWRat17_121712")

@unittest.skipUnless(SESSION.is_dir(),f"Session not found: {SESSION}")
class CausalPipelineTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.session=load_aligned_session(SESSION); cls.timeline=build_state_timeline(cls.session)

 def test_strict_label_counts_and_boundary(self):
  c=self.timeline.coverage
  self.assertEqual((c.wake_seconds,c.nrem_seconds,c.rem_seconds,c.ignore_seconds),(2426,952,103,2578))
  self.assertEqual(c.unlabeled_seconds,2055); self.assertEqual(c.conflict_seconds,0); self.assertEqual(c.out_of_bounds_annotation_count,2)
  self.assertEqual(self.timeline.target_label[2430],'WAKE')
  self.assertEqual(self.timeline.target_label[2431],'IGNORE')
  self.assertEqual(self.timeline.invalid_reason[2431],'fine_state_gap')

 def test_window_boundary_is_strictly_past(self):
  ds=CausalSessionDataset(self.session,30); i=next(i for i,r in enumerate(ds.rows) if r.decision_time_s==2431)
  sample=ds.get_sample(i)
  self.assertEqual((sample.index.context_start_s,sample.index.context_stop_s),(2401,2431))
  self.assertLess(sample.lfp.time_s.max(),2431); self.assertLessEqual(sample.spike_bin_stop_s.max(),2431)
  self.assertEqual(sample.spike_counts.shape,(30,50)); self.assertEqual(sample.label,'WAKE')

 def test_context_lengths_share_one_implementation(self):
  for width in (5,10,30):
   ds=CausalSessionDataset(self.session,width); sample=ds.get_sample(0)
   self.assertEqual(sample.spike_counts.shape,(width,50)); self.assertEqual(sample.lfp.counts.shape[0],width*1250)

 def test_spike_bins_and_tail_are_explicit(self):
  b=bin_stable_spikes(self.session.spikes,self.timeline.bin_start_s,self.timeline.bin_stop_s)
  self.assertEqual(b.counts.shape,(6059,50)); self.assertEqual(int(b.counts.sum()),345196); self.assertEqual(b.excluded_spike_count,7)

 def test_out_of_bounds_annotations_never_create_samples(self):
  ds=CausalSessionDataset(self.session,30,include_invalid_targets=True)
  self.assertEqual(ds.timeline.coverage.out_of_bounds_annotation_count,2)
  self.assertTrue(all(r.decision_time_s<=6059 for r in ds.rows))
  self.assertFalse(any(r.target_start_s in (6801,8145) and r.valid for r in ds.rows))

 def test_future_lfp_perturbation_invariance(self):
  base=np.arange(32,dtype='<i2').reshape(16,2); changed=base.copy(); changed[8:]+=10000
  with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
   metas=[]
   for folder,values,name in ((a,base,'a'),(b,changed,'b')):
    path=Path(folder); (path/f'{name}.eeg').write_bytes(values.tobytes())
    metas.append(replace(self.session.metadata,session_dir=path,basename=name,n_channels=2,lfp_sample_rate_hz=4.0,recording_intervals_s=np.array([[0.,4.]]),good_lfp_channel_one_based=1,up_state_channel_one_based=1,spindle_channel_one_based=1,theta_channel_one_based=2,anatomy_labels=('X','Y'),anatomical_groups_zero_based=((0,1),),spike_groups=()))
   before_a=load_lfp_window(metas[0],1,2,[1,2]); before_b=load_lfp_window(metas[1],1,2,[1,2])
   np.testing.assert_array_equal(before_a.counts,before_b.counts)
  common=dict(source_path=Path('synthetic'),shank_one_based=np.array([1]),cell_index_within_shank=np.array([1]),bad_cell_ids_one_based={})
  spikes_a=StableSpikes(timestamps_s=(np.array([0.2,1.5,2.5]),),**common)
  spikes_b=StableSpikes(timestamps_s=(np.array([0.2,1.5,2.6,3.2]),),**common)
  starts=np.arange(4,dtype=float); stops=starts+1
  counts_a=bin_stable_spikes(spikes_a,starts,stops).window(0,2)
  counts_b=bin_stable_spikes(spikes_b,starts,stops).window(0,2)
  np.testing.assert_array_equal(counts_a,counts_b)

if __name__=='__main__': unittest.main()
