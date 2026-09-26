from typing import List, Dict
from pydantic import BaseModel, Field


class StatMetric(BaseModel):
    label: str
    value: int
    change: str
    description: str


class IncidentSummary(BaseModel):
    id: str
    timestamp: str
    title: str
    risk_score: int
    risk_level: str
    caller_claimed: str
    flags: List[str]
    status: str = "FLAGGED"


class DistributionPoint(BaseModel):
    name: str
    value: int
    color: str


class DashboardStats(BaseModel):
    is_demo_data: bool = True
    total_calls_analyzed: int
    high_risk_calls: int
    possible_spoof_calls: int
    speaker_mismatches: int
    average_risk_score: float
    risk_distribution: List[DistributionPoint]
    fraud_category_distribution: List[DistributionPoint]
    signal_frequencies: List[DistributionPoint]
    recent_incidents: List[IncidentSummary]
