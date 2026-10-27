"""Strict JSON data contracts shared by the AI layer and the React frontend.

Every endpoint returns an `ApiResponse` envelope whose `data` field is one of
the feature models below. The same Pydantic models are handed to Claude as
structured-output schemas, so the model can only ever produce valid shapes.
"""

from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

Severity = Literal["low", "medium", "high", "critical"]
Confidence = Literal["low", "medium", "high"]


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    feature: str
    mode: Literal["live", "mock"]
    data: Optional[T] = None
    error: Optional[str] = None


# ---------------------------------------------------------------- safety


class PPEItem(BaseModel):
    item: str = Field(description="PPE item, e.g. helmet, high-visibility vest, gloves, safety boots, harness")
    status: Literal["compliant", "partial", "non_compliant", "not_visible"]
    note: str


class Hazard(BaseModel):
    type: str = Field(description="Hazard category, e.g. fall from height, struck-by, electrical, housekeeping")
    description: str
    severity: Severity
    location: str = Field(description="Where in the image or site the hazard is")
    recommendation: str


class SafetyReport(BaseModel):
    overall_risk_level: Severity
    safety_score: int = Field(description="0 (very unsafe) to 100 (fully safe)")
    summary: str
    workers_visible: int
    ppe_compliance: list[PPEItem]
    hazards: list[Hazard]
    violations: list[str]
    immediate_actions: list[str]


# ---------------------------------------------------------------- cracks


class CrackReport(BaseModel):
    crack_detected: bool
    crack_type: str = Field(description="e.g. hairline, shrinkage, settlement, structural flexural, shear, none")
    pattern: str = Field(description="e.g. vertical, horizontal, diagonal, map/alligator, stepped")
    severity: Severity
    estimated_width_mm: float = Field(description="Best estimate of crack width in millimetres; 0 if none")
    estimated_length_cm: float = Field(description="Best estimate of visible length in centimetres; 0 if none")
    material: str = Field(description="Material the crack appears in, e.g. concrete, brick masonry, plaster")
    probable_causes: list[str]
    structural_risk: str
    recommended_repairs: list[str]
    urgency: Literal["monitor", "repair_within_months", "repair_within_weeks", "immediate"]
    needs_engineer_inspection: bool
    summary: str


# ---------------------------------------------------------------- valuation


class ValueDriver(BaseModel):
    factor: str
    impact: Literal["positive", "negative", "neutral"]
    note: str


class ValuationReport(BaseModel):
    currency: str = Field(description="ISO currency code, e.g. INR, USD")
    estimated_value_low: float
    estimated_value_mid: float
    estimated_value_high: float
    price_per_sqft: float
    estimated_monthly_rent: float
    confidence: Confidence
    key_value_drivers: list[ValueDriver]
    market_outlook: str
    recommendations: list[str]
    assumptions: list[str]


# ---------------------------------------------------------------- planning


class Phase(BaseModel):
    name: str
    start_week: int
    duration_weeks: int
    tasks: list[str]
    milestones: list[str]
    estimated_cost: float


class LaborNeed(BaseModel):
    role: str
    count: int


class MaterialNeed(BaseModel):
    item: str
    quantity: float
    unit: str


class ProjectRisk(BaseModel):
    risk: str
    likelihood: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]
    mitigation: str


class ProjectPlan(BaseModel):
    project_title: str
    summary: str
    currency: str
    total_duration_weeks: int
    estimated_cost_total: float
    budget_status: Literal["within_budget", "tight", "over_budget"]
    phases: list[Phase]
    labor: list[LaborNeed]
    equipment: list[str]
    materials: list[MaterialNeed]
    risks: list[ProjectRisk]


# ---------------------------------------------------------------- daily site assistant


class SiteIssue(BaseModel):
    issue: str
    priority: Literal["low", "medium", "high"]
    suggested_owner: str


class DailySiteReport(BaseModel):
    date: str
    summary: str
    progress_status: Literal["on_track", "at_risk", "delayed"]
    work_completed: list[str]
    issues: list[SiteIssue]
    tomorrow_plan: list[str]
    safety_reminders: list[str]
    material_requests: list[str]


# ---------------------------------------------------------------- weather


class WeatherDay(BaseModel):
    date: str
    condition: str
    temp_min_c: float
    temp_max_c: float
    precipitation_mm: float
    wind_kmh: float
    work_suitability: Literal["good", "caution", "unsuitable"]
    note: str


class ActivityAdvice(BaseModel):
    activity: str
    recommendation: str
    best_days: list[str]


class WeatherAdvisory(BaseModel):
    location: str
    forecast_summary: str
    days: list[WeatherDay]
    activity_advice: list[ActivityAdvice]
    precautions: list[str]


# ---------------------------------------------------------------- knowledge


class KnowledgeAnswer(BaseModel):
    answer: str
    key_points: list[str]
    related_codes_and_standards: list[str]
    follow_up_questions: list[str]
    confidence: Confidence
