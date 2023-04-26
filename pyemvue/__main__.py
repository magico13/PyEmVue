import sys
import datetime
import dateutil

# Our files
from pyemvue.device import VueDevice, VueUsageDevice
from pyemvue.enums import Scale, Unit
from pyemvue.pyemvue import PyEmVue

def print_recursive(usage_dict: dict[int, VueUsageDevice], info: dict[int, VueDevice], scaleBy: float=1, unit='kWh', depth=0):
    for gid, device in usage_dict.items():
        for channelnum, channel in device.channels.items():
            name = channel.name
            if name == 'Main':
                name = info[gid].device_name
            usage = channel.usage or 0
            print('-'*depth, f'{gid} {channelnum} {name} {usage*scaleBy} {unit}')
            if channel.nested_devices:
                print_recursive(channel.nested_devices, info, scaleBy=scaleBy, unit=unit, depth=depth+1)

def main():
    errorMsg = 'Please pass a file containing the "email" and "password" as json.'
    if len(sys.argv) == 1:
        print(errorMsg)
        sys.exit(1)

    filepath = sys.argv[1]
    vue = PyEmVue()
    vue.login(token_storage_file=filepath)
    print('Logged in. Authtoken follows:')
    print(vue.auth.tokens["id_token"])
    print()
    channelTypes = vue.get_channel_types()
    devices = vue.get_devices()
    deviceGids: list[int] = []
    deviceInfo: dict[int, VueDevice] = {}
    for device in devices:
        if not device.device_gid in deviceGids:
            deviceGids.append(device.device_gid)
            deviceInfo[device.device_gid] = device
            print(device.device_gid, device.manufacturer_id, device.model, device.firmware)
            for chan in device.channels:
                channelTypeInfo = next((c for c in channelTypes if c.channel_type_gid == chan.channel_type_gid), None)
                print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier, channelTypeInfo.description if channelTypeInfo else chan.channel_type_gid)
        else:
            deviceInfo[device.device_gid].channels += device.channels
            for chan in device.channels:
                channelTypeInfo = next((c for c in channelTypes if c.channel_type_gid == chan.channel_type_gid), None)
                print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier, channelTypeInfo.description if channelTypeInfo else chan.channel_type_gid)

    monthly, start = vue.get_chart_usage(devices[0].channels[0],scale=Scale.MONTH.value)
    print(monthly[0], 'kwh used since', start.isoformat())
    now = datetime.datetime.now(datetime.timezone.utc)
    midnight=(datetime.datetime
             .now(dateutil.tz.gettz(devices[0].time_zone))
             .replace(hour=0, minute=0, second=0, microsecond=0)
             .astimezone(dateutil.tz.tzutc()))
    yesterday = midnight - datetime.timedelta(days=1)
    yesterday = yesterday.replace(tzinfo=None)
    print('Total usage for today in kwh: ')

    use = vue.get_device_list_usage(deviceGids, now, Scale.DAY.value)
    print_recursive(use, deviceInfo)
    print('Total usage for yesterday in kwh: ')
    for gid, device in deviceInfo.items():
        for chan in device.channels:
            usage = vue.get_chart_usage(chan, yesterday, yesterday+datetime.timedelta(hours=23, minutes=59), Scale.DAY.value)
            if usage and usage[0]:
                print(f'{chan.device_gid} ({chan.channel_num}): {usage[0][0]} kwh')
    print('Average usage over the last minute in watts: ')
    use = vue.get_device_list_usage(deviceGids, None, Scale.MINUTE.value)
    print_recursive(use, deviceInfo, scaleBy=60000, unit='W')

    usage_over_time, start_time = vue.get_chart_usage(devices[0].channels[0], datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=7), datetime.datetime.now(datetime.timezone.utc), scale=Scale.DAY.value, unit=Unit.KWH.value)

    print('Usage for the last seven days starting', start_time.isoformat())
    for usage in usage_over_time:
        print(usage, 'kwh')

    (outlets, chargers) = vue.get_devices_status(devices)
    print('List of Outlets:')
    for outlet in outlets:
        print(f"\t{outlet.device_gid} On? {outlet.outlet_on}")

    print('List of Chargers:')
    for charger in chargers:
        print(f"\t{charger.device_gid} On? {charger.charger_on} Charge rate: {charger.charging_rate}/{charger.max_charging_rate} Status: {charger.status}")

if __name__ == '__main__':
    main()