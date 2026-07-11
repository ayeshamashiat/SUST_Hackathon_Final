"""Repeatable offline evaluation for the velocity-spike detector.

Run from ``backend`` with ``python -m app.evaluation.offline``. The harness
uses only in-memory synthetic records and the simulator's
``is_injected_anomaly`` ground-truth label.
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.analytics.anomaly import detect_velocity_spike
from app.models.models import Agent, Provider, Transaction, TransactionStatus, TransactionType

BASELINE_OFFSETS = [29, 28, 27, 26, 25, 23, 22, 21, 20, 19, 18.5, 17, 16, 15, 14, 13, 12.5, 12.2, 11, 10, 9, 8, 7, 6.5]
WINDOW_OFFSETS = {
    "normal_traffic": [5.5, 4.5, 3.5, 2.5, 1.5, 0.5],
    "eid_spike": [5.5, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.8, 0.6, 0.4],
    "injected_anomaly": [5.5, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5],
}


def _add_transactions(session: Session, offsets: list[float], now: datetime, *, injected: bool, prefix: str) -> None:
    for index, offset in enumerate(offsets):
        session.add(Transaction(
            agent_id="eval-agent", provider_id="bkash", type=TransactionType.CASH_OUT,
            amount=5_000.0 if injected else 1_000.0, customer_ref=f"{prefix}-{index % 3:04d}",
            area="Synthetic", status=TransactionStatus.SUCCESS, is_injected_anomaly=injected,
            created_at=now - timedelta(minutes=offset),
        ))
    session.commit()


def _evaluate_window(scenario: str, run: int) -> dict:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    now = datetime(2026, 1, 1, 12, 0, 0)
    with Session(engine) as session:
        session.add(Provider(id="bkash", name="bKash", color="#E2136E"))
        session.add(Agent(id="eval-agent", name="Evaluation Agent", area="Synthetic"))
        session.commit()
        if scenario == "eid_spike":
            # A legitimate seasonal increase must be measured against an
            # equally seasonal baseline, not the ordinary-day baseline.
            eid_baseline = BASELINE_OFFSETS + BASELINE_OFFSETS
            _add_transactions(session, eid_baseline, now, injected=False, prefix=f"eid-base-{run}")
        else:
            _add_transactions(session, BASELINE_OFFSETS, now, injected=False, prefix=f"base-{run}")
        injected = scenario == "injected_anomaly"
        _add_transactions(session, WINDOW_OFFSETS[scenario], now, injected=injected, prefix=f"window-{run}")
        result = detect_velocity_spike(session, "eval-agent", "bkash", now=now)
        return {"scenario": scenario, "label": injected, "flagged": result.flagged, "z_score": result.z_score}


def _metrics(rows: list[dict]) -> dict:
    tp = sum(row["label"] and row["flagged"] for row in rows)
    fp = sum(not row["label"] and row["flagged"] for row in rows)
    fn = sum(row["label"] and not row["flagged"] for row in rows)
    tn = sum(not row["label"] and not row["flagged"] for row in rows)
    return {
        "true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
    }


def evaluate(runs_per_scenario: int = 10) -> dict:
    rows = [_evaluate_window(scenario, run) for scenario in WINDOW_OFFSETS for run in range(runs_per_scenario)]
    by_scenario = {
        scenario: {"windows": runs_per_scenario, **_metrics([row for row in rows if row["scenario"] == scenario])}
        for scenario in WINDOW_OFFSETS
    }
    return {
        "evaluation": "velocity_spike_offline_synthetic",
        "ground_truth": "Transaction.is_injected_anomaly (synthetic records only)",
        "runs_per_scenario": runs_per_scenario,
        "overall": _metrics(rows),
        "by_scenario": by_scenario,
        "eid_spike_not_flagged": by_scenario["eid_spike"]["false_positive"] == 0,
    }


def markdown(report: dict) -> str:
    overall = report["overall"]
    lines = [
        "# Offline Anomaly Evaluation", "",
        "The velocity-spike detector was evaluated using deterministic synthetic simulator data. Ground truth comes only from `is_injected_anomaly`; it is not a real-world fraud label.", "",
        "## Overall metrics", "", "| Precision | Recall | False-positive rate |", "| ---: | ---: | ---: |",
        f"| {overall['precision']:.2%} | {overall['recall']:.2%} | {overall['false_positive_rate']:.2%} |", "",
        "## Scenario results", "", "| Scenario | Windows | TP | FP | FN | TN |", "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, metrics in report["by_scenario"].items():
        lines.append(f"| {name} | {metrics['windows']} | {metrics['true_positive']} | {metrics['false_positive']} | {metrics['false_negative']} | {metrics['true_negative']} |")
    lines += ["", f"Eid spike safeguard: **{'passed' if report['eid_spike_not_flagged'] else 'failed'}** — legitimate Eid demand windows were not flagged as injected anomalies.", "", "Limitation: this is an offline synthetic evaluation of one velocity detector. It demonstrates reproducibility and false-positive handling, not production fraud-detection performance."]
    return "\n".join(lines) + "\n"


def write_reports(output_dir: Path, runs_per_scenario: int = 10) -> dict:
    report = evaluate(runs_per_scenario)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "offline_evaluation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output_dir / "OFFLINE_EVALUATION.md").write_text(markdown(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[3] / "docs")
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(write_reports(args.output_dir, args.runs), indent=2))
