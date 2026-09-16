"""Full-release reporting around the approved common pipeline; no raw repairs."""
from pathlib import Path
import sys, csv, json, math, hashlib
from collections import Counter
from dataclasses import asdict
import numpy as np
from scipy.io import loadmat
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from data import (audit_session, load_session_metadata, derive_session_time_support,
                  load_stable_spikes, load_sleep_states, load_aligned_session,
                  build_state_timeline)
from data.session_manifest import SessionManifestEntry
from data.deep_qc import annotation_diagnostics, field_role
from run_milestone3b1 import preflight, _strict_causal_check, _support_pattern

RAW = Path(r'F:\CfC-Sleep\crcns-downloader\fcx-1\data')
OUT = ROOT / 'reports/milestone3b2'
if '--report-dir' in sys.argv:
    OUT = ROOT / sys.argv[sys.argv.index('--report-dir') + 1]
MAP = ROOT / 'reports/milestone3b/fcx1_animal_session_map.csv'

def safe(x):
    if isinstance(x, np.ndarray): return safe(x.tolist())
    if isinstance(x, np.generic): return safe(x.item())
    if isinstance(x, float) and not math.isfinite(x):
        return 'NaN' if math.isnan(x) else ('Infinity' if x > 0 else '-Infinity')
    if isinstance(x, dict): return {k:safe(v) for k,v in x.items()}
    if isinstance(x, (tuple,list)): return [safe(v) for v in x]
    if isinstance(x, Path): return str(x)
    return x

def js(x): return json.dumps(safe(x), ensure_ascii=False, allow_nan=False)
def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
        w.writerows({k:js(v) if isinstance(v,(dict,list,tuple)) else safe(v) for k,v in r.items()} for r in rows)
def mdtable(rows, keys):
    return '\n'.join(['| '+' | '.join(keys)+' |','|'+'---|'*len(keys)]+[
        '| '+' | '.join(str(safe(r.get(k))) .replace('|',';') for k in keys)+' |' for r in rows])
def summary(values):
    v=[float(x) for x in values if isinstance(x,(int,float)) and math.isfinite(x)]
    return dict(n=len(v),min=min(v) if v else None,median=float(np.median(v)) if v else None,max=max(v) if v else None)

def raw_evidence(entry):
    """Independent raw observations, never fed back into support resolution."""
    d=entry.local_path; s=entry.session_id
    b=loadmat(d/f'{s}_BasicMetaData.mat',simplify_cells=True)['bmd']
    g=loadmat(d/f'{s}_GoodSleepInterval.mat',simplify_cells=True)['GoodSleepInterval']['timePairFormat']
    xml=ET.parse(d/f'{s}.xml'); n=int(xml.findtext('acquisitionSystem/nChannels'))
    hz=float(xml.findtext('fieldPotentials/lfpSamplingRate'))
    acq=float(xml.findtext('acquisitionSystem/samplingRate'))
    size=(d/f'{s}.eeg').stat().st_size; frames,rem=divmod(size,n*2)
    with (d/f'{s}_ChannelAnatomy.csv').open(encoding='utf-8-sig') as f: anatomy={int(r[0]):r[1] for r in csv.reader(f)}
    ri=np.asarray(b['RecordingFileIntervals']).reshape(-1,2)
    gi=np.asarray(g).reshape(-1,2)
    sp=loadmat(d/f'{s}_SStable.mat',simplify_cells=False,variable_names=['S_CellFormat','numgoodcells'])
    trains=[np.asarray(t,dtype=float).reshape(-1) for t in sp['S_CellFormat'].ravel(order='F')]
    bad=[]
    for i,t in enumerate(trains):
        ix=np.flatnonzero(np.abs(t*acq-np.rint(t*acq))>1e-6)
        if ix.size:
            bad.append(dict(unit_one_based=i+1,off_grid_count=int(ix.size),examples_s=t[ix[:5]].tolist(),max_tick_error=float(np.max(np.abs(t*acq-np.rint(t*acq))))))
    return dict(raw_metadata_recording_intervals_s=ri,raw_good_sleep_intervals_s=gi,
        metadata_recording_end_s=float(ri[:,1].max()),good_sleep_support_end_s=float(gi[:,1].max()),
        eeg_file_size_bytes=size,eeg_frame_width_bytes=n*2,eeg_remainder_bytes=rem,
        diagnostic_complete_frame_duration_s=frames/hz,
        lfp_support_intervals_s=[[0,frames/hz]] if rem==0 else None,
        lfp_support_end_s=frames/hz if rem==0 else None,
        n_channels=n,lfp_sample_rate_hz=hz,acquisition_sample_rate_hz=acq,
        mat_acquisition_sample_rate_hz=b['Par']['SampleRate'],
        recommended_lfp_channel=int(b['goodeegchannel']),recommended_lfp_anatomy=anatomy.get(int(b['goodeegchannel'])),
        theta_channel=int(b['Thetachannel']),theta_channel_anatomy=anatomy.get(int(b['Thetachannel'])),
        anatomical_regions=sorted(set(anatomy.values())-{''}),channels_without_anatomy_label=sum(not v for v in anatomy.values()),
        raw_stable_unit_count=int(np.asarray(sp['numgoodcells']).squeeze()),raw_unit_count_matches_cells=int(np.asarray(sp['numgoodcells']).squeeze())==len(trains),raw_total_stable_spikes=sum(t.size for t in trains),
        raw_spike_grid_violations=bad,invalid_metadata_rows=[dict(row_index=i,interval_s=r) for i,r in enumerate(ri) if not np.isfinite(r[0]) or np.isnan(r[1]) or r[1]<r[0]],
        zero_duration_provenance_rows=[dict(row_index=i,interval_s=r) for i,r in enumerate(ri) if r[0]==r[1]],
        open_ended_provenance=bool(np.isposinf(ri[:,1]).any() or np.isposinf(gi[:,1]).any()))

