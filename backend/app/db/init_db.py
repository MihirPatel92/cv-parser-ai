import asyncio
from sqlalchemy import text
from sqlalchemy.future import select
from .database import engine, Base, SessionLocal
from .models import User, AIModelConfig
from ..core.security import hash_password
from ..core.config import settings


async def init_db():
    # ── Create tables and apply auto-migrations ────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Ensure newly added columns exist in existing database tables
        migration_statements = [
            "ALTER TABLE cv_templates ADD COLUMN IF NOT EXISTS file_data TEXT;",
            "ALTER TABLE cv_templates ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT;",
            "ALTER TABLE cv_templates ADD COLUMN IF NOT EXISTS file_name VARCHAR(255) DEFAULT 'template.docx';",
            "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS source_cv_data TEXT;",
            "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS output_docx_data TEXT;",
            "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS output_pdf_data TEXT;",
            "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS processing_time_seconds FLOAT;",
            "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS error_message TEXT;",
        ]
        for stmt in migration_statements:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                print(f"Migration statement note: {stmt} -> {e}")

    async with SessionLocal() as session:
        # ── Seed Super Admin ──────────────────────────────────────────────────
        try:
            result = await session.execute(select(User).where(User.email == "admin@cvparser.com"))
            admin = result.scalars().first()

            if not admin:
                new_admin = User(
                    email="admin@cvparser.com",
                    full_name="Super Administrator",
                    hashed_password=hash_password("Admin@123"),
                    role="super_admin",
                    is_active=True,
                )
                session.add(new_admin)
                print("✅ Seeded Super Admin: admin@cvparser.com / Admin@123")
        except Exception as e:
            print(f"Seed Super Admin note: {e}")

        # ── Seed AI Config ────────────────────────────────────────────────────
        try:
            config_result = await session.execute(select(AIModelConfig))
            config = config_result.scalars().first()

            if not config:
                new_config = AIModelConfig(
                    provider="gemini",
                    model_name="gemini-1.5-flash",
                    api_key_encrypted=settings.GEMINI_API_KEY,
                    ollama_base_url=settings.OLLAMA_BASE_URL,
                    temperature=0.1,
                    max_tokens=4096,
                    is_active=True,
                )
                session.add(new_config)
                print("✅ Seeded default AI config: Gemini gemini-1.5-flash")
        except Exception as e:
            print(f"Seed AI Config note: {e}")

        await session.commit()
