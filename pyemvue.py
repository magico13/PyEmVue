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

class PyEmVue(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_devices(self):
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
        url = API_ROOT + API_CUSTOMER.format(email=self.username)
        response = self._get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            return Customer().from_json_dictionary(j)
        return None

    def _get_request(self, full_endpoint):
        if not self.cognito: raise Exception('Must call "login" before calling any API methods.')
        self._check_token() # ensure our token hasn't expired, refresh if it has
        headers = {'authtoken': self.cognito.id_token}
        return requests.get(full_endpoint, headers=headers)

    def login(self):
        # Use warrant to go through the SRP authentication to get an auth token and refresh token
        client = boto3.client('cognito-idp', region_name='us-east-2', 
            config=botocore.client.Config(signature_version=botocore.UNSIGNED))
        self.cognito = Cognito('us-east-2_ghlOXVLi1', '4qte47jbstod8apnfic0bunmrq', 
            user_pool_region='use-east-2', username=self.username)
        self.cognito.client = client
        self.cognito.authenticate(password=self.password)
        if self.cognito.access_token is not None:
            self.customer = self.get_customer_details()
        return self.customer is not None
        
    def _check_token(self):
        self.cognito.check_token()

class VueDevice(object):
    def __init__(self, gid=0, manId='', modelNum='', firmwareVersion=''):
        self.device_gid = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.channels = []

    def from_json_dictionary(self, js):
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
        if 'customerGid' in js: self.customer_gid = js['customerGid']
        if 'email' in js: self.email = js['email']
        if 'firstName' in js: self.first_name = js['firstName']
        if 'lastName' in js: self.lastName = js['lastName']
        if 'createdAt' in js: self.created_at = js['createdAt']
        return self

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

def _format_time(time):
    return time.isoformat()+'Z'

if __name__ == '__main__':
    data = {}
    email = 0
    passw = None
    try:
        with open('keys.json') as f:
            data = json.load(f)
    except:
        print('Please create a "keys.json" file containing the "email" and "password"')
        sys.exit(1)
    if not 'email' in data or not 'password' in data:
        print('Please create a "keys.json" file containing the "email" and "password"')
        sys.exit(1)
    email = data['email']
    passw = data['password']
    if not email:
        print('email invalid')
        sys.exit(1)
    if not passw:
        print('password invalid')
        sys.exit(1)
    vue = PyEmVue(email, passw)
    vue.login()
    print('Logged in. Auth token follows:')
    print(vue.cognito.id_token)
    print()
    print(vue.get_devices())
