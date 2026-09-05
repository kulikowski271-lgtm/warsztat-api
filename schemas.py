"""Schematy Pydantic do walidacji żądań i serializacji odpowiedzi."""

from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

class OrderStatus(str, Enum):
    #Możliwe statusy zlecenia serwisowego.
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ServiceOrderBase(BaseModel):
    #Wspólne pola zlecenia serwisowego.
    description: str
    status: OrderStatus = OrderStatus.PENDING
    total_cost: float = Field(
        0.0,
        ge=0,
        description="koszt nie może być ujemny"
    )

    @field_validator("total_cost")
    @classmethod
    def round_total_cost(cls, v: float) -> float:
        #Zaokrągla koszt do dwóch miejsc po przecinku.
        return round(v, 2)

class ServiceOrderCreate(ServiceOrderBase):
    #Żądanie utworzenia zlecenia serwisowego.
    car_id: int

class ServiceOrderResponse(ServiceOrderBase):
    #Odpowiedź API z danymi zlecenia serwisowego.
    id: int
    car_id: int

    class Config:
        from_attributes = True

class ServiceOrderUpdate(BaseModel):
    #Częściowa aktualizacja zlecenia (PATCH) - wszystkie pola opcjonalne.
    description: Optional[str] = None
    status: Optional[OrderStatus] = None
    total_cost: float = Field(
        None,
        ge=0,
        description="Koszt nie może być ujemny"
    )

class CarBase(BaseModel):
    #Wspólne pola pojazdu.
    brand: str
    model: str
    registration_number: str = Field(..., min_length=2, max_length=15, description="Numer rejestracyjny")
    mileage: int = Field(..., ge=0, description="Przebieg nie może być ujemny")
    body_type: str
    production_year: int = Field(..., ge=1900, description="Prawidłowy rok produkcji")

    @field_validator("registration_number")
    @classmethod
    def clean_registration_number(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Numer rejestracyjny nie może być pusty")
        return cleaned

    @field_validator("production_year")
    @classmethod
    def validate_production_year(cls, v: str) -> int:
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError(f"Rok produkcji nie może być większy niż bieżący rok ({current_year})")
        return v

class CarCreate(CarBase):
    #Żądanie utworzenia pojazdu.
    owner_id: int

class CarResponse(CarBase):
    #Odpowiedź API z danymi pojazdu i właściciela.
    id: int
    owner_id: int
    owner: Optional["ClientBase"] = None

    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    #Wspólne pola klienta.
    first_name: str
    last_name: str
    phone: str
    email: EmailStr

class ClientCreate(ClientBase):
    #Żądanie utworzenia klienta.
    pass

class ClientResponse(ClientBase):
    #Odpowiedź API z danymi klienta i jego pojazdami.
    id: int
    cars: List[CarResponse] = []

    class Config:
        from_attributes = True

class UserRole(str, Enum):
    #Dostępne role użytkowników.
    ADMIN = "ADMIN"
    MECHANIC = "MECHANIC"

class UserRoleUpdate(BaseModel):
    #Żądanie zmiany roli użytkownika (wymaga ADMIN).
    role: UserRole

class UserCreate(BaseModel):
    #Żądanie rejestracji
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    #Odpowiedź API z danymi użytkownika
    id: int
    email: str
    is_active: bool
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    #Odpowiedź API po udanym logowaniu.
    access_token: str
    token_type: str

class TokenData(BaseModel):
    #Dane zakodowane wewnątrz tokenu JWT.
    email: Optional[str] = None
    role: Optional[str] = None