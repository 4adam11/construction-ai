"""Deterministic offline responses used when no API key is configured (MOCK_MODE).

They follow the exact same schemas as the live AI output, so the frontend can be
developed and demoed without network access or API spend. Where inputs allow
(valuation, planning, weather) the numbers are computed from them; image
features return a representative sample report.
"""

from datetime import date, timedelta

from .schemas import (
    ActivityAdvice, CrackReport, DailySiteReport, Hazard, KnowledgeAnswer, LaborNeed,
    MaterialNeed, Phase, PPEItem, ProjectPlan, ProjectRisk, SafetyReport, SiteIssue,
    ValuationReport, ValueDriver, WeatherAdvisory, WeatherDay,
)


def safety(context: str) -> SafetyReport:
    return SafetyReport(
        overall_risk_level="high",
        safety_score=58,
        summary="Sample report (mock mode). Active slab work with several workers at height; edge protection "
                "is incomplete and two workers lack full PPE.",
        workers_visible=6,
        ppe_compliance=[
            PPEItem(item="Helmet", status="partial", note="5 of 6 workers wearing helmets."),
            PPEItem(item="High-visibility vest", status="partial", note="Two workers without vests near the hoist."),
            PPEItem(item="Safety harness", status="non_compliant", note="Worker at slab edge not tied off."),
            PPEItem(item="Safety boots", status="not_visible", note="Footwear not clearly visible."),
        ],
        hazards=[
            Hazard(type="Fall from height", description="Unprotected slab edge on the east side.", severity="critical",
                   location="Right side of frame, upper level", recommendation="Install guardrails or safety nets before work resumes."),
            Hazard(type="Housekeeping", description="Loose rebar offcuts and timber on the walkway.", severity="medium",
                   location="Foreground", recommendation="Clear walkways and set up a scrap collection point."),
            Hazard(type="Struck-by", description="Material hoist operating without a barricaded drop zone.", severity="high",
                   location="Centre-left", recommendation="Barricade the hoist zone and assign a banksman."),
        ],
        violations=["Work at height without fall arrest", "Incomplete PPE", "No exclusion zone under lifting operation"],
        immediate_actions=["Stop work at the east slab edge until guardrails are fitted",
                           "Issue helmets and vests to all workers on site",
                           "Barricade the hoist drop zone"],
    )


def crack(structure: str) -> CrackReport:
    return CrackReport(
        crack_detected=True,
        crack_type="Settlement crack",
        pattern="Diagonal, stepped through mortar joints",
        severity="medium",
        estimated_width_mm=2.5,
        estimated_length_cm=85,
        material="Brick masonry with cement plaster",
        probable_causes=["Differential foundation settlement", "Moisture variation in clayey soil", "Absence of plinth beam"],
        structural_risk="Moderate. Width above 2 mm indicates active movement; not an immediate collapse risk but "
                        "may progress if the cause is not addressed.",
        recommended_repairs=["Install tell-tale crack monitors for 4-6 weeks",
                             "If stable, rake out and fill with polymer-modified mortar",
                             "If widening, investigate foundation and consider underpinning",
                             "Improve drainage around the foundation"],
        urgency="repair_within_weeks",
        needs_engineer_inspection=True,
        summary=f"Sample report (mock mode) for a {structure or 'wall'}: a diagonal settlement crack of about 2.5 mm "
                "suggests differential movement. Monitor and have a structural engineer inspect.",
    )


CITY_RATES = {"mumbai": 28000, "delhi": 16000, "bangalore": 11000, "bengaluru": 11000, "pune": 9500,
              "hyderabad": 8500, "chennai": 9000, "kolkata": 7000, "ahmedabad": 6500, "jaipur": 5500}


