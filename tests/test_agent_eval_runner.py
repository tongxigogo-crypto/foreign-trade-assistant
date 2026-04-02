from __future__ import annotations

from pathlib import Path

from agent_system.eval.runner import run_eval_suite


def test_eval_runner_works_on_repo_dataset() -> None:
    root = Path(__file__).resolve().parents[1]
    summary = run_eval_suite(
        dataset_path=root / "agent_system" / "config" / "eval_trade_20.jsonl",
        rubric_path=root / "agent_system" / "config" / "eval_rubric_trade.json",
    )
    assert summary["status"] == "ok"
    assert summary["dataset_size"] == 20
    assert 0.0 <= float(summary["overall_score"]) <= 1.0
    assert "dimension_scores" in summary

