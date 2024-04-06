from typing import List, Optional, Union
from pydantic import BaseModel


class MapModel(BaseModel):
    height: int
    width: int
    field: List[List[int]]


class MineModel(BaseModel):
    id: int
    x: int
    y: int
    serial_number: str


class MinesModel(BaseModel):
    height: int
    width: int
    field: List[List[Union[int, str]]]


class MineCreateModel(BaseModel):
    x: int
    y: int
    serial_number: str


class MineUpdateModel(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    serial_number: Optional[str] = None


class RoverCommandModel(BaseModel):
    commands: str


class RoverModel(BaseModel):
    id: int
    status: str
    position: List[int]
    commands: str
    grid: Optional[List[List[Union[int, str]]]] = None
