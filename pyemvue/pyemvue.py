from typing import Any, Optional, Union
import requests
import datetime
import json
from dateutil.parser import parse
from urllib.parse import quote

# Our files
from pyemvue.auth import Auth
from pyemvue.enums import Scale, Unit
from pyemvue.customer import Customer
from pyemvue.device import ChargerDevice, VueDevice, OutletDevice, VueDeviceChannel, VueDeviceChannelUsage, VueUsageDevice, ChannelType

API_ROOT = 'https://api.emporiaenergy.com'
API_CHANNELS = 'devices/{deviceGid}/channels'
API_CHANNEL_TYPES = 'devices/channels/channeltypes'
API_CHARGER = 'devices/evcharger'
API_CHART_USAGE = 'AppAPI?apiMethod=getChartUsage&deviceGid={deviceGid}&channel={channel}&start={start}&end={end}&scale={scale}&energyUnit={unit}'
API_CUSTOMER = 'customers?email={email}'
API_CUSTOMER_DEVICES = 'customers/devices'
API_DEVICES_USAGE = 'AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGids}&instant={instant}&scale={scale}&energyUnit={unit}'
API_DEVICE_PROPERTIES = 'devices/{deviceGid}/locationProperties'
API_GET_STATUS = 'customers/devices/status'
API_OUTLET = 'devices/outlet'

API_MAINTENANCE = 'https://s3.amazonaws.com/com.emporiaenergy.manual.ota/maintenance/maintenance.json'

