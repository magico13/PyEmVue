import requests
import datetime
import json
from dateutil.parser import parse

# These provide AWS cognito authentication support
import boto3
import botocore
from warrant import Cognito

# Our files
from pyemvue.enums import Scale, Unit, TotalTimeFrame, TotalUnit
from pyemvue.customer import Customer
from pyemvue.device import VueDevice, VueDeviceChannel, VuewDeviceChannelUsage

API_ROOT = 'https://api.emporiaenergy.com'
API_CUSTOMER = '/customers?email={email}'
API_CUSTOMER_DEVICES = '/customers/{customerGid}/devices?detailed=true&hierarchy=true'
API_USAGE_DEVICES = '/usage/devices?start={startTime}&end={endTime}&scale={scale}&unit={unit}&customerGid={customerGid}'
API_USAGE_TIME = '/usage/time?start={startTime}&end={endTime}&type=INSTANT&deviceGid={deviceGid}&scale={scale}&unit={unit}&channels={channels}'
API_USAGE_DATE = '/usage/date?start={startDate}&end={endDate}&type=INSTANT&deviceGid={deviceGid}&scale={scale}&unit={unit}&channels={channels}'
API_USAGE_TOTAL = '/usage/total?deviceGid={deviceGid}&timeframe={timeFrame}&unit={unit}&channels={channels}'
API_DEVICE_PROPERTIES = '/devices/{deviceGid}/locationProperties'

CLIENT_ID = '4qte47jbstod8apnfic0bunmrq'
USER_POOL = 'us-east-2_ghlOXVLi1'

class PyEmVue(object):
    def __init__(self):
        self.username = None
        self.token_storage_file = None
        self.customer = None
        self.cognito = None

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
        url = API_ROOT + API_CUSTOMER.format(email=self.username)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            return Customer().from_json_dictionary(j)
        return None

    def get_total_usage(self, channel, timeFrame=TotalTimeFrame.ALL.value, unit=TotalUnit.WATTHOURS.value):
        """Get total usage over the provided timeframe for the given device channel."""
        url = API_ROOT + API_USAGE_TOTAL.format(deviceGid=channel.device_gid, 
            timeFrame=timeFrame, unit=unit, channels=channel.channel_num)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if 'usage' in j: return j['usage']
        return 0
    
    def get_usage_over_time(self, channel, start, end, scale=Scale.SECOND.value, unit=Unit.WATTS.value):
        """Get usage over the given time range. Used for primarily for plotting history. Supports time scales less than DAY."""
        if scale != Scale.SECOND.value and scale != Scale.MINUTE.value and scale != Scale.MINUTES_15.value and scale != Scale.HOUR.value:
            raise ValueError(f'Scale of {scale} is invalid, must be 1S, 1MIN, 15MIN, or 1H.')
        url = API_ROOT + API_USAGE_TIME.format(deviceGid=channel.device_gid, startTime=_format_time(start), endTime=_format_time(end),
            scale=scale, unit=unit, channels=channel.channel_num)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if 'usage' in j: return j['usage']
        return []

    def get_usage_over_date_range(self, channel, start, end, scale=Scale.DAY.value, unit=Unit.WATTS.value):
        """Get usage over the given date range. Used for primarily for plotting history. Supports time scales of DAY or larger"""
        if scale != Scale.DAY.value and scale != Scale.WEEK.value and scale != Scale.MONTH.value and scale != Scale.YEAR.value:
            raise ValueError(f'Scale of {scale} is invalid, must be 1D, 1W, 1MON, or 1Y.')
        url = API_ROOT + API_USAGE_DATE.format(deviceGid=channel.device_gid, startDate=_format_date(start), endDate=_format_date(end),
            scale=scale, unit=unit, channels=channel.channel_num)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if 'usage' in j: return j['usage']
        return []
    
    def get_recent_usage(self, scale=Scale.HOUR.value, unit=Unit.WATTS.value):
        """Get usage over the last 'scale' timeframe."""
        now = datetime.datetime.utcnow()
        return self.get_usage_for_time_scale(now, scale, unit)[0]

    def get_usage_for_time_scale(self, time, scale=Scale.HOUR.value, unit=Unit.WATTS.value):
        """ Get usage for the 'scale' timeframe ending at the given time. 
            Only supported for scales less than one day, otherwise time value is ignored and most recent data is given.
        """
        start = time - datetime.timedelta(seconds=1)
        end = time
        url = API_ROOT + API_USAGE_DEVICES.format(customerGid=self.customer.customer_gid, 
            scale=scale, unit=unit, startTime=_format_time(start), endTime=_format_time(end))
        response = self._get_request(url)
        response.raise_for_status()
        channels = []
        realStart = None
        realEnd = None
        if response.text:
            j = response.json()
            if 'start' in j: 
                realStart = parse(j['start'])
            if 'end' in j: 
                realEnd = parse(j['end'])
            if 'channels' in j:
                for channel in j['channels']:
                    channels.append(VuewDeviceChannelUsage().from_json_dictionary(channel))
        return channels, realStart, realEnd


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

def _format_time(time):
    return time.isoformat()+'Z'

def _format_date(date):
    return date.strftime('%Y-%m-%d')
