"""
Parses audl-stats json into models
"""
import json
from datetime import datetime
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from sqlalchemy import insert
from typing import List, Tuple
from requests import Response
from app.sql.models import (
    GameORM,
    PlayerORM,
    RosterORM,
    TeamORM,
    EventORM,
    uuid16,
)
from app.etl.event_types import EVENT_TYPES, EVENT_TYPES_GENERAL


def parse_roster(
    engine: Engine, roster_list: List[dict], team_id: str
) -> Tuple[list, dict]:
    """
    Parses add loads roster and on_roster, adding players to the db if they are not
    already there. Returns roster_id.
    """
    session = Session(engine)
    # Using a dict to workaround some erroneous duplicates from the source
    roster_dict = {}
    players_to_add = []

    for rostered_player in roster_list:
        player = (
            session.query(PlayerORM)
            .filter_by(audl_id=rostered_player["player_id"])
            .first()
        )
        if bool(player):
            player_id = player.id
        else:
            player_id = uuid16()

            # Using a list of dicts for faster batch inserts
            players_to_add.append(
                {
                    "id": player_id,
                    "audl_id": rostered_player["player"]["id"],
                    "first_name": rostered_player["player"]["first_name"],
                    "last_name": rostered_player["player"]["last_name"],
                }
            )
        jersey_number = rostered_player["jersey_number"]
        roster_dict[player_id] = {
            "player_id": player_id,
            "team_id": team_id,
            "audl_id": rostered_player["id"],
            "jersey_number": jersey_number if jersey_number else None,
            "active": rostered_player["active"],
        }

    return players_to_add, roster_dict


def parse_team(engine: Engine, team_dict: dict) -> str:
    """
    Parses team and returns the team id from db if exists, otherwise
    creates a new entry for the team and returns the newly-created id.
    """
    session = Session(engine)
    team = session.query(TeamORM).filter_by(audl_id=team_dict["team_id"]).first()
    if bool(team):
        return team.id
    else:
        team_id = uuid16()
        team = TeamORM(
            id=team_id,
            audl_id=team_dict["team_id"],
            division=team_dict["division_id"],
            city=team_dict["city"],
            name=team_dict["team"]["name"],
            abbreviation=team_dict["abbrev"],
        )
        session.add(team)
        session.commit()
    return team_id


def parse_event(
    event: dict, game_id: str, team_id: str, roster_lookup: dict, event_sequence: int
) -> EventORM:
    """
    Event parser for non-line events.
    """
    e = EventORM(
        id=uuid16(),
        coordinate_x=event.get("x"),
        coordinate_y=event.get("y"),
        player_id=roster_lookup.get(event.get("r")),
        event_type=EVENT_TYPES[event["t"]],
        event_data_json=event,
        sequence=event_sequence,
        team_id=team_id,
        game_id=game_id,
    )

    return e


def parse_load_game(engine: Engine, response: Response) -> None:
    """ """
    ## Get list of all players
    gamejson = json.loads(response.content.decode())
    game_id = uuid16()

    # Parse teams to ensure the teams exist
    home_team_id = parse_team(engine, gamejson["game"]["team_season_home"])
    away_team_id = parse_team(engine, gamejson["game"]["team_season_away"])

    home_players_to_add, home_roster_dict = parse_roster(
        engine, gamejson["rostersHome"], home_team_id
    )
    away_players_to_add, away_roster_dict = parse_roster(
        engine, gamejson["rostersAway"], away_team_id
    )

    players_to_add = home_players_to_add + away_players_to_add

    game = GameORM(
        id=game_id,
        audl_id=gamejson["game"]["id"],
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=gamejson["game"]["score_home"],
        away_score=gamejson["game"]["score_away"],
        start_timestamp=datetime.fromisoformat(
            gamejson["game"]["start_timestamp"].replace("Z", "")
        ),
        start_timezone=gamejson["game"]["start_timezone"],
        ext_game_id=gamejson["game"]["ext_game_id"],
    )

    home_roster_lookup = {}
    for player_id, vdict in home_roster_dict.items():
        home_roster_lookup[vdict["audl_id"]] = player_id
    # Build a roster lookup for audl_rostered_player_id --> player.id
    event_sequence = 0
    for e in json.loads(gamejson["tsgHome"]["events"]):
        game.events.append(
            parse_event(
                e,
                game_id,
                home_team_id,
                home_roster_lookup,
                event_sequence=event_sequence,
            )
        )
        event_sequence += 1

    away_roster_lookup = {}
    for player_id, vdict in away_roster_dict.items():
        away_roster_lookup[vdict["audl_id"]] = player_id
    event_sequence = 0
    for e in json.loads(gamejson["tsgAway"]["events"]):
        game.events.append(
            parse_event(
                e,
                game_id,
                away_team_id,
                away_roster_lookup,
                event_sequence=event_sequence,
            )
        )
        event_sequence += 1

    print("Loading data to db")
    with Session(engine) as session:
        # Load players
        if players_to_add:
            stmt = insert(PlayerORM).values(players_to_add)
            session.execute(stmt)
            session.commit()

        # Load game
        session.add(game)
        session.commit()

        # Load roster
        for roster_dict in [home_roster_dict, away_roster_dict]:
            for vdict in roster_dict.values():
                vdict["game_id"] = game_id  # Add game_id attrb
            stmt = insert(RosterORM).values(list(roster_dict.values()))
            session.execute(stmt)
            session.commit()
