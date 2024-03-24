from __future__ import annotations

import datetime
from typing import Any, Optional

import pydantic
from pydantic import Field
from humps import camelize

class BaseModel(pydantic.BaseModel):
    class Config:
        alias_generator = camelize

    # for backwards compatibility
    def as_dictionary(self) -> dict[str, Any]:
        return self.model_dump()


class LatitudeLongitude(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class LocationInformation(BaseModel):
    air_conditioning: Optional[str]
    heat_source: Optional[str]
    location_sq_ft: Optional[str]
    num_electric_cars: Optional[str]
    location_type: Optional[str]
    num_people: Optional[str]
    swimming_pool: Optional[str]
    hot_tub: Optional[str]

class LocationProperties(BaseModel):
    display_name: Optional[str] = Field(default=None)
    device_gid: Optional[int] = Field(default=None)
    device_name: Optional[str] = Field(default=None)
    latitude_longitude: Optional[LatitudeLongitude] = Field(default=None)
    time_zone: Optional[str] = Field(default=None)
    utility_rate_gid: Optional[str] = Field(default=None)
    billing_cycle_start_day: Optional[int] = Field(default=None)
    location_information: Optional[LocationInformation] = Field(default=None)
    peak_demand_dollar_per_kw: Optional[float] = Field(default=None)
    usageCentPerKwHour: Optional[float] = Field(default = None)
    zip_code: Optional[str] = Field(default=None)


class ChannelUsageData(BaseModel):
    first_usage_instant: datetime.datetime
    usage_list: list[Optional[float]]
