import requests
import datetime
import json
from dateutil.parser import parse
from urllib.parse import quote

# These provide AWS cognito authentication support
import boto3
import botocore
from warrant import Cognito

# Our files
from pyemvue.enums import Scale, Unit
from pyemvue.customer import Customer
from pyemvue.device import ChargerDevice, VueDevice, VueDeviceChannel, VueDeviceChannelUsage, OutletDevice, VueUsageDevice

API_ROOT = 'https://api.emporiaenergy.com'
API_CUSTOMER = '/customers?email={email}'
API_CUSTOMER_DEVICES = '/customers/devices'
API_DEVICES_USAGE = '/AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGids}&instant={instant}&scale={scale}&energyUnit={unit}'
API_CHART_USAGE = '/AppAPI?apiMethod=getChartUsage&deviceGid={deviceGid}&channel={channel}&start={start}&end={end}&scale={scale}&energyUnit={unit}'
API_DEVICE_PROPERTIES = '/devices/{deviceGid}/locationProperties'
API_OUTLET = '/devices/outlet'
API_GET_OUTLETS = '/customers/outlets'
API_CHARGER = '/devices/evcharger'
API_GET_CHARGERS = '/customers/evchargers'

API_MAINTENANCE = 'https://s3.amazonaws.com/com.emporiaenergy.manual.ota/maintenance/maintenance.json'

CLIENT_ID = '4qte47jbstod8apnfic0bunmrq'
USER_POOL = 'us-east-2_ghlOXVLi1'

