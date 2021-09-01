# PyEmVue

A Python Library for reading data from the Emporia Vue energy monitoring system.

The library can be invoked directly to pull back some basic info but requires your email and password to be added to a keys.json file, which is then replaced with the access tokens.

The backing API documentation can be [accessed here](https://github.com/magico13/PyEmVue/blob/master/api_docs.md)

keys.json

```json
{
    "username": "you@email.com",
    "password": "password"
}
```

## Usage

### Log in with username/password

```python
vue = PyEmVue()
vue.login(username='you@email.com', password='password', token_storage_file='keys.json')
```

`token_storage_file` is an optional file path where the access tokens will be written for reuse in later invocations. It will be updated whenever the tokens are automatically refreshed.

### Log in with access tokens

```python
with open('keys.json') as f:
    data = json.load(f)

vue = PyEmVue()
vue.login(id_token=data['id_token'],
    access_token=data['access_token'],
    refresh_token=data['refresh_token'],
    token_storage_file='keys.json')
```

### Get customer details

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

customer = vue.get_customer_details()
```

Returns a Customer object with email address, name, customer_gid, and creation date

### Get devices

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

vue.get_devices()
```

Returns a list of VueDevices with device information, including device_gid and list of VueDeviceChannels associated with the device. VueDeviceChannels are passed to other methods to get information for the specific channel.

### Get additional device properties

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

device1 = vue.get_devices()[0]
print(device1.device_name) # prints ""
device1 = vue.populate_device_properties(device1)
print(device1.device_name) # prints "Home"
```

Updates and returns the passed VueDevice with additional information about the device such as the device name (as set in the app), zip code, timezone, electricity costs, etc.

#### Arguments

- **device**: A VueDevice as returned by `get_devices`. Will be updated and returned.

### Get usages for devices

```python
def print_recursive(usage_dict, info, depth=0):
    for gid, device in usage_dict.items():
        for channelnum, channel in device.channels.items():
            name = channel.name
            if name == 'Main':
                name = info[gid].device_name
            print('-'*depth, f'{gid} {channelnum} {name} {channel.usage} kwh')
            if channel.nested_devices:
                print_recursive(channel.nested_devices, depth+1)

vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

devices = vue.get_devices()
deviceGids = []
info = {}
for device in devices:
    if not device.device_gid in device_gids:
        device_gids.append(device.device_gid)
        info[device.device_gid] = device
    else:
        info[device.device_gid].channels += device.channels

device_usage_dict = vue.get_device_list_usage(deviceGids=device_gids, instant=datetime.now(datetime.timezone.utc), scale=Scale.HOUR.value, unit=Unit.KWH.value)
print_recursive(device_usage_dict, info)
```

Gets the usage for the given devices (specified by device_gid) over the provided time scale. May need to scale it manually to convert it to a rate, eg for 1 second data `kilowatt={usage in kwh/s}*3600s/1h` or for 1 minute data `kilowatt={usage in kwh/m}*60m/1h`.

#### Arguments

- **deviceGids**: A list of device_gid values pulled from get_devices() or a single device_gid.
- **instant**: What instant of time to check, will default to now if None.
- **scale**: The time scale to check the usage over.
- **unit**: The unit of measurement.

### Get usage over time

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

devices = vue.get_devices()

usage_over_time, start_time = vue.get_chart_usage(devices[0].channels[0], datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=7), datetime.datetime.now(datetime.timezone.utc), scale=Scale.DAY.value, unit=Unit.KWH.value)

print('Usage for the last seven days starting', start_time.isoformat())
for usage in usage_over_time:
    print(usage, 'kwh')
```

Gets the usage in the scale and unit provided over the given time range. Returns a tuple with the first element the usage list and the second the datetime that the range starts.

#### Arguments

- **channel**: A VueDeviceChannel object, typically pulled from a VueDevice.
- **start**: The start time for the time period. Defaults to now if None.
- **end**: The end time for the time period. Default to now if None.
- **scale**: The time scale to check the usage over.
- **unit**: The unit of measurement.

### Toggle outlets

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

outlets = vue.get_outlets()
for outlet in outlets:
    vue.update_outlet(outlet, on=(not outlet.outlet_on))
    # alternatively it can be set on the outlet object first
    outlet.outlet_on = not outlet.outlet_on
    outlet = vue.update_outlet(outlet)
```

The `get_outlets` call returns a list of outlets directly but it is also possible to get a full `VueDevice` for the outlet first through the `get_devices` call and access an `OutletDevice` through the `outlet` attribute off of the `VueDevice` (ie `device.outlet`).

### Toggle EV Charger (EVSE)

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

chargers = vue.get_chargers()
for charger in chargers:
    vue.update_charger(outlet, on=(not charger.charger_on), charge_rate=charger.max_charging_rate)
    # alternatively you can update the charger object first
    charger.charger_on = not charger.charger_on
    charger.charging_rate = 6
    charger.max_charging_rate = 16
    charger = vue.update_charger(charger)
```

The `get_chargers` call returns a list of chargers directly but it is also possible to get a full `VueDevice` for the charger first through the `get_devices` call and access a `ChargerDevice` through the `ev_charger` attribute off of the `VueDevice` (ie `device.ev_charger`).


### Disclaimer

This project is not affiliated with or endorsed by Emporia Energy.
