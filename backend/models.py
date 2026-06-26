from pydantic import BaseModel
from typing import List

class Coordinate(BaseModel):
    lat: float
    lng: float

class Environment(BaseModel):
    weather: str
    traffic: str

class WeatherZone(BaseModel):
    type: str
    lat: float
    lng: float
    radius: float

class SimulationPayload(BaseModel):
    origin: Coordinate
    destination: Coordinate
    environment: Environment
    obstacles: List[List[float]] 
    weather_zones: List[WeatherZone] = []
    waypoints: List[Coordinate] = []