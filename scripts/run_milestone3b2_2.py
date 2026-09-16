"""Re-run every release session after the approved M3-B2.2 extensions."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/milestone3b2_2'

def raw_snapshot():
    with (ROOT/'config/fcx1_milestone3b2_sessions.csv').open(encoding='utf-8-sig') as f:
        entries=list(csv.DictReader(f))
    result={}
    for e in entries:
        for p in Path(e['local_path']).iterdir():
            if not p.is_file(): continue
            stat=p.stat()
            result[str(p)]=dict(size=stat.st_size,mtime_ns=stat.st_mtime_ns)
            if p.suffix != '.eeg' and stat.st_size < 100_000_000:
                result[str(p)]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    return result

if __name__ == '__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    before=raw_snapshot()
    (OUT/'raw_files_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    run=subprocess.run([sys.executable,str(ROOT/'scripts/run_milestone3b2.py'),
                        '--report-dir','reports/milestone3b2_2'],cwd=ROOT.parent)
    after=raw_snapshot()
    changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    (OUT/'raw_preservation_check.json').write_text(json.dumps(dict(
        files_checked=len(before),changed_files=changed,
        method='All file sizes/mtime; SHA256 for non-EEG files below 100 MB. EEG was only opened read-only; no full EEG rehash.'),indent=2),encoding='utf-8')
    if changed: raise RuntimeError(f'Raw preservation check failed: {changed}')
    if run.returncode: raise SystemExit(run.returncode)
