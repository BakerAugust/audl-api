"""
One-off script to create all the tables in the database
"""

from sql.models import Base
from sql.utils import make_engine


if __name__ == "__main__":
    engine = make_engine()
    Base.metadata.create_all(engine)
