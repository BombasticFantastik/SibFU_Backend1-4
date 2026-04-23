from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from config import settings

# from .test import router as test_router
# from .posts import router as posts_router


from .recipe import router as recipe_router
from .cuisine import router as cuisine_router
from .ingredient import router as ingredient_router
from .allergen import router as allergen_router
from .users import router as users_router
from .auth import router as auth_router

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix=settings.url.prefix,
    dependencies=[Depends(http_bearer)],
)
router.include_router(recipe_router)
router.include_router(cuisine_router)
router.include_router(ingredient_router)
router.include_router(allergen_router)
router.include_router(users_router)
router.include_router(auth_router)
