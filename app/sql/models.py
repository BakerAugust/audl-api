import uuid
import json

from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKeyConstraint


from sqlalchemy.sql.sqltypes import JSON, Boolean, DateTime, Float

Base = declarative_base()


def uuid16() -> str:
    """
    returns a random 16-digit uuid as str
    """
    return uuid.uuid4().hex[:16]


class Team(Base):
    __tablename__ = "team"
    id = Column(String(16), primary_key=True, default=uuid16())
    audl_id = Column(Integer, nullable=False)
    division = Column(Integer, nullable=False)
    city = Column(String(32), nullable=False)
    name = Column(String(32), nullable=False)
    abbreviation = Column(String(3), nullable=False)

    def __init__(
        self,
        audl_id: str,
        division: int,
        city: str,
        name: str,
        abbreviation: str,
        id: Optional[str] = None,
    ):
        self.id = id
        self.audl_id = audl_id
        self.division = division
        self.city = city
        self.name = name
        self.abbreviation = abbreviation


class Roster(Base):
    __tablename__ = "roster"
    __table_args__ = (ForeignKeyConstraint(["team_id"], ["team.id"]),)

    id = Column(String(16), primary_key=True, default=uuid16())
    team_id = Column(String(16))

    def __init__(self, team_id: str, id: Optional[str] = None):
        self.id = id
        self.team_id = team_id


class Game(Base):
    __tablename__ = "game"
    __table_args__ = (
        ForeignKeyConstraint(["home_roster_id"], ["roster.id"]),
        ForeignKeyConstraint(["away_roster_id"], ["roster.id"]),
    )

    id = Column(String(16), primary_key=True, default=uuid16())
    audl_id = Column(Integer)
    home_roster_id = Column(String(16), nullable=False)
    away_roster_id = Column(String(16), nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    start_timestamp = Column(DateTime)
    start_timezone = Column(String(3))
    upload_timestamp = Column(DateTime, default=datetime.now())

    events = relationship("Event", back_populates="game")

    def __init__(
        self,
        audl_id: str,
        home_roster_id: str,
        away_roster_id: str,
        home_score: int,
        away_score: int,
        start_timestamp: datetime,
        start_timezone: str,
        id: Optional[str] = None,
        events: Optional[list] = [],
    ):
        self.id = id
        self.audl_id = audl_id
        self.home_roster_id = home_roster_id
        self.away_roster_id = away_roster_id
        self.home_score = home_score
        self.away_score = away_score
        self.start_timestamp = start_timestamp
        self.start_timezone = start_timezone
        self.events = events


class Player(Base):
    __tablename__ = "player"
    id = Column(String(16), primary_key=True, default=uuid16())
    audl_id = Column(Integer)
    first_name = Column(String(32), nullable=False)
    last_name = Column(String(32), nullable=False)

    def __init__(self, audl_id: str, first_name: str, last_name: str):
        self.audl_id = audl_id
        self.first_name = first_name
        self.last_name = last_name


class Event(Base):
    __tablename__ = "event"
    __table_args__ = (
        ForeignKeyConstraint(["player_id"], ["player.id"]),
        ForeignKeyConstraint(["team_id"], ["team.id"]),
        ForeignKeyConstraint(["game_id"], ["game.id"]),
    )

    id = Column(String(16), primary_key=True, default=uuid16())
    coordinate_x = Column(Float)
    coordinate_y = Column(Float)
    player_id = Column(String(16))
    event_type = Column(String(32))
    sequence = Column(Integer, nullable=False)
    event_data_json = Column(JSON)
    team_id = Column(String(16), nullable=False)
    game_id = Column(String(16), ForeignKey("game.id"), nullable=False)

    game = relationship("Game", back_populates="events")

    def __init__(
        self,
        id: str,
        game_id: str,
        team_id: str,
        coordinate_x: float,
        coordinate_y: float,
        player_id: str,
        event_type: str,
        event_data_json: dict,
        sequence: int,
    ):
        self.id = id
        self.game_id = game_id
        self.team_id = team_id
        self.coordinate_x = coordinate_x
        self.coordinate_y = coordinate_y
        self.player_id = player_id
        self.event_type = event_type
        self.event_data_json = json.dumps(event_data_json)
        self.sequence = sequence


class OnRoster(Base):
    __tablename__ = "on_roster"
    __table_args__ = (
        ForeignKeyConstraint(["roster_id"], ["roster.id"]),
        ForeignKeyConstraint(["player_id"], ["player.id"]),
    )

    roster_id = Column(String(16), nullable=False, primary_key=True)
    player_id = Column(String(16), nullable=False, primary_key=True)
    audl_id = Column(Integer, nullable=False)
    jersey_number = Column(Integer)
    active = Column(Boolean)

    def __init__(
        self,
        roster_id: str,
        player_id: str,
        audl_id: int,
        jersey_number: int,
        active: bool,
    ):
        self.roster_id = roster_id
        self.player_id = player_id
        self.audl_id = audl_id
        self.jersey_number = jersey_number
        self.active = active
