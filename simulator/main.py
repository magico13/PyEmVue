from __future__ import annotations

import datetime
from typing import Any, Optional
from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from simulator.models import (
    ChannelType,
    CreateChargerRequest,
    CreateOutletRequest,
    CreateVueRequest,
    CustomerDevicesResponse,
    DeviceUsageResponse,
    EvseControlCommandRequest,
    EvseSettingsRequest,
    ExcessGenerationConfigRequest,
    SimulatorCharger,
    SimulatorChargerRequest,
    SimulatorCustomer,
    SimulatorDevice,
    SimulatorLocationProperties,
    SimulatorOutlet,
    UpdateUsageRequest,
)
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


# ---------------------------------------------------------------------------
# Legacy API Routes
# ---------------------------------------------------------------------------


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
    raise NotAuthorizedException(deviceGid)


@app.get("/devices/channels/channeltypes")
def get_devices_channels_channelTypes() -> list[ChannelType]:
    return state.channel_types


@app.get("/customers/devices/status")
@app.get("/v1/customers/devices/status")
def get_customers_devices_status(
    authorization: Optional[str] = Header(None),
    authtoken: Optional[str] = Header(None),
) -> Any:
    if authorization is not None and not authorization.startswith("Bearer "):
        raise CustomException(401, "Invalid Bearer token")
    return state.get_status_v1()


@app.put("/devices/outlet")
def put_devices_outlet(outlet: SimulatorOutlet) -> SimulatorOutlet:
    for existingOutlet in state.outlets:
        if existingOutlet.deviceGid == outlet.deviceGid:
            existingOutlet.outletOn = outlet.outletOn
            existingOutlet.loadGid = outlet.loadGid
            return existingOutlet
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
    raise NotAuthorizedException(charger.deviceGid)


@app.get("/AppAPI")
def get_app_api(
    deviceGids: Optional[str] = None,
    instant: Optional[datetime.datetime] = None,
    scale: str = "1MIN",
    energyUnit: str = "KilowattHours",
) -> DeviceUsageResponse:
    return state.get_devices_usage(
        deviceGids, instant or datetime.datetime.now(datetime.timezone.utc), scale, energyUnit
    )


# ---------------------------------------------------------------------------
# V1 API Routes
# ---------------------------------------------------------------------------


@app.get("/v1/customers/devices")
def get_customers_devices_v1() -> dict[str, Any]:
    return state.get_customers_devices_v1()


@app.get("/v1/customers/devices/channels")
def get_customers_devices_channels_v1() -> list[dict[str, Any]]:
    return state.get_channels_v1()


@app.get("/v1/customers/sites")
def get_customers_sites_v1() -> dict[str, Any]:
    return state.get_sites_v1()


@app.get("/v1/customers/devices/usages")
@app.get("/v1/customers/devices/usage-timeseries")
def get_customers_devices_usages_v1(
    device_gids: Optional[str] = None,
    deviceGids: Optional[str] = None,
    instant: Optional[datetime.datetime] = None,
    scale: str = "SECOND",
    energy_unit: str = "KILOWATT_HOURS",
    energyUnit: Optional[str] = None,
) -> dict[str, Any]:
    effective_gids = device_gids or deviceGids
    effective_unit = energyUnit or energy_unit
    return state.get_usages_v1(
        device_gids=effective_gids,
        instant=instant,
        scale=scale,
        energy_unit=effective_unit,
    )


@app.get("/v1/customers/evse/control")
@app.get("/customers/evse/control")
def get_evse_control(device_id: Optional[str] = None) -> dict[str, Any]:
    return state.get_evse_control(device_id)


@app.post("/v1/customers/evse/control")
@app.post("/customers/evse/control")
def post_evse_control(payload: EvseControlCommandRequest) -> dict[str, Any]:
    success = state.post_evse_control(payload.device_id, payload.command)
    return {"success": success}


@app.get("/v1/devices/evses")
@app.get("/devices/evses")
def get_devices_evses(device_ids: Optional[str] = None) -> dict[str, Any]:
    ids = (
        [x.strip() for x in device_ids.split(",") if x.strip()]
        if device_ids
        else None
    )
    return state.get_evses_v1(ids)


@app.put("/v1/devices/evses/settings")
@app.put("/devices/evses/settings")
@app.put("/v1/customers/devices/settings")
@app.put("/customers/devices/settings")
def put_devices_evses_settings(payload: EvseSettingsRequest) -> dict[str, Any]:
    settings_dicts = [
        {"device_id": item.device_id, "charge_rate_amps": item.charge_rate_amps}
        for item in payload.settings
    ]
    return state.set_evse_settings_v1(settings_dicts)


@app.get("/v1/customers/excess-generation")
@app.get("/customers/excess-generation")
def get_excess_generation_monitors() -> dict[str, Any]:
    return state.get_excess_generation_monitors()


@app.get("/v1/customers/energy-monitor/excess-generation")
@app.get("/customers/energy-monitor/excess-generation")
def get_energy_monitor_excess_generation(device_id: str) -> dict[str, Any]:
    return state.get_excess_generation(device_id)


@app.post("/v1/customers/energy-monitor/excess-generation")
@app.post("/customers/energy-monitor/excess-generation")
def post_energy_monitor_excess_generation(
    payload: ExcessGenerationConfigRequest,
) -> dict[str, Any]:
    success = state.set_excess_generation(
        device_id=payload.device_id,
        loads=payload.loads,
        solar_window=payload.solar_window,
        sunrise=payload.sunrise,
        sunset=payload.sunset,
    )
    return {"success": success}


@app.get("/v1/customers/stream")
def get_customers_stream(event_types: Optional[str] = None) -> PlainTextResponse:
    return PlainTextResponse(
        "event: DEVICE_STATUS\ndata: {}\n\n", media_type="text/event-stream"
    )


# ---------------------------------------------------------------------------
# Simulator Control Meta APIs
# ---------------------------------------------------------------------------


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
        if updateUsage.usage is not None:
            state.set_channel_1min_usage(deviceGid, channelNum, updateUsage.usage)
        elif updateUsage.watts is not None:
            state.set_channel_1min_watts(deviceGid, channelNum, updateUsage.watts)
        else:
            raise ValueError("Either usage or watts must be provided")
        return state.get_channel_1min_usage(deviceGid, channelNum)
    return None
