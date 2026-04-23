from pydantic import BaseModel
from typing import Annotated
import shutil

from fastapi.responses import JSONResponse

from fastapi import (
    APIRouter,Query,Path,Form,UploadFile,
)

from config import settings

router = APIRouter(
    tags=["Test"],
    prefix=settings.url.test,
)

class SomeItem(BaseModel):
    name:str
    description: str | None=None
    price: float
    tax: float | None=None
    tags: list=[]

class FormData(BaseModel):
    username:str
    password:str


@router.get('/items/')
async def read_items(q: Annotated[str | None, Query(max_lenght=50)]=None):
    result={'items': [{'item_id':"Foo"},{'item_id':'Bar'}]}
    if q:
        result.update({"q":q})
    return result

@router.get('/items/{item_id}')
async def read_items(
    item_id: Annotated[int,Path(title='Id некоторого предмета для получения')],
    q: Annotated[str | None,Query(alias='item-query')]=None):
    result={'item_id':item_id}
    if q:
        result.update({'q':q})
    return result

# @router.post("/login/")
# async def login(username:Annotated[str,Form()],password:Annotated[str,Form()]): ---предварительный вариант, ниже более актуальный
#     return {'username':username}

@router.post("/login/")
async def login(data:Annotated[FormData,Form()]):
    return data.username

@router.post("")
async def create_item(item:SomeItem):
    return item

@router.get("")
def index():
    return {"message": "Привет, как тебе мой бэк ?"}

@router.get('/banned_users')
async def read_banned_users(format:str):
    if format=='json':
        return {'username':'хакер хакерович',
                'username':'токсич токсикович'}
    
    elif format=='html':
        
        return"""
            <html>
                <head>
                </head>
                <body>
                    <h3>Список нехороших типов</h3>
                    <p>хакер хакерович</p>
                    <p>токсич токсикович</p>
                </body>
            </html>
            """
    
    else:
        return 'введёт неправельный формат в поле format. Он должен иметь одно из следующих значения - {json,html}'

@router.put("/items/{item_id}")
async def update_item(item_id:int,item:SomeItem):
    result={'item_id':item_id,'item':item}
    return result

# @router.post('/upload_img')
# async def upload_img(file:UploadFile):
#     return JSONResponse({"url": f'images/{file.filename}'})
#     #return result

import os


    
@router.post('/upload_img')
async def upload_img(file:UploadFile):
    try:
        file_path = f'static/images/{file.filename}'
        print(os.getcwd())
        with open(file_path, "wb") as f:
                f.write(file.file.read())
        #return {"message": "File saved successfully"}
        return {"url": f'/static/images/{file.filename}'}
    except Exception as e:
        return {"message": e.args}