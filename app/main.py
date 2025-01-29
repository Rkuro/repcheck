import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api import (
    router_people,
    router_status,
    router_areas,
    router_bills
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://repcheck.us"
]

handler = TimedRotatingFileHandler(
    "service.log",  # Log file path
    when="midnight",  # Rotate the log file at midnight
    interval=1,  # Rotate every 1 day
    backupCount=7  # Keep 7 days of logs,
)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router_people)
app.include_router(router_status)
app.include_router(router_areas)
app.include_router(router_bills)

