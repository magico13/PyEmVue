import datetime
import json
from typing import Any, Optional, Union

import requests

# Our files
from pyemvue.auth import Auth, SimulatedAuth
from pyemvue.basemodel import ChannelUsageData
from pyemvue.customer import Customer
from pyemvue.device import (
    Channel,
    ChannelTypeList,
    Charger,
    CustomerDevices,
    DeviceListUsage,
    DevicesStatus,
    Outlet,
    VehicleList,
    VehicleStatus,
    VueDevice,
    VueDeviceChannel,
    VueDeviceChannelUsage,
)
from pyemvue.enums import Scale, Unit

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

API_MAINTENANCE = (
    "https://s3.amazonaws.com/com.emporiaenergy.manual.ota/maintenance/maintenance.json"
)


class PyEmVue(object):
    def __init__(self, connect_timeout: float = 6.03, read_timeout: float = 10.03):
        self.username: Optional[str] = None
        self.token_storage_file: Optional[str] = None
        self.customer: Optional[Customer] = None
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

    def _get_raw(self, endpoint: str, **kwargs: Any) -> Any:
        # TODO backoff?
        response = self.auth.request("get", endpoint.format(**kwargs))
        response.raise_for_status()
        return response.json()

    def get_devices(self) -> CustomerDevices:
        """Get all devices under the current customer account."""
        data = self._get_raw(API_CUSTOMER_DEVICES)
        return CustomerDevices(**data)

    def populate_device_properties(self, device: VueDevice) -> VueDevice:
        """Get details about a specific device"""
        # not sure if this is needed any more
        data = self._get_raw(API_DEVICE_PROPERTIES, deviceGid=device.device_gid)
        return VueDevice(**data)

    def update_channel(self, channel: VueDeviceChannel) -> VueDeviceChannel:
        """Update the channel with the provided state."""
        url = API_CHANNELS.format(deviceGid=channel.device_gid)
        response = self.auth.request("put", url, json=channel.as_dictionary())
        response.raise_for_status()
        if response.text:
            channel = VueDeviceChannel(**response.json())
        return channel

    def get_customer_details(self) -> Optional[Customer]:
        """Get details for the current customer."""
        data = self._get_raw(API_CUSTOMER)
        return Customer(**data)

    def get_device_list_usage(
        self,
        deviceGids: Union[str, list[str]],
        instant: Optional[datetime.datetime],
        scale=Scale.SECOND,
        unit=Unit.KWH,
    ) -> DeviceListUsage:
        """Returns a DeviceListUsage with the total usage of the devices over the specified scale. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if not instant:
            instant = datetime.datetime.now(datetime.timezone.utc)
        gids = deviceGids
        if isinstance(deviceGids, list):
            gids = "+".join(map(str, deviceGids))

        url = API_DEVICES_USAGE.format(
            deviceGids=gids, instant=_format_time(instant), scale=scale, unit=unit
        )
        data = self._get_raw(url)
        return DeviceListUsage(**data)

    def get_chart_usage(
        self,
        channel: Union[Channel, VueDeviceChannelUsage],
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        scale: Scale = Scale.SECOND,
        unit: Unit = Unit.KWH,
    ) -> ChannelUsageData:
        """Gets the usage over a given time period and the start of the measurement period. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if not start:
            start = datetime.datetime.now(datetime.timezone.utc)
        if not end:
            end = datetime.datetime.now(datetime.timezone.utc)
        if channel.channel_num in ["MainsFromGrid", "MainsToGrid"]:
            # These is not populated for the special Mains data as of right now
            return ChannelUsageData(first_usage_instant=start, usage_list=[])
        return ChannelUsageData(
            **self._get_raw(
                API_CHART_USAGE,
                deviceGid=channel.device_gid,
                channel=channel.channel_num,
                start=_format_time(start),
                end=_format_time(end),
                scale=scale,
                unit=unit,
            )
        )

    def update_outlet(self, outlet: Outlet, on: Optional[bool] = None) -> Outlet:
        """Primarily to turn an outlet on or off. If the on parameter is not provided then uses the value in the outlet object.
        If on parameter provided uses the provided value."""
        if on is not None:
            outlet.outlet_on = on

        response = self.auth.request("put", API_OUTLET, json=outlet.as_dictionary())
        response.raise_for_status()
        outlet = Outlet(**response.json())
        return outlet

    def update_charger(
        self,
        charger: Charger,
        on: Optional[bool] = None,
        charge_rate: Optional[int] = None,
    ) -> Charger:
        """Primarily to enable/disable an evse/charger. The on and charge_rate parameters override the values in the object if provided"""
        if on is not None:
            charger.charger_on = on
        if charge_rate:
            charger.charging_rate = charge_rate

        response = self.auth.request("put", API_CHARGER, json=charger.as_dictionary())
        response.raise_for_status()
        return Charger(**response.json())

    def get_devices_status(self) -> DevicesStatus:
        """Gets the list of outlets and chargers."""

        data = self._get_raw(API_GET_STATUS)
        return DevicesStatus(**data)

    def get_channel_types(self) -> ChannelTypeList:
        """Gets the list of channel types"""
        data = self._get_raw(API_CHANNEL_TYPES)
        return ChannelTypeList(data)

    def get_vehicles(self) -> VehicleList:
        """Get all vehicles under the current customer account."""
        data = self._get_raw(API_VEHICLES)
        return VehicleList(data)

    def get_vehicle_status(self, vehicle_gid: int) -> Optional[VehicleStatus]:
        """Get details for the current vehicle."""
        data = self._get_raw(API_VEHICLE_STATUS, vehicleGid=vehicle_gid)
        if data:
            return VehicleStatus(**data)
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
        except self.auth.cognito.client.exceptions.NotAuthorizedException:
            return False

        if self.auth.tokens:
            self.username = self.auth.get_username()
            self.customer = self.get_customer_details()
            self._store_tokens(self.auth.tokens)
        return self.customer is not None

    def login_simulator(
        self, host: str, username: Optional[str] = None, password: Optional[str] = None
    ) -> bool:
        self.username = username.lower() if username else None
        self.auth = SimulatedAuth(host=host, username=self.username, password=password)
        self.customer = self.get_customer_details()
        return self.customer is not None

    def _store_tokens(self, tokens: "dict[str, Any]"):
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
