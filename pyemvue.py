import requests
import datetime
from enum import Enum
import json
import sys

api_root = "https://api.emporiaenergy.com"
api_usage_devices = "/usage/devices?start={startTime}&end={endTime}&scale={scale}&unit={unit}&customerGid={customerGid}"
api_usage_time = "/usage/time?start={startTime}&end={endTime}&type={type}}&deviceGid={deviceGid}&scale={scale}&unit={unit}&channels={channels}"

class pyemvue(object):
    def __init__(self, customerGid, authtoken):
        self.customer_gid = customerGid
        self.auth_token = authtoken
    
    def get_current_channels(self):
        now = datetime.datetime.now()
        minute_ago = now - datetime.timedelta(minutes=1)
        url = api_root + api_usage_devices.format(startTime = format_time(minute_ago), endTime = format_time(now), scale = scale.MINUTE, unit = unit.WATTS, customerGid = self.customer_gid)
        response = self.get_request(url)
        response.raise_for_status()
        if response.text:
            j = response.json()
            if 'channels' in j:
                return j['channels']
        return None

    def get_request(self, full_endpoint):
        headers = {'authtoken': self.auth_token}
        return requests.get(full_endpoint, headers=headers)


class scale(Enum):
    SECOND = "1S"
    MINUTE = "1MIN"
    MINUTES_15 = "15MIN"
    HOUR = "1H"

class unit(Enum):
    WATTS = "WATTS"
    USD = "USD"
    TREES = "TREES"
    GAS = "GALLONSGAS"
    DRIVEN = "MILESDRIVEN"
    FLOWN = "MILESFLOWN"


def format_time(time):
    return time.isoformat()+'Z'

if __name__ == "__main__":
    data = {}
    cgid = 0
    auth = None
    try:
        with open('keys.json') as f:
            data = json.load(f)
    except:
        print('Please create a "keys.json" file containing the "customerGid" and "authtoken"')
        sys.exit(1)
    if not 'customerGid' in data or not 'authtoken' in data:
        print('Please create a "keys.json" file containing the "customerGid" and "authtoken"')
        sys.exit(1)
    cgid = data['customerGid']
    auth = data['authtoken']
    if cgid <= 0:
        print('customerGid invalid')
        sys.exit(1)
    if len(auth) <= 0:
        print('authtoken invalid')
        sys.exit(1)
    vue = pyemvue(cgid, auth)
    print(vue.get_current_channels())
