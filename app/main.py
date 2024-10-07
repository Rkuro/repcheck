import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI

from .api.routes import router

handler = handler = TimedRotatingFileHandler(
    "service.log",  # Log file path
    when="midnight",  # Rotate the log file at midnight
    interval=1,  # Rotate every 1 day
    backupCount=7  # Keep 7 days of logs
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = FastAPI()

app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}
