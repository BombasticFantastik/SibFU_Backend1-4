from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ForeignKey

from .base import Base

if TYPE_CHECKING:
    from .cuisine import Cuisine
    from .allergen import Allergen
    from .ingredient import RecipeIngredient
    from .users import User 

# class Recipe(Base):
#     __tablename__ = "recipes"

#     id: Mapped[int] = mapped_column(primary_key=True)
#     title: Mapped[str] = mapped_column(String(255))
#     description: Mapped[str] = mapped_column(Text)
#     cooking_time: Mapped[int] = mapped_column(Integer)
#     difficulty: Mapped[int] = mapped_column(Integer, default=1)
#     author_id: Mapped[int] = mapped_column(
#         ForeignKey("user.id", ondelete="CASCADE"), 
#         nullable=False
#     )

#     author: Mapped["User"] = relationship(back_populates="recipes")

#     cuisine_id: Mapped[int] = mapped_column(ForeignKey("cuisines.id"), nullable=True) 
#     cuisine: Mapped["Cuisine"] = relationship(back_populates="recipes")

#     allergens: Mapped[list["Allergen"]] = relationship(
#         secondary="recipe_allergens", 
#         back_populates="recipes"
#     )

#     ingredient_associations: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe")

#     def __repr__(self):
#         return f"Recipe(id={self.id}, title={self.title}, author_id={self.author_id})"
    

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