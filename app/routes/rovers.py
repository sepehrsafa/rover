from fastapi import APIRouter, HTTPException, status, Path
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
from ..utils import (
    db,
    print_grid,
    move,
    turn,
    is_valid_position,
)
from .mines import delete_mine

router = APIRouter(
    tags=["rovers"],
)


async def delete_mine_by_position(position):
    x, y = position
    mine = db.mines.find_one({"x": x, "y": y})
    if mine:
        await delete_mine(mine["id"])


@router.get("/rovers", response_model=List[RoverModel])
async def get_all_rovers():
    rovers = list(db.rovers.find())
    return [RoverModel(**rover) for rover in rovers]


@router.get("/rovers/{rover_id}", response_model=RoverModel)
async def get_rover(rover_id: str = Path(..., title="The ID of the rover to retrieve")):
    try:
        rover_id_int = int(rover_id)  # Convert the ID to integer
    except ValueError:
        raise HTTPException(status_code=400, detail="Rover ID must be an integer")

    rover = db.rovers.find_one({"id": rover_id_int})
    if not rover:
        raise HTTPException(
            status_code=404, detail=f"Rover with id {rover_id} not found"
        )
    return RoverModel(**rover)


@router.post("/rovers", response_model=RoverModel)
async def create_rover(rover_data: RoverCommandModel):
    # Find the highest current rover ID and increment by 1 for the new rover
    latest_rover = db.rovers.find_one(sort=[("id", DESCENDING)])
    next_id = latest_rover["id"] + 1 if latest_rover else 1
    new_rover = {
        "id": next_id,
        "status": "Not Started",
        "position": [0, 0],
        "commands": rover_data.commands,
    }
    db.rovers.insert_one(new_rover)
    new_rover.pop("_id", None)
    return RoverModel(**new_rover)


@router.delete("/rovers/{rover_id}")
async def delete_rover(rover_id: str):
    try:
        # Convert rover_id to int since it is stored as an integer
        rover_id_int = int(rover_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rover ID must be an integer")

    # Delete based on the rover ID, not the MongoDB ObjectId
    result = db.rovers.delete_one({"id": rover_id_int})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404, detail=f"Rover with id {rover_id} not found"
        )
    return {"message": "Rover deleted successfully"}


@router.put("/rovers/{rover_id}", response_model=RoverModel)
async def update_rover_commands(rover_id: int, commands_data: RoverCommandModel):
    # Retrieve the rover document
    rover = db.rovers.find_one({"id": rover_id})
    if not rover:
        raise HTTPException(
            status_code=404, detail=f"Rover with id {rover_id} not found"
        )

    # Check the status of the rover
    if rover["status"] not in ["Not Started", "Finished"]:
        return {"failure": "Rover cannot receive new commands at this status."}

    # Update the rover's commands
    updated_result = db.rovers.update_one(
        {"id": rover_id}, {"$set": {"commands": commands_data.commands}}
    )

    if updated_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update rover commands")

    rover["commands"] = commands_data.commands
    return RoverModel(**rover)


@router.post("/rovers/{rover_id}/dispatch", response_model=RoverModel)
async def dispatch_rover(rover_id: int):
    rover = db.rovers.find_one({"id": rover_id})
    if not rover:
        raise HTTPException(
            status_code=404, detail=f"Rover with id {rover_id} not found"
        )

    commands = rover["commands"]
    original_grid = db.map.find_one()["field"]
    grid = [row[:] for row in original_grid]  # Deep copy of the original grid
    rover_position = [0, 0]
    rover_direction = rover.get("direction", "S")
    status = "Moving"
    executed_commands = ""

    # Initialize a path_grid to visualize the rover's path
    path_grid = [row[:] for row in original_grid]  # Initialize with zeros
    path_grid[rover_position[0]][rover_position[1]] = "*"  # Mark the starting position

    for cmd in commands:
        print_grid(path_grid)  # Print the grid before executing the command
        if cmd == "M":
            next_position = move(rover_direction, rover_position)
            if is_valid_position(next_position, grid):
                if grid[rover_position[0]][rover_position[1]] == 1:
                    status = "Eliminated"
                    break
                else:
                    path_grid[rover_position[0]][
                        rover_position[1]
                    ] = "*"  # Mark the new position
                    rover_position = next_position
        elif cmd == "D":
            if grid[rover_position[0]][rover_position[1]] == 1:
                await delete_mine_by_position(rover_position)
                grid[rover_position[0]][rover_position[1]] = 0
                path_grid[rover_position[0]][
                    rover_position[1]
                ] = "*"  # Mark disarmed mine
        elif cmd in ["R", "L"]:
            rover_direction = turn(rover_direction, cmd)

        executed_commands += cmd

    if status != "Eliminated":
        status = "Finished"

    db.rovers.update_one(
        {"id": rover_id},
        {
            "$set": {
                "position": rover_position,
                "status": status,
                "executed_commands": executed_commands,
            }
        },
    )

    updated_rover_doc = db.rovers.find_one({"id": rover_id})
    if not updated_rover_doc:
        raise HTTPException(
            status_code=404, detail="Rover update failed after dispatch"
        )

    return RoverModel(
        id=updated_rover_doc["id"],
        status=updated_rover_doc["status"],
        position=updated_rover_doc["position"],
        commands=executed_commands,
        grid=path_grid,  # Include the path grid for visualization
    )
