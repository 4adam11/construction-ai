from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .. import config, services
from ..llm import AIError, image_block
from ..schemas import (
    ApiResponse, CrackReport, DailySiteReport, KnowledgeAnswer, ProjectPlan, SafetyReport,
    ValuationReport, WeatherAdvisory,
)
from ..services import KnowledgeRequest, PlanRequest, ValuationRequest, WeatherRequest

router = APIRouter(prefix="/api")


async def _envelope(feature: str, call) -> dict:
    try:
        data, mode = await call
    except AIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except services.LocationNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "feature": feature, "mode": mode, "data": data, "error": None}


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


@router.post("/safety/analyze", response_model=ApiResponse[SafetyReport])
async def safety_analyze(image: UploadFile = File(...), context: str = Form("")):
    img = await _read_image(image, required=True)
    return await _envelope("safety", services.safety(img, context))


@router.post("/cracks/analyze", response_model=ApiResponse[CrackReport])
async def crack_analyze(image: UploadFile = File(...), structure_type: str = Form(""), notes: str = Form("")):
    img = await _read_image(image, required=True)
    return await _envelope("cracks", services.cracks(img, structure_type, notes))


@router.post("/daily/report", response_model=ApiResponse[DailySiteReport])
async def daily_report(notes: str = Form(...), project: str = Form(""), image: Optional[UploadFile] = File(None)):
    if not notes.strip():
        raise HTTPException(status_code=422, detail="Site notes are required.")
    img = await _read_image(image, required=False)
    return await _envelope("daily", services.daily(notes, project, img))


@router.post("/valuation/estimate", response_model=ApiResponse[ValuationReport])
async def valuation_estimate(req: ValuationRequest):
    return await _envelope("valuation", services.valuation(req))


@router.post("/planning/generate", response_model=ApiResponse[ProjectPlan])
async def planning_generate(req: PlanRequest):
    return await _envelope("planning", services.planning(req))


@router.post("/weather/advisory", response_model=ApiResponse[WeatherAdvisory])
async def weather_advisory(req: WeatherRequest):
    return await _envelope("weather", services.weather(req))


@router.post("/knowledge/ask", response_model=ApiResponse[KnowledgeAnswer])
async def knowledge_ask(req: KnowledgeRequest):
    return await _envelope("knowledge", services.knowledge(req))
