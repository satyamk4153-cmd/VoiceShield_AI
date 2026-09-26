from typing import List
from app.schemas.fraud import ContextualSignal, FraudSignal


class ContextualEngineService:
    @staticmethod
    def evaluate_context(fraud_signals: List[FraudSignal], contextual_signals: List[ContextualSignal]) -> int:
        """
        Calculates contextual multiplier / penalty points based on psychological pressure tactics.
        Only applies when contextual signals are actively provided.
        """
        if not contextual_signals:
            return 0

        urgency_points = 0
        for ctx in contextual_signals:
            if ctx.severity == "HIGH":
                urgency_points += 8
            elif ctx.severity == "MEDIUM":
                urgency_points += 4

        # High density of threat + auth requests amplifies risk
        has_auth = any(s.category == "AUTHENTICATION" for s in fraud_signals)
        has_threat = any(s.category == "THREAT" for s in fraud_signals)
        if has_auth and has_threat:
            urgency_points += 5

        return min(25, urgency_points)
