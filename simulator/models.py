from typing import Optional
from pydantic import BaseModel
import datetime

def _format_time(time: datetime.datetime) -> str:
    '''Convert time to utc, then format'''
    # check if aware
    if time.tzinfo and time.tzinfo.utcoffset(time) is not None:
        # aware, convert to utc
        time = time.astimezone(datetime.timezone.utc)
    else:
        #unaware, assume it's already utc
        time = time.replace(tzinfo=
        datetime.timezone.utc)
    time = time.replace(tzinfo=None) # make it unaware
    iso_formatted = time.isoformat()
    # drop the milliseconds
    return iso_formatted[:iso_formatted.rfind('.')]+'Z'

class SimulatorBase(BaseModel):
    class Config:
        json_encoders = {
            datetime.datetime: _format_time
        }

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

class SimulatorDeviceConnected(SimulatorBase):
    deviceGid: int
    connected: bool
    offlineSince: Optional[datetime.datetime]

class SimulatorChannel(SimulatorBase):
    deviceGid: int
    name: Optional[str]
    channelNum: str
    channelMultiplier: float = 1.0
    channelTypeGid: int

class SimulatorLatitudeLongitude(SimulatorBase):
    latitude: float
    longitude: float

class SimulatorLocationInformation(SimulatorBase):
    airConditioning: str
    heatSource: str
    locationSqFt: str
    numElectricCars: str
    locationType: str
    numPeople: str

class SimulatorLocationProperties(SimulatorBase):
    timeZone: str
    latitudeLongitude: SimulatorLatitudeLongitude
    utilityRateGid: Optional[int]
    deviceName: str
    deviceGid: int
    zipCode: str
    billingCycleStartDay: int
    usageCentPerKwHour: float
    peakDemandDollarPerKw: float
    locationInformation: SimulatorLocationInformation

class SimulatorDevice(SimulatorBase):
    deviceGid: int
    manufacturerDeviceId: str
    model: str
    firmware: str
    parentDeviceGid: int
    parentChannelNum: str
    locationProperties: SimulatorLocationProperties
    outlet: Optional[SimulatorOutlet]
    evCharger: Optional[dict]
    battery: Optional[dict]
    deviceConnected: SimulatorDeviceConnected
    devices: list
    channels: list[SimulatorChannel]

class SimulatorCustomerDevices(SimulatorBase):
    customerGid: int
    email: str
    firstName: str
    lastName: str
    createdAt: datetime.datetime
    devices: list[SimulatorDevice]