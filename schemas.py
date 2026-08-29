from pydantic import BaseModel, EmailStr
from typing import Optional

class ClientBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: int

    class Config:
        from_attributes = True

class CarBase(BaseModel):
    brand: str
    model: str
    registration_number: str
    mileage: int
    body_type: str
    production_year: int

class CarCreate(CarBase):
    owner_id: int

class CarResponse(CarBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True