from sqlalchemy.sql.expression import or_, select
from sql.models import GameORM, TeamORM
from sql.utils import make_engine
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

if __name__ == "__main__":
    engine = make_engine()
    conn = engine.connect()
    sql = """
    show databases
    """
    result = conn.execute(sql)
    for r in result:
        print(r)
