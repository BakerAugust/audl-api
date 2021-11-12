import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from urllib.parse import quote_plus
from typing import Optional
from sqlalchemy.engine.base import Engine


def make_engine(echo: Optional[bool] = False) -> Engine:
    """
    Creates an engine with app admin credentials.
    """
    load_dotenv()
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_ADMIN_USER")
    pw = quote_plus(os.getenv("MYSQL_ADMIN_PW"))
    db = os.getenv("MYSQL_DATABASE")
    return create_engine(f"mysql+pymysql://{user}:{pw}@{host}/{db}", echo=echo)
