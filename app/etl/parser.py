"""
Parses audl-stats json into models
"""
import json
from datetime import datetime
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from sqlalchemy import insert
from typing import List, Tuple
from dataclasses import dataclass
from requests import Response
from app.sql.models import (
    Game,
    Player,
    Roster,
    Team,
    OnRoster,
    PlayedPoint,
    Point,
    Event,
    uuid16,
)
from app.etl.event_types import EVENT_TYPES, EVENT_TYPES_GENERAL


@dataclass
class ParsedGame:
    game: Game
    player: List[Player]
    roster: Tuple[Roster, Roster]
    home_team: Team
    away_team: Team
    on_roster: List[OnRoster]
    played_point: List[PlayedPoint]
    point: List[Point]
    pass_event: List[Event]


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


def parse_point():
    return


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
    event: dict, point_id: str, roster_lookup: dict, event_sequence: int
) -> Event:
    """
    Event parser for non-line events.
    """
    e = Event(
        id=uuid16(),
        point_id=point_id,
        coordinate_x=event.get(event.get("x")),
        coordinate_y=event.get(event.get("y")),
        player_id=roster_lookup.get(event.get("r")),
        event_type=EVENT_TYPES[event["t"]],
        sequence=event_sequence,
    )

    return e


@dataclass
class RawPoint:
    on_offense: bool
    events: list


def split_event_series(events: List[dict]) -> List[List[dict]]:
    """preprocess list of events into one list for each point."""
    point_groups = []

    # initiate the first point
    p = RawPoint(events[0]["t"] == 1, [])

    while events:
        e = events.pop(0)
        if e["t"] in [1, 2] and len(p.events) > 0:
            point_groups.append(p)
            p = RawPoint(e["t"] == 1, [])
            p.events.append(e)
        else:
            p.events.append(e)
    return point_groups


def parse_game_events(
    engine: Engine,
    events_home: List[dict],
    events_away: List[dict],
    score_times_home: List[int],
    score_times_away: List[int],
    roster_lookup: dict,
    game_id: str,
) -> List[dict]:
    """
    Parses points and related events. Loads data to point, played_point and event.
    """
    print("Parsing game events")
    points = []

    # Event_stack keeps track of who is in possesion
    #  this should always start with the defense.
    #  Mod division used to toggle between as possesion changes.
    event_stack = [events_home, events_away]
    if events_home[0]["t"] == 2:
        event_stack_idx = 0
    else:
        event_stack_idx = 1

    # Time vars
    point_start = 0
    score_times_away.remove(1)
    score_times_home.remove(1)
    score_times = sorted(score_times_home + score_times_away)
    quarter = 1

    played_point = []  # List of dicts for batch loading
    point_sequence = 1
    point_id = uuid16()
    event_sequence = 0
    p = Point(  # TODO add a event_sequence number?
        id=point_id,
        quarter=quarter,
        start_time=point_start,
        end_time=9999,  # temp?
        game_id=game_id,
        sequence=point_sequence,
    )

    while len(event_stack[0]) > 0 or len(event_stack[1]) > 0:
        e = event_stack[event_stack_idx % 2].pop(0)
        etype = EVENT_TYPES.get(e["t"])
        print(f"E sequence {event_sequence}. Team = {event_stack_idx%2}, {e}")
        if not etype:  # Catch unknown event types
            raise UnknownEventException(f'Unknown event of type {e["t"]}!')

        elif etype in (
            "Start of D-Point",
            "Start of O-Point",
            "Substitutions",
        ):
            played_point += parse_line_event(e, point_id, roster_lookup)

        # Handle change of possesion
        elif EVENT_TYPES_GENERAL.get(e["t"]):
            if EVENT_TYPES_GENERAL.get(e["t"]) == "End of Period":
                quarter += 1
            else:
                p.events.append(parse_event(e, point_id, roster_lookup, event_sequence))
                event_sequence += 1
            event_stack_idx += 1

        # Handle events that do not impact possesion
        else:
            p.events.append(parse_event(e, point_id, roster_lookup, event_sequence))
            event_sequence += 1

        # Look at the top of both stacks to see if we can move to the next point
        if len(event_stack[0]) == 0 and len(event_stack[1]) == 0:
            pass

        elif len(event_stack[0]) == 0 and len(event_stack[1]) != 0:
            event_stack_idx = 1

        elif len(event_stack[0]) != 0 and len(event_stack[1]) == 0:
            event_stack_idx = 0

        # Move to next point
        elif (event_stack[0][0]["t"] in (1, 2)) and (event_stack[1][0]["t"] in (1, 2)):
            point_start = score_times.pop(0)
            p.end_time = point_start
            points.append(p)

            event_sequence = 0
            point_sequence += 1
            p = Point(
                id=point_id,
                quarter=quarter,
                start_time=point_start,
                end_time=9999,  # temp
                game_id=game_id,
                sequence=point_sequence,
            )

            if events_home[0]["t"] == 2:
                event_stack_idx = 0
            else:
                event_stack_idx = 1
            print(f"point #{point_sequence}")

    return played_point, points


def parse_game(engine: Engine, response: Response) -> ParsedGame:
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

    game = Game(
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

    played_points, points = parse_game_events(
        engine,
        events_home=json.loads(gamejson["tsgHome"]["events"]),
        events_away=json.loads(gamejson["tsgAway"]["events"]),
        score_times_home=gamejson["game"]["score_times_home"],
        score_times_away=gamejson["game"]["score_times_away"],
        roster_lookup=roster_lookup,
        game_id=game_id,
    )

    total_score = gamejson["game"]["score_home"] + gamejson["game"]["score_away"]
    assert (
        len(points) == total_score
    ), f"Point number mismatch. Total points: {total_score}. Parsed points: {len(points)}"

    session = Session(engine)

    print("Loading game data")
    session.add(game)
    session.commit()

    print("Loading point, event and roster data")
    session.add_all(points)
    session.commit()

    stmt = insert(PlayedPoint).values(played_points)
    session.execute(stmt)
