from sqlalchemy import String, Integer, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

    cars: Mapped[list["Car"]] = relationship(back_populates="owner")


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    body_type: Mapped[str] = mapped_column(String(50), nullable=False)
    production_year: Mapped[int] = mapped_column(Integer, nullable=False)

    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False)
    owner: Mapped["Client"] = relationship(back_populates="cars")

    service_orders: Mapped[list["ServiceOrder"]] = relationship(back_populates="car")


class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    car_id: Mapped[int] = mapped_column(Integer, ForeignKey("cars.id"), nullable=False)
    car: Mapped["Car"] = relationship(back_populates="service_orders")