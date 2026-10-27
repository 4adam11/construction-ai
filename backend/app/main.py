from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config
from .routers import features

app = FastAPI(title="Construction Intelligence Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _feature(request: Request) -> str:
    parts = request.url.path.strip("/").split("/")
    return parts[1] if len(parts) > 1 else "unknown"


def _error(request: Request, status: int, message: str) -> JSONResponse:
    # Errors keep the same envelope as successes so the frontend has one contract to handle.
    mode = "mock" if config.MOCK_MODE else "live"
    return JSONResponse(status_code=status, content={
        "success": False, "feature": _feature(request), "mode": mode, "data": None, "error": message,
    })


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return _error(request, exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "request"
    return _error(request, 422, f"Invalid {field}: {first.get('msg', 'bad input')}")


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    return _error(request, 500, "Unexpected server error.")


@app.get("/api/health")
async def health():
    return {"status": "ok", "mode": "mock" if config.MOCK_MODE else "live", "model": config.CLAUDE_MODEL}


app.include_router(features.router)
