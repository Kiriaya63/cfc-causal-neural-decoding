"""Pilot deep QC and full release inventory; raw data is read-only."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from data import load_session_manifest, load_aligned_session, build_state_timeline, audit_manifest
from data.deep_qc import annotation_diagnostics, animal_summary

def write_csv(path, rows, fields=None):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',type=Path,default=ROOT/'config/fcx1_milestone3_sessions.csv')
    p.add_argument('--output',type=Path,default=ROOT/'reports/milestone3b')
    args=p.parse_args()
    entries=load_session_manifest(args.manifest)
    args.output.mkdir(parents=True,exist_ok=True)
    results=audit_manifest(entries)
    details={}
    fields=[]
    conflicts=[]
    for entry in entries:
        s=load_aligned_session(entry.local_path)
        d=annotation_diagnostics(s,build_state_timeline(s))
        details[entry.session_id]=d
        fields.extend(dict(session_id=entry.session_id,**r) for r in d['out_of_bounds_by_field'])
        conflicts.extend(dict(session_id=entry.session_id,**r) for r in d['conflicts'])
    (args.output/'pilot_deep_qc.json').write_text(json.dumps(details,indent=2),encoding='utf-8')
    write_csv(args.output/'out_of_bounds_fields.csv',fields)
    write_csv(args.output/'conflict_intervals.csv',conflicts,['session_id','type','start_s','stop_s','duration_s'])
    animals=animal_summary(results)
    write_csv(args.output/'animal_qc.csv',animals)
    write_csv(args.output/'session_qc.csv',[r.to_dict() for r in results])
    distributions=dict(scope='5-session pilot only; not full-dataset estimates',
        stable_units=[dict(session_id=r.session_id,animal_id=r.animal_id,count=r.stable_unit_count) for r in results],
        regions_session_count=dict(Counter(region for r in results for region in r.anatomical_regions)),
        channel_availability=[dict(session_id=r.session_id,lfp=r.recommended_lfp_channel,lfp_region=r.recommended_lfp_anatomy,theta=r.theta_channel,theta_region=r.theta_channel_anatomy,unlabeled_channels=r.channels_without_anatomy_label) for r in results],
        coverage=[dict(session_id=r.session_id,**{k:getattr(r,k) for k in ('wake_seconds','nrem_seconds','rem_seconds','ignore_seconds','full_1s_bin_count')}) for r in results])
    (args.output/'pilot_distributions.json').write_text(json.dumps(distributions,indent=2),encoding='utf-8')
    data_root=entries[0].local_path.parent
    official=data_root.parent/'filelist.txt'
    names=re.findall(r'data/([^\s/]+)\.tar\.gz',official.read_text())
    known={e.session_id:e.animal_id for e in entries}
    inventory=[dict(session_id=n,animal_id=known.get(n,'unknown'),local_path=str(data_root/n),availability=(data_root/n).is_dir(),processing_status='pilot_deep_qc_complete' if n in details else 'missing_not_audited') for n in names]
    write_csv(args.output/'full_release_inventory.csv',inventory)
    lines=['# Milestone 3-B: pilot deep QC and full-data availability','',
           'M3-A has been accepted by the user. M3-B is incomplete: only 5 of 27 release sessions are locally extracted. Animal identities for missing sessions remain unknown pending source verification.',
           '', 'All results below describe the pilot only. IGNORE is excluded supervision time, not a valid sleep class. Animal totals sum session durations; units are per-session counts, not distinct neurons across days.',
           '', '## Out-of-bounds fields','', '| Session | Field | Role | Rows |','|---|---|---|---:|']
    lines += [f"| {r['session_id']} | {r['field']} | {r['role']} | {r['count']} |" for r in fields if r['count']]
    lines += ['', 'Counts refer to source rows, not unique episodes or seconds. Core target fields are Wake/REM/SWSPacket; Sleep/WakeSleep are broad-state/episode validation; MA/WakeInterruption are auxiliary.', '', '## Exact conflict intervals','', 'Half-open seconds; combinations include broad SLEEP as context. Only bins marked conflicting by the unchanged strict policy are listed.', '', '| Session | Active annotations | Start | Stop | Seconds |','|---|---|---:|---:|---:|']
    lines += [f"| {r['session_id']} | {r['type']} | {r['start_s']} | {r['stop_s']} | {r['duration_s']} |" for r in conflicts]
    lines += ['', '## Animal summary','', '| Animal | Sessions | Support s | WAKE | NREM | REM | IGNORE | Units/session | Missing class |','|---|---:|---:|---:|---:|---:|---:|---|---|']
    lines += [f"| {r['animal_id']} | {r['session_count']} | {r['effective_recording_duration_s']} | {r['wake_seconds']} | {r['nrem_seconds']} | {r['rem_seconds']} | {r['ignore_seconds']} | {r['stable_units_per_session']} | {r['missing_core_classes']} |" for r in animals]
    (args.output/'pilot_deep_qc.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(conflicts={k:v['conflict_duration_by_type_s'] for k,v in details.items()},out_of_bounds={k:{r['field']:r['count'] for r in v['out_of_bounds_by_field'] if r['count']} for k,v in details.items()},release_sessions=len(names),available=sum(r['availability'] for r in inventory)),indent=2))

if __name__=='__main__':
    main()
