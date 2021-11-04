from datetime import datetime
from typing import Optional
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.schema import ForeignKeyConstraint
import uuid

from sqlalchemy.sql.sqltypes import Boolean, DateTime, Float

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
    ):
        self.id = id
        self.audl_id = audl_id
        self.home_roster_id = home_roster_id
        self.away_roster_id = away_roster_id
        self.home_score = home_score
        self.away_score = away_score
        self.start_timestamp = start_timestamp
        self.start_timezone = start_timezone


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


class Point(Base):
    __tablename__ = "point"
    __table_args__ = (ForeignKeyConstraint(["game_id"], ["game.id"]),)

    id = Column(String(16), primary_key=True, default=uuid16())
    quarter = Column(Integer)
    start_time = Column(Integer)
    end_time = Column(Integer)
    game_id = Column(String(16), nullable=False)

    events = relationship("Event", back_populates="point")


class Event(Base):
    __tablename__ = "event"
    __table_args__ = (
        ForeignKeyConstraint(["thrower_player_id"], ["player.id"]),
        ForeignKeyConstraint(["thrower_receiver_id"], ["player.id"]),
        ForeignKeyConstraint(["point_id"], ["point.id"]),
    )

    id = Column(String(16), primary_key=True, default=uuid16())
    point_id = Column(String(16), ForeignKey("point.id"), nullable=False)
    received_at_x = Column(Float)
    received_at_y = Column(Float)
    thrower_player_id = Column(String(16))
    thrower_receiver_id = Column(String(16))
    pass_type = Column(String(32))  # TODO add enums here
    outcome = Column(String(32))  # TODO add enums here

    point = relationship(
        "Point", back_populates="events"
    )  # TODO -- is this the right structure for uploading points and events?


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


class PlayedPoint(Base):
    __tablename__ = "played_point"
    __table_args__ = (
        ForeignKeyConstraint(["player_id"], ["player.id"]),
        ForeignKeyConstraint(["point_id"], ["point.id"]),
    )

    player_id = Column(String(16), nullable=False, primary_key=True)
    point_id = Column(String(16), nullable=False, primary_key=True)
