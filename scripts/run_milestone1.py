"""Validate one fcx-1 session and generate Milestone 1 sanity figures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data import load_aligned_session  # noqa: E402
from visualization import plot_multimodal_window, plot_wake_sleep_episode  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dir", type=Path)
    parser.add_argument(
        "--output-dir", type=Path, default=PROJECT_ROOT / "figures"
    )
    parser.add_argument("--short-start", type=float, default=3375.0)
    parser.add_argument("--short-stop", type=float, default=3520.0)
    args = parser.parse_args()

    session = load_aligned_session(args.session_dir)
    print(session.report.to_json())
    if not session.report.core_alignment_valid:
        raise SystemExit("Core alignment failed; no figures were generated.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = session.metadata.basename
    short_token = f"{args.short_start:g}_{args.short_stop:g}".replace(".", "p")
    short_path = args.output_dir / f"{stem}_multimodal_{short_token}.png"
    episode_path = args.output_dir / f"{stem}_wake_sleep_episode.png"
    report_path = args.output_dir / f"{stem}_alignment_report.json"

    plot_multimodal_window(
        session, args.short_start, args.short_stop, short_path
    )
    plot_wake_sleep_episode(session, episode_path, episode_index=0)
    report_path.write_text(
        json.dumps(session.report.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"short_figure={short_path}")
    print(f"episode_figure={episode_path}")
    print(f"alignment_report={report_path}")


if __name__ == "__main__":
    main()
