from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path
from urllib import parse
import os
import logging

log = logging.getLogger(__name__)

parent_dir = Path(__file__).resolve().parent.parent.parent
env_path = parent_dir / '.env'
log.info(f"Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path)

POSTGRES_DB_PASSWORD = os.getenv("POSTGRES_DB_PASSWORD")

# Set up SQLAlchemy base and engine
Base = declarative_base()

# Define connection parameters
connection_params = {
    'username': 'postgres',
    'password': parse.quote(POSTGRES_DB_PASSWORD),
    'host': 'localhost',  # or '127.0.0.1'
    'port': '5432',  # Default PostgreSQL port
    'database': 'repcheck'
}

# Create an engine using key-value parameters
engine = create_engine(
    f"postgresql+psycopg2://"
    f"{connection_params['username']}:"
    f"{connection_params['password']}"
    f"@{connection_params['host']}:{connection_params['port']}"
    f"/{connection_params['database']}"
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Dependency to get the session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()