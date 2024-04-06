from fastapi import APIRouter, HTTPException, status
from typing import List
from pymongo import DESCENDING
from ..schemas import (
    MapModel,
    MineModel,
    MinesModel,
    MineCreateModel,
    MineUpdateModel,
    RoverCommandModel,
    RoverModel,
)
from ..utils import db
from bson import ObjectId

router = APIRouter(
    tags=["map"],
)


@router.get("/map", response_model=MapModel)
async def get_map():
    map_document = db.map.find_one({"_id": ObjectId("6611b1aafb651aa34ab379b0")})
    if map_document:
        return MapModel(**map_document)
    else:
        raise HTTPException(status_code=404, detail="Map not found")


@router.put("/map", response_model=MapModel, status_code=status.HTTP_202_ACCEPTED)
def update_map(map_data: MapModel):
    map_collection = db.get_collection("map")
    mines_collection = db.get_collection("minesField")

    existing_map = map_collection.find_one()
    existing_mines = mines_collection.find_one()

    if existing_map is None or existing_mines is None:
        raise HTTPException(status_code=404, detail="Map or minesField not found")

    # Resize the map field
    new_map_field = [[0 for _ in range(map_data.width)] for _ in range(map_data.height)]
    new_mines_field = [
        [0 for _ in range(map_data.width)] for _ in range(map_data.height)
    ]

    # Copy and truncate the existing fields if needed
    for i in range(min(existing_map["height"], map_data.height)):
        for j in range(min(existing_map["width"], map_data.width)):
            new_map_field[i][j] = existing_map["field"][i][j]
            new_mines_field[i][j] = existing_mines["field"][i][j]

    # Update the map and minesField collections with the new fields
    map_collection.update_one(
        {},
        {
            "$set": {
                "height": map_data.height,
                "width": map_data.width,
                "field": new_map_field,
            }
        },
    )
    mines_collection.update_one(
        {},
        {
            "$set": {
                "height": map_data.height,
                "width": map_data.width,
                "field": new_mines_field,
            }
        },
    )

    return {"height": map_data.height, "width": map_data.width, "field": new_map_field}