def valuation(location: str, area_sqft: float, property_type: str, bedrooms: int, age_years: int,
              condition: str, amenities: list[str]) -> ValuationReport:
    base = next((r for c, r in CITY_RATES.items() if c in location.lower()), 6000)
    factor = {"apartment": 1.0, "villa": 1.25, "independent house": 1.15, "plot": 0.7, "commercial": 1.4}.get(property_type.lower(), 1.0)
    factor *= {"excellent": 1.1, "good": 1.0, "fair": 0.9, "poor": 0.75}.get(condition.lower(), 1.0)
    factor *= max(0.7, 1 - age_years * 0.01)
    factor *= 1 + min(len(amenities), 8) * 0.015
    pps = round(base * factor)
    mid = pps * area_sqft
    return ValuationReport(
        currency="INR",
        estimated_value_low=round(mid * 0.9),
        estimated_value_mid=round(mid),
        estimated_value_high=round(mid * 1.1),
        price_per_sqft=pps,
        estimated_monthly_rent=round(mid * 0.0028),
        confidence="low",
        key_value_drivers=[
            ValueDriver(factor="Location", impact="positive" if base > 8000 else "neutral", note=f"Benchmark rate ~INR {base:,}/sq ft for {location}."),
            ValueDriver(factor="Property age", impact="negative" if age_years > 10 else "neutral", note=f"{age_years} years old; depreciation applied."),
            ValueDriver(factor="Condition", impact="positive" if condition.lower() in {"excellent", "good"} else "negative", note=f"Reported as {condition}."),
            ValueDriver(factor="Amenities", impact="positive" if amenities else "neutral", note=f"{len(amenities)} amenities listed."),
        ],
        market_outlook="Mock estimate from a rule-based model. Connect an API key for an AI market analysis.",
        recommendations=["Compare with 3-5 recent registered sales within 1 km", "Get a certified valuer's report before any transaction"],
        assumptions=["Clear title and approved building plan", "Carpet-to-built-up ratio of about 0.75", f"{bedrooms} bedroom configuration"],
    )


