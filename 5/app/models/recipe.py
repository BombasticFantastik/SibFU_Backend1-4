from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ForeignKey
from pydantic import Field,BaseModel
from typing import List
from .base import Base
from enum import Enum
from .ingredient import Ingredient

if TYPE_CHECKING:
    from .cuisine import Cuisine
    from .allergen import Allergen
    from .ingredient import RecipeIngredient
    from .users import User 

class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    cooking_time: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), 
        nullable=False
    )

    author: Mapped["User"] = relationship(back_populates="recipes")

    cuisine_id: Mapped[int] = mapped_column(ForeignKey("cuisines.id"), nullable=True) 
    cuisine: Mapped["Cuisine"] = relationship(back_populates="recipes")

    allergens: Mapped[list["Allergen"]] = relationship(
            secondary="recipe_allergens", 
            back_populates="recipes",
            cascade="all, delete"  
        )

    ingredient_associations: Mapped[list["RecipeIngredient"]] = relationship(
            back_populates="recipe",
            cascade="all, delete-orphan" 
        )
    def __repr__(self):
        return f"Recipe(id={self.id}, title={self.title}, author_id={self.author_id})"
    

class MeasurementUnit(str, Enum):
    GRAMS = "GRAMS"
    PIECES = "PIECES"
    MILLILITERS = "MILLILITERS"


class IngredientGenerationSchema(BaseModel):
    name: str = Field(..., description="Название ингредиента")
    amount: float = Field(..., description="Количество")
    measurement: MeasurementUnit = Field(..., description="Единица измерения")

class RecipeGenerationSchema(BaseModel):
    title: str = Field(..., description="Название блюда")
    description: str = Field(..., description="Краткое описание")
    instructions: str = Field(..., description="Пошаговая инструкция")
    cuisine: str = Field(..., description="Название кухни")
    allergens: List[str] = Field(..., description="Список названий аллергенов")
    ingredients: List[IngredientGenerationSchema]