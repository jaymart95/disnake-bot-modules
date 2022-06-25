import sqlalchemy as db
from sqlalchemy import Column, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Create and configure the DB engine and location
DB_URL = "sqlite:///modules/trivia/data/trivia.db"
engine = db.create_engine(DB_URL)

# Create a Base class for our Model class definitions
Base = declarative_base()

# Create and configure the ORM session bound to our engine
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()


# Our Model class holds table name and column definitions
class Model(Base):
    __tablename__ = "trivia"

    member_id = Column(Integer, primary_key=True)
    points = Column(Integer, nullable=False)
    total_corr = Column(Integer, nullable=False)
    total_wro = Column(Integer, nullable=False)


# Create the database, table, and columns and bind it to the connection engine
Base.metadata.create_all(engine)
Base.metadata.bind = engine


def get_member(member):
    """
    Return the member row from DB where the member_id == the id of the
    discord member (member.id)

    Parameters
    ----------
    member: The Discord member object
    """
    return session.query(Model).filter(Model.member_id == member.id).first()


def update_member(member, points: int = 0, correct: int = 0, wrong: int = 0):
    """
    Update the member row in the database, if member exists, else
    add the member row, data, then commit and close the db session

    Paramters
    ---------
    member:  The discord member object
    points: (int) The trivia points the member earned (Default 0)
    correct: (int) If the user answered correctly, this will be one to increase their total_corr count (Default 0)
    wront: (int) If the user answered incorrectly, or timed out, this will be one to increase their total_wro count (Default 0)
    """
    result = get_member(member)
    if result is None:
        session.add(
            Model(
                member_id=member.id,
                points=points,
                total_corr=correct,
                total_wro=wrong,
            )
        )
    else:
        result.points += points
        result.total_corr += correct
        result.total_wro += wrong

    session.commit()


def fetch_leaderboard_points():
    """Fetch all rows from the database and sort by points(desc)"""
    return session.query(Model).order_by(Model.points.desc()).all()


def fetch_leaderboard_correct():
    """Fetch all rows from the database and sort by total_corr(desc)"""
    return session.query(Model).order_by(Model.total_corr.desc()).all()
