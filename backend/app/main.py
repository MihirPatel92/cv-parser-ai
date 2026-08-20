import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .core.config import settings
from .db.init_db import init_db
from .api import auth, users, templates, conversions, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    # Create upload directories (use /tmp on Render free tier)
    for sub in ["cvs", "templates", "outputs"]:
        os.makedirs(os.path.join(settings.UPLOAD_DIR, sub), exist_ok=True)

    await init_db()
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────


app = FastAPI(
    title="CV Parser & Formatter API",
    description="AI-powered CV transformation engine with multi-LLM support",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow local dev + Render production frontend + any onrender.com subdomain
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://cv-parser-frontend.onrender.com",
    # Also allow any onrender.com subdomain in case name differs
    "https://*.onrender.com",
]

# Add FRONTEND_URL from env if set (most reliable for production)
frontend_url = os.environ.get("FRONTEND_URL", "")
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",  # Allow ALL onrender.com subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploads) ────────────────────────────────────────────────────
# Only mount if the uploads dir exists (it's created at startup)
uploads_dir = settings.UPLOAD_DIR
if os.path.exists(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(templates.router, prefix="/templates", tags=["Templates"])
app.include_router(conversions.router, prefix="/conversions", tags=["Conversions"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "CV Parser API is running. Visit /docs for Swagger UI."}
