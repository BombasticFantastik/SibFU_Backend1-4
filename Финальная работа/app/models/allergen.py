from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Table, Column
from .base import Base

if TYPE_CHECKING:
    from .recipe import Recipe

recipe_allergens_association = Table(
    "recipe_allergens",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id"), primary_key=True),
    Column("allergen_id", ForeignKey("allergens.id"), primary_key=True),
)

class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    recipes: Mapped[list["Recipe"]] = relationship(
        secondary=recipe_allergens_association,
        back_populates="allergens"
    )

    def __repr__(self):
        return f"Allergen(id={self.id}, name={self.name})"