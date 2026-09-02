from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ServiceOrderBase(BaseModel):
    description: str
    status: OrderStatus = OrderStatus.PENDING
    total_cost: float = 0.0

class ServiceOrderCreate(ServiceOrderBase):
    car_id: int

class ServiceOrderResponse(ServiceOrderBase):
    id: int
    car_id: int

    class Config:
        from_attributes = True

class ServiceOrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    total_cost: Optional[float] = None

class CarBase(BaseModel):
    brand: str
    model: str
    registration_number: str = Field(..., min_length=2, max_length=15, description="Numer rejestracyjny")
    mileage: int = Field(..., ge=0, description="Przebieg nie może być ujemny")
    body_type: str
    production_year: int = Field(..., ge=1900, le=2026, description="Prawidłowy rok produkcji")

    @field_validator("registration_number")
    @classmethod
    def clean_registration_number(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Numer rejestracyjny nie może być pusty")
        return cleaned

class CarCreate(CarBase):
    owner_id: int

class CarResponse(CarBase):
    id: int
    owner_id: int
    owner: Optional["ClientBase"] = None

    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: int
    cars: List[CarResponse] = []

    class Config:
        from_attributes = True