def support_fields(support):
    keys=['raw_metadata_recording_intervals_s','raw_good_sleep_intervals_s','lfp_support_intervals_s',
          'resolved_metadata_constraint_s','resolved_good_sleep_constraint_s','candidate_analysis_intervals_s','support_resolution_method','duration_mismatch']
    return {k:getattr(support,k) for k in keys}

def audit_one(entry, source):
    q=audit_session(entry); row=q.to_dict(); evidence=raw_evidence(entry)
    row.update(preflight_status='PASS',official_caveats=source['notes'],caveat_source=source['mapping_source'],
        annotation_oob_by_field=None,annotation_oob_by_role=None,core_target_oob=None,auxiliary_oob=None,broad_state_oob=None,
        exact_conflict_intervals=None,conflict_types=None,malformed_annotation_rows=None,
        valid_supervision_fraction=None,missing_core_classes=None,structural_issue=None)
    for k,v in evidence.items():
        if k not in row or row[k] is None or row[k]==(): row[k]=v
    row['open_ended_provenance']=evidence['open_ended_provenance']
    row['support_pattern']=None
    for label in ('wake','nrem','rem','ignore'): row[label+'_fraction']=None
    for stage in ('metadata','lfp','spike','sleep_annotation'): row[stage+'_load_status']='NOT_RUN'
    for w in (5,10,30): row[f'causal_{w}s_valid']=False; row[f'causal_sample_count_{w}s']=None
    detail={'raw_evidence':evidence,'frozen_pipeline_qc':q.to_dict()}
    # Replay the same public stages to locate a failure, without bypassing guards.
    try:
        stage='metadata'; m=load_session_metadata(entry.local_path); row['metadata_load_status']='PASS'
        stage='lfp'; support,info=derive_session_time_support(m); row.update(support_fields(support)); row['lfp_load_status']='PASS'
        stage='spike'; load_stable_spikes(m,recording_end_s=support.analysis_end_s); row['spike_load_status']='PASS'
        stage='sleep_annotation'; load_sleep_states(m,recording_end_s=support.analysis_end_s); row['sleep_annotation_load_status']='PASS'
        stage='alignment'; s=load_aligned_session(entry.local_path); t=build_state_timeline(s)
        row['support_pattern']=_support_pattern(s)
        diag=annotation_diagnostics(s,t); detail['annotation_diagnostics']=diag
        fields={r['field']:r['count'] for r in diag['out_of_bounds_by_field']}
        roles=Counter()
        for f,n in fields.items(): roles[field_role(f)]+=n
        row.update(annotation_oob_by_field=fields,annotation_oob_by_role=dict(roles),annotation_oob_total=sum(fields.values()),
            core_target_oob=roles['core_target'],auxiliary_oob=roles['auxiliary_substate'],broad_state_oob=roles['broad_state_or_episode'],
            exact_conflict_intervals=diag['conflicts'],conflict_types=diag['conflict_duration_by_type_s'],
            malformed_annotation_rows=[asdict(i) for i in s.sleep_states.issues if 'outside recording' not in i.reason],
            valid_supervision_fraction=float(t.valid_label.mean()),missing_core_classes=[c for c in ('WAKE','NREM','REM') if not np.any(t.target_label==c)])
        for label in ('wake','nrem','rem','ignore'): row[label+'_fraction']=row[label+'_seconds']/len(t.bin_start_s)
        invariant=bool(np.all(t.valid_label==(t.target_label!='IGNORE')) and set(t.target_label).issubset({'WAKE','NREM','REM','IGNORE'}))
        invariant &= all(not s.sleep_states.valid_masks[i.field][i.row_index] for i in s.sleep_states.issues)
        invariant &= bool(np.all(~t.valid_label[t.invalid_reason=='conflicting_annotations']))
        row['target_invariants_valid']=invariant
        for w in (5,10,30):
            ok,n,error=_strict_causal_check(s,w); row[f'causal_{w}s_valid']=ok; row[f'causal_sample_count_{w}s']=n
            if error: detail.setdefault('causal_errors',{})[str(w)]=error
        if not invariant or not all(row[f'causal_{w}s_valid'] for w in (5,10,30)):
            row['qc_status']='FAIL'; row['structural_issue']='target_or_causal_invariant_failure'
    except Exception as error:
        row[stage+'_load_status']='FAIL'; row['structural_issue']=f'{stage}: {type(error).__name__}: {error}'
        row['qc_status']='FAIL'; detail['minimal_reproduction']=f'python -m data.align_session "{entry.local_path}"'
    if row['qc_status']=='PASS' and source['notes']: row['qc_status']='WARN'
    # Explicit provenance comparisons even if a later stage fails.
    if evidence['lfp_support_end_s'] is not None:
        row['duration_mismatch']=any(not math.isclose(float(evidence[k]),evidence['lfp_support_end_s'],rel_tol=0,abs_tol=1e-9) for k in ('metadata_recording_end_s','good_sleep_support_end_s'))
    row['secondary_structural_evidence'] = ['EEG frame remainder is nonzero'] if evidence['eeg_remainder_bytes'] else []
    row['raw_anatomy_source']='ChannelAnatomy.csv; selected channels from BasicMetaData'
    detail['qc']=row
    if row.get('lfp_frame_diagnostics'):
        row.update(row['lfp_frame_diagnostics'])
    if row.get('spike_clock_diagnostics'):
        row['declared_grid_mismatch']=row['spike_clock_diagnostics']['declared_grid_mismatch']
        row['observed_event_clock_hz']=row['spike_clock_diagnostics']['observed_event_clock_hz']
    return row,detail

