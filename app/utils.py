from pymongo.mongo_client import MongoClient
from pydantic import BaseModel
from typing import List, Union
from .schemas import MineModel
import requests

uri = "mongodb+srv://sepehrsafa:sepehrsafa@cluster0.z4yqm0a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
db = client["Cluster0"]  # use your database name
rovers_collection = db["rovers"]


def get_mines_from_field(mines_field: List[List[Union[int, str]]]) -> List[MineModel]:
    mines = []
    mine_id = 0
    for i, row in enumerate(mines_field):
        for j, value in enumerate(row):
            if isinstance(value, str):  # assuming that serial numbers are strings
                mines.append(MineModel(id=mine_id, x=i, y=j, serial_number=value))
                mine_id += 1
    return mines


def print_grid(grid):
    for row in grid:
        print(" ".join(str(cell) for cell in row))
    print("\n")


def move(direction, position):
    moves = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
    dx, dy = moves[direction]
    return [position[0] + dx, position[1] + dy]


def is_valid_position(position, grid):
    x, y = position
    return 0 <= x < len(grid) and 0 <= y < len(grid[0])


def turn(direction, cmd):
    dirs = "NESW"
    idx = dirs.index(direction)
    if cmd == "R":
        return dirs[(idx + 1) % 4]
    elif cmd == "L":
        return dirs[(idx - 1) % 4]
