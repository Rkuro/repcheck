from sqlmodel import SQLModel, Field, Relationship
from geoalchemy2 import Geometry
from sqlalchemy import Column, ARRAY, Text, JSON
from typing import List, Optional
from datetime import datetime, date


class Zipcode(SQLModel, table=True):
    __tablename__ = 'zipcodes'
    
    zip_code: str = Field(primary_key=True, nullable=False)
    geometry: Optional[Geometry] = Field(
        sa_column=Column(Geometry("POLYGON", srid=4326), nullable=True)
    )

    # Define relationships if needed
    zipcode_people: List["ZipcodePeopleJoinTable"] = Relationship(back_populates="zipcode")

    class Config:
        arbitrary_types_allowed = True  # Allows Geometry type


class ZipcodePeopleJoinTable(SQLModel, table=True):
    __tablename__ = 'zipcode_people_join_table'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    zip_code: str = Field(foreign_key="zipcodes.zip_code")
    person_id: str = Field(foreign_key="people.id")

    # Define relationships
    zipcode: Optional[Zipcode] = Relationship(back_populates="zipcode_people")
    person: Optional["Person"] = Relationship(back_populates="zipcode_people")


class Person(SQLModel, table=True):
    __tablename__ = 'people'
    
    id: str = Field(primary_key=True, nullable=False)
    name: str = Field(nullable=False)
    current_party: Optional[str] = None
    current_district: Optional[str] = None
    current_chamber: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    image: Optional[str] = None
    links: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(Text)))  # Array of Text
    sources: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(Text)))  # Array of Text
    capitol_address: Optional[str] = None
    capitol_voice: Optional[str] = None
    capitol_fax: Optional[str] = None
    district_address: Optional[str] = None
    district_voice: Optional[str] = None
    district_fax: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    wikidata: Optional[str] = None
    jurisdiction_id: Optional[str] = None

    # Define relationships if needed
    zipcode_people: List[ZipcodePeopleJoinTable] = Relationship(back_populates="person")


class Bill(SQLModel, table=True):
    __tablename__ = 'bills'

    id: str = Field(primary_key=True)
    session: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    jurisdiction: Optional[dict] = Field(sa_column=Column(JSON))  # JSON column for dict
    from_organization: Optional[dict] = Field(sa_column=Column(JSON))  # JSON column for dict
    identifier: Optional[str] = None
    title: Optional[str] = None
    classification: Optional[List[str]] = Field(sa_column=Column(JSON))  # JSON for list of strings
    subject: Optional[List[str]] = Field(sa_column=Column(JSON))  # JSON for list of strings
    extras: Optional[dict] = Field(sa_column=Column(JSON))  # JSON column for dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    openstates_url: Optional[str] = None
    first_action_date: Optional[datetime] = None
    latest_action_date: Optional[datetime] = None
    latest_action_description: Optional[str] = None
    latest_passage_date: Optional[datetime] = None
    related_bills: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    abstracts: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    other_titles: Optional[List[str]] = Field(sa_column=Column(JSON))  # JSON for list of strings
    other_identifiers: Optional[List[str]] = Field(sa_column=Column(JSON))  # JSON for list of strings
    sponsorships: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    actions: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    sources: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    versions: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    documents: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts
    votes: Optional[List[dict]] = Field(sa_column=Column(JSON))  # JSON column for list of dicts



class Jurisdiction(SQLModel, table=True):
    __tablename__ = 'jurisdictions'

    id: str = Field(primary_key=True)
    name: Optional[str] = None
    classification: Optional[str] = None
    division_id: Optional[str] = None
    url: Optional[str] = None
    latest_bill_update: Optional[datetime] = None
    latest_people_update: Optional[datetime] = None
    organizations: Optional[dict] = Field(sa_column=Column(JSON))  # JSON column for dict
    legislative_sessions: Optional[dict] = Field(sa_column=Column(JSON))  # JSON column for dict
    latest_runs: Optional[dict] = Field(sa_column=Column(JSON))  # JSON column for dict
    last_processed: Optional[datetime] = None
