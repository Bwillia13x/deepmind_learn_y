"""Evals package for LLM quality assurance."""

from app.evals.run_evals import EvalCase, EvalCaseResult, run_all_evals, run_eval_case
from app.evals.scorers import (
    CulturalSensitivityScorer,
    EngagementScorer,
    EvalResult,
    GradeAppropriatenessScorer,
    RelevanceScorer,
    SafetyScorer,
    ScoreCategory,
    run_all_scorers,
)

__all__ = [
    # Scorers
    "ScoreCategory",
    "EvalResult",
    "SafetyScorer",
    "RelevanceScorer",
    "EngagementScorer",
    "CulturalSensitivityScorer",
    "GradeAppropriatenessScorer",
    "run_all_scorers",
    # Runner
    "EvalCase",
    "EvalCaseResult",
    "run_eval_case",
    "run_all_evals",
]
