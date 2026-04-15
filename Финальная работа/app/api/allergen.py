from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from models.db_helper import db_helper
from models.allergen import Allergen
from pydantic import BaseModel,ConfigDict


router = APIRouter(prefix="/allergen", tags=["Allergen"])


class AllergenBase(BaseModel):
    name: str
    

class AllergenRead(AllergenBase):
    name: str
    id: int
    model_config = ConfigDict(from_attributes=True)

class AllergenCreate(AllergenBase):
    name: str

@router.get("", response_model=list[AllergenRead])
async def get_allergens(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    stmt = select(Allergen).order_by(Allergen.id)
    result = await session.scalars(stmt)
    return result.all()


@router.post("", response_model=AllergenRead, status_code=status.HTTP_201_CREATED)
async def create_allergen(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    allergen_in: AllergenCreate,
):
    allergen = Allergen(name=allergen_in.name)
    session.add(allergen)
    await session.commit()
    await session.refresh(allergen) 
    return allergen

@router.get("/{id}", response_model=AllergenRead) 
async def get_allergen(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(status_code=404, detail="Allergen not found")
    return allergen





@router.put("/{id}", response_model=AllergenRead)
async def update(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
    allergen_update: AllergenCreate,
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Allergen with id {id} not found"
        )
    allergen.name = allergen_update.name 
    
    await session.commit()
    await session.refresh(allergen) 
    return allergen


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Allergen with id {id} not found" 
        )

    await session.delete(allergen)
    await session.commit()
    