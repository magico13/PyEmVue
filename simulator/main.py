from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from simulator.models import *
from simulator.simulator_state import SimulatorState

state = SimulatorState()

# Set up a default home with an 8 channel Vue, 4 outlets, and 1 EV charger
state.add_vue(1000, "Home", channelCount=8)
state.add_outlet(1001, "plug1", True, parentDeviceGid=1000, parentChannelNum="1")
state.add_outlet(1002, "plug2", False, parentDeviceGid=1000, parentChannelNum="1")
state.add_outlet(1003, "plug3", True, parentDeviceGid=1000, parentChannelNum="4")
state.add_outlet(1004, "plug4", False, parentDeviceGid=1000, parentChannelNum="1,2,3")
state.add_charger(
    1005, "EV", True, breakerSize=50, parentDeviceGid=1000, parentChannelNum="1,2,3"
)
# the EV charger is pulling 40 amps at 240 volts
state.set_channel_1min_watts(1005, "1,2,3", 40 * 240)

# plug 3 is pulling 10 amps at 120 volts
state.set_channel_1min_watts(1003, "1,2,3", 10 * 120)

# plug 1 is pulling 5 amps at 120 volts
state.set_channel_1min_watts(1001, "1,2,3", 5 * 120)

# channel 2 is generating 10 amps and is bidirectional
state.set_channel_bidirectionality(1000, "2", True)
state.set_channel_1min_watts(1000, "2", -10 * 120)

# the overall house is pulling 85 amps at 240 volts
state.set_channel_1min_watts(1000, "1,2,3", 85 * 240)

# the balance is effectively 42.5 amps
# TODO: this should be calculated based on the actual usage
state.set_channel_1min_watts(1000, "Balance", 42.5 * 240)


app = FastAPI()

# All APIs that are supported are:
# API_CHANNELS = 'devices/{deviceGid}/channels'
# API_CHANNEL_TYPES = 'devices/channels/channeltypes'
# API_CHARGER = 'devices/evcharger'
# API_CHART_USAGE = 'AppAPI?apiMethod=getChartUsage&deviceGid={deviceGid}&channel={channel}&start={start}&end={end}&scale={scale}&energyUnit={unit}'
# API_CUSTOMER = 'customers'
# API_CUSTOMER_DEVICES = 'customers/devices'
# API_DEVICES_USAGE = 'AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGids}&instant={instant}&scale={scale}&energyUnit={unit}'
# API_DEVICE_PROPERTIES = 'devices/{deviceGid}/locationProperties'
# API_GET_STATUS = 'customers/devices/status'
# API_OUTLET = 'devices/outlet'
# API_VEHICLES = 'customers/vehicles'
# API_VEHICLE_STATUS = 'vehicles/v2/settings?vehicleGid={vehicleGid}'


class CustomException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class NotAuthorizedException(CustomException):
    def __init__(self, deviceGid: int):
        self.status_code = 401
        self.message = f"{state.customer.email} is not authorized on the requested deviceGid {deviceGid}"


@app.exception_handler(CustomException)
async def unicorn_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )


@app.get("/customers")
def get_customers() -> SimulatorCustomer:
    return state.customer


@app.get("/customers/devices")
def get_customers_devices() -> CustomerDevicesResponse:
    return state.get_customers_devices()


@app.get("/devices/{deviceGid}/locationProperties")
def get_devices_locationProperties(deviceGid: int) -> SimulatorLocationProperties:
    for device in state.devices:
        if device.deviceGid == deviceGid:
            return device.locationProperties
    # return a 401 if the deviceGid is not found
    raise NotAuthorizedException(deviceGid)


@app.get("/devices/channels/channeltypes")
def get_devices_channels_channelTypes() -> list[ChannelType]:
    return state.channel_types


@app.get("/customers/devices/status")
def get_customers_devices_status() -> StatusResponse:
    return state.get_status()


@app.put("/devices/outlet")
def put_devices_outlet(outlet: SimulatorOutlet) -> SimulatorOutlet:
    for existingOutlet in state.outlets:
        if existingOutlet.deviceGid == outlet.deviceGid:
            existingOutlet.outletOn = outlet.outletOn
            existingOutlet.loadGid = outlet.loadGid
            return existingOutlet
    # return a 401 if the deviceGid is not found
    raise NotAuthorizedException(outlet.deviceGid)


@app.put("/devices/evcharger")
def put_devices_evcharger(charger: SimulatorChargerRequest) -> SimulatorCharger:
    for existingCharger in state.chargers:
        if existingCharger.deviceGid == charger.deviceGid:
            existingCharger.chargerOn = charger.chargerOn
            existingCharger.chargingRate = charger.chargingRate
            existingCharger.maxChargingRate = charger.maxChargingRate
            existingCharger.breakerPIN = charger.breakerPIN
            return existingCharger
    # return a 401 if the deviceGid is not found
    raise NotAuthorizedException(charger.deviceGid)


# API_DEVICES_USAGE = 'AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGids}&instant={instant}&scale={scale}&energyUnit={unit}'
@app.get("/AppAPI")
def get_app_api(
    deviceGids: Optional[str] = None,
    instant: Optional[datetime.datetime] = None,
    scale: str = "1MIN",
    energyUnit: str = "KilowattHours",
) -> DeviceUsageResponse:
    return state.get_devices_usage(
        deviceGids, instant or datetime.datetime.utcnow(), scale, energyUnit
    )


# meta APIs for controlling the simulator
@app.post("/simulator/vue")
def post_create_vue(vue: CreateVueRequest) -> SimulatorDevice:
    created = state.add_vue(
        vue.deviceGid,
        vue.name,
        vue.channelCount,
        vue.parentDeviceGid,
        vue.parentChannelNum,
    )
    return created


@app.post("/simulator/outlet")
def post_create_outlet(outlet: CreateOutletRequest) -> SimulatorOutlet:
    created = state.add_outlet(
        outlet.deviceGid,
        outlet.name,
        outlet.outletOn,
        outlet.parentDeviceGid,
        outlet.parentChannelNum,
    )
    return created


@app.post("/simulator/charger")
def post_create_charger(charger: CreateChargerRequest) -> SimulatorCharger:
    created = state.add_charger(
        charger.deviceGid,
        charger.name,
        charger.chargerOn,
        charger.breakerSize,
        charger.parentDeviceGid,
        charger.parentChannelNum,
    )
    return created


@app.delete("/simulator/device/{deviceGid}")
def delete_device(deviceGid: int, response: Response) -> SimulatorDevice:
    deleted = state.delete_device(deviceGid)
    if deleted is None:
        response.status_code = 404
        return response  # type: ignore
    return deleted


@app.put("/simulator/device/{deviceGid}/channel/{channelNum}/usage")
def put_channel_usage(
    deviceGid: int, channelNum: str, updateUsage: UpdateUsageRequest
) -> float | None:
    if updateUsage.scale == "1MIN":
        if updateUsage.usage is not None:  # usage takes precedence
            state.set_channel_1min_usage(deviceGid, channelNum, updateUsage.usage)
        elif updateUsage.watts is not None:
            state.set_channel_1min_watts(deviceGid, channelNum, updateUsage.watts)
        else:
            # return a 400 if neither usage nor watts is provided
            raise ValueError("Either usage or watts must be provided")
        # probably should return the state of the channel here
        return state.get_channel_1min_usage(deviceGid, channelNum)
    # other scales are not supported yet
