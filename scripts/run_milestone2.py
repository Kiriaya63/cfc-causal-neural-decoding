"""Build strict labels, one causal dataset view, and Milestone 2 figures."""
from __future__ import annotations
import argparse, json, sys
from dataclasses import asdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from data import CausalSessionDataset, build_state_timeline, load_aligned_session  # noqa:E402
from visualization import plot_causal_sample, plot_label_coverage  # noqa:E402

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('session_dir',type=Path)
    p.add_argument('--context',type=int,default=30); p.add_argument('--decision-time',type=float,default=2431.0)
    p.add_argument('--output-dir',type=Path,default=ROOT/'figures'); a=p.parse_args()
    session=load_aligned_session(a.session_dir); timeline=build_state_timeline(session)
    dataset=CausalSessionDataset(session,a.context); row_i=next((i for i,r in enumerate(dataset.rows) if r.decision_time_s==a.decision_time),None)
    if row_i is None: raise SystemExit('Requested decision time is not a valid strict-label sample.')
    sample=dataset.get_sample(row_i); a.output_dir.mkdir(parents=True,exist_ok=True); stem=session.metadata.basename
    sample_path=a.output_dir/f'{stem}_causal_sample_t{a.decision_time:g}_w{a.context}.png'
    coverage_path=a.output_dir/f'{stem}_label_coverage.png'; report_path=a.output_dir/f'{stem}_milestone2_report.json'
    plot_causal_sample(sample,sample_path); plot_label_coverage(timeline,stem,coverage_path)
    report={'alignment':session.report.to_dict(),'label_coverage':asdict(timeline.coverage),'spike_bins':{'shape':list(dataset.spike_bins.counts.shape),'unit':'spikes/bin','excluded_tail_spikes':dataset.spike_bins.excluded_spike_count},'sample':asdict(sample.index)}
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False)); print(sample_path); print(coverage_path); print(report_path)
if __name__=='__main__': main()
