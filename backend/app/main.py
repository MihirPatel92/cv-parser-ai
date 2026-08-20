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
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "cvs"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "templates"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "outputs"), exist_ok=True)
    await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(title="CV Parser & Formatter API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(conversions.router, prefix="/conversions", tags=["conversions"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
