from openai import AsyncOpenAI
from config import settings
from task_queue.taskiq_broker import broker
from models import db_helper, Recipe, Cuisine, Allergen, Ingredient, RecipeIngredient
from models.recipe import RecipeGenerationSchema # Твоя Pydantic схема
from sqlalchemy import select

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.api.router_key, # Исправлено
)

@broker.task(task_retry=3)
async def generate_recipe_task(prompt: str, user_id: int):
    # 1. Запрос к LLM
    response = await client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=[{"role": "user", "content": prompt}],
        response_format={
            "type": "json_schema", 
            "json_schema": {
                "name": "recipe_schema",
                "schema": RecipeGenerationSchema.model_json_schema()
            }
        }
    )
    
    # 2. Валидация данных через Pydantic
    recipe_data = RecipeGenerationSchema.model_validate_json(response.choices[0].message.content)

    # 3. Работа с БД
    async with db_helper.session_factory() as session:
        # Логика Cuisine
        res = await session.execute(select(Cuisine).where(Cuisine.name == recipe_data.cuisine))
        cuisine = res.scalar_one_or_none()
        if not cuisine:
            cuisine = Cuisine(name=recipe_data.cuisine)
            session.add(cuisine)
            await session.flush()

        # Создаем Recipe
        new_recipe = Recipe(
            title=recipe_data.title,
            description=recipe_data.description,
            cooking_time=recipe_data.cooking_time,
            difficulty=recipe_data.difficulty,
            author_id=user_id,
            cuisine_id=cuisine.id
        )
        session.add(new_recipe)
        await session.flush()

        # Аллергены
        for allergen_name in recipe_data.allergens:
            res = await session.execute(select(Allergen).where(Allergen.name == allergen_name))
            allergen = res.scalar_one_or_none()
            if not allergen:
                allergen = Allergen(name=allergen_name)
                session.add(allergen)
                await session.flush()
            new_recipe.allergens.append(allergen)

        # Ингредиенты
        for ing in recipe_data.ingredients:
            res = await session.execute(select(Ingredient).where(Ingredient.name == ing.name))
            db_ingredient = res.scalar_one_or_none()
            if not db_ingredient:
                db_ingredient = Ingredient(name=ing.name)
                session.add(db_ingredient)
                await session.flush()
            
            ri = RecipeIngredient(
                recipe_id=new_recipe.id,
                ingredient_id=db_ingredient.id,
                quantity=ing.amount,
                measurement=ing.measurement.value # Обязательно .value если это Enum
            )
            session.add(ri)

        await session.commit()