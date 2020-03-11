import requests
import datetime
from enum import Enum
import json
import sys

# These provide AWS cognito authentication support
import boto3
import botocore
from warrant import Cognito

API_ROOT = 'https://api.emporiaenergy.com'
API_CUSTOMER = '/customers?email={email}'
API_CUSTOMER_DEVICES = '/customers/{customerGid}/devices?detailed=true&hierarchy=true'
API_USAGE_DEVICES = '/usage/devices?start={startTime}&end={endTime}&scale={scale}&unit={unit}&customerGid={customerGid}'
API_USAGE_TIME = '/usage/time?start={startTime}&end={endTime}&type={type}}&deviceGid={deviceGid}&scale={scale}&unit={unit}&channels={channels}'
API_USAGE_TOTAL = '/usage/total?deviceGid={deviceGid}&timeframe={timeFrame}&unit={unit}&channels={channels}'

CLIENT_ID = '4qte47jbstod8apnfic0bunmrq'
USER_POOL = 'us-east-2_ghlOXVLi1'


class Scale(Enum):
    SECOND = '1S'
    MINUTE = '1MIN'
    MINUTES_15 = '15MIN'
    HOUR = '1H'

class Unit(Enum):
    WATTS = 'WATTS'
    USD = 'USD'
    TREES = 'TREES'
    GAS = 'GALLONSGAS'
    DRIVEN = 'MILESDRIVEN'
    FLOWN = 'MILESFLOWN'

class TotalUnit(Enum):
    WATTHOURS = 'WATTHOURS'

class TotalTimeFrame(Enum):
    ALL = 'ALLTODATE'
    MONTH = 'MONTHTODATE'


