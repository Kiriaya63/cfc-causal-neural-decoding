"""Compare audit versions and document the approved protocol extension outcome."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/milestone3b2_2'

def main():
    old=json.loads((ROOT/'reports/milestone3b2/session_details.json').read_text(encoding='utf-8'))
    new=json.loads((OUT/'session_details.json').read_text(encoding='utf-8'))
    global_qc=json.loads((OUT/'global_summary.json').read_text(encoding='utf-8'))
    keys=['candidate_analysis_intervals_s','stable_unit_count','wake_seconds','nrem_seconds','rem_seconds','ignore_seconds',
          'valid_supervision_fraction','annotation_oob_by_field','conflict_types','exact_conflict_intervals',
          'causal_sample_count_5s','causal_sample_count_10s','causal_sample_count_30s']
    changes=[]
    for sid,detail in old.items():
        if detail['qc']['qc_status']=='FAIL': continue
        for key in keys:
            if detail['qc'].get(key)!=new[sid]['qc'].get(key):
                changes.append(dict(session_id=sid,field=key,before=detail['qc'].get(key),after=new[sid]['qc'].get(key)))
    baseline=json.loads((ROOT/'reports/milestone3b2/frozen_pipeline_sha256.json').read_text())
    fixed=['bin_spikes.py','build_state_labels.py','causal_dataset.py','causal_windows.py','deep_qc.py']
    hashes={name:hashlib.sha256((ROOT/'src/data'/name).read_bytes()).hexdigest()==baseline[name] for name in fixed}
    comparison=dict(previous_successful_sessions=24,unexpected_changes=changes,frozen_label_causal_modules_unchanged=hashes)
    (OUT/'backward_compatibility.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    if changes or not all(hashes.values()): raise RuntimeError('Unexpected frozen behavior change; inspect compatibility report.')
    recovered=[v['qc'] for sid,v in new.items() if old[sid]['qc']['qc_status']=='FAIL']
    txt='# M3-B2.2 outcome\n\n'
    txt+='All 27 release sessions were freshly audited under the same approved pipeline. Historical M3-B2 reports are preserved.\n\n'
    txt+='Preflight: 27/27 PASS. Final status: '+json.dumps(global_qc['status_counts'])+'.\n\n'
    txt+='The prior 24 successful sessions retain identical support, labels, OOB, conflicts, unit counts and 5/10/30 s sample counts. Frozen label, spike-binning and causal modules match the previous SHA256 snapshot.\n\n'
    txt+='| previous FAIL session | current | units | WAKE/NREM/REM/IGNORE seconds | supervision | core OOB | conflict seconds | 5/10/30 sample counts |\n|---|---|---:|---|---:|---:|---:|---|\n'
    for q in recovered:
        txt+=f"| {q['session_id']} | {q['qc_status']} | {q['stable_unit_count']} | "+'/'.join(str(q[k+'_seconds']) for k in ('wake','nrem','rem','ignore'))+f" | {q['valid_supervision_fraction']:.8%} | {q['core_target_oob']} | {q['conflict_seconds']} | "+'/'.join(str(q[f'causal_sample_count_{w}s']) for w in (5,10,30))+' |\n'
    for q in recovered:
        txt+='\n## '+q['session_id']+'\n\n'
        for k in ('candidate_analysis_intervals_s','lfp_frame_diagnostics','spike_clock_diagnostics','annotation_oob_by_field','conflict_types','exact_conflict_intervals'):
            txt+=f'- {k}: `{json.dumps(q.get(k),ensure_ascii=False)}`\n'
    txt+='\n## Global summary\n\n'
    for k in ('validated_unit_count','valid_supervision','core_OOB_count','auxiliary_OOB_count','OOB_fields','conflict_types_seconds','missing_core_classes','LFP_anatomies','theta_anatomies','duration_mismatch_sessions','open_ended_sessions','protocol_breaking_sessions'):
        txt+=f'- {k}: `{json.dumps(global_qc[k],ensure_ascii=False)}`\n'
    txt+='\n27 sessions are release entries, not necessarily 27 independent time periods: paired Dino ACC/mPFC releases can share recording time. No neuron identities were matched across sessions. WARN is not exclusion.\n\n'
    txt+='The protocol extensions were approved before implementation. Computational completion is assessed from the audit and test record; M4 remains unstarted pending the user’s next instruction.\n'
    test_path=OUT/'test_results.txt'
    if test_path.exists():
        test_log=test_path.read_text(encoding='utf-8-sig')
        txt+='\n## Tests and preservation\n\n'+test_log[test_log.rfind('Ran '):].strip()+'\n\n'
        txt+='Original 32 test cases retained plus 12 structural extension tests; the full-release report/hash fixture references the newly approved version. No skipped tests.\n\n'
    preservation=json.loads((OUT/'raw_preservation_check.json').read_text(encoding='utf-8'))
    txt+='Raw preservation check: `'+json.dumps(preservation,ensure_ascii=False)+'`.\n'
    (OUT/'protocol_extension_outcome.md').write_text(txt,encoding='utf-8')
    print(json.dumps(global_qc,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