def plan(project_type: str, area_sqft: float, floors: int, budget: float, location: str) -> ProjectPlan:
    cost_per_sqft = {"residential": 2200, "commercial": 3000, "industrial": 2600, "infrastructure": 3500}.get(project_type.lower(), 2400)
    total_area = area_sqft * max(floors, 1)
    total = round(total_area * cost_per_sqft)
    weeks = max(16, round(12 + total_area / 400 + floors * 3))
    split = [("Pre-construction & approvals", 0.10, 0.03), ("Site preparation & foundation", 0.15, 0.15),
             ("Superstructure", 0.35, 0.40), ("MEP services", 0.15, 0.17),
             ("Finishing", 0.20, 0.20), ("Handover & snagging", 0.05, 0.05)]
    phases, week = [], 1
    for name, t, c in split:
        dur = max(1, round(weeks * t))
        phases.append(Phase(name=name, start_week=week, duration_weeks=dur, tasks=_TASKS[name],
                            milestones=[f"{name} complete"], estimated_cost=round(total * c)))
        week += dur
    status = "within_budget" if budget >= total * 1.05 else "tight" if budget >= total * 0.95 else "over_budget"
    return ProjectPlan(
        project_title=f"{floors}-storey {project_type} project, {location}",
        summary=f"Mock plan (rule-based). {total_area:,.0f} sq ft built-up at ~INR {cost_per_sqft:,}/sq ft.",
        currency="INR",
        total_duration_weeks=week - 1,
        estimated_cost_total=total,
        budget_status=status,
        phases=phases,
        labor=[LaborNeed(role="Site engineer", count=1), LaborNeed(role="Mason", count=4 + floors),
               LaborNeed(role="Bar bender", count=2 + floors // 2), LaborNeed(role="Carpenter", count=3),
               LaborNeed(role="Electrician", count=2), LaborNeed(role="Plumber", count=2), LaborNeed(role="Helper", count=8 + floors * 2)],
        equipment=["Concrete mixer", "Vibrator", "Steel scaffolding", "Material hoist", "Bar bending machine"],
        materials=[MaterialNeed(item="Cement", quantity=round(total_area * 0.4), unit="bags"),
                   MaterialNeed(item="Steel (TMT)", quantity=round(total_area * 4), unit="kg"),
                   MaterialNeed(item="Sand", quantity=round(total_area * 1.2), unit="cu ft"),
                   MaterialNeed(item="Aggregate", quantity=round(total_area * 1.35), unit="cu ft"),
                   MaterialNeed(item="Bricks / blocks", quantity=round(total_area * 8), unit="nos")],
        risks=[ProjectRisk(risk="Monsoon delays to foundation work", likelihood="medium", impact="high", mitigation="Schedule excavation outside monsoon; keep dewatering pumps ready."),
               ProjectRisk(risk="Material price escalation", likelihood="high", impact="medium", mitigation="Lock steel and cement rates early; keep 8-10% contingency."),
               ProjectRisk(risk="Approval delays", likelihood="medium", impact="medium", mitigation="Engage a liaison consultant and submit complete drawings.")],
    )


_TASKS = {
    "Pre-construction & approvals": ["Soil investigation", "Architectural & structural drawings", "Building permit"],
    "Site preparation & foundation": ["Site clearing & layout", "Excavation", "PCC & footings", "Plinth beam & backfilling"],
    "Superstructure": ["Columns & beams", "Slab casting per floor", "Masonry walls", "Staircase"],
    "MEP services": ["Electrical conduits & wiring", "Plumbing & drainage", "HVAC provisions"],
    "Finishing": ["Plastering", "Flooring & tiling", "Doors & windows", "Painting"],
    "Handover & snagging": ["Snag list closure", "Occupancy certificate", "Handover documentation"],
}


def daily(notes: str) -> DailySiteReport:
    return DailySiteReport(
        date=date.today().isoformat(),
        summary="Mock summary. Connect an API key to have the AI read your actual notes. "
                f"Received {len(notes.split())} words of site notes.",
        progress_status="at_risk",
        work_completed=["2nd floor slab shuttering 80% complete", "Column casting C4-C9 done"],
        issues=[SiteIssue(issue="Cement delivery delayed by one day", priority="high", suggested_owner="Procurement"),
                SiteIssue(issue="Water seepage in basement retaining wall", priority="medium", suggested_owner="Site engineer")],
        tomorrow_plan=["Complete shuttering and reinforcement check", "Schedule slab pour pending cube results"],
        safety_reminders=["Edge protection on 2nd floor before pour", "Toolbox talk on working at height"],
        material_requests=["120 bags OPC 53 grade", "2 t of 12 mm TMT bars"],
    )


def weather(location: str, activities: list[str], forecast: dict | None) -> WeatherAdvisory:
    if forecast:
        raw, place = forecast["days"], forecast["location"]
    else:
        place = location
        raw = [{"date": (date.today() + timedelta(days=i)).isoformat(), "condition": c, "temp_min_c": 22 + i % 3,
                "temp_max_c": 31 + i % 4, "precipitation_mm": p, "wind_kmh": w}
               for i, (c, p, w) in enumerate([("Partly cloudy", 0, 12), ("Light rain", 4, 18), ("Rain", 18, 25),
                                               ("Overcast", 1, 14), ("Clear sky", 0, 10), ("Clear sky", 0, 9), ("Showers", 8, 20)])]
    days = []
    for d in raw:
        suit = "unsuitable" if d["precipitation_mm"] >= 10 or d["wind_kmh"] >= 40 or d["temp_max_c"] >= 42 else \
               "caution" if d["precipitation_mm"] >= 2 or d["wind_kmh"] >= 25 or d["temp_max_c"] >= 38 else "good"
        days.append(WeatherDay(**d, work_suitability=suit, note={"good": "Normal operations.",
                    "caution": "Plan covers and limit exposed work.", "unsuitable": "Avoid concreting, roofing and crane lifts."}[suit]))
    good = [d.date for d in days if d.work_suitability == "good"]
    return WeatherAdvisory(
        location=place,
        forecast_summary=("Live forecast; " if forecast else "Sample forecast; ") + "rule-based advice (mock mode). "
                         f"{len(good)} of {len(days)} days suitable for full outdoor work.",
        days=days,
        activity_advice=[ActivityAdvice(activity=a, recommendation="Schedule on dry, low-wind days.", best_days=good[:3]) for a in activities],
        precautions=["Keep tarpaulins ready for fresh concrete", "Suspend crane lifts above 38 km/h wind", "Ensure drinking water and shade on hot days"],
    )


def knowledge(question: str) -> KnowledgeAnswer:
    return KnowledgeAnswer(
        answer="This is a mock answer. Set ANTHROPIC_API_KEY on the backend to get real answers from the AI. "
               f'Your question was: "{question}"',
        key_points=["Mock mode is active", "All other platform features still work with sample data"],
        related_codes_and_standards=["IS 456:2000 (Plain and reinforced concrete)", "OSHA 29 CFR 1926 (Construction safety)"],
        follow_up_questions=["What is the curing period for M25 concrete?", "How is a slump test done?"],
        confidence="low",
    )