def aggregate(rows):
    animals=[]; variability=[]
    for animal in sorted({r['animal_id'] for r in rows}):
        allrows=[r for r in rows if r['animal_id']==animal]; good=[r for r in allrows if r['qc_status']!='FAIL']
        a=dict(animal_id=animal,n_sessions=len(allrows),sessions=[r['session_id'] for r in allrows],n_pipeline_valid=len(good),
            total_recording_duration_s=sum(r['recording_duration_s'] for r in good),
            total_valid_supervision_seconds=sum(sum(r[k+'_seconds'] for k in ('wake','nrem','rem')) for r in good),
            stable_units=summary(r['stable_unit_count'] for r in good),raw_stable_units_all_sessions=summary(r['raw_stable_unit_count'] for r in allrows),
            valid_fraction_range=summary(r['valid_supervision_fraction'] for r in good),
            LFP_anatomies=sorted({r['recommended_lfp_anatomy'] for r in allrows}),theta_anatomies=sorted({r['theta_channel_anatomy'] for r in allrows}),
            duration_mismatch_session_count=sum(r['duration_mismatch'] is True for r in allrows),
            open_ended_session_count=sum(r['open_ended_provenance'] for r in allrows),
            core_OOB_total=sum(r['core_target_oob'] for r in good),auxiliary_OOB_total=sum(r['auxiliary_oob'] for r in good),
            total_conflict_seconds=sum(r['conflict_seconds'] for r in good),conflict_types=sorted({k for r in good for k in r['conflict_types']}),
            official_caveats={r['session_id']:r['official_caveats'] for r in allrows},status_counts=dict(Counter(r['qc_status'] for r in allrows)))
        for label in ('wake','nrem','rem','ignore'): a[label+'_total']=sum(r[label+'_seconds'] for r in good)
        for name in ('min','median','max'):
            a['stable_unit_'+name]=a['raw_stable_units_all_sessions'][name]
            a['validated_stable_unit_'+name]=a['stable_units'][name]
        for status in ('PASS','WARN','FAIL'): a[status+'_count']=a['status_counts'].get(status,0)
        animals.append(a)
        v=dict(animal_id=animal,session_count=len(allrows),assessed_session_count=len(good),
            duration_range=summary(r['recording_duration_s'] for r in good),unit_count_range=summary(r['raw_stable_unit_count'] for r in allrows),
            valid_supervision_range=a['valid_fraction_range'],LFP_anatomies=a['LFP_anatomies'],theta_anatomies=a['theta_anatomies'],
            support_patterns={r['session_id']:r['support_pattern'] or r['structural_issue'] for r in allrows},
            duration_mismatch_sessions=[r['session_id'] for r in allrows if r['duration_mismatch'] is True],
            OOB_range=summary(r['annotation_oob_total'] for r in good),conflict_range=summary(r['conflict_seconds'] for r in good),official_caveats=a['official_caveats'])
        for label in ('wake','nrem','rem','ignore'): v[label+'_fraction_range']=summary(r[label+'_fraction'] for r in good)
        variability.append(v)
    return animals,variability

