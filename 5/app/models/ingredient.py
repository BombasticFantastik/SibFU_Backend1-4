from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer
from .base import Base
from .enum import MeasurementEnum

if TYPE_CHECKING:
    from .recipe import Recipe

class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    recipe_associations: Mapped[list["RecipeIngredient"]] = relationship(back_populates="ingredient")

    def __repr__(self):
        return f"Ingredient(id={self.id}, name={self.name})"

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    measurement: Mapped[MeasurementEnum] = mapped_column(Integer, nullable=False)

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredient_associations")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_associations")

    def __repr__(self):
        return f"RecipeIngredient(recipe_id={self.recipe_id}, ingredient_id={self.ingredient_id})"