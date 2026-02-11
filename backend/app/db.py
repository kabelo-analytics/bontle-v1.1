from sqlmodel import SQLModel, create_engine
from .config import settings

def get_engine():
    url = (settings.database_url or "").strip()
    if not url:
        url = "sqlite:///./bontle.db"
        return create_engine(url, echo=False, connect_args={"check_same_thread": False})
    return create_engine(url, echo=False)

engine = get_engine()

def init_db():
    SQLModel.metadata.create_all(engine)
