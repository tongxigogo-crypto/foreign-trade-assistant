from __future__ import annotations

import json
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

from agent_system.adapters.model_adapter import ModelAdapter, ModelAdapterConfig, get_default_provider_profile


@dataclass
class EvalCase:
    id: str
    scene: str
    user_query: str
    local_facts: list[str]
    expected_must_include: list[str]
    expected_must_not_include: list[str]
    gold_outline: list[str]
    difficulty: str


def _safe_lower_list(items: list[str]) -> list[str]:
    return [str(item).strip().lower() for item in items if str(item).strip()]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_eval_dataset(path: Path) -> list[EvalCase]:
    rows: list[EvalCase] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        item = json.loads(line)
        rows.append(
            EvalCase(
                id=str(item.get("id", f"line-{lineno}")),
                scene=str(item.get("scene", "")),
                user_query=str(item.get("user_query", "")),
                local_facts=[str(x) for x in item.get("local_facts", [])],
                expected_must_include=[str(x) for x in item.get("expected_must_include", [])],
                expected_must_not_include=[str(x) for x in item.get("expected_must_not_include", [])],
                gold_outline=[str(x) for x in item.get("gold_outline", [])],
                difficulty=str(item.get("difficulty", "medium")),
            )
        )
    return rows


def _synthesize_answer(case: EvalCase) -> str:
    facts = "; ".join(case.local_facts[:4])
    base = (
        f"问题理解：{case.user_query}。"
        f"已知事实：{facts or '暂无明确事实'}。"
        "建议先明确边界条件，再给出可执行替代方案，并约定下一步时间点。"
    )
    if "信息不足" in case.scene:
        base += " 为继续推进，请补充预算、数量、交期与贸易术语。"
    return base


def _case_scores(case: EvalCase, answer: str) -> dict[str, Any]:
    answer_l = answer.lower()
    must_include = _safe_lower_list(case.expected_must_include)
    must_not = _safe_lower_list(case.expected_must_not_include)
    gold = _safe_lower_list(case.gold_outline)

    include_hits = sum(1 for token in must_include if token in answer_l)
    not_hits = sum(1 for token in must_not if token in answer_l)
    gold_hits = sum(1 for token in gold if token in answer_l)

    include_score = include_hits / max(1, len(must_include))
    violation_score = 1.0 - (not_hits / max(1, len(must_not)))
    structure_score = gold_hits / max(1, len(gold))
    clarification_score = (
        1.0
        if ("信息不足" not in case.scene and "clarification" not in case.scene.lower())
        or ("请补充" in answer or "please provide" in answer.lower())
        else 0.0
    )
    tone_score = 1.0 if all(x not in answer_l for x in ["随便", "whatever", "无条件", "always yes"]) else 0.0

    return {
        "must_include_hit_rate": include_score,
        "must_not_violation_rate": violation_score,
        "structure_completeness": structure_score,
        "clarification_quality": clarification_score,
        "business_tone_safety": tone_score,
        "include_hits": include_hits,
        "include_total": len(must_include),
        "not_hits": not_hits,
        "not_total": len(must_not),
    }


def _score_dataset(
    *,
    dataset: list[EvalCase],
    weights: dict[str, float],
    answerer: Any,
) -> dict[str, Any]:
    agg = {k: 0.0 for k in weights}
    case_reports: list[dict[str, Any]] = []
    failed_case_ids: list[str] = []
    for case in dataset:
        answer = str(answerer(case))
        scores = _case_scores(case, answer)
        case_score = 0.0
        for key, weight in weights.items():
            value = float(scores.get(key, 0.0))
            agg[key] += value
            case_score += value * weight
        if case_score < 0.6:
            failed_case_ids.append(case.id)
        case_reports.append(
            {
                "id": case.id,
                "scene": case.scene,
                "difficulty": case.difficulty,
                "score": round(case_score, 4),
                "scores": {k: round(float(scores.get(k, 0.0)), 4) for k in weights},
            }
        )

    size = len(dataset)
    dimension_scores = {k: round(v / size, 4) for k, v in agg.items()}
    overall_score = round(sum(dimension_scores[k] * weights[k] for k in weights), 4)
    return {
        "dataset_size": size,
        "overall_score": overall_score,
        "dimension_scores": dimension_scores,
        "failed_case_ids": failed_case_ids,
        "top_regressions": failed_case_ids[:5],
        "cases": case_reports,
    }


