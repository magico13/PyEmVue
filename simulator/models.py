from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel
import datetime


def _format_time(time: datetime.datetime) -> str:
    """Convert time to utc, then format"""
    # check if aware
    if time.tzinfo and time.tzinfo.utcoffset(time) is not None:
        # aware, convert to utc
        time = time.astimezone(datetime.timezone.utc)
    else:
        # unaware, assume it's already utc
        time = time.replace(tzinfo=datetime.timezone.utc)
    time = time.replace(tzinfo=None)  # make it unaware
    iso_formatted = time.isoformat()
    # drop the milliseconds
    return iso_formatted[: iso_formatted.rfind(".")] + "Z"


class SimulatorBase(BaseModel):
    class Config:
        json_encoders = {datetime.datetime: _format_time}


class SimulatorCustomer(SimulatorBase):
    customerGid: int
    email: str
    firstName: str
    lastName: str
    createdAt: datetime.datetime


class SimulatorOutlet(SimulatorBase):
    deviceGid: int
    outletOn: bool
    loadGid: int


class SimulatorChargerRequest(SimulatorBase):
    deviceGid: int
    loadGid: int
    chargerOn: bool
    chargingRate: int
    maxChargingRate: int
    breakerPIN: Optional[str] = None


class SimulatorCharger(SimulatorBase):
    deviceGid: int
    loadGid: int
    message: str = "EV is not accepting charge"
    status: str = "Standby"
    icon: str = "CarConnected"
    iconLabel: str = "Offering Charge"
    debugCode: str = "311"
    iconDetailText: str = "Check your vehicle for a scheduled charge time."
    faultText: Optional[str] = None
    proControlCode: Optional[str] = None
    breakerPIN: Optional[str] = "0000"
    chargerOn: bool = True
    chargingRate: int = 40
    maxChargingRate: int = 40
    loadManagementEnabled: bool = False
    hideChargeRateSliderText: Optional[str] = None

    def set_to_standby(self):
        self.message = "EV is not accepting charge"
        self.status = "Standby"
        self.icon = "CarConnected"
        self.iconLabel = "Offering Charge"
        self.debugCode = "311"
        self.iconDetailText = "Check your vehicle for a scheduled charge time."


class SimulatorDeviceConnected(SimulatorBase):
    deviceGid: int
    connected: bool
    offlineSince: Optional[datetime.datetime]


class SimulatorChannel(SimulatorBase):
    deviceGid: int
    name: Optional[str]
    channelNum: str
    channelMultiplier: float = 1.0
    channelTypeGid: Optional[int]
    type: str


class SimulatorLatitudeLongitude(SimulatorBase):
    latitude: float
    longitude: float


class SimulatorLocationInformation(SimulatorBase):
    airConditioning: str = "true"
    heatSource: str = "electricFurnace"
    locationSqFt: str = "2000"
    numElectricCars: str = "0"
    locationType: str = "houseMultiLevel"
    numPeople: str = "4"
    swimmingPool: str = "false"
    hotTub: str = "false"
    primaryVehicle: Optional[str] = None


class SimulatorLocationProperties(SimulatorBase):
    timeZone: str
    latitudeLongitude: SimulatorLatitudeLongitude
    utilityRateGid: Optional[int]
    deviceName: Optional[str]
    displayName: Optional[str]
    deviceGid: int
    zipCode: str
    billingCycleStartDay: int
    usageCentPerKwHour: float
    peakDemandDollarPerKw: float
    locationInformation: SimulatorLocationInformation


class SimulatorSubDevice(SimulatorBase):
    deviceGid: int
    manufacturerDeviceId: str
    model: str
    firmware: Optional[str]
    channels: list[SimulatorChannel]


class SimulatorDevice(SimulatorBase):
    deviceGid: int
    manufacturerDeviceId: str
    model: str
    firmware: Optional[str]
    parentDeviceGid: Optional[int]
    parentChannelNum: Optional[str]
    locationProperties: SimulatorLocationProperties
    outlet: Optional[SimulatorOutlet]
    evCharger: Optional[SimulatorCharger]
    battery: Optional[dict]
    deviceConnected: SimulatorDeviceConnected
    devices: list[SimulatorSubDevice]
    channels: list[SimulatorChannel]


class CustomerDevicesResponse(SimulatorBase):
    customerGid: int
    email: str
    firstName: str
    lastName: str
    createdAt: datetime.datetime
    devices: list[SimulatorDevice]


class ChannelType(SimulatorBase):
    channelTypeGid: int
    description: str
    selectable: bool
    allowsBidirectional: bool


class SimulatorLoad(SimulatorBase):
    loadGid: int
    schedulesEnabled: bool
    nextScheduledEventText: Optional[str]
    peakDemandEnabled: bool
    excessGenerationEnabled: bool
    energyManagementText: Optional[str]
    energyManagementOverridden: bool
    warningText: Optional[str]


class StatusResponse(SimulatorBase):
    devicesConnected: list[SimulatorDeviceConnected]
    evChargers: list[SimulatorCharger]
    loads: list[SimulatorLoad]
    batteries: list[dict]
    outlets: list[SimulatorOutlet]


class CreateOutletRequest(SimulatorBase):
    deviceGid: int
    outletOn: bool = True
    name: Optional[str] = None
    parentDeviceGid: Optional[int] = None
    parentChannelNum: Optional[str] = None


class CreateChargerRequest(SimulatorBase):
    deviceGid: int
    chargerOn: bool = True
    name: Optional[str] = None
    breakerSize: int = 50
    parentDeviceGid: Optional[int] = None
    parentChannelNum: Optional[str] = None


class CreateVueRequest(SimulatorBase):
    deviceGid: int
    name: Optional[str] = None
    channelCount: int = 8
    parentDeviceGid: Optional[int] = None
    parentChannelNum: Optional[str] = None

class UpdateUsageRequest(SimulatorBase):
    watts: Optional[float] = None
    usage: Optional[float] = None
    scale: Optional[str] = "1MIN"

if TYPE_CHECKING:
    from .models import DeviceUsage  # Avoid circular import


class ChannelUsage(SimulatorBase):
    name: str
    percentage: float
    nestedDevices: list["DeviceUsage"]
    usage: Optional[float]
    deviceGid: int
    channelNum: str


class DeviceUsage(SimulatorBase):
    deviceGid: int
    channelUsages: list[ChannelUsage]


class DeviceListUsage(SimulatorBase):
    devices: list[DeviceUsage]
    energyUnit: str
    instant: datetime.datetime
    scale: str


class DeviceUsageResponse(SimulatorBase):
    deviceListUsages: DeviceListUsage
