from datetime import date, datetime
from pydantic import BaseModel, Json
from typing import List, Optional
from app.sql.models import Base


class Event(BaseModel):
    id: str
    game_id: str
    team_id: str
    coordinate_x: Optional[float]
    coordinate_y: Optional[float]
    player_id: Optional[str]
    event_type: str
    event_data_json: Json
    sequence: int

    class Config:
        orm_mode = True


class Player(BaseModel):
    id: str
    audl_id: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class Team(BaseModel):
    id: str
    audl_id: str
    division: int
    city: str
    name: str
    abbreviation: str

    class Config:
        orm_mode = True


class Roster(BaseModel):
    game_id: str
    team_id: str
    player_id: str
    audl_id: int
    jersey_number: int
    active: bool

    class Config:
        orm_mode = True


class Game(BaseModel):
    id: str
    audl_id: str
    ext_game_id: str
    home_team_id: str
    away_team_id: str
    home_score: int
    away_score: int
    start_timestamp: datetime
    start_timezone: str
    upload_timestamp: datetime

    # events: List[Event]
    home_team: Team
    away_team: Team

    class Config:
        orm_mode = True


class SeasonSummary(BaseModel):
    team: Team
