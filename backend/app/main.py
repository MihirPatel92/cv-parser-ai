import os
import re
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .db.init_db import init_db
from .api import auth, users, templates, conversions, admin


# ── Dynamic CORS Middleware ────────────────────────────────────────────────────
# Allows any *.onrender.com subdomain and localhost — no matter what random
# suffix Render assigns to the frontend service URL.
ALLOWED_ORIGIN_RE = re.compile(
    r"^https?://"
    r"(localhost(:\d+)?"           # localhost with any port
    r"|127\.0\.0\.1(:\d+)?"        # 127.0.0.1 with any port
    r"|[\w-]+\.onrender\.com"      # any *.onrender.com subdomain
    r")$"
)


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """Reflect the requesting origin in CORS headers if it matches the allowlist pattern."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")

        # Handle pre-flight OPTIONS request immediately
        if request.method == "OPTIONS" and origin and ALLOWED_ORIGIN_RE.match(origin):
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Requested-With"
            response.headers["Access-Control-Max-Age"] = "86400"
            response.headers["Vary"] = "Origin"
            return response

        response = await call_next(request)

        # Inject CORS headers on all matching origins
        if origin and ALLOWED_ORIGIN_RE.match(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Requested-With"
            response.headers["Vary"] = "Origin"

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
)

# Register dynamic CORS middleware (must be first)
app.add_middleware(DynamicCORSMiddleware)

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
