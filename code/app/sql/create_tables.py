"""
One-off script to create all the tables in the database
"""

from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from app.sql.models import Base
from app.sql.utils import make_engine
from urllib.parse import quote_plus


if __name__ == "__main__":
    engine = make_engine()
    Base.metadata.create_all(engine)
