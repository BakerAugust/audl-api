from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from typing import List

from app.schema.schema import Game, Team
from app.sql.utils import make_engine
from app.sql.models import TeamORM, GameORM
from app.views.season import summarize_season

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

engine = make_engine(echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})


@app.get("/teams/view", response_class=HTMLResponse)
async def view_teams(request: Request, db: Session = Depends(get_db)):
    teams = db.query(TeamORM).order_by(TeamORM.name).all()
    return templates.TemplateResponse(
        "teams/view_all.html", {"request": request, "teams": teams}
    )


@app.get("/teams/{team_id}/view", response_class=HTMLResponse)
async def view_teams(request: Request, team_id: str, db: Session = Depends(get_db)):
    team_orm = db.query(TeamORM).filter(TeamORM.id == {team_id})
    team = Team.from_orm(team_orm[0])
    games_orm = db.execute(
        select(GameORM)
        .options(joinedload(GameORM.home_team), joinedload(GameORM.away_team))
        .filter(or_(GameORM.home_team_id == team_id, GameORM.away_team_id == team_id))
        .order_by(GameORM.start_timestamp)
    ).all()
    games = [Game.from_orm(g[0]) for g in games_orm]
    return templates.TemplateResponse(
        "teams/team.html",
        {
            "request": request,
            "team": team,
            "games": games,
            "season_summary": summarize_season(team, games),
        },
    )


@app.get("/teams/{team_id}/view", response_class=HTMLResponse)
async def view_team(request: Request, team_id: str, db: Session = Depends(get_db)):
    return


@app.get("/games/{team_id}/view", response_class=HTMLResponse)
async def view_team_games(
    request: Request, team_id: str, db: Session = Depends(get_db)
):
    games_orm = db.execute(
        select(GameORM)
        .options(joinedload(GameORM.home_team), joinedload(GameORM.away_team))
        .filter(or_(GameORM.home_team_id == team_id, GameORM.away_team_id == team_id))
        .order_by(GameORM.start_timestamp)
    ).all()

    if games_orm:
        games = [Game.from_orm(g[0]) for g in games_orm]
        if games[0].away_team_id == team_id:
            team_name = games[0].away_team.name
        else:
            team_name = games[0].home_team.name
        return templates.TemplateResponse(
            "games/view_all.html",
            {"request": request, "games": games, "team_name": team_name},
        )
    else:
        return None


@app.get("/games/view", response_class=HTMLResponse)
async def view_games(request: Request, db: Session = Depends(get_db)):
    games_orm = db.execute(
        select(GameORM)
        .options(joinedload(GameORM.home_team), joinedload(GameORM.away_team))
        .order_by(GameORM.start_timestamp)
    ).all()
    games = [Game.from_orm(g[0]) for g in games_orm]
    return templates.TemplateResponse(
        "games/view_all.html", {"request": request, "games": games, "team_name": "All"}
    )
