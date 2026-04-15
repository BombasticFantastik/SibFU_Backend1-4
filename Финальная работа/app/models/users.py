from typing import TYPE_CHECKING 
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Integer,String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .recipe import Recipe


class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    first_name: Mapped[str] = mapped_column(String(length=100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(length=100), nullable=True)

    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe", 
        back_populates="author", 
        cascade="all, delete-orphan"
    )