from fastapi import FastAPI
from database import engine, Base
import models

app = FastAPI(title="Warsztat samochodowy API")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def home():
    return {"status": "online", "message": "Witaj w API Warsztatu!"}

@app.get("/api/v1/health")
def health_check():
    return {"database": "ok", "server": "ok"}