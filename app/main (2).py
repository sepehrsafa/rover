from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional, Union, Tuple
from pymongo import DESCENDING, MongoClient
from fastapi import FastAPI, HTTPException, status, Body, Path
import requests
from fastapi.middleware.cors import CORSMiddleware
from .routes import map, mines, rovers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(map.router)
app.include_router(mines.router)
app.include_router(rovers.router)