def main():
    if '--render-only' in sys.argv:
        details=json.loads((OUT/'session_details.json').read_text(encoding='utf-8'))
        rows=[v['qc'] for v in details.values()]
        animals,variation=aggregate(rows)
        write_csv(OUT/'fcx1_11animal_fullrelease_summary.csv',animals)
        write_csv(OUT/'fcx1_within_animal_session_variability.csv',variation)
        write_reports(rows,animals,variation)
        return
    sources=read_csv(MAP)
    assert len(sources)==len({r['session_id'] for r in sources})==27
    assert len({r['animal_id'] for r in sources})==11
    entries=[SessionManifestEntry(r['session_id'],r['animal_id'],RAW/r['session_id'],True,'audit_requested') for r in sources]
    checks=[dict(session_id=e.session_id,animal_id=e.animal_id,preflight_status='PASS' if (p:=preflight(e.local_path,e.session_id))[0] else 'FAIL',issues=p[1]) for e in entries]
    OUT.mkdir(parents=True,exist_ok=True); write_csv(OUT/'preflight.csv',checks)
    if any(r['preflight_status']=='FAIL' for r in checks): raise SystemExit('Preflight failed; stopped.')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/data').glob('*.py')}
    rows=[]; details={}
    for e,source in zip(entries,sources):
        r,d=audit_one(e,source); rows.append(r); details[e.session_id]=d
        print(e.session_id,r['qc_status'],r['structural_issue'] or '',flush=True)
    animals,variation=aggregate(rows)
    write_csv(OUT/'fcx1_27session_qc.csv',rows)
    write_csv(OUT/'fcx1_11animal_fullrelease_summary.csv',animals)
    write_csv(OUT/'fcx1_within_animal_session_variability.csv',variation)
    (OUT/'session_details.json').write_text(json.dumps(safe(details),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (OUT/'frozen_pipeline_sha256.json').write_text(js(hashes),encoding='utf-8')
    assert hashes=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/data').glob('*.py')}
    (ROOT/'config/fcx1_milestone3b2_sessions.csv').parent.mkdir(exist_ok=True)
    write_csv(ROOT/'config/fcx1_milestone3b2_sessions.csv',[dict(session_id=e.session_id,animal_id=e.animal_id,local_path=str(e.local_path),availability=True,processing_status='audited') for e in entries])
    inventory=read_csv(ROOT/'reports/milestone3b/full_release_inventory.csv'); byid={r['session_id']:r for r in rows}
    for r in inventory:
        q=byid[r['session_id']]; r.update(availability=True,processing_status='audited',downloaded=True,extracted=True,preflight_passed=True,audited=True,qc_status=q['qc_status'])
    write_csv(ROOT/'reports/milestone3b/full_release_inventory.csv',inventory)
    write_reports(rows,animals,variation)

def write_reports(rows,animals,variation):
    good=[r for r in rows if r['qc_status']!='FAIL']; failed=[r for r in rows if r['qc_status']=='FAIL']
    scopes='All 27 sessions were attempted. Coverage/causal totals describe pipeline-valid sessions only; NA is unassessed, never zero. Raw unit counts and channel provenance are independently read for all 27. Durations summed across release sessions are not unique animal-time: same-date Dino ACC/mPFC releases may overlap. Neuron identities are not matched across sessions.'
    (OUT/'fcx1_27session_qc.md').write_text('# M3-B2 session QC\n\n'+scopes+'\n\n'+mdtable(rows,['animal_id','session_id','qc_status','stable_unit_count','raw_stable_unit_count','wake_seconds','nrem_seconds','rem_seconds','ignore_seconds','valid_supervision_fraction','structural_issue']),encoding='utf-8')
    for filename,data,title in [('fcx1_11animal_fullrelease_summary',animals,'Animal full-release summary'),('fcx1_within_animal_session_variability',variation,'Within-animal variability')]:
        txt='# '+title+'\n\n'+scopes+'\n'
        for r in data: txt+='\n## '+r['animal_id']+'\n\n'+mdtable([dict(field=k,value=js(v)) for k,v in r.items()],['field','value'])+'\n'
        (OUT/(filename+'.md')).write_text(txt,encoding='utf-8')
    conflicts=Counter(); oob=Counter()
    for r in good: conflicts.update(r['conflict_types']); oob.update(r['annotation_oob_by_field'])
    global_data=dict(total_sessions=len(rows),total_animals=len(animals),status_counts={k:sum(r['qc_status']==k for r in rows) for k in ('PASS','WARN','FAIL')},
        pipeline_valid_sessions=len(good),total_analysis_duration_s=sum(r['recording_duration_s'] for r in good),
        total_supervised_seconds=sum(sum(r[k+'_seconds'] for k in ('wake','nrem','rem')) for r in good),
        verified_physical_lfp_duration_s=sum(r['lfp_support_end_s'] for r in rows if r['lfp_support_end_s'] is not None),
        verified_physical_lfp_sessions=sum(r['lfp_support_end_s'] is not None for r in rows),
        raw_unit_count_all_27=summary(r['raw_stable_unit_count'] for r in rows),validated_unit_count=summary(r['stable_unit_count'] for r in good),
        valid_supervision=summary(r['valid_supervision_fraction'] for r in good),
        support_resolution_methods=dict(Counter(r['support_resolution_method'] for r in rows)),
        open_ended_sessions=[r['session_id'] for r in rows if r['open_ended_provenance']],
        duration_mismatch_sessions=[r['session_id'] for r in rows if r['duration_mismatch'] is True],
        core_OOB_count=sum(r['core_target_oob'] for r in good),auxiliary_OOB_count=sum(r['auxiliary_oob'] for r in good),
        OOB_fields=dict(oob),conflict_types_seconds=dict(conflicts),conflict_duration_distribution=summary(r['conflict_seconds'] for r in good),
        LFP_anatomies=dict(Counter(r['recommended_lfp_anatomy'] for r in rows)),theta_anatomies=dict(Counter(r['theta_channel_anatomy'] for r in rows)),
        region_session_availability=dict(Counter(k for r in rows for k in r['anatomical_regions'])),
        missing_core_classes={r['session_id']:r['missing_core_classes'] for r in good if r['missing_core_classes']},
        protocol_breaking_sessions={r['session_id']:r['structural_issue'] for r in failed})
    prior=json.loads((ROOT/'reports/milestone3b1/session_details.json').read_text(encoding='utf-8'))
    prior_types={k for v in prior.values() for k in v['annotation_diagnostics']['conflict_duration_by_type_s']}
    global_data['new_conflict_types_since_m3b1_1']=sorted(set(conflicts)-prior_types)
    global_data['missing_theta_anatomy_sessions']=[r['session_id'] for r in rows if not r['theta_channel_anatomy']]
    global_data['incomplete_tail_sessions']=[r['session_id'] for r in rows if r['eeg_remainder_bytes']]
    global_data['invalid_frame_geometry_sessions']=[r['session_id'] for r in rows if r['eeg_remainder_bytes'] and not r.get('incomplete_tail_verified')]
    global_data['declared_grid_mismatch_sessions']=[r['session_id'] for r in rows if r.get('declared_grid_mismatch')]
    global_data['zero_duration_provenance_sessions']=[r['session_id'] for r in rows if r.get('zero_duration_provenance_rows')]
    global_data['metadata_shorter_than_verified_LFP']=[r['session_id'] for r in rows if r['lfp_support_end_s'] is not None and float(r['metadata_recording_end_s'])<r['lfp_support_end_s']-1e-9]
    global_data['GoodSleep_shorter_than_verified_LFP']=[r['session_id'] for r in rows if r['lfp_support_end_s'] is not None and float(r['good_sleep_support_end_s'])<r['lfp_support_end_s']-1e-9]
    for label in ('wake','nrem','rem','ignore'): global_data[label+'_fraction']=summary(r[label+'_fraction'] for r in good)
    for name,key,reverse,pool in [('lowest_valid_supervision','valid_supervision_fraction',False,good),('highest_IGNORE','ignore_fraction',True,good),('lowest_REM','rem_fraction',False,good),('lowest_units','raw_stable_unit_count',False,rows),('highest_units','raw_stable_unit_count',True,rows)]:
        global_data[name]=[{r['session_id']:r[key]} for r in sorted(pool,key=lambda r:r[key],reverse=reverse)[:5]]
    (OUT/'global_summary.json').write_text(json.dumps(safe(global_data),ensure_ascii=False,indent=2),encoding='utf-8')
    text='# M3-B2 full-release global summary\n\n'+scopes+'\n\n'+mdtable([dict(metric=k,value=js(v)) for k,v in global_data.items()],['metric','value'])
    (OUT/'fcx1_fullrelease_global_summary.md').write_text(text,encoding='utf-8')
    if failed:
        text='# Unresolved structural issues\n\nNo protocol modifications or exclusions were made.\n'
        for r in failed:
            text+='\n## '+r['session_id']+'\n\n'+r['structural_issue']+'\n\n'
            for k in ('secondary_structural_evidence','raw_metadata_recording_intervals_s','raw_good_sleep_intervals_s','eeg_file_size_bytes','eeg_frame_width_bytes','eeg_remainder_bytes','invalid_metadata_rows','acquisition_sample_rate_hz','mat_acquisition_sample_rate_hz','raw_spike_grid_violations'):
                text+=f'- {k}: `{js(r.get(k))}`\n'
            text+='\nReproduce from work/src: `python -m data.align_session "'+r['local_path']+'"`\n'
        (OUT/'structural_issues.md').write_text(text,encoding='utf-8')
    note_path=ROOT/'notes'/f'{OUT.name}_fullrelease_audit.md'
    note_path.write_text('# Full-release audit record\n\n'+scopes+'\n\n'+f'Preflight: 27/27 PASS. Pipeline-valid: {len(good)}/27. '+js(global_data['status_counts'])+'\n\nApproved common pipeline unchanged during this run (SHA256 snapshot supplied). Checksum 34/34 match is user-reported; this audit checks extracted required files.\n\nOfficial caveats retained from the previously source-verified mapping notes. Raw data unchanged; M4 not started.\n',encoding='utf-8')
    interpretation=ROOT/'notes/milestone3b2_interpretation.md'
    if interpretation.exists() and OUT.name == 'milestone3b2':
        narrative=interpretation.read_text(encoding='utf-8')
        for path in (OUT/'fcx1_fullrelease_global_summary.md',OUT/'fcx1_within_animal_session_variability.md',ROOT/'notes/milestone3b2_fullrelease_audit.md'):
            with path.open('a',encoding='utf-8') as f: f.write('\n\n'+narrative)

if __name__=='__main__': main()
