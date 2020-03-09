import requests
import datetime
from enum import Enum
import json
import sys

# These provide AWS cognito authentication support
import boto3
import botocore
from warrant.aws_srp import AWSSRP

API_ROOT = "https://api.emporiaenergy.com"
API_CUSTOMER_DEVICES = "/customers/{customerGid}/devices?detailed=true&hierarchy=true"
API_USAGE_DEVICES = "/usage/devices?start={startTime}&end={endTime}&scale={scale}&unit={unit}&customerGid={customerGid}"
API_USAGE_TIME = "/usage/time?start={startTime}&end={endTime}&type={type}}&deviceGid={deviceGid}&scale={scale}&unit={unit}&channels={channels}"

class PyEmVue(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_devices(self):
        url = API_ROOT + API_CUSTOMER_DEVICES.format(customerGid = self.customer_gid)
        response = self._get_request(url)
        response.raise_for_status()
        devices = []
        if response.text:
            j = response.json()
            if 'devices' in j:
                for dev in j['devices']:
                    devices.append(VueDevice().from_json_dictionary(dev))
        return devices

    # def get_devices(self):
    #     now = datetime.datetime.now()
    #     minute_ago = now - datetime.timedelta(minutes=1)
    #     url = API_ROOT + API_USAGE_DEVICES.format(startTime = _format_time(minute_ago), endTime = _format_time(now), scale = scale.MINUTE, unit = unit.WATTS, customerGid = self.customer_gid)
    #     response = self._get_request(url)
    #     response.raise_for_status()
    #     if response.text:
    #         j = response.json()
    #         if 'channels' in j:
    #             return j['channels']
    #     return None

    def _get_request(self, full_endpoint):
        headers = {'authtoken': self.auth_token}
        return requests.get(full_endpoint, headers=headers)

    def login(self):
        # Use warrant to go through the SRP authentication to get an auth token and refresh token
        client = boto3.client('cognito-idp', region_name="us-east-2", config=botocore.client.Config(signature_version=botocore.UNSIGNED)) #region might actually be closest, not static as this
        aws = AWSSRP(username=self.username, password=self.password, pool_id='us-east-2_ghlOXVLi1',
                    client_id='4qte47jbstod8apnfic0bunmrq', client=client)
        tokens = aws.authenticate_user()
        print(tokens)

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

class Scale(Enum):
    SECOND = "1S"
    MINUTE = "1MIN"
    MINUTES_15 = "15MIN"
    HOUR = "1H"

class Unit(Enum):
    WATTS = "WATTS"
    USD = "USD"
    TREES = "TREES"
    GAS = "GALLONSGAS"
    DRIVEN = "MILESDRIVEN"
    FLOWN = "MILESFLOWN"

class TotalUnit(Enum):
    WATTHOURS = "WATTHOURS"

class TotalTimeFrame(Enum):
    ALL = "ALLTODATE"
    MONTH = "MONTHTODATE"

def _format_time(time):
    return time.isoformat()+'Z'

if __name__ == "__main__":
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
    #print(vue.get_devices())
