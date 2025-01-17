from sqlmodel import create_engine, Session, SQLModel, inspect
from sqlalchemy.dialects.postgresql import insert
import logging
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote
import os

log = logging.getLogger(__name__)

# Load dotenv variables
parent_dir = Path(__file__).resolve().parent.parent.parent
env_path = parent_dir / '.env'
log.info(f"Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

POSTGRES_DB_PASSWORD = os.getenv("POSTGRES_DB_PASSWORD")

# Define connection parameters
connection_params = {
    'username': 'postgres',
    'password': quote(POSTGRES_DB_PASSWORD),
    'host': 'localhost',  # or '127.0.0.1'
    'port': '5432',  # Default PostgreSQL port
    'database': 'repcheck'
}

def get_engine():
    # Create an engine using SQLModel
    database_url = (
        f"postgresql+psycopg2://{connection_params['username']}:{connection_params['password']}"
        f"@{connection_params['host']}:{connection_params['port']}/{connection_params['database']}"
    )
    engine = create_engine(database_url)
    # Ensure all tables exist!
    SQLModel.metadata.create_all(engine)
    return engine


def get_session():
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
