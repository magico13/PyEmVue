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

### Typical Example - Getting Recent Usage
This example prints out the device list and energy usage over the last minute.
```python
#!/usr/bin/python3

import pyemvue
from pyemvue.enums import Scale, Unit

def print_recursive(usage_dict, info, depth=0):
    for gid, device in usage_dict.items():
        for channelnum, channel in device.channels.items():
            name = channel.name
            if name == 'Main':
                name = info[gid].device_name
            print('-'*depth, f'{gid} {channelnum} {name} {channel.usage} kwh')
            if channel.nested_devices:
                print_recursive(channel.nested_devices, info, depth+1)

vue = pyemvue.PyEmVue()
vue.login(username='put_username_here', password='put_password_here', token_storage_file='keys.json')

devices = vue.get_devices()
device_gids = []
device_info = {}
for device in devices:
    if not device.device_gid in device_gids:
        device_gids.append(device.device_gid)
        device_info[device.device_gid] = device
    else:
        device_info[device.device_gid].channels += device.channels

device_usage_dict = vue.get_device_list_usage(deviceGids=device_gids, instant=None, scale=Scale.MINUTE.value, unit=Unit.KWH.value)
print('device_gid channel_num name usage unit')
print_recursive(device_usage_dict, device_info)
```

This will print out something like:
```
device_gid channel_num name usage unit
 1234 1,2,3 Home 0.018625023078918456 kwh
- 2345 1,2,3 Furnace 0.0 kwh
- 2346 1,2,3 EV 0.0 kwh
 1234 1 Oven 0.0 kwh
 1234 2 Dryer 0.0 kwh
 1234 3 Water Heater 0.0 kwh
 1234 4 Kitchen 1 0.0 kwh
- 3456 1,2,3 Washer 2.0127220576742082e-06 kwh
 1234 5 Living Room 0.00031066492724719774 kwh
- 123456 1,2,3 myplug None kwh
- 123457 1,2,3 Tree None kwh
- 123458 1,2,3 Kitchen Counter 5.368702827258442e-05 kwh
 1234 6 Bar Area 0.0020457032945421006 kwh
 1234 7 Kitchen 2 0.0 kwh
 1234 8 Dishwasher 0.0002561144436730279 kwh
 1234 9 Bathroom Heater 0.0 kwh
 1234 10 Microwave 0.0 kwh
 1234 11 AC 0.0 kwh
 1234 12 Basement 0.0011743871887920825 kwh
- 123459 1,2,3 Dehumidifier 0.005342410305036585 kwh
 1234 13 Deck 0.0 kwh
 1234 14 Front Room 0.0027938466452995143 kwh
- 123450 1,2,3 Library 0.0001436362373061446 kwh
 1234 15 Office 0.004370743334687561 kwh
- 123451 1,2,3 Network 0.001209796911216301 kwh
- 123452 1,2,3 Bedroom Fan None kwh
 1234 16 Garage 0.0005456661001841227 kwh
 1234 Balance Balance 0.00037836666266123273 kwh
```


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

`See Typical Example above.`

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

### Get Vehicles and Status (including battery charge level).
Note: this call may take an extended amount of time depending on the vehicle, and may "wake" the vehicle to check status - be mindful of call volume, and aware of 10 second timeout that will hit if the vehicle doesn't reply in time (future may want to increase that).

```python
vehicles = vue.get_vehicles()
print('List of Vehicles')
for vehicle in vehicles:
    print(f'\t{vehicle.vehicle_gid} ({vehicle.display_name}) - {vehicle.year} {vehicle.make} {vehicle.model}')

print('List of Vehicle Statuses')
for vehicle in vehicles:
    vehicleStatus = vue.get_vehicle_status(vehicle)
    print(f'\t{vehicleStatus.vehicle_gid} {vehicleStatus.vehicle_state} - Charging: {vehicleStatus.charging_state} Battery level: {vehicleStatus.battery_level}')
```

### Disclaimer

This project is not affiliated with or endorsed by Emporia Energy.
