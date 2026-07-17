from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, Session

from app.users.service import create_initial_data
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def init_initial_data():
    with Session(engine) as session:
        create_initial_data(session)
