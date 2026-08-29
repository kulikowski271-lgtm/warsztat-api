from typing import List
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

@app.get("/clients", response_model=List[schemas.ClientResponse])
async def get_clients(db: AsyncSession = Depends(get_db)):
    results = await db.execute(select(models.Client))
    clients = results.scalars().all()
    return clients

@app.get("/clients/{client_id}", response_model=schemas.ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == client_id))
    client = result.scalars().one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Klient o id {client_id} nie został znaleziony.",
        )

    return client

@app.post("/cars", response_model=schemas.CarsResponse, status_code=status.HTTP_201_CREATED)
async def create_car(car: schemas.CarCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == car.owner_id))
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Klient o id {car.owner_id} nie istnieje."
        )

    new_car = models.Car(
        brand=car.brand,
        model=car.model,
        registration_number=car.registration_number,
        mileage=car.mileage,
        body_type=car.body_type,
        production_year=car.production_year,
        owner_id=car.owner_id,
    )

    db.add(new_car)
    await db.commit()
    await db.refresh(new_car)

    return new_car

@app.get("/cars", response_model=List[schemas.CarResponse])
async def get_cars(db: AsyncSession = Depends(get_db)):
    results = await db.execute(select(models.Car))
    cars = results.scalars().all()
    return cars

