from pydantic.main import BaseModel
from app.schema.schema import Team, Game
from pydantic import BaseModel
from typing import List


class SeasonSummary(BaseModel):
    wins: int
    losses: int
    ties: int
    avg_points_scored: float
    avg_points_allowed: float


def summarize_season(team: Team, games: List[Game]) -> SeasonSummary:
    """ """
    points_scored = 0
    points_allowed = 0
    wins = 0
    losses = 0
    ties = 0

    for g in games:
        print(str(g))
        if g.home_team_id == team.id:
            points_scored += g.home_score
            points_allowed += g.away_score
            if g.home_score > g.away_score:
                wins += 1
            elif g.home_score < g.away_score:
                losses += 1
            else:
                ties += 1
        else:  # Away team
            points_scored += g.away_score
            points_allowed += g.home_score
            if g.home_score < g.away_score:
                wins += 1
            elif g.home_score > g.away_score:
                losses += 1
            else:
                ties += 1
    return SeasonSummary(
        wins=wins,
        losses=losses,
        ties=ties,
        avg_points_scored=round(points_scored / len(games), 1),
        avg_points_allowed=round(points_allowed / len(games), 1),
    )
