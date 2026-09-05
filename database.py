"""Konfiguracja połączenia z bazą danych PostgreSQL i sesji SQLAlchemy."""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Brak zmiennej środowiskowej DATABASE_URL. "
        "Ustaw ją w pliku .env (patrz .env.example)."
    )

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

engine = create_async_engine(DATABASE_URL, echo=DEBUG)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
class Base(DeclarativeBase):
    #Bazowa klasa dla wszystkich modeli ORM.
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
