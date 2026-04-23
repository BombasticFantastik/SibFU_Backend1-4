from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel,Field,ConfigDict,AliasPath
from config import settings
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_filter import FilterDepends
from fastapi_pagination.ext.sqlalchemy import paginate as apaginate
from sqlalchemy.orm import selectinload,joinedload
from models import Cuisine, Allergen, Ingredient, RecipeIngredient,Recipe,db_helper,User
from authentication.schemas.user import (
    UserRead,
    UserUpdate,
)
from authentication import user_manager
from api.cuisine import CuisineRead
from api.allergen import AllergenRead
from typing import Optional, List
from fastapi_filter.contrib.sqlalchemy import Filter
#from authentication.user_manager import current_active_user
from authentication.fastapi_users import current_active_user
from tasks.recipe_tasks import generate_recipe_task

router = APIRouter(
    tags=["Recipe"],
    prefix=settings.url.recipe,
)

class RecipeGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, example="Хочу рецепт пасты с курицей и сливочным соусом")

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_recipe(
    request: RecipeGenerateRequest,
    user: User = Depends(current_active_user),
):
    """
    Эндпоинт для запуска асинхронной генерации рецепта через LLM.
    """
    await generate_recipe_task.kiq(
        prompt=request.prompt, 
        user_id=user.id
    )
    
    return {"status": "Генерация началась"}

class RecipeBase(BaseModel):
  title: str 
  description: str 
  cooking_time: int 
  difficulty: int

#2
class IngredientIn(BaseModel):
    ingredient_id: int
    quantity: int
    measurement: int

class IngredientOut(IngredientIn):
    name: str = Field(validation_alias=AliasPath("ingredient", "name"))

#новый метод
class RecipeRead(RecipeBase):
    id: int
    cuisine: CuisineRead | None = None
    author: UserRead  
    allergens: list[AllergenRead]
    ingredients: list[IngredientOut] = Field(validation_alias='ingredient_associations')
    model_config = ConfigDict(from_attributes=True)

class RecipeCreate(RecipeBase):
    cuisine_id: int
    allergen_ids: list[int]
    ingredients: list[IngredientIn]

from fastapi import Query
from pydantic import field_validator

class RecipeFilter(Filter):
    title__ilike: Optional[str] = Field(default=None)
    ingredient_id: Optional[List[int]] = Field(default=None, alias="ingredient_id")
    
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Recipe
        ordering_model_fields = ["id", "difficulty"]

    @field_validator("ingredient_id", mode="before")
    @classmethod
    def split_str_to_list(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    def filter(self, query):
        data = self.model_dump(exclude={'ingredient_id'})
        
        for field, value in data.items():
            if value is not None and field != 'order_by':
                query = super().filter(query)
                break 

        if self.ingredient_id:
            query = (
                query
                .join(Recipe.ingredient_associations)
                .filter(RecipeIngredient.ingredient_id.in_(self.ingredient_id))
                .distinct()
            )
            
        return query


@router.get("", response_model=Page[RecipeRead]) 
async def get_recipes(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    recipe_filter: RecipeFilter = FilterDepends(RecipeFilter),
):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.author),
            joinedload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredient_associations).joinedload(RecipeIngredient.ingredient)
        )
    )

    stmt = recipe_filter.filter(stmt)
    stmt = recipe_filter.sort(stmt)

    return await apaginate(session, stmt, unique=True)

@router.get("/{id}", response_model=RecipeRead)
async def show(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.author),
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredient_associations).selectinload(RecipeIngredient.ingredient)
        )
        .where(Recipe.id == id)
    )
    result = await session.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def store(
    
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    recipe_create: RecipeCreate,
    user: User = Depends(current_active_user),
):
    recipe = Recipe(
        **recipe_create.model_dump(exclude={'allergen_ids', 'ingredients'}), 
        author_id=user.id,
    )
    
    if recipe_create.allergen_ids:
        allergens = await session.scalars(
            select(Allergen).where(Allergen.id.in_(recipe_create.allergen_ids))
        )
        recipe.allergens = list(allergens.all())
            
    session.add(recipe)
    await session.flush() 

    for ing in recipe_create.ingredients:
        ri = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ing.ingredient_id,
            quantity=ing.quantity,
            measurement=ing.measurement
        )
        session.add(ri)

    await session.commit()
    
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredient_associations).joinedload(RecipeIngredient.ingredient)
        )
        .where(Recipe.id == recipe.id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()

@router.put("/{id}", response_model=RecipeRead)
async def update(
    id: int,
    recipe_update: RecipeCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(current_active_user),
):

    recipe = await session.get(Recipe, id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    if recipe.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not the author of this recipe"
        )

    update_data = recipe_update.model_dump(exclude={'allergen_ids', 'ingredients'})
    for key, value in update_data.items():
        setattr(recipe, key, value)
    
    await session.commit()

    
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.author),
            joinedload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredient_associations).joinedload(RecipeIngredient.ingredient)
        )
        .where(Recipe.id == id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()



@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(current_active_user), # NEW
):
    recipe = await session.get(Recipe, id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    #проверка на автора
    if recipe.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not the author of this recipe"
        )

    await session.delete(recipe)
    await session.commit()
