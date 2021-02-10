import sys
import datetime
import json
import dateutil

# Our files
from pyemvue.enums import Scale, Unit
from pyemvue.customer import Customer
from pyemvue.device import VueDevice, VueDeviceChannel, VueDeviceChannelUsage
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
    deviceGids = []
    for device in devices:
        deviceGids.append(device.device_gid)
        print(device.device_gid, device.manufacturer_id, device.model, device.firmware)
        vue.populate_device_properties(device)
        for chan in device.channels:
            print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier)
    monthly, start = vue.get_chart_usage(devices[0].channels[0], None, None, Scale.MONTH.value)
    print(monthly[0], 'kwh used since', start.isoformat())
    now = datetime.datetime.utcnow()
    midnight=(datetime.datetime
             .now(dateutil.tz.gettz(devices[0].time_zone))
             .replace(hour=0, minute=0, second=0, microsecond=0)
             .astimezone(dateutil.tz.tzutc()))
    yesterday = midnight - datetime.timedelta(days=1)
    yesterday = yesterday.replace(tzinfo=None)
    minAgo = now - datetime.timedelta(minutes=1)
    print('Total usage for today in kwh: ')

    use = vue.get_devices_usage(deviceGids, now, Scale.DAY.value)
    for chan in use:
        print(f'{chan.device_gid} ({chan.channel_num}): {chan.usage} kwh')
    print('Total usage for yesterday in kwh: ')
    for chan in use:
        usage = vue.get_chart_usage(chan, yesterday, yesterday+datetime.timedelta(hours=23, minutes=59), Scale.DAY.value)
        if usage:
            print(f'{chan.device_gid} ({chan.channel_num}): {usage[0][0]} kwh')
    print('Average usage over the last minute in watts: ')
    use = vue.get_devices_usage(deviceGids, None, Scale.MINUTE.value)
    for chan in use:
        print(f'{chan.device_gid} ({chan.channel_num}): {chan.usage*1000*60} W')

if __name__ == '__main__':
    main()