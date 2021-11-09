"""
Parses audl-stats json into models
"""
import json
from datetime import datetime
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from sqlalchemy import insert
from typing import List
from requests import Response
from app.sql.models import (
    Game,
    Player,
    Roster,
    Team,
    OnRoster,
    Event,
    uuid16,
)
from app.etl.event_types import EVENT_TYPES, EVENT_TYPES_GENERAL


class UnknownEventException(Exception):
    pass


def parse_roster(engine: Engine, roster_list: List[dict], team_id: str) -> str:
    """
    Parses add loads roster and on_roster, adding players to the db if they are not
    already there. Returns roster_id.
    """
    session = Session(engine)
    roster_id = uuid16()
    roster = Roster(id=roster_id, team_id=team_id)
    session.add(roster)
    session.commit()
    on_roster_list = []
    players_to_add = []

    for rostered_player in roster_list:
        player = (
            session.query(Player)
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

        on_roster_list.append(
            {
                "roster_id": roster_id,
                "player_id": player_id,
                "audl_id": rostered_player["id"],
                "jersey_number": rostered_player["jersey_number"],
                "active": rostered_player["active"],
            }
        )

    if players_to_add:
        stmt = insert(Player).values(players_to_add)
        session.execute(stmt)
        session.commit()

    stmt = insert(OnRoster).values(on_roster_list)
    session.execute(stmt)
    session.commit()

    return roster_id


def parse_team(engine: Engine, team_dict: dict) -> str:
    """
    Parses team and returns the team id from db if exists, otherwise
    creates a new entry for the team and returns the newly-created id.
    """
    session = Session(engine)
    team = session.query(Team).filter_by(audl_id=team_dict["team_id"]).first()
    if bool(team):
        return team.id
    else:
        team_id = uuid16()
        team = Team(
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


def parse_line_event(event: dict, point_id: str, roster_lookup: dict) -> List[dict]:
    """
    Handler for events involving lines and substitutions.
    """
    if event["t"] in [1, 2]:
        return [
            {"player_id": roster_lookup[x], "point_id": point_id} for x in event["l"]
        ]
    elif EVENT_TYPES[event["t"]] == "Substitutions":
        return [
            {"player_id": roster_lookup[x], "point_id": point_id, "substitution": True}
            for x in event["l"]
        ]


def parse_event(
    event: dict, game_id: str, team_id: str, roster_lookup: dict, event_sequence: int
) -> Event:
    """
    Event parser for non-line events.
    """
    e = Event(
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


def parse_game(engine: Engine, response: Response) -> None:
    """ """
    ## TODO check if the game has already been loaded

    ## Get list of all players
    gamejson = json.loads(response.content.decode())
    game_id = uuid16()

    # Parse teams to ensure the teams exist
    home_team_id = parse_team(engine, gamejson["game"]["team_season_home"])
    away_team_id = parse_team(engine, gamejson["game"]["team_season_away"])

    # Need to pass a game_id in here too
    home_roster_id = parse_roster(engine, gamejson["rostersHome"], home_team_id)
    away_roster_id = parse_roster(engine, gamejson["rostersAway"], away_team_id)

    game = Game(  # TODO add game str
        id=game_id,
        audl_id=gamejson["game"]["id"],
        home_roster_id=home_roster_id,
        away_roster_id=away_roster_id,
        home_score=gamejson["game"]["score_home"],
        away_score=gamejson["game"]["score_away"],
        start_timestamp=datetime.fromisoformat(
            gamejson["game"]["start_timestamp"].replace("Z", "")
        ),
        start_timezone=gamejson["game"]["start_timezone"],
    )

    # Build a roster lookup for audl_rostered_player_id --> player.id
    session = Session(engine)
    roster_lookup = {}
    rostered_players = (
        session.query(OnRoster)
        .filter(OnRoster.roster_id.in_([home_roster_id, away_roster_id]))
        .all()
    )
    for player in rostered_players:
        roster_lookup[player.audl_id] = player.player_id

    event_sequence = 0
    for e in json.loads(gamejson["tsgHome"]["events"]):
        game.events.append(
            parse_event(
                e, game_id, home_team_id, roster_lookup, event_sequence=event_sequence
            )
        )
        event_sequence += 1

    event_sequence = 0
    for e in json.loads(gamejson["tsgAway"]["events"]):
        game.events.append(
            parse_event(
                e,
                game_id,
                away_team_id,
                roster_lookup,
                event_sequence=event_sequence,
            )
        )
        event_sequence += 1

    session = Session(engine)

    print("Loading game data")
    session.add(game)
    session.commit()
