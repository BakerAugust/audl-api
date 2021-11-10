"""
Identify game URLs not already loaded and load them into mysql db. 
"""

import requests
import pandas as pd
from sqlalchemy.orm.session import Session
from app.etl.parser import parse_load_game
from app.sql.utils import make_engine
from app.sql.models import Game


if __name__ == "__main__":
    engine = make_engine(echo=False)

    session = Session(engine)

    game_urls = pd.read_csv("app/etl/urls_2021.csv", skiprows=0)
    for game_url in game_urls.values:
        ext_game_id = game_url[0].split("/")[-1]
        print(f"Checking for game {ext_game_id}")
        # Check if game is already loaded
        if not session.query(Game).filter(Game.ext_game_id == ext_game_id).first():
            print(f"Parsing and loading data.")
            response = requests.get(game_url[0])
            try:
                parse_load_game(engine, response)
            except Exception as e:
                print(f"Error in loading!: {e}")
        else:
            print(f"Already loaded.")
