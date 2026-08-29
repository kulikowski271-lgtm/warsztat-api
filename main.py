from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import engine, Base, get_db
import models
import schemas

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

@app.post("/clients", response_model=schemas.ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(client: schemas.ClientCreate, db: AsyncSession = Depends(get_db)):
    new_client = models.Client(
        first_name=client.first_name,
        last_name=client.last_name,
        email=client.email,
        phone=client.phone
    )

    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)

    return new_client