class PyEmVue(object):
    def __init__(self, username=None, password=None, idToken=None, accessToken=None, refreshToken=None):
        self.username = username
        self.password = password
        self.id_token = idToken
        self.access_token = accessToken
        self.refresh_token = refreshToken

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
        return devices

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
        return None

    def login(self, tokenStorageFile=None):
        """ Authenticates the current user using access tokens if provided or username/password if no tokens available.
            Provide a path for storing the token data that can be used to reauthenticate without providing the password.
            Tokens stored in the file are updated when they expire.
        """
        # Use warrant to go through the SRP authentication to get an auth token and refresh token
        client = boto3.client('cognito-idp', region_name='us-east-2', 
            config=botocore.client.Config(signature_version=botocore.UNSIGNED))
        if self.id_token is not None and self.access_token is not None and self.refresh_token is not None:
            # use existing tokens
            #print('Logging in with auth tokens')
            self.cognito = Cognito(USER_POOL, CLIENT_ID,
                user_pool_region='us-east-2', 
                id_token=self.id_token, 
                access_token=self.access_token, 
                refresh_token=self.refresh_token)
            self.cognito.client = client
        elif self.username is not None and self.password is not None:
            #log in with username and password
            #print('Logging in with username and password')
            self.cognito = Cognito(USER_POOL, CLIENT_ID, 
                user_pool_region='us-east-2', username=self.username)
            self.cognito.client = client
            self.cognito.authenticate(password=self.password)
        else:
            raise Exception('No authentication method found. Must supply username/password or id/auth/refresh tokens.')
        if self.cognito.access_token is not None:
            if tokenStorageFile is not None: self.token_storage_file = tokenStorageFile
            self.customer = self.get_customer_details()
            self.username = self.customer.email
            self._store_tokens()
        return self.customer is not None
        
    def _check_token(self):
        if self.cognito.check_token(renew=True):
            # Token expired and we renewed it. Store new token
            self._store_tokens()

    def _store_tokens(self):
        if not self.token_storage_file: return
        data = {
            'email': self.username,
            'idToken': self.cognito.id_token,
            'accessToken': self.cognito.access_token,
            'refreshToken': self.cognito.refresh_token
        }
        with open(self.token_storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_request(self, full_endpoint):
        if not self.cognito: raise Exception('Must call "login" before calling any API methods.')
        self._check_token() # ensure our token hasn't expired, refresh if it has
        headers = {'authtoken': self.cognito.id_token}
        return requests.get(full_endpoint, headers=headers)

class VueDevice(object):
    def __init__(self, gid=0, manId='', modelNum='', firmwareVersion=''):
        self.device_gid = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.channels = []

    def from_json_dictionary(self, js):
        """Populate device data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'manufacturerDeviceId' in js: self.manufacturer_id = js['manufacturerDeviceId']
        if 'model' in js: self.model = js['model']
        if 'firmware' in js: self.firmware = js['firmware']
        # 'devices' is empty in my system, will add support later if possible
        if 'channels' in js:
            # Channels are another subtype and the channelNum is used in other calls
            self.channels = []
            for chnl in js['channels']:
                self.channels.append(VueDeviceChannel().from_json_dictionary(chnl))
        return self

class VueDeviceChannel(object):
    def __init__(self, gid=0, name='', channelNum='1,2,3', channelMultiplier=1.0):
        self.device_gid = gid
        self.name = name
        self.channel_num = channelNum
        self.channel_multiplier = channelMultiplier

    def from_json_dictionary(self, js):
        """Populate device channel data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'name' in js: self.name = js['name']
        if 'channelNum' in js: self.channel_num = js['channelNum']
        if 'channelMultiplier' in js: self.channel_multiplier = js['channelMultiplier']
        return self

class Customer(object):
    def __init__(self, gid=0, email='', firstName='', lastName='', createdAt=datetime.datetime(1970, 1, 1)):
        self.customer_gid = gid
        self.email = email
        self.first_name = firstName
        self.lastName = lastName
        self.created_at = createdAt

    def from_json_dictionary(self, js):
        """Populate customer data from a dictionary extracted from the response json."""
        if 'customerGid' in js: self.customer_gid = js['customerGid']
        if 'email' in js: self.email = js['email']
        if 'firstName' in js: self.first_name = js['firstName']
        if 'lastName' in js: self.lastName = js['lastName']
        if 'createdAt' in js: self.created_at = js['createdAt']
        return self

def _format_time(time):
    return time.isoformat()+'Z'

if __name__ == '__main__':
    data = {}
    email = None
    passw = None
    idToken = None
    accessToken = None
    refreshToken = None
    try:
        with open('keys.json') as f:
            data = json.load(f)
    except:
        print('Please create a "keys.json" file containing the "email" and "password"')
        sys.exit(1)
    if ('email' not in data or 'password' not in data) and ('idToken' not in data or 'accessToken' not in data or 'refreshToken' not in data):
        print('Please create a "keys.json" file containing the "email" and "password"')
        sys.exit(1)
    canLogIn = False
    if 'email' in data:
        email = data['email']
        if 'password' in data:
            passw = data['password']
            canLogIn = True
    if 'idToken' in data and 'accessToken' in data and 'refreshToken' in data:
        idToken = data['idToken']
        accessToken = data['accessToken']
        refreshToken = data['refreshToken']
        canLogIn = True
    if not canLogIn:
        print('Please create a "keys.json" file containing the "email" and "password"')
        sys.exit(1)
    vue = PyEmVue(email, passw, idToken, accessToken, refreshToken)
    vue.login(tokenStorageFile='keys.json')
    print('Logged in. Authtoken follows:')
    print(vue.cognito.id_token)
    print()
    devices = vue.get_devices()
    for device in devices:
        print(device.device_gid, device.manufacturer_id, device.model, device.firmware)
        for chan in device.channels:
            print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier)
    print(vue.get_total_usage(devices[0].channels[0], TotalTimeFrame.MONTH.value) / 1000, 'kwh used month to date')
    print(vue.get_total_usage(devices[0].channels[0], TotalTimeFrame.ALL.value) / 1000, 'kwh used total')
