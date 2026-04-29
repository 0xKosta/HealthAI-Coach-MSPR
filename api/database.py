# api/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Générateur de session BDD.
    Utilisé via Depends(get_db) dans chaque endpoint FastAPI.
    Ouvre une session, la passe à l'endpoint, puis la ferme proprement.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