class PyEmVue(object):
    def __init__(self):
        self.username = None
        self.token_storage_file = None
        self.customer = None
        self.cognito = None

    def down_for_maintenance(self):
        """Checks to see if the API is down for maintenance, returns the reported message if present."""
        response = requests.get(API_MAINTENANCE)
        if response.status_code == 404: return None
        if response.text:
            j = response.json()
            if 'msg' in j:
                return j['msg']

    def get_devices(self):
        """Get all devices under the current customer account."""
        url = API_ROOT + API_CUSTOMER_DEVICES.format(customerGid = self.customer.customer_gid)
        response = self._get_request(url)
        response.raise_for_status()
        devices = []
        if response.text:
            j = response.json()
            if 'devices' in j:
                for dev in j['devices']:
                    devices.append(VueDevice().from_json_dictionary(dev))
                    if 'devices' in dev:
                        for subdev in dev['devices']:
                            devices.append(VueDevice().from_json_dictionary(subdev))
        return devices

    def populate_device_properties(self, device):
        """Get details about a specific device"""
        url = API_ROOT + API_DEVICE_PROPERTIES.format(deviceGid=device.device_gid)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            device.populate_location_properties_from_json(j)
        return device

    def get_customer_details(self):
        """Get details for the current customer."""
        
        url = API_ROOT + API_CUSTOMER.format(email=quote(self.username))
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            return Customer().from_json_dictionary(j)
        return None

    def get_device_list_usage(self, deviceGids, instant, scale=Scale.SECOND.value, unit=Unit.KWH.value):
        """Returns a nested dictionary of VueUsageDevice and VueDeviceChannelUsage with the total usage of the devices over the specified scale. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if not instant: instant = datetime.datetime.utcnow()
        gids = deviceGids
        if isinstance(deviceGids, list):
            gids = '+'.join(map(str, deviceGids))
        
        url = API_ROOT + API_DEVICES_USAGE.format(deviceGids=gids, instant=_format_time(instant), scale=scale, unit=unit)
        response = self._get_request(url)
        response.raise_for_status()
        devices = {}
        if response.text:
            j = response.json()
            if 'deviceListUsages' in j and 'devices' in j['deviceListUsages']:
                timestamp = parse(j['deviceListUsages']['instant'])
                for device in j['deviceListUsages']['devices']:
                    populated = VueUsageDevice(timestamp=timestamp).from_json_dictionary(device)
                    devices[populated.device_gid] = populated
        return devices


    def get_chart_usage(self, channel, start, end, scale=Scale.SECOND.value, unit=Unit.KWH.value):
        """Gets the usage over a given time period and the start of the measurement period. Note that you may need to scale this to get a rate (1MIN in kw = 60*result)"""
        if channel.channel_num in ['MainsFromGrid', 'MainsToGrid']:
            # These is not populated for the special Mains data as of right now
            return [], start
        if not start: start = datetime.datetime.utcnow()
        if not end: end = datetime.datetime.utcnow()
        url = API_ROOT + API_CHART_USAGE.format(deviceGid=channel.device_gid, channel=channel.channel_num, start=_format_time(start), end=_format_time(end), scale=scale, unit=unit)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if 'firstUsageInstant' in j: instant = parse(j['firstUsageInstant'])
            else: instant = start
            if 'usageList' in j: usage = j['usageList']
            else: usage = []
            return usage, instant
        return [], start

    def get_outlets(self):
        """ Return a list of outlets linked to the account. """
        url = API_ROOT + API_GET_OUTLETS
        response = self._get_request(url)
        response.raise_for_status()
        outlets = []
        if response.text:
            j = response.json()
            for raw_outlet in j:
                outlets.append(OutletDevice().from_json_dictionary(raw_outlet))
        return outlets

    def update_outlet(self, outlet, on=None):
        """ Primarily to turn an outlet on or off. If the on parameter is not provided then uses the value in the outlet object.
            If on parameter provided uses the provided value."""
        url = API_ROOT + API_OUTLET
        if on is not None:
            outlet.outlet_on = on

        response = self._put_request(url, outlet.as_dictionary())
        response.raise_for_status()
        outlet.from_json_dictionary(response.json())
        return outlet

    def get_chargers(self):
        """ Return a list of EVSEs/chargers linked to the account. """
        url = API_ROOT + API_GET_CHARGERS
        response = self._get_request(url)
        response.raise_for_status()
        chargers = []
        if response.text:
            j = response.json()
            for raw_charger in j:
                chargers.append(ChargerDevice().from_json_dictionary(raw_charger))
        return chargers

    def update_charger(self, charger, on = None, charge_rate = None):
        """ Primarily to enable/disable an evse/charger. The on and charge_rate parameters override the values in the object if provided"""
        url = API_ROOT + API_CHARGER
        if on is not None:
            charger.charger_on = on
        if charge_rate:
            charger.charging_rate = charge_rate

        response = self._put_request(url, charger.as_dictionary())
        response.raise_for_status()
        charger.from_json_dictionary(response.json())
        return charger

    def login(self, username=None, password=None, id_token=None, access_token=None, refresh_token=None, token_storage_file=None):
        """ Authenticates the current user using access tokens if provided or username/password if no tokens available.
            Provide a path for storing the token data that can be used to reauthenticate without providing the password.
            Tokens stored in the file are updated when they expire.
        """
        # Use warrant to go through the SRP authentication to get an auth token and refresh token
        client = boto3.client('cognito-idp', region_name='us-east-2', 
            config=botocore.client.Config(signature_version=botocore.UNSIGNED))
        if id_token is not None and access_token is not None and refresh_token is not None:
            # use existing tokens
            self.cognito = Cognito(USER_POOL, CLIENT_ID,
                user_pool_region='us-east-2', 
                id_token=id_token, 
                access_token=access_token, 
                refresh_token=refresh_token)
            self.cognito.client = client
        elif username is not None and password is not None:
            #log in with username and password
            self.cognito = Cognito(USER_POOL, CLIENT_ID, 
                user_pool_region='us-east-2', username=username)
            self.cognito.client = client
            self.cognito.authenticate(password=password)
        else:
            raise Exception('No authentication method found. Must supply username/password or id/auth/refresh tokens.')
        if self.cognito.access_token is not None:
            if token_storage_file is not None: self.token_storage_file = token_storage_file
            self._check_token()
            user = self.cognito.get_user()
            self.username = user._data['email']
            self.customer = self.get_customer_details()
            self._store_tokens()
        return self.customer is not None
        
    def _check_token(self):
        if self.cognito.check_token(renew=True):
            # Token expired and we renewed it. Store new token
            self._store_tokens()

    def _store_tokens(self):
        if not self.token_storage_file: return
        data = {
            'idToken': self.cognito.id_token,
            'accessToken': self.cognito.access_token,
            'refreshToken': self.cognito.refresh_token
        }
        if self.username:
            data['email'] = self.username
        with open(self.token_storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_request(self, full_endpoint):
        if not self.cognito: raise Exception('Must call "login" before calling any API methods.')
        self._check_token() # ensure our token hasn't expired, refresh if it has
        headers = {'authtoken': self.cognito.id_token}
        return requests.get(full_endpoint, headers=headers)

    def _put_request(self, full_endpoint, body):
        if not self.cognito: raise Exception('Must call "login" before calling any API methods.')
        self._check_token() # ensure our token hasn't expired, refresh if it has
        headers = {'authtoken': self.cognito.id_token}
        return requests.put(full_endpoint, headers=headers, json=body)

def _format_time(time):
    return time.isoformat()+'Z'

def _format_date(date):
    return date.strftime('%Y-%m-%d')