def run_eval_suite(
    *,
    dataset_path: Path,
    rubric_path: Path,
    provider: str = "internal",
    model: str = "heuristic-v1",
) -> dict[str, Any]:
    dataset = _load_eval_dataset(dataset_path)
    rubric = _load_json(rubric_path)
    dimensions = list(rubric.get("dimensions", []))
    if not dataset:
        return {
            "status": "error",
            "message": "empty eval dataset",
            "dataset_size": 0,
        }

    weights: dict[str, float] = {}
    for item in dimensions:
        key = str(item.get("id", "")).strip()
        if not key:
            continue
        try:
            weights[key] = float(item.get("weight", 0.0))
        except (TypeError, ValueError):
            weights[key] = 0.0
    if not weights:
        weights = {
            "must_include_hit_rate": 0.35,
            "must_not_violation_rate": 0.25,
            "structure_completeness": 0.2,
            "clarification_quality": 0.1,
            "business_tone_safety": 0.1,
        }

    pass_threshold = float(rubric.get("pass_threshold", 0.75))
    baseline = _score_dataset(dataset=dataset, weights=weights, answerer=_synthesize_answer)
    baseline["status"] = "ok"
    baseline["provider"] = "internal"
    baseline["model"] = "heuristic-v1"
    baseline["pass_threshold"] = pass_threshold
    baseline["pass"] = baseline["overall_score"] >= pass_threshold

    live_eval: dict[str, Any] = {"status": "skipped", "reason": "missing_live_eval_env"}
    env_key = str(os.getenv("MODEL_EVAL_API_KEY", "")).strip()
    env_provider = str(os.getenv("MODEL_EVAL_PROVIDER", "")).strip().lower()
    env_model = str(os.getenv("MODEL_EVAL_MODEL", "")).strip()
    env_url = str(os.getenv("MODEL_EVAL_API_URL", "")).strip()
    if env_key and env_provider:
        profile = get_default_provider_profile(env_provider)
        live_cfg = ModelAdapterConfig(
            provider=env_provider,
            model=env_model or str(profile.get("model", "")),
            api_url=env_url or str(profile.get("api_url", "")),
            api_key=env_key,
            timeout_sec=int(profile.get("timeout_sec", 30)),
        )

        adapter = ModelAdapter(live_cfg)

        def _live_answer(case: EvalCase) -> str:
            system = "You are a foreign-trade assistant. Provide concise and actionable answer."
            user = f"Question: {case.user_query}\nLocal facts:\n" + "\n".join(f"- {x}" for x in case.local_facts)
            return adapter.chat([{"role": "system", "content": system}, {"role": "user", "content": user}])

        try:
            live_eval = _score_dataset(dataset=dataset, weights=weights, answerer=_live_answer)
            live_eval.update(
                {
                    "status": "ok",
                    "provider": env_provider,
                    "model": live_cfg.model,
                    "pass_threshold": pass_threshold,
                    "pass": live_eval["overall_score"] >= pass_threshold,
                }
            )
        except Exception as exc:  # pragma: no cover
            live_eval = {"status": "error", "message": str(exc), "provider": env_provider, "model": live_cfg.model}

    return {
        "status": "ok",
        "provider": provider,
        "model": model,
        "dataset_size": baseline["dataset_size"],
        "overall_score": baseline["overall_score"],
        "pass_threshold": pass_threshold,
        "pass": baseline["pass"],
        "dimension_scores": baseline["dimension_scores"],
        "failed_case_ids": baseline["failed_case_ids"],
        "top_regressions": baseline["top_regressions"],
        "cases": baseline["cases"],
        "baseline_eval": baseline,
        "live_eval": live_eval,
        "comparison": {
            "live_minus_baseline": round(float(live_eval.get("overall_score", 0.0)) - float(baseline["overall_score"]), 4)
            if live_eval.get("status") == "ok"
            else None
        },
    }
