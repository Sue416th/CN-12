from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class EvaluationResult:
    sentiment: str
    satisfaction_score: float
    issues_detected: List[str]
    user_suggestions: List[str]
    system_suggestions: List[str]
    summary: str

    def to_dict(self) -> Dict[str, object]:
        suggestion = self.user_suggestions[0] if self.user_suggestions else self.summary
        return {
            "sentiment": self.sentiment,
            "score": self.satisfaction_score,
            "suggestion": suggestion,
            "satisfaction_score": self.satisfaction_score,
            "issues_detected": self.issues_detected,
            "user_suggestions": self.user_suggestions,
            "system_suggestions": self.system_suggestions,
            "summary": self.summary,
        }


class PostTripEvaluationAgent:
    _POSITIVE_CUES: Sequence[str] = (
        "beautiful",
        "great",
        "good",
        "excellent",
        "amazing",
        "enjoy",
        "friendly",
        "comfortable",
        "smooth",
    )
    _NEGATIVE_CUES: Sequence[str] = (
        "crowded",
        "queue",
        "long wait",
        "rushed",
        "delay",
        "traffic",
        "expensive",
        "poor",
        "bad",
    )

    _ISSUE_RULES: Sequence[tuple[Sequence[str], str, str, str]] = (
        (
            ("queue", "long wait", "waiting", "crowded"),
            "long waiting time",
            "Try visiting popular attractions in off-peak time slots.",
            "Optimize the planning model with crowd-aware scheduling.",
        ),
        (
            ("rushed", "tight schedule", "schedule"),
            "tight schedule",
            "Keep fewer attractions per day and add rest blocks.",
            "Rebalance itinerary pace by day length and transfer time.",
        ),
        (
            ("transport", "traffic", "bus", "train", "metro", "transfer"),
            "transportation inconvenience",
            "Choose routes with fewer transfers and stable travel times.",
            "Integrate transport reliability into route scoring.",
        ),
        (
            ("expensive", "costly", "price"),
            "high travel cost",
            "Add budget-friendly alternatives for meals and attractions.",
            "Improve price-performance optimization for recommendations.",
        ),
    )

    def evaluate(self, review_text: str) -> Dict[str, object]:
        result = self._evaluate_internal(review_text)
        return result.to_dict()

    def _evaluate_internal(self, review_text: str) -> EvaluationResult:
        text = (review_text or "").strip()
        if not text:
            return EvaluationResult(
                sentiment="neutral",
                satisfaction_score=0.5,
                issues_detected=[],
                user_suggestions=["Please provide more specific trip feedback."],
                system_suggestions=["Collect richer user signals before optimization."],
                summary="The feedback is neutral and too brief for deeper analysis.",
            )

        lowered = text.lower()
        positive_hits = sum(1 for cue in self._POSITIVE_CUES if cue in lowered)
        negative_hits = sum(1 for cue in self._NEGATIVE_CUES if cue in lowered)

        sentiment = self._resolve_sentiment(positive_hits, negative_hits)
        satisfaction_score = self._compute_score(positive_hits, negative_hits)
        issues, user_suggestions, system_suggestions = self._extract_actions(lowered)
        summary = self._build_summary(sentiment, satisfaction_score, issues, system_suggestions)

        return EvaluationResult(
            sentiment=sentiment,
            satisfaction_score=satisfaction_score,
            issues_detected=issues,
            user_suggestions=user_suggestions,
            system_suggestions=system_suggestions,
            summary=summary,
        )

    @staticmethod
    def _resolve_sentiment(positive_hits: int, negative_hits: int) -> str:
        if positive_hits > 0 and negative_hits > 0:
            return "mixed"
        if positive_hits > negative_hits:
            return "positive"
        if negative_hits > positive_hits:
            return "negative"
        return "neutral"

    @staticmethod
    def _compute_score(positive_hits: int, negative_hits: int) -> float:
        raw = 0.68 + 0.08 * positive_hits - 0.08 * negative_hits
        return round(max(0.0, min(1.0, raw)), 2)

    def _extract_actions(self, lowered_text: str) -> tuple[List[str], List[str], List[str]]:
        issues: List[str] = []
        user_suggestions: List[str] = []
        system_suggestions: List[str] = []

        for keywords, issue, user_tip, system_tip in self._ISSUE_RULES:
            if any(keyword in lowered_text for keyword in keywords):
                if issue not in issues:
                    issues.append(issue)
                if user_tip not in user_suggestions:
                    user_suggestions.append(user_tip)
                if system_tip not in system_suggestions:
                    system_suggestions.append(system_tip)

        if not issues:
            user_suggestions.append("Keep your current travel style and explore more local culture spots.")
            system_suggestions.append("Maintain itinerary quality and continue personalization tuning.")

        return issues, user_suggestions, system_suggestions

    @staticmethod
    def _build_summary(sentiment: str, score: float, issues: List[str], system_suggestions: List[str]) -> str:
        if issues:
            issue_text = ", ".join(issues[:2])
            suggestion_text = " and ".join(system_suggestions[:2])
            return (
                f"The trip was overall {sentiment} (satisfaction score: {score:.2f}). "
                f"Key issues include {issue_text}. "
                f"Recommended optimization: {suggestion_text}."
            )
        return (
            f"The trip was overall {sentiment} (satisfaction score: {score:.2f}) "
            "with no major issues detected."
        )

