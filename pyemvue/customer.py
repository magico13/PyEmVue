from datetime import datetime

from pyemvue.basemodel import BaseModel
from pydantic import Field


class Customer(BaseModel):        
    customer_gid: int = Field(default=0)
    email: str = Field(default="")
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    created_at: datetime = Field(default=datetime(1970, 1, 1))
