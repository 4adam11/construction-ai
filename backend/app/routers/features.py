import json
from datetime import date
from typing import Awaitable, Callable, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .. import config, mock
from ..llm import AIError, generate, image_block
from ..schemas import (
    ApiResponse, CrackReport, DailySiteReport, KnowledgeAnswer, ProjectPlan, SafetyReport,
    ValuationReport, WeatherAdvisory,
)
from ..weather import get_forecast

router = APIRouter(prefix="/api")


async def _run(feature: str, live: Callable[[], Awaitable[BaseModel]], offline: Callable[[], BaseModel]) -> dict:
    if config.MOCK_MODE:
        return {"success": True, "feature": feature, "mode": "mock", "data": offline(), "error": None}
    try:
        data = await live()
    except AIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"success": True, "feature": feature, "mode": "live", "data": data, "error": None}


async def _read_image(file: Optional[UploadFile], required: bool) -> Optional[dict]:
    if file is None or not file.filename:
        if required:
            raise HTTPException(status_code=422, detail="An image is required.")
        return None
    if file.content_type not in config.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, WebP or GIF image.")
    data = await file.read()
    if len(data) > config.MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is larger than 5 MB.")
    return image_block(data, file.content_type)


# ---------------------------------------------------------------- image features


@router.post("/safety/analyze", response_model=ApiResponse[SafetyReport])
async def safety_analyze(image: UploadFile = File(...), context: str = Form("")):
    img = await _read_image(image, required=True)
    prompt = (
        "Analyse this construction site photo for safety. Count visible workers, assess PPE compliance item "
        "by item, list every hazard with severity and where it is in the frame, list regulatory violations, "
        "and give the immediate actions a safety officer should take, most urgent first."
        + (f"\n\nSite context from the user: {context}" if context else "")
    )
    return await _run("safety", lambda: generate(SafetyReport, prompt, [img]), lambda: mock.safety(context))


@router.post("/cracks/analyze", response_model=ApiResponse[CrackReport])
async def crack_analyze(image: UploadFile = File(...), structure_type: str = Form(""), notes: str = Form("")):
    img = await _read_image(image, required=True)
    prompt = (
        "Inspect this image for cracks in a building or structural element. Classify the crack type and "
        "pattern, estimate width and length (state in the summary how you estimated scale), identify the "
        "material, list probable causes, assess structural risk, and recommend repairs and urgency. If no "
        "crack is visible, set crack_detected to false, severity low, and explain."
        + (f"\n\nStructure / element: {structure_type}" if structure_type else "")
        + (f"\nUser notes: {notes}" if notes else "")
    )
    return await _run("cracks", lambda: generate(CrackReport, prompt, [img]), lambda: mock.crack(structure_type))


@router.post("/daily/report", response_model=ApiResponse[DailySiteReport])
async def daily_report(notes: str = Form(...), project: str = Form(""), image: Optional[UploadFile] = File(None)):
    if not notes.strip():
        raise HTTPException(status_code=422, detail="Site notes are required.")
    img = await _read_image(image, required=False)
    prompt = (
        f"Today is {date.today().isoformat()}. Turn these raw site notes"
        + (" and the attached site photo" if img else "")
        + " into a structured daily site report: what was completed, issues with priority and a suggested "
        "owner, tomorrow's plan, safety reminders and material requests. Judge overall progress status."
        + (f"\n\nProject: {project}" if project else "")
        + f"\n\nSite notes:\n{notes}"
    )
    return await _run("daily", lambda: generate(DailySiteReport, prompt, [img] if img else None), lambda: mock.daily(notes))


# ---------------------------------------------------------------- structured-data features


class ValuationRequest(BaseModel):
    location: str = Field(min_length=2)
    property_type: str = "Apartment"
    area_sqft: float = Field(gt=0)
    bedrooms: int = Field(ge=0, default=2)
    bathrooms: int = Field(ge=0, default=2)
    age_years: int = Field(ge=0, default=0)
    floor: Optional[int] = None
    condition: str = "Good"
    amenities: list[str] = []
    notes: str = ""


@router.post("/valuation/estimate", response_model=ApiResponse[ValuationReport])
async def valuation_estimate(req: ValuationRequest):
    prompt = (
        "Estimate the current market value of this property. Use typical local market rates for the location "
        "(use the local currency), give a low/mid/high range, price per sq ft, expected monthly rent, the key "
        "value drivers, a short market outlook, recommendations and the assumptions you made.\n\n"
        f"Property details (JSON):\n{req.model_dump_json(indent=2)}"
    )
    return await _run(
        "valuation", lambda: generate(ValuationReport, prompt),
        lambda: mock.valuation(req.location, req.area_sqft, req.property_type, req.bedrooms, req.age_years, req.condition, req.amenities),
    )


class PlanRequest(BaseModel):
    project_name: str = ""
    project_type: str = "Residential"
    location: str = Field(min_length=2)
    plot_area_sqft: float = Field(gt=0)
    floors: int = Field(ge=1, default=1)
    budget: float = Field(gt=0)
    currency: str = "INR"
    start_date: Optional[str] = None
    requirements: str = ""


@router.post("/planning/generate", response_model=ApiResponse[ProjectPlan])
async def planning_generate(req: PlanRequest):
    prompt = (
        "Create a realistic construction project plan. Break it into sequential phases with start week, "
        "duration, tasks, milestones and cost; size the labour crew, equipment and key material quantities; "
        "estimate the total cost in the given currency and compare it to the budget; list the main risks "
        "with mitigation.\n\n"
        f"Project details (JSON):\n{req.model_dump_json(indent=2)}"
    )
    return await _run(
        "planning", lambda: generate(ProjectPlan, prompt),
        lambda: mock.plan(req.project_type, req.plot_area_sqft, req.floors, req.budget, req.location),
    )


class WeatherRequest(BaseModel):
    location: str = Field(min_length=2)
    activities: list[str] = ["Concrete pouring"]


@router.post("/weather/advisory", response_model=ApiResponse[WeatherAdvisory])
async def weather_advisory(req: WeatherRequest):
    forecast = await get_forecast(req.location)
    if forecast is None and not config.MOCK_MODE:
        raise HTTPException(status_code=404, detail=f"Could not find a forecast for '{req.location}'. Try a city name.")
    prompt = (
        "Using this 7-day forecast, rate each day's suitability for outdoor construction work and give "
        "activity-specific advice (best days, what to avoid) plus general precautions. Keep the forecast "
        "numbers exactly as given.\n\n"
        f"Planned activities: {', '.join(req.activities)}\n\nForecast (JSON):\n{json.dumps(forecast, indent=2)}"
    )
    return await _run("weather", lambda: generate(WeatherAdvisory, prompt), lambda: mock.weather(req.location, req.activities, forecast))


class ChatTurn(BaseModel):
    role: str
    content: str


class KnowledgeRequest(BaseModel):
    question: str = Field(min_length=3)
    history: list[ChatTurn] = []


@router.post("/knowledge/ask", response_model=ApiResponse[KnowledgeAnswer])
async def knowledge_ask(req: KnowledgeRequest):
    history = "\n".join(f"{t.role}: {t.content}" for t in req.history[-8:])
    prompt = (
        "Answer this construction question clearly for a practising engineer or site supervisor. Mention "
        "relevant codes and standards, give key points, and suggest follow-up questions."
        + (f"\n\nEarlier conversation:\n{history}" if history else "")
        + f"\n\nQuestion: {req.question}"
    )
    return await _run("knowledge", lambda: generate(KnowledgeAnswer, prompt), lambda: mock.knowledge(req.question))
