from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus


if __name__ == "__main__":
    load_dotenv()
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_ADMIN_USER")
    pw = quote_plus(os.getenv("MYSQL_ADMIN_PW"))
    db = os.getenv("MYSQL_DATABASE")
    engine = create_engine(f"mysql+pymysql://{user}:{pw}@{host}/audl", echo=True)

    conn = engine.connect()
    sql = """
    show databases
    """
    result = conn.execute(sql)
    for r in result:
        print(r)