class PyEmVue(object):
    def __init__(self, connect_timeout: float = 6.03, read_timeout: float = 10.03):
        self.username = None
        self.token_storage_file = None
        self.customer = None
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def down_for_maintenance(self) -> Optional[str]:
        """Checks to see if the API is down for maintenance, returns the reported message if present."""
        response = requests.get(API_MAINTENANCE)
        if response.status_code == 404: return None
        if response.text:
            j = response.json()
            if 'msg' in j:
                return j['msg']

    def get_devices(self) -> 'list[VueDevice]':
        """Get all devices under the current customer account."""
        response = self.auth.request('get', API_CUSTOMER_DEVICES)
        response.raise_for_status()
        devices: list[VueDevice] = []
        if response.text:
            j = response.json()
            if 'devices' in j:
                for dev in j['devices']:
                    devices.append(VueDevice().from_json_dictionary(dev))
                    if 'devices' in dev:
                        for subdev in dev['devices']:
                            devices.append(VueDevice().from_json_dictionary(subdev))
        return devices

    def populate_device_properties(self, device: VueDevice) -> VueDevice:
        """Get details about a specific device"""
        url = API_DEVICE_PROPERTIES.format(deviceGid=device.device_gid)
        response = self.auth.request('get', url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            device.populate_location_properties_from_json(j)
        return device

    def update_channel(self, channel: VueDeviceChannel) -> VueDeviceChannel:
        """Update the channel with the provided state."""
        url = API_CHANNELS.format(deviceGid=channel.device_gid)
        response = self.auth.request('put', url, json=channel.as_dictionary())
        response.raise_for_status()
        if response.text:
            j = response.json()
            channel.from_json_dictionary(j)
        return channel

    def get_customer_details(self, username: str) -> Optional[Customer]:
        """Get details for the current customer."""
        url = API_CUSTOMER.format(email=quote(username))
        response = self.auth.request('get', url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            return Customer().from_json_dictionary(j)
        return None

    def get_device_list_usage(self, deviceGids: Union[str, 'list[str]'], instant: Optional[datetime.datetime], scale=Scale.SECOND.value, unit=Unit.KWH.value) -> 'dict[int, VueUsageDevice]':
        """Returns a nested dictionary of VueUsageDevice and VueDeviceChannelUsage with the total usage of the devices over the specified scale. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if not instant: instant = datetime.datetime.now(datetime.timezone.utc)
        gids = deviceGids
        if isinstance(deviceGids, list):
            gids = '+'.join(map(str, deviceGids))

        url = API_DEVICES_USAGE.format(deviceGids=gids, instant=_format_time(instant), scale=scale, unit=unit)
        response = self.auth.request('get', url)
        response.raise_for_status()
        devices: dict[int, VueUsageDevice] = {}
        if response.text:
            j = response.json()
            if 'deviceListUsages' in j and 'devices' in j['deviceListUsages']:
                timestamp = parse(j['deviceListUsages']['instant'])
                for device in j['deviceListUsages']['devices']:
                    populated = VueUsageDevice(timestamp=timestamp).from_json_dictionary(device)
                    devices[populated.device_gid] = populated
        return devices

    def get_chart_usage(self, channel: Union[VueDeviceChannel, VueDeviceChannelUsage], start: Optional[datetime.datetime] = None, end: Optional[datetime.datetime] = None, scale=Scale.SECOND.value, unit=Unit.KWH.value) -> 'tuple[list[float], Optional[datetime.datetime]]':
        """Gets the usage over a given time period and the start of the measurement period. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if channel.channel_num in ['MainsFromGrid', 'MainsToGrid']:
            # These is not populated for the special Mains data as of right now
            return [], start
        if not start: start = datetime.datetime.now(datetime.timezone.utc)
        if not end: end = datetime.datetime.now(datetime.timezone.utc)
        url = API_CHART_USAGE.format(deviceGid=channel.device_gid, channel=channel.channel_num, start=_format_time(start), end=_format_time(end), scale=scale, unit=unit)
        response = self.auth.request('get', url)
        response.raise_for_status()
        usage: list[float] = []
        instant = start
        if response.text:
            j = response.json()
            if 'firstUsageInstant' in j: instant = parse(j['firstUsageInstant'])
            if 'usageList' in j: usage = j['usageList']
        return usage, instant

    def get_outlets(self) -> 'list[OutletDevice]':
        """ Return a list of outlets linked to the account. Deprecated, use get_devices_status instead."""
        response = self.auth.request('get', API_GET_STATUS)
        response.raise_for_status()
        outlets = []
        if response.text:
            j = response.json()
            if j and 'outlets' in j and j['outlets']:
                for raw_outlet in j['outlets']:
                    outlets.append(OutletDevice().from_json_dictionary(raw_outlet))
        return outlets

    def update_outlet(self, outlet: OutletDevice, on: Optional[bool]=None) -> OutletDevice:
        """ Primarily to turn an outlet on or off. If the on parameter is not provided then uses the value in the outlet object.
            If on parameter provided uses the provided value."""
        if on is not None:
            outlet.outlet_on = on

        response = self.auth.request('put', API_OUTLET, json=outlet.as_dictionary())
        response.raise_for_status()
        outlet.from_json_dictionary(response.json())
        return outlet

    def get_chargers(self) -> 'list[ChargerDevice]':
        """ Return a list of EVSEs/chargers linked to the account. Deprecated, use get_devices_status instead."""
        response = self.auth.request('get', API_GET_STATUS)
        response.raise_for_status()
        chargers = []
        if response.text:
            j = response.json()
            if j and 'evChargers' in j and j['evChargers']:
                for raw_charger in j['evChargers']:
                    chargers.append(ChargerDevice().from_json_dictionary(raw_charger))
        return chargers

    def update_charger(self, charger: ChargerDevice, on: Optional[bool] = None, charge_rate: Optional[int] = None) -> ChargerDevice:
        """ Primarily to enable/disable an evse/charger. The on and charge_rate parameters override the values in the object if provided"""
        if on is not None:
            charger.charger_on = on
        if charge_rate:
            charger.charging_rate = charge_rate

        response = self.auth.request('put', API_CHARGER, json=charger.as_dictionary())
        response.raise_for_status()
        charger.from_json_dictionary(response.json())
        return charger

    def get_devices_status(self, device_list: Optional['list[VueDevice]'] = None) -> 'tuple[list[OutletDevice], list[ChargerDevice]]':
        """Gets the list of outlets and chargers. If device list is provided, updates the connected status on each device."""
        response = self.auth.request('get', API_GET_STATUS)
        response.raise_for_status()
        chargers: list[ChargerDevice] = []
        outlets: list[OutletDevice] = []
        if response.text:
            j = response.json()
            if j and 'evChargers' in j and j['evChargers']:
                for raw_charger in j['evChargers']:
                    chargers.append(ChargerDevice().from_json_dictionary(raw_charger))
            if j and 'outlets' in j and j['outlets']:
                for raw_outlet in j['outlets']:
                    outlets.append(OutletDevice().from_json_dictionary(raw_outlet))
            if device_list and j and 'devicesConnected' in j and j['devicesConnected']:
                for raw_device_data in j['devicesConnected']:
                    if raw_device_data and 'deviceGid' in raw_device_data and raw_device_data['deviceGid']:
                        for device in device_list:
                            if device.device_gid == raw_device_data['deviceGid']:
                                device.connected = raw_device_data['connected']
                                device.offline_since = raw_device_data['offlineSince']
                                break

        return (outlets, chargers)
    
    def get_channel_types(self) -> 'list[ChannelType]':
        """Gets the list of channel types"""
        response = self.auth.request('get', API_CHANNEL_TYPES)
        response.raise_for_status()
        channel_types: list[ChannelType] = []
        if response.text:
            j = response.json()
            if j:
                for raw_channel_type in j:
                    channel_types.append(ChannelType().from_json_dictionary(raw_channel_type))
        return channel_types

    def login(self, username: Optional[str]=None, password: Optional[str]=None, id_token: Optional[str]=None, access_token: Optional[str]=None, refresh_token: Optional[str]=None, token_storage_file: Optional[str]=None) -> bool:
        """ Authenticates the current user using access tokens if provided or username/password if no tokens available.
            Provide a path for storing the token data that can be used to reauthenticate without providing the password.
            Tokens stored in the file are updated when they expire.
        """
        # try to pull data out of the token storage file if present
        self.username = username.lower() if username else None
        if token_storage_file: self.token_storage_file = token_storage_file
        if not password and not id_token and token_storage_file:
            with open(token_storage_file, 'r') as f:
                data = json.load(f)
                if 'id_token' in data: id_token = data['id_token']
                if 'access_token' in data: access_token = data['access_token']
                if 'refresh_token' in data: refresh_token = data['refresh_token']
                if 'username' in data: self.username = data['username']
                if 'password' in data: password = data['password']

        self.auth = Auth(
            host=API_ROOT,
            username=self.username,
            password=password,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            tokens={
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token
            },
            token_updater=self._store_tokens
        )

        if self.auth.tokens:
            self.username = self.auth.get_username()
            self.customer = self.get_customer_details(self.username)
            self._store_tokens(self.auth.tokens)
        return self.customer is not None

    def _store_tokens(self, tokens: 'dict[str, Any]'):
        if not self.token_storage_file: return
        if self.username:
            tokens['username'] = self.username
        with open(self.token_storage_file, 'w') as f:
            json.dump(tokens, f, indent=2)

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
    return time.isoformat()+'Z'
