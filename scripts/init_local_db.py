import asyncio
import sys
import os
sys.path.append(os.getcwd())

from backend.models.base import engine, Base
from backend.models.claim import Claim, AnalysisResult
from backend.models.user import User

async def init_db():
    print("Initializing local SQLite database...")
    async with engine.begin() as conn:
        # We drop and recreate for a clean local testing state if needed,
        # but here we'll just create what's missing.
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialization complete: veridian.db created.")

if __name__ == "__main__":
    asyncio.run(init_db())
