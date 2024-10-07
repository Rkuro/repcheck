from typing import (
    List
)
from pydantic import (
    BaseModel,
    PastDate,
    EmailStr,
    HttpUrl
)

class Representative(BaseModel):
    # Source data fields
    id: int
    name: str
    current_party: str = ""
    current_district: str = ""
    current_chamber: str = ""
    first_name: str = ""
    last_name: str = ""
    gender: str = ""
    biography: str = ""
    birth_date: PastDate = "1970-01-01"
    death_date: PastDate = "1970-01-01"
    image: HttpUrl = ""
    email: EmailStr = ""
    links: List[str]
    sources: List[str]
    capitol_address: str = ""
    capitol_phone: str = ""
    capitol_fax: str = ""
    district_address: str = ""
    district_phone: str = ""
    district_fax: str = ""
    twitter: str = ""
    youtube: str = ""
    instagram: str = ""
    facebook: str = ""

    # Derived fields
    state: str
    
