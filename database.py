from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_URL = "sqlite:///./fastapi_blog.db"

engine = create_engine(url=DB_URL, connect_args={"check_same_thread": False}, echo=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db_session():
    with SessionLocal() as db_session:
        yield db_session


