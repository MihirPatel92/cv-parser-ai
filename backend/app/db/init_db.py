import asyncio
from sqlalchemy.future import select
from .database import engine, Base, SessionLocal
from .models import User, AIModelConfig
from ..core.security import hash_password
from ..core.config import settings


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # ── Seed Super Admin ──────────────────────────────────────────────────
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

        # ── Seed AI Config ────────────────────────────────────────────────────
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

        await session.commit()
