from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

import models
import schemas
from database import engine, Base, get_db
from auth import hash_password, verify_password, create_access_token, get_current_user


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

    if client.email:
        clean_email = client.email.strip().lower()
        existing_email = await db.execute(
            select(models.Client).where(models.Client.email == clean_email)
        )
        if existing_email.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Klient z adresem email {clean_email} już istnieje w bazie."
            )
    else:
        clean_email = None

    new_client = models.Client(
        first_name=client.first_name,
        last_name=client.last_name,
        email=clean_email,
        phone=client.phone
    )

    db.add(new_client)
    await db.commit()

    result = await db.execute(
        select(models.Client)
        .options(selectinload(models.Client.cars))
        .where(models.Client.id == new_client.id)
    )
    return result.scalar_one()

@app.get("/clients", response_model=List[schemas.ClientResponse])
async def get_clients(db: AsyncSession = Depends(get_db)):
    results = await db.execute(
        select(models.Client).options(selectinload(models.Client.cars))
    )
    clients = results.scalars().all()
    return clients

@app.get("/clients/{client_id}", response_model=schemas.ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Client)
        .options(selectinload(models.Client.cars))
        .where(models.Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Klient o id {client_id} nie został znaleziony.",
        )

    return client

@app.post("/cars", response_model=schemas.CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(car: schemas.CarCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Client).where(models.Client.id == car.owner_id))
    client = result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Klient o id {car.owner_id} nie istnieje."
        )

    formatted_reg = car.registration_number.strip().upper()

    result_car = await db.execute(
        select(models.Car).where(models.Car.registration_number == formatted_reg)
    )
    existing_car = result_car.scalar_one_or_none()

    if existing_car is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Samochód o numerze rejestracyjnym '{formatted_reg}' jest już w bazie.",

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

    result = await db.execute(
        select(models.Car)
        .options(selectinload(models.Car.owner))
        .where(models.Car.id == new_car.id)
    )
    return result.scalar_one()

@app.get("/cars", response_model=List[schemas.CarResponse])
async def get_cars(
    brand: Optional[str] = Query(None, description="Filtruj po marce (np. BMW)"),
    model: Optional[str] = Query(None, description="Filtruj po modelu (np. M3)"),
    owner_id: Optional[int] = Query(None, description="Filtruj po ID właściciela"),
    limit: int = Query(10, ge=1, le=100, description="Liczba rekordów na stronę (1-100)"),
    offset: int = Query(0, ge=0, description="Liczba pomijanych rekordów"),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Car)

    if brand:
        query = query.where(models.Car.brand.ilike(f"%{brand.strip()}%"))
    if model:
        query = query.where(models.Car.model.ilike(f"%{model.strip()}%"))
    if owner_id is not None:
        query = query.where(models.Car.owner_id == owner_id)

    query = query.offset(offset).limit(limit)

    results = await db.execute(query)
    return results.scalars().all()

@app.get("/cars/{car_id}", response_model=schemas.CarResponse)
async def get_car(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Car)
        .options(selectinload(models.Car.owner))
        .where(models.Car.id == car_id)
    )
    car = result.scalar_one_or_none()

    if car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Samochód o id {car_id} nie został znaleziony."
        )

    return car

@app.delete("/cars/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Car).where(models.Car.id == car_id))
    car = result.scalar_one_or_none()

    if car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"samochód o id {car_id} nie został znaleziony."
        )
    await db.delete(car)
    await db.commit()
    return None

@app.post("/orders", response_model=schemas.ServiceOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: schemas.ServiceOrderCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Car).where(models.Car.id == order.car_id))
    car = result.scalar_one_or_none()

    if car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Samochód o id {order.car_id} nie istnieje."
        )

    new_order = models.ServiceOrder(
        description=order.description,
        status=order.status.value,
        total_cost=order.total_cost,
        car_id=order.car_id
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    return new_order

@app.get("/orders", response_model=List[schemas.ServiceOrderResponse])
async def get_orders(
    status: Optional[schemas.OrderStatus] = Query(None, description="Filtruj po statusie"),
    car_id: Optional[int] = Query(None, description="Filtruj po ID samochodu"),
    min_cost: Optional[float] = Query(None, ge=0, description="Minimalny koszt zlecenia"),
    max_cost: Optional[float] = Query(None, ge=0, description="Maksymalny koszt zlecenia"),
    limit: int = Query(10, ge=1, le=100, description="Liczba rekordów na stronę (1-100)"),
    offset: int = Query(0, ge=0, description="Liczba pomijanych rekordów"),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.ServiceOrder)

    if status is not None:
        query = query.where(models.ServiceOrder.status == status.value)
    if car_id is not None:
        query = query.where(models.ServiceOrder.car_id == car_id)
    if min_cost is not None:
        query = query.where(models.ServiceOrder.total_cost >= min_cost)
    if max_cost is not None:
        query = query.where(models.ServiceOrder.total_cost <= max_cost)

    query = query.offset(offset).limit(limit)

    results = await db.execute(query)
    return results.scalars().all()


@app.get("/orders/{order_id}", response_model=schemas.ServiceOrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ServiceOrder).where(models.ServiceOrder.id == order_id))
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zlecenie o id {order_id} nie zostało znalezione."
        )

    return order

@app.patch("/orders/{order_id}", response_model=schemas.ServiceOrderResponse)
async def update_order(
        order_id: int,
        order_update: schemas.ServiceOrderUpdate,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.ServiceOrder).where(models.ServiceOrder.id == order_id))
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zlecenie o id {order_id} nie zostało znalezione."
        )

    if order_update.status is not None:
        order.status = order_update.status.value

    if order_update.total_cost is not None:
        order.total_cost = order_update.total_cost

    await db.commit()
    await db.refresh(order)

    return order

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik o podanym adresie email już istnieje."
        )

    new_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawny email lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )

    acces_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": acces_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
