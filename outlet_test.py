import sys
import json

from pyemvue.enums import Scale, Unit, TotalTimeFrame, TotalUnit
from pyemvue.customer import Customer
from pyemvue.device import VueDevice, VueDeviceChannel, VuewDeviceChannelUsage, OutletDevice
from pyemvue.pyemvue import PyEmVue

filepath = 'keys.json'

data = {}
email = None
passw = None
idToken = None
accessToken = None
refreshToken = None
try:
    with open(filepath) as f:
        data = json.load(f)
except:
    print('Error opening file.')
    raise
if ('email' not in data or 'password' not in data) and ('idToken' not in data or 'accessToken' not in data or 'refreshToken' not in data):
    print("error")
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
    print('Not enough details to log in.')
    sys.exit(1)
vue = PyEmVue()
vue.login(email, passw, idToken, accessToken, refreshToken, token_storage_file='keys.json')
print('Logged in. Authtoken follows:')
print(vue.cognito.id_token)
print()
devices = vue.get_devices()
for device in devices:
    print(device.device_gid, device.manufacturer_id, device.model, device.firmware)
    if (device.outlet is not None):
        print('Is an outlet! On? ', device.outlet.outlet_on)
    vue.populate_device_properties(device)
    for chan in device.channels:
        print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier)
    
