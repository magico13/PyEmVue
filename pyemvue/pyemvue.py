from __future__ import annotations

import time
from typing import Any, Optional, Union
import requests
import datetime
import json
from dateutil.parser import parse

# Our files
from pyemvue.auth import Auth, SimulatedAuth
from pyemvue.enums import Scale, Unit
from pyemvue.customer import Customer
from pyemvue.device import (
    ChannelDevice,
    ChargerDevice,
    EnergyMonitorExcessGeneration,
    EvseControlStatus,
    ExcessGenerationLoad,
    ExcessGenerationMonitors,
    VueDevice,
    VueSite,
    OutletDevice,
    VueDeviceChannel,
    VueDeviceChannelUsage,
    VueUsageDevice,
    ChannelType,
    Vehicle,
    VehicleStatus,
)

API_ROOT = "https://api.emporiaenergy.com"
API_CHANNELS = "devices/{deviceGid}/channels"
API_CHANNEL_TYPES = "devices/channels/channeltypes"
API_CHARGER = "devices/evcharger"
API_CHART_USAGE = "AppAPI?apiMethod=getChartUsage&deviceGid={deviceGid}&channel={channel}&start={start}&end={end}&scale={scale}&energyUnit={unit}"
API_CUSTOMER = "customers"
API_CUSTOMER_DEVICES = "customers/devices"
API_DEVICES_USAGE = "AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGids}&instant={instant}&scale={scale}&energyUnit={unit}"
API_DEVICE_PROPERTIES = "devices/{deviceGid}/locationProperties"
API_GET_STATUS = "customers/devices/status"
API_OUTLET = "devices/outlet"
API_VEHICLES = "customers/vehicles"
API_VEHICLE_STATUS = "vehicles/v2/settings?vehicleGid={vehicleGid}"

# V1 API endpoints
API_ROOT_V1 = "https://api.emporiaenergy.com/v1"
API_DEVICES_V1 = "customers/devices"
API_CHANNELS_V1 = "customers/devices/channels"
API_SITES_V1 = "customers/sites"
API_DEVICES_USAGE_V1 = "customers/devices/usages"
API_GET_EVSES = "devices/evses?device_ids={deviceIds}"
API_EVSE_CONTROL = "customers/evse/control"
API_EVSE_SETTINGS = "devices/evses/settings"
API_EXCESS_GENERATION = "customers/excess-generation"
API_ENERGY_MONITOR_EXCESS_GENERATION = "customers/energy-monitor/excess-generation"

VALID_EVSE_CONTROL_COMMANDS: tuple[str, ...] = (
    "TURN_ON",
    "TURN_OFF",
    "CHARGE_AT_FULL_POWER",
)

API_MAINTENANCE = (
    "https://s3.amazonaws.com/com.emporiaenergy.manual.ota/maintenance/maintenance.json"
)


class PyEmVue(object):
    def __init__(self, connect_timeout: float = 6.03, read_timeout: float = 10.03):
        self.username = None
        self.token_storage_file = None
        self.customer = None
        self.auth: Optional[Auth] = None
        self.auth_v1: Optional[Auth] = None
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def down_for_maintenance(self) -> Optional[str]:
        """Checks to see if the API is down for maintenance, returns the reported message if present."""
        response = requests.get(API_MAINTENANCE)
        if response.status_code == 404:
            return None
        if response.text:
            j = response.json()
            if "msg" in j:
                return j["msg"]

    def get_devices(self) -> "list[VueDevice]":
        """Get all devices under the current customer account."""
        response = self.auth.request("get", API_CUSTOMER_DEVICES)
        response.raise_for_status()
        devices: list[VueDevice] = []
        if response.text:
            j = response.json()
            if "devices" in j:
                for dev in j["devices"]:
                    devices.append(VueDevice().from_json_dictionary(dev))
                    if "devices" in dev:
                        for subdev in dev["devices"]:
                            devices.append(VueDevice().from_json_dictionary(subdev))
        return devices

    def get_devices_v1(self, include_channels: bool = True) -> list[VueDevice]:
        """Get all devices under the current customer account using the V1 endpoint."""
        auth = self.auth_v1 or self.auth
        response = auth.request("get", API_DEVICES_V1)
        response.raise_for_status()
        devices: list[VueDevice] = []
        if response.text:
            j = response.json()
            raw_devices = j.get("devices", []) if isinstance(j, dict) else j
            for dev in raw_devices:
                devices.append(VueDevice().from_json_dictionary(dev))

        # Post-parse tree linking pass:
        # Resolve parent_device_id -> parent_device_gid, parent_device_gid -> parent_device_id, and parent.children
        devices_by_id: dict[str, VueDevice] = {
            d.device_id: d for d in devices if d.device_id
        }
        devices_by_gid: dict[int, VueDevice] = {
            d.device_gid: d for d in devices if d.device_gid
        }

        for d in devices:
            parent = None
            if d.parent_device_id and d.parent_device_id in devices_by_id:
                parent = devices_by_id[d.parent_device_id]
                if not d.parent_device_gid:
                    d.parent_device_gid = parent.device_gid
            elif d.parent_device_gid and d.parent_device_gid in devices_by_gid:
                parent = devices_by_gid[d.parent_device_gid]
                if not d.parent_device_id:
                    d.parent_device_id = parent.device_id

            if parent:
                # Map parent_channel_id -> parent_channel_num if channel number is missing
                if d.parent_channel_id and not d.parent_channel_num:
                    if parent.channels:
                        for ch in parent.channels:
                            if (
                                ch.channel_id
                                and ch.channel_id.lower() == d.parent_channel_id.lower()
                            ):
                                d.parent_channel_num = ch.channel_num
                                break
                            if (
                                ch.channel_num
                                and ch.channel_num.lower()
                                == d.parent_channel_id.lower()
                            ):
                                d.parent_channel_num = ch.channel_num
                                break
                    if not d.parent_channel_num:
                        if d.parent_channel_id == "Mains":
                            d.parent_channel_num = "1,2,3"
                        elif d.parent_channel_id.startswith("Branch_"):
                            d.parent_channel_num = d.parent_channel_id.split("_")[1]
                        else:
                            d.parent_channel_num = d.parent_channel_id

                # Map parent_channel_num -> parent_channel_id if channel id is missing
                elif (
                    d.parent_channel_num and not d.parent_channel_id and parent.channels
                ):
                    for ch in parent.channels:
                        if (
                            ch.channel_num
                            and ch.channel_num.lower() == d.parent_channel_num.lower()
                        ):
                            d.parent_channel_id = ch.channel_id
                            break

                if d not in parent.children:
                    parent.children.append(d)

        if not include_channels:
            for d in devices:
                d.channels = []

        return devices

    def get_sites(self) -> list[VueSite]:
        """Get all configured sites for the customer."""
        auth = self.auth_v1 or self.auth
        response = auth.request("get", API_SITES_V1)
        response.raise_for_status()
        sites: list[VueSite] = []
        if response.text:
            j = response.json()
            raw_sites = j.get("sites", []) if isinstance(j, dict) else j
            for s in raw_sites:
                sites.append(VueSite().from_json_dictionary(s))
        return sites

    def get_channels(self) -> list[ChannelDevice]:
        """Get all channels under the current customer account using the V1 endpoint."""
        auth = self.auth_v1 or self.auth
        response = auth.request("get", API_CHANNELS_V1)
        response.raise_for_status()
        channels: list[ChannelDevice] = []
        if response.text:
            j = response.json()
            if isinstance(j, list):
                for channel in j:
                    channels.append(ChannelDevice().from_json_dictionary(channel))
        return channels

    def populate_device_properties(self, device: VueDevice) -> VueDevice:
        """Get details about a specific device"""
        url = API_DEVICE_PROPERTIES.format(deviceGid=device.device_gid)
        response = self.auth.request("get", url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            device.populate_location_properties_from_json(j)
        return device

    def update_channel(self, channel: VueDeviceChannel) -> VueDeviceChannel:
        """Update the channel with the provided state."""
        url = API_CHANNELS.format(deviceGid=channel.device_gid)
        response = self.auth.request("put", url, json=channel.as_dictionary())
        response.raise_for_status()
        if response.text:
            j = response.json()
            channel.from_json_dictionary(j)
        return channel

    def get_customer_details(self) -> Optional[Customer]:
        """Get details for the current customer."""
        response = self.auth.request("get", API_CUSTOMER)
        response.raise_for_status()
        if response.text:
            j = response.json()
            return Customer().from_json_dictionary(j)
        return None

    def get_device_list_usage(
        self,
        deviceGids: Union[str, "list[str]"],
        instant: Optional[datetime.datetime],
        scale=Scale.SECOND.value,
        unit=Unit.KWH.value,
        max_retry_attempts: int = 5,
        initial_retry_delay: float = 2.0,
        max_retry_delay: float = 30.0,
    ) -> "dict[int, VueUsageDevice]":
        """Returns a nested dictionary of VueUsageDevice and VueDeviceChannelUsage with the total usage of the devices over the specified scale. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if not instant:
            instant = datetime.datetime.now(datetime.timezone.utc)
        gids = deviceGids
        if isinstance(deviceGids, list):
            gids = "+".join(map(str, deviceGids))

        url = API_DEVICES_USAGE.format(
            deviceGids=gids, instant=_format_time(instant), scale=scale, unit=unit
        )
        attempts = 0
        update_failed = True
        max_retry_attempts = max(max_retry_attempts, 1)
        initial_retry_delay = max(initial_retry_delay, 0.5)
        max_retry_delay = max(max_retry_delay, 0)
        devices: dict[int, VueUsageDevice] = {}

        while attempts < max_retry_attempts and update_failed:
            update_failed = False  # reset the flag, if we fail we'll set it again
            if attempts > 0:
                # if we're retrying, wait a bit before trying again using an exponential backoff
                delay = min(
                    initial_retry_delay * (2 ** (attempts - 1)),
                    max_retry_delay,
                )
                time.sleep(delay)
            attempts += 1
            response = self.auth.request("get", url)
            if response.status_code == 200 and response.text:
                j = response.json()
                if "deviceListUsages" in j and "devices" in j["deviceListUsages"]:
                    timestamp = parse(j["deviceListUsages"]["instant"])
                    for device in j["deviceListUsages"]["devices"]:
                        populated = VueUsageDevice(
                            timestamp=timestamp
                        ).from_json_dictionary(device)
                        # data is missing if any usage is None for any channels. In that case we retry the request and merge results.
                        data_missing = any(
                            channel_usage.usage is None
                            for channel_usage in populated.channels.values()
                        )
                        update_failed = update_failed or data_missing
                        if not data_missing or attempts >= max_retry_attempts:
                            # only overwrite the device data if we have all the data or we've run out of retries
                            devices[populated.device_gid] = populated
                else:
                    update_failed = True
            else:
                update_failed = True

        # if we still haven't fully succeeded, return the data we did manage to get

        if response:
            response.raise_for_status()
        return devices

    def get_device_list_usage_v1(
        self,
        device_gids: list[Union[int, str]],
        instant: Optional[datetime.datetime] = None,
        scale: str = "SECOND",
        energy_unit: str = "KILOWATT_HOURS",
    ) -> dict[int, VueUsageDevice]:
        """Returns a dictionary of VueUsageDevice with the usage of the devices over the specified scale from the V1 API."""
        auth = self.auth_v1 or self.auth
        if not auth:
            raise ValueError(
                "Not authenticated. Call login() or login_with_tokens() first."
            )

        if not instant:
            instant = datetime.datetime.now(datetime.timezone.utc)

        if hasattr(scale, "name"):
            scale_val = scale.name
        else:
            scale_val = str(scale)

        if hasattr(energy_unit, "name"):
            if energy_unit == Unit.VOLTS:
                unit_val = "VOLTAGE"
            elif energy_unit == Unit.KWH:
                unit_val = "KILOWATT_HOURS"
            else:
                unit_val = energy_unit.name
        else:
            unit_val = str(energy_unit)

        if isinstance(device_gids, (str, int)):
            gids_str = str(device_gids)
        else:
            gids_str = ",".join(map(str, device_gids))

        params = {
            "device_gids": gids_str,
            "instant": _format_time(instant),
            "scale": scale_val,
            "energy_unit": unit_val,
        }

        response = auth.request("get", API_DEVICES_USAGE_V1, params=params)
        response.raise_for_status()

        devices: dict[int, VueUsageDevice] = {}
        if response.text:
            j = response.json()
            timestamp = (
                parse(j["instant"])
                if isinstance(j, dict) and "instant" in j and j["instant"]
                else instant
            )
            raw_usages = j.get("device_usages", []) if isinstance(j, dict) else j
            for dev in raw_usages:
                populated = VueUsageDevice(timestamp=timestamp).from_json_dictionary(
                    dev
                )
                devices[populated.device_gid] = populated

        return devices

    def get_chart_usage(
        self,
        channel: Union[VueDeviceChannel, VueDeviceChannelUsage],
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        scale=Scale.SECOND.value,
        unit=Unit.KWH.value,
    ) -> "tuple[list[float], Optional[datetime.datetime]]":
        """Gets the usage over a given time period and the start of the measurement period. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if channel.channel_num in ["MainsFromGrid", "MainsToGrid"]:
            # This is not populated for the special Mains data as of right now
            return [], start
        if not start:
            start = datetime.datetime.now(datetime.timezone.utc)
        if not end:
            end = datetime.datetime.now(datetime.timezone.utc)
        url = API_CHART_USAGE.format(
            deviceGid=channel.device_gid,
            channel=channel.channel_num,
            start=_format_time(start),
            end=_format_time(end),
            scale=scale,
            unit=unit,
        )
        response = self.auth.request("get", url)
        response.raise_for_status()
        usage: list[float] = []
        instant = start
        if response.text:
            j = response.json()
            if "firstUsageInstant" in j:
                instant = parse(j["firstUsageInstant"])
            if "usageList" in j:
                usage = j["usageList"]
        return usage, instant

    def get_outlets(self) -> "list[OutletDevice]":
        """Return a list of outlets linked to the account. Deprecated, use get_devices_status instead."""
        response = self.auth.request("get", API_GET_STATUS)
        response.raise_for_status()
        outlets = []
        if response.text:
            j = response.json()
            if j and "outlets" in j and j["outlets"]:
                for raw_outlet in j["outlets"]:
                    outlets.append(OutletDevice().from_json_dictionary(raw_outlet))
        return outlets

    def update_outlet(
        self, outlet: OutletDevice, on: Optional[bool] = None
    ) -> OutletDevice:
        """Primarily to turn an outlet on or off. If the on parameter is not provided then uses the value in the outlet object.
        If on parameter provided uses the provided value."""
        if on is not None:
            outlet.outlet_on = on

        response = self.auth.request("put", API_OUTLET, json=outlet.as_dictionary())
        response.raise_for_status()
        outlet.from_json_dictionary(response.json())
        return outlet

    def get_chargers(self) -> "list[ChargerDevice]":
        """Return a list of EVSEs/chargers linked to the account. Deprecated, use get_devices_status instead."""
        response = (self.auth_v1 or self.auth).request("get", API_GET_STATUS)
        response.raise_for_status()
        chargers = []
        if response.text:
            j = response.json()
            if j:
                evses_raw = j.get("evses") or j.get("evChargers") or []
                for raw_charger in evses_raw:
                    chargers.append(ChargerDevice().from_json_dictionary(raw_charger))
        return chargers

    def update_charger(
        self,
        charger: ChargerDevice,
        on: Optional[bool] = None,
        charge_rate: Optional[int] = None,
    ) -> ChargerDevice:
        """Primarily to enable/disable an evse/charger. The on and charge_rate parameters override the values in the object if provided"""
        if on is not None:
            charger.charger_on = on
        if charge_rate:
            charger.charging_rate = charge_rate

        response = self.auth.request("put", API_CHARGER, json=charger.as_dictionary())
        response.raise_for_status()
        charger.from_json_dictionary(response.json())
        return charger

    def get_devices_status(
        self, device_list: Optional["list[VueDevice]"] = None
    ) -> "tuple[list[OutletDevice], list[ChargerDevice]]":
        """Gets the list of outlets and chargers. If device list is provided, updates the connected status on each device."""
        response = (self.auth_v1 or self.auth).request("get", API_GET_STATUS)
        response.raise_for_status()
        chargers: list[ChargerDevice] = []
        outlets: list[OutletDevice] = []
        if response.text:
            j = response.json()
            if not j:
                return (outlets, chargers)
            evses_raw = j.get("evses") or j.get("evChargers") or []
            for raw_charger in evses_raw:
                chargers.append(ChargerDevice().from_json_dictionary(raw_charger))
            outlets_raw = j.get("outlets") or []
            for raw_outlet in outlets_raw:
                outlets.append(OutletDevice().from_json_dictionary(raw_outlet))
            devices_conn = j.get("devices_connected") or j.get("devicesConnected") or []
            if device_list and devices_conn:
                for raw_device_data in devices_conn:
                    if not raw_device_data:
                        continue
                    gid = raw_device_data.get("device_gid") or raw_device_data.get(
                        "deviceGid"
                    )
                    if gid:
                        for device in device_list:
                            if device.device_gid == gid:
                                if "device_id" in raw_device_data:
                                    device.device_id = raw_device_data["device_id"]
                                elif "deviceId" in raw_device_data:
                                    device.device_id = raw_device_data["deviceId"]
                                device.connected = raw_device_data.get(
                                    "connected", device.connected
                                )
                                offline = raw_device_data.get(
                                    "offline_since"
                                ) or raw_device_data.get("offlineSince")
                                if offline is not None:
                                    device.offline_since = offline
                                break

        return (outlets, chargers)

    def get_evses(self, device_ids: list[str]) -> list[ChargerDevice]:
        """Gets the details for the specified EVSEs."""
        device_ids_str = ""
        if device_ids:
            device_ids_str = ",".join(device_ids)
        url = API_GET_EVSES.format(deviceIds=device_ids_str)
        response = (self.auth_v1 or self.auth).request("get", url)
        response.raise_for_status()
        chargers: list[ChargerDevice] = []
        if response.text:
            j = response.json()
            if not j:
                return chargers
            raw_evses = j.get("success") or j.get("evses") or []
            for raw_charger in raw_evses:
                chargers.append(ChargerDevice().from_json_dictionary(raw_charger))
        return chargers

    def post_evse_control(self, device_id: str, command: str) -> bool:
        """Dispatches a runtime control command to an EVSE."""
        normalized_cmd = command.strip().upper() if isinstance(command, str) else ""
        if normalized_cmd not in VALID_EVSE_CONTROL_COMMANDS:
            raise ValueError(
                f"Unsupported EVSE control command: {command!r}. Allowed commands: {VALID_EVSE_CONTROL_COMMANDS}"
            )
        payload = {
            "device_id": str(device_id),
            "command": normalized_cmd,
        }
        response = (self.auth_v1 or self.auth).request(
            "post", API_EVSE_CONTROL, json=payload
        )
        response.raise_for_status()
        return True

    def set_evse_state(self, device_id: str, enabled: bool) -> bool:
        """Sets the EVSE state to enabled or disabled."""
        command = "TURN_ON" if enabled else "TURN_OFF"
        return self.post_evse_control(device_id, command)

    def set_evse_settings(self, device_id: str, charge_rate_amps: int) -> bool:
        """Sets the EVSE charge rate in amps."""
        payload = {
            "settings": [
                {
                    "device_id": device_id,
                    "charge_rate_amps": charge_rate_amps,
                }
            ]
        }
        response = (self.auth_v1 or self.auth).request(
            "put", API_EVSE_SETTINGS, json=payload
        )
        response.raise_for_status()
        if response.text:
            try:
                j = response.json()
                if isinstance(j, dict) and "success" in j:
                    return device_id in j.get("success", [])
            except Exception:
                pass
        return True

    def get_evse_control(self, device_id: str) -> Optional[EvseControlStatus]:
        """Gets live charging session telemetry and control status for an EVSE."""
        url = f"{API_EVSE_CONTROL}?device_id={device_id}"
        response = (self.auth_v1 or self.auth).request("get", url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if j:
                status = EvseControlStatus().from_json_dictionary(j)
                if not status.device_id:
                    status.device_id = device_id
                return status
        return None

    def get_excess_generation_monitors(self) -> Optional[ExcessGenerationMonitors]:
        """Gets the list of excess generation eligible monitors and unavailable monitors."""
        response = (self.auth_v1 or self.auth).request("get", API_EXCESS_GENERATION)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if j:
                return ExcessGenerationMonitors().from_json_dictionary(j)
        return None

    def get_excess_generation(
        self, device_id: str
    ) -> Optional[EnergyMonitorExcessGeneration]:
        """Gets excess generation configuration for an energy monitor."""
        url = f"{API_ENERGY_MONITOR_EXCESS_GENERATION}?device_id={device_id}"
        response = (self.auth_v1 or self.auth).request("get", url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if j:
                return EnergyMonitorExcessGeneration().from_json_dictionary(j)
        return None

    def set_excess_generation(
        self,
        device_id: str,
        loads: list[dict[str, Any] | ExcessGenerationLoad],
        solar_window: Optional[dict[str, Any]] = None,
        sunrise: Optional[str] = None,
        sunset: Optional[str] = None,
    ) -> bool:
        """Sets excess generation configuration for an energy monitor."""
        serialized_loads = [
            load.as_dictionary() if hasattr(load, "as_dictionary") else load
            for load in loads
        ]
        payload = {
            "device_id": device_id,
            "loads": serialized_loads,
            "solar_window": solar_window,
            "sunrise": sunrise,
            "sunset": sunset,
        }
        response = (self.auth_v1 or self.auth).request(
            "post", API_ENERGY_MONITOR_EXCESS_GENERATION, json=payload
        )
        response.raise_for_status()
        return True

    def get_channel_types(self) -> "list[ChannelType]":
        """Gets the list of channel types"""
        response = self.auth.request("get", API_CHANNEL_TYPES)
        response.raise_for_status()
        channel_types: list[ChannelType] = []
        if response.text:
            j = response.json()
            if j:
                for raw_channel_type in j:
                    channel_types.append(
                        ChannelType().from_json_dictionary(raw_channel_type)
                    )
        return channel_types

    def get_vehicles(self) -> "list[Vehicle]":
        """Get all vehicles under the current customer account."""
        response = self.auth.request("get", API_VEHICLES)
        response.raise_for_status()
        vehicles: list[Vehicle] = []
        if response.text:
            j = response.json()
            for veh in j:
                vehicles.append(Vehicle().from_json_dictionary(veh))
        return vehicles

    def get_vehicle_status(self, vehicle_gid: int) -> Optional[VehicleStatus]:
        """Get details for the current vehicle."""
        url = API_VEHICLE_STATUS.format(vehicleGid=vehicle_gid)
        response = self.auth.request("get", url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            return VehicleStatus().from_json_dictionary(j)
        return None

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        id_token: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_storage_file: Optional[str] = None,
    ) -> bool:
        """Authenticates the current user using access tokens if provided or username/password if no tokens available.
        Provide a path for storing the token data that can be used to reauthenticate without providing the password.
        Tokens stored in the file are updated when they expire.
        """
        # try to pull data out of the token storage file if present
        self.username = username.lower() if username else None
        if token_storage_file:
            self.token_storage_file = token_storage_file
        if not password and not id_token and token_storage_file:
            with open(token_storage_file, "r") as f:
                data = json.load(f)
                if "id_token" in data:
                    id_token = data["id_token"]
                if "access_token" in data:
                    access_token = data["access_token"]
                if "refresh_token" in data:
                    refresh_token = data["refresh_token"]
                if "username" in data:
                    self.username = data["username"]
                if "password" in data:
                    password = data["password"]

        self.auth = Auth(
            host=API_ROOT,
            username=self.username,
            password=password,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            tokens={
                "access_token": access_token,
                "id_token": id_token,
                "refresh_token": refresh_token,
            },
            token_updater=self._store_tokens,
        )

        try:
            self.auth.refresh_tokens()
        except self.auth.cognito.client.exceptions.NotAuthorizedException as ex:
            return False

        if self.auth.tokens:
            self.username = self.auth.get_username()
            # Setup V1 auth for newer API calls
            self.auth_v1 = Auth(
                host=API_ROOT_V1,
                username=self.username,
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
                tokens=self.auth.tokens,
                token_updater=self._store_tokens,
                as_bearer=True,
            )
            try:
                self.auth_v1.refresh_tokens()
            except self.auth_v1.cognito.client.exceptions.NotAuthorizedException:
                return False

            self.customer = self.get_customer_details()
            self._store_tokens(self.auth.tokens)
        return self.customer is not None

    def login_simulator(
        self, host: str, username: Optional[str] = None, password: Optional[str] = None
    ) -> bool:
        self.username = username.lower() if username else None
        self.auth = SimulatedAuth(host=host, username=self.username, password=password)
        self.auth_v1 = SimulatedAuth(
            host=f"{host}/v1" if not host.endswith("/v1") else host,
            username=self.username,
            password=password,
            as_bearer=True,
        )
        self.customer = self.get_customer_details()
        return self.customer is not None

    def _store_tokens(self, tokens: "dict[str, Any]"):
        if self.auth:
            self.auth.tokens = tokens
        if self.auth_v1:
            self.auth_v1.tokens = tokens
        if not self.token_storage_file:
            return
        if self.username:
            tokens["username"] = self.username
        with open(self.token_storage_file, "w") as f:
            json.dump(tokens, f, indent=2)


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
    return time.isoformat() + "Z"
