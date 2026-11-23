from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import health, matching, profile, subjects
from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.core.rate_limit import limiter

settings = get_settings()

app = FastAPI(title="PFE Finder API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
# Ajouté en dernier pour être le plus externe : les en-têtes CORS sont aussi
# présents sur les réponses d'erreur (par exemple 429).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(UpstreamError)
async def upstream_error_handler(request: Request, exc: UpstreamError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(health.router)
app.include_router(profile.router, prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(subjects.router, prefix="/api")
