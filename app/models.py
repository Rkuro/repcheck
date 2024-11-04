from sqlalchemy import Column, String
from geoalchemy2 import Geometry
from .database.database import Base

class ZipCode(Base):
    __tablename__ = "zipcodes"

    zip_code = Column(String, primary_key=True, index=True)
    geometry = Column(Geometry('POLYGON'))
