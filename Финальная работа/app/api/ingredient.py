from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, status, HTTPException,Query
from models.db_helper import db_helper
from models.ingredient import Ingredient
from pydantic import BaseModel
from sqlalchemy.orm import selectinload,contains_eager,joinedload,load_only
from models.ingredient import RecipeIngredient
from models.recipe import Recipe


router = APIRouter(prefix="/ingredient", tags=["Ingredient"])

class IngredientBase(BaseModel):
    name: str

class IngredientRead(IngredientBase):
    id: int


class IngredientCreate(IngredientBase):
    pass

@router.get("", response_model=list[IngredientRead])
async def get(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    cuisines = select(Ingredient).order_by(Ingredient.id)
    cuisines = await session.scalars(cuisines)
    return cuisines.all()


@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
async def store(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    cuisine_create: IngredientCreate,
):
    cuisine = Ingredient(name=cuisine_create.name)
    session.add(cuisine)
    await session.commit()
    return cuisine


@router.get("/{id}/ingredient", response_model=list[dict]) 
async def get_ingredient(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    post = await session.get(Ingredient, id)
    return post


@router.get("/{ingredient_id}/recipes")
async def get_recipes_by_ingredient(
    ingredient_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    include: Optional[str] = Query(None, description="cuisine,ingredients,allergens"),
    select_fields: Optional[str] = Query(None, alias="select", description="name,difficulty,etc.")
):
    stmt = select(Recipe).join(Recipe.ingredient_associations).where(
        RecipeIngredient.ingredient_id == ingredient_id
    )

    if include:
        include_list = include.split(",")
        if "cuisine" in include_list:
            stmt = stmt.options(joinedload(Recipe.cuisine))
        if "ingredients" in include_list:
            stmt = stmt.options(
                contains_eager(Recipe.ingredient_associations).joinedload(RecipeIngredient.ingredient)
            )
        if "allergens" in include_list:
            stmt = stmt.options(selectinload(Recipe.allergens))

    if select_fields:
        fields = select_fields.split(",")
        try:
            orm_fields = [getattr(Recipe, f.strip()) for f in fields]
            stmt = stmt.options(load_only(*orm_fields))
        except AttributeError:
            raise HTTPException(status_code=400, detail="Invalid fields in select parameter")

    result = await session.execute(stmt)
    recipes = result.unique().scalars().all()
    
    return recipes


@router.get("/{id}/recipes")
async def get_recipes_by_ingredient(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    stmt = (
        select(Recipe)
        .join(Recipe.ingredient_associations)
        .where(RecipeIngredient.ingredient_id == id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            contains_eager(Recipe.ingredient_associations).joinedload(RecipeIngredient.ingredient),
            
        )
    )
    
    result = await session.execute(stmt)
    recipes = result.scalars().unique().all() 
    
    return recipes


@router.put("/{id}", response_model=IngredientRead)
async def update(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    ingredient_update: IngredientCreate,
):
    ingredient = await session.get(Ingredient, id)
    ingredient.title = ingredient_update.title
    await session.commit()
    return ingredient


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    await session.delete(ingredient)
    await session.commit()
