import datetime
from typing import Any, Optional

from pydantic import Field, RootModel

from pyemvue.basemodel import BaseModel, LocationProperties


class Outlet(BaseModel):
    device_gid: int = Field(default=0)
    outlet_on: bool = Field(default=False)
    load_gid: int = Field(default=0)
    # don't have support for schedules yet


class Charger(BaseModel):
    device_gid: int = Field(default=0)
    charger_on: bool = Field(default=False)
    message: str = Field(default="")
    status: str = Field(default="")
    icon: str = Field(default="")
    icon_label: str = Field(default="")
    icon_detail_text: str = Field(default="")
    fault_text: str = Field(default="")
    charging_rate: float = Field(default=0)
    max_charging_rate: float = Field(default=0)
    off_peak_schedules_enabled: bool = Field(default=False)
    # don't have support for schedules yet
    load_gid: int = Field(default=0)
    debug_code: str = Field(default="")
    pro_control_code: str = Field(default="")
    breaker_pin: str = Field(default="")


class DeviceConnected(BaseModel):
    device_gid: int = Field(default=0)
    connected: bool = Field(default=False)
    offline_since: Optional[datetime.datetime] = Field(default=None)


class Channel(BaseModel):
    device_gid: int = Field(default=0)
    name: Optional[str] = Field(default=None)
    channel_num: str
    channel_multiplier: float
    channel_type_gid: Optional[int]


class VueDeviceChannel(BaseModel):
    device_gid: int = Field(default=0)
    manufacturer_device_id: str = Field(default="")
    model: str
    firmware: Optional[str]
    channels: list[Channel]


class VueDevice(BaseModel):
    device_gid: int = Field(default=0)
    manufacturer_device_id: str = Field(default="")
    model: str = Field(default="")
    firmware: str = Field(default="")
    parent_device_gid: Optional[int] = Field(default=None)
    parent_channel_num: Optional[str] = Field(default=None)
    location_properties: LocationProperties = Field(default=LocationProperties())
    outlet: Optional[Outlet] = Field(default=None)
    ev_charger: Optional[Charger] = Field(default=None)
    battery: None
    device_connected: DeviceConnected = Field(...)
    devices: list[VueDeviceChannel] = Field(default=[])
    channels: list[Channel] = Field(default=[])


class CustomerDevices(BaseModel):
    customer_gid: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime.datetime
    devices: list[VueDevice]


class ChannelUsage(BaseModel):
    name: str
    usage: float
    device_gid: int
    channel_num: str
    percentage: float
    nested_devices: list["Device"]


class Device(BaseModel):
    device_gid: int
    channel_usages: list[ChannelUsage]


class DeviceListUsages(BaseModel):
    instant: datetime.datetime
    scale: str
    devices: list[Device]
    energy_unit: str


class DeviceListUsage(BaseModel):
    device_list_usages: DeviceListUsages


class Load(BaseModel):
    load_gid: int
    schedules_enabled: bool
    next_scheduled_event_text: Optional[str]
    peak_demand_enabled: bool
    excess_generation_enabled: bool
    energy_management_text: Optional[str]
    energy_management_overridden: bool
    warning_text: Optional[str]


class DevicesStatus(BaseModel):
    devicesConnected: list[DeviceConnected]
    evChargers: list[Charger]
    loads: list[Load]
    batteries: list[dict[str, Any]]
    outlets: list[Outlet]


# TODO...
VueDeviceChannelUsage = dict[str, Any]
VueUsageDevice = dict[str, Any]


class ChannelType(BaseModel):
    channel_type_gid: int = Field(default=0)
    description: str = Field(default="")
    selectable: bool = Field(default=False)


class ChannelTypeList(RootModel):
    root: list[ChannelType]


class Vehicle(BaseModel):
    vehicle_gid: int = Field(default=0)
    vendor: str = Field(default="")
    api_id: str = Field(default="")
    display_name: str = Field(default="")
    load_gid: str = Field(default="")
    make: str = Field(default="")
    model: str = Field(default="")
    year: int = Field(default=0)


class VehicleList(RootModel):
    root: list[Vehicle]


class VehicleStatus(BaseModel):
    vehicle_gid: int = Field(default=0)
    vehicle_state: str = Field(default="")
    battery_level: float = Field(default=0.0)
    battery_range: float = Field(default=0.0)
    charging_state: str = Field(default="")
    charge_limit_percent: float = Field(default=0.0)
    minutes_to_full_charge: float = Field(default=0.0)
    charge_current_request: int = Field(default=0)
    charge_current_request_max: int = Field(default=0)
