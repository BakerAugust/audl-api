from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import OperationalError
from sqlalchemy import or_, and_
from schema.schema import Player
from sql.models import PlayerORM
from schema.schema import Game, Team, Roster
from sql.utils import make_engine
from sql.models import TeamORM, GameORM, RosterORM
from views.season import summarize_season

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    try:
        teams = db.query(TeamORM).order_by(TeamORM.name).all()
        return templates.TemplateResponse(
            "teams/view_all.html", {"request": request, "teams": teams}
        )
    except OperationalError:
        return templates.TemplateResponse("error_page.html", {"request": request})


@app.get("/teams/{team_id}/view", response_class=HTMLResponse)
async def view_teams(request: Request, team_id: str, db: Session = Depends(get_db)):
    team_orm = db.query(TeamORM).filter(TeamORM.id == {team_id})
    team = Team.from_orm(team_orm[0])
    try:
        games_orm = db.execute(
            select(GameORM)
            .options(joinedload(GameORM.home_team), joinedload(GameORM.away_team))
            .filter(
                or_(GameORM.home_team_id == team_id, GameORM.away_team_id == team_id)
            )
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
    except OperationalError:
        return templates.TemplateResponse("error_page.html", {"request": request})


@app.get("/games/view_all", response_class=HTMLResponse)
async def view_games(request: Request, db: Session = Depends(get_db)):
    try:

        games_orm = db.execute(
            select(GameORM)
            .options(joinedload(GameORM.home_team), joinedload(GameORM.away_team))
            .order_by(GameORM.start_timestamp)
        ).all()
        games = [Game.from_orm(g[0]) for g in games_orm]
        return templates.TemplateResponse(
            "games/view_all.html",
            {"request": request, "games": games, "team_name": "All"},
        )

    except OperationalError:
        return templates.TemplateResponse("error_page.html", {"request": request})


@app.get("/games/{game_id}/view", response_class=HTMLResponse)
async def view_team_games(
    request: Request, game_id: str, db: Session = Depends(get_db)
):
    try:
        games_orm = db.execute(
            select(GameORM)
            .options(joinedload(GameORM.home_team), joinedload(GameORM.away_team))
            .filter(GameORM.id == game_id)
        ).first()
        print(games_orm)
        if games_orm:
            game = Game.from_orm(games_orm[0])

            home_rosters_orm = db.execute(
                select(RosterORM)
                .options(joinedload(RosterORM.player))
                .filter(
                    and_(
                        RosterORM.game_id == game_id,
                        RosterORM.active == True,
                        RosterORM.team_id == game.home_team_id,
                    )
                )
                .order_by(RosterORM.jersey_number)
            )

            away_rosters_orm = db.execute(
                select(RosterORM)
                .options(joinedload(RosterORM.player))
                .filter(
                    and_(
                        RosterORM.game_id == game_id,
                        RosterORM.active == True,
                        RosterORM.team_id == game.away_team_id,
                    )
                )
                .order_by(RosterORM.jersey_number)
            )
            home_roster = [Roster.from_orm(r[0]) for r in home_rosters_orm]
            away_roster = [Roster.from_orm(r[0]) for r in away_rosters_orm]
            return templates.TemplateResponse(
                "games/view.html",
                {
                    "request": request,
                    "game": game,
                    "home_roster": home_roster,
                    "away_roster": away_roster,
                },
            )
        else:
            return None
    except OperationalError:
        return templates.TemplateResponse("error_page.html", {"request": request})


@app.get("/players/{player_id}/view", response_class=HTMLResponse)
async def view_player(request: Request, player_id: str, db: Session = Depends(get_db)):
    try:
        player_orm = db.execute(
            select(PlayerORM).filter(PlayerORM.id == player_id)
        ).first()
        player = Player.from_orm(player_orm[0])
        return templates.TemplateResponse(
            "players/view.html",
            {"request": request, "player": player},
        )
    except OperationalError:
        return templates.TemplateResponse("error_page.html", {"request": request})
