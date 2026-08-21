import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .db.init_db import init_db
from .api import auth, users, templates, conversions, admin


class EnsureCORSHeadersMiddleware(BaseHTTPMiddleware):
    """Guarantees CORS headers on EVERY response, including redirects (307/308) and errors."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "*")
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "86400"
            return response

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    for sub in ["cvs", "templates", "outputs"]:
        os.makedirs(os.path.join(settings.UPLOAD_DIR, sub), exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="CV Parser & Formatter API",
    description="AI-powered CV transformation engine with multi-LLM support",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False, # Disable auto-redirecting slashes to prevent CORS redirect drops
)

# Custom CORS middleware to guarantee headers on all response codes
app.add_middleware(EnsureCORSHeadersMiddleware)

# Standard CORSMiddleware as second layer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Static files (uploads) ────────────────────────────────────────────────────
uploads_dir = settings.UPLOAD_DIR
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="/auth",        tags=["Authentication"])
app.include_router(users.router,       prefix="/users",       tags=["Users"])
app.include_router(templates.router,   prefix="/templates",   tags=["Templates"])
app.include_router(conversions.router, prefix="/conversions", tags=["Conversions"])
app.include_router(admin.router,       prefix="/admin",       tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "CV Parser API is running. Visit /docs for the Swagger UI."}
