import sys
import datetime
import json
import pytz

# Our files
from pyemvue.enums import Scale, Unit, TotalTimeFrame, TotalUnit
from pyemvue.customer import Customer
from pyemvue.device import VueDevice, VueDeviceChannel, VuewDeviceChannelUsage
from pyemvue.pyemvue import PyEmVue

def main():
    errorMsg = 'Please pass a file containing the "email" and "password" as json.'
    if len(sys.argv) == 1:
        print(errorMsg)
        sys.exit(1)

    filepath = sys.argv[1]

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
        print('Error opening file.', errorMsg)
        raise
    if ('email' not in data or 'password' not in data) and ('idToken' not in data or 'accessToken' not in data or 'refreshToken' not in data):
        print(errorMsg)
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
        print('Not enough details to log in.', errorMsg)
        sys.exit(1)
    vue = PyEmVue()
    vue.login(email, passw, idToken, accessToken, refreshToken, token_storage_file='keys.json')
    print('Logged in. Authtoken follows:')
    print(vue.cognito.id_token)
    print()
    devices = vue.get_devices()
    for device in devices:
        print(device.device_gid, device.manufacturer_id, device.model, device.firmware)
        vue.populate_device_properties(device)
        for chan in device.channels:
            print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier)
    print(vue.get_total_usage(devices[0].channels[0], TotalTimeFrame.MONTH.value) / 1000, 'kwh used month to date')
    print(vue.get_total_usage(devices[0].channels[0], TotalTimeFrame.ALL.value) / 1000, 'kwh used total')
    now = datetime.datetime.utcnow()
    yesterday = datetime.datetime.now(pytz.timezone(devices[0].time_zone))
    yesterday = yesterday.replace(hour=23, minute=59, second=59) - datetime.timedelta(days=1)
    yesterday = yesterday.astimezone(pytz.utc).replace(tzinfo=None)
    print(yesterday.isoformat())
    minAgo = now - datetime.timedelta(minutes=1)
    print('Total usage for today in kwh: ')
    use = vue.get_recent_usage(Scale.DAY.value)
    for chan in use:
        print(f'{chan.device_gid} ({chan.channel_num}): {chan.usage/1000} kwh')
    print('Total usage for yesterday in kwh: ')
    use, realStart, realEnd = vue.get_usage_for_time_scale(yesterday, Scale.DAY.value)
    print(f'Time range: {realStart} to {realEnd}')
    for chan in use:
        print(f'{chan.device_gid} ({chan.channel_num}): {chan.usage/1000} kwh')
    print('Average usage over the last minute in watts: ')
    use = vue.get_recent_usage(Scale.MINUTE.value)
    for chan in use:
        print(f'{chan.device_gid} ({chan.channel_num}): {chan.usage} W')
    
    print('Usage over the last minute in watts: ', vue.get_usage_over_time(devices[0].channels[0], minAgo, now))

if __name__ == '__main__':
    main()