from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from models import db_helper, Post,Cuisine
from pydantic import BaseModel,ConfigDict
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(
    tags=["Cuisine"],
    prefix=settings.url.cuisine,
)

class CuisineBase(BaseModel):
    name:str


class CuisineRead(CuisineBase):
    id: int
    name: str
    model_config=ConfigDict(from_attributes=True)


class CuisineCreate(CuisineBase):
    pass

@router.get("", response_model=list[CuisineRead])
async def get(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    cuisines = select(Cuisine).order_by(Cuisine.id)
    cuisines = await session.scalars(cuisines)
    return cuisines.all()


@router.post("", response_model=CuisineRead, status_code=status.HTTP_201_CREATED)
async def store(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    cuisine_create: CuisineCreate,
):
    cuisine = Cuisine(name=cuisine_create.name) 
    session.add(cuisine)
    await session.commit()
    await session.refresh(cuisine)
    return cuisine

@router.get("/{id}", response_model=CuisineRead)
async def show(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Cuisine not found")
    return cuisine




@router.put("/{id}", response_model=CuisineRead)
async def update(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id: int,
    cuisine_update: CuisineCreate,
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Cuisine not found")
    
    cuisine.name = cuisine_update.name 
    await session.commit()
    await session.refresh(cuisine)
    return cuisine


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Cuisine with id {id} not found"
        )

    await session.delete(cuisine)
    await session.commit()



