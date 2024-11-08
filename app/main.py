import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    router_people,
    router_status,
    router_zipcodes
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
    backupCount=7  # Keep 7 days of logs
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

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
app.include_router(router_zipcodes)

