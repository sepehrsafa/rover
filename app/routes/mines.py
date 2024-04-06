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

router = APIRouter(
    tags=["mines"],
)


@router.get("/mines", response_model=List[MineModel])
async def get_all_mines():
    mines_collection = db.get_collection("mines")
    mines_documents = list(mines_collection.find({}))
    return [MineModel(**mine) for mine in mines_documents]


@router.get("/mines/{mine_id}", response_model=MineModel)
async def get_mine(mine_id: int):
    mines_collection = db.get_collection("mines")
    mine_document = mines_collection.find_one({"id": mine_id})
    if not mine_document:
        raise HTTPException(status_code=404, detail=f"Mine with id {mine_id} not found")
    return MineModel(**mine_document)


# Endpoint to create a mine and update the map collection
@router.post("/mines", response_model=MineModel)
async def create_mine(mine_data: MineCreateModel):
    # Validate the position is within the bounds of the map
    map_collection = db.get_collection("map")
    map_document = map_collection.find_one()
    if mine_data.x >= map_document["height"] or mine_data.y >= map_document["width"]:
        raise HTTPException(status_code=400, detail="Position out of bounds")

    # Check if a mine already exists at the given coordinates
    if map_document["field"][mine_data.x][mine_data.y] != 0:
        raise HTTPException(
            status_code=400, detail="A mine already exists at the provided coordinates"
        )

    # Add the mine to the 'map' collection
    map_collection.update_one(
        {"_id": map_document["_id"]},
        {"$set": {f"field.{mine_data.x}.{mine_data.y}": 1}},
    )

    # Add the mine to the 'minesField' collection
    mines_field_collection = db.get_collection("minesField")
    mines_field_document = mines_field_collection.find_one()
    if not mines_field_document:
        raise HTTPException(status_code=404, detail="minesField document not found")

    # Verify that the array structure exists before updating
    if len(mines_field_document["field"]) > mine_data.x:
        if len(mines_field_document["field"][mine_data.x]) > mine_data.y:
            mines_field_collection.update_one(
                {"_id": mines_field_document["_id"]},
                {
                    "$set": {
                        f"field.{mine_data.x}.{mine_data.y}": mine_data.serial_number
                    }
                },
            )
        else:
            raise HTTPException(
                status_code=400, detail="Array index out of bounds on y-axis"
            )
    else:
        raise HTTPException(
            status_code=400, detail="Array index out of bounds on x-axis"
        )

    # Create a new mine document in the 'mines' collection
    # Create a new mine document in the 'mines' collection
    mines_collection = db.get_collection("mines")

    # Find the highest existing id and increment it by one for the new mine
    # If there are no mines in the collection, start with id 1
    max_id_document = mines_collection.find_one(
        sort=[("id", -1)]
    )  # This finds the document with the highest 'id'
    if max_id_document:
        mine_id = max_id_document["id"] + 1
    else:
        mine_id = 1

    new_mine = {
        "id": mine_id,
        "x": mine_data.x,
        "y": mine_data.y,
        "serial_number": mine_data.serial_number,
    }
    mines_collection.insert_one(new_mine)
    return MineModel(**new_mine)


@router.put("/mines/{mine_id}", response_model=MineModel)
async def update_mine(mine_id: int, mine_data: MineUpdateModel):
    # Retrieve the mine from the 'mines' collection
    mines_collection = db.get_collection("mines")
    mine_document = mines_collection.find_one({"id": mine_id})
    if not mine_document:
        raise HTTPException(status_code=404, detail="Mine not found")

    map_collection = db.get_collection("map")
    map_document = map_collection.find_one()
    mines_field_collection = db.get_collection("minesField")
    mines_field_document = mines_field_collection.find_one()

    # Validate new position if provided
    if mine_data.x is not None and mine_data.y is not None:
        if (
            mine_data.x >= map_document["height"]
            or mine_data.y >= map_document["width"]
        ):
            raise HTTPException(status_code=400, detail="New position out of bounds")

        # Check if new position is not already occupied
        if map_document["field"][mine_data.x][mine_data.y] == 1:
            raise HTTPException(
                status_code=400,
                detail="New position is already occupied by another mine",
            )

        # Update the map and minesField to remove the mine from the old position
        map_document["field"][mine_document["x"]][mine_document["y"]] = 0
        mines_field_document["field"][mine_document["x"]][mine_document["y"]] = 0
        map_collection.update_one(
            {"_id": map_document["_id"]}, {"$set": {"field": map_document["field"]}}
        )
        mines_field_collection.update_one(
            {"_id": mines_field_document["_id"]},
            {"$set": {f"field.{mine_document['x']}.{mine_document['y']}": 0}},
        )

        # Update the mine's new position
        mine_document["x"] = mine_data.x
        mine_document["y"] = mine_data.y

    # Update serial number if provided
    if mine_data.serial_number:
        mine_document["serial_number"] = mine_data.serial_number

    # Update the mines collection with new data
    mines_collection.update_one({"id": mine_id}, {"$set": mine_document})

    # Set the new mine location and serial number in the map and minesField
    map_document["field"][mine_document["x"]][mine_document["y"]] = 1
    mines_field_document["field"][mine_document["x"]][mine_document["y"]] = (
        mine_document["serial_number"]
    )
    map_collection.update_one(
        {"_id": map_document["_id"]}, {"$set": {"field": map_document["field"]}}
    )
    mines_field_collection.update_one(
        {"_id": mines_field_document["_id"]},
        {
            "$set": {
                f"field.{mine_document['x']}.{mine_document['y']}": mine_document[
                    "serial_number"
                ]
            }
        },
    )

    # Return the full updated mine object
    return MineModel(**mine_document)


# Endpoint to delete a mine and update the map collection
@router.delete("/mines/{mine_id}", response_model=dict)
async def delete_mine(mine_id: int):
    # Retrieve the mine from the 'mines' collection
    mines_collection = db.get_collection("mines")
    mine_document = mines_collection.find_one({"id": mine_id})
    if not mine_document:
        raise HTTPException(status_code=404, detail="Mine not found")

    # Update 'map' and 'minesField' collections to remove the mine
    map_collection = db.get_collection("map")
    map_document = map_collection.find_one()
    map_document["field"][mine_document["x"]][mine_document["y"]] = 0
    map_collection.update_one(
        {"_id": map_document["_id"]}, {"$set": {"field": map_document["field"]}}
    )

    mines_field_collection = db.get_collection("minesField")
    # Set the corresponding position in minesField to 0, denoting removal of the mine
    mines_field_update_query = {
        f"field.{mine_document['x']}.{mine_document['y']}": mine_document[
            "serial_number"
        ]
    }
    mines_field_update_action = {
        "$set": {f"field.{mine_document['x']}.{mine_document['y']}": 0}
    }
    mines_field_collection.update_one(
        mines_field_update_query, mines_field_update_action
    )

    # Delete the mine from the 'mines' collection
    result = mines_collection.delete_one({"id": mine_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mine not found")

    return {"message": "Mine deleted successfully"}
