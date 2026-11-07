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

### Get devices (V1 API)

```python
vue = PyEmVue()
vue.login(username='you@email.com', password='password')

# Returns modern VueDevice tree with physical hierarchy and active channel status
devices = vue.get_devices_v1()
for device in devices:
    print(f'{device.device_gid}: {device.device_name} (Model: {device.model})')
    for channel in device.channels:
        # has_data indicates if a physical CT is connected or actively reporting
        if channel.has_data:
            print(f'  Channel {channel.channel_num}: {channel.name}')
    for child in device.children:
        print(f'  Nested Device: {child.device_gid} ({child.device_name})')
```

Returns a list of `VueDevice` objects directly from Emporia's `/v1/customers/devices` API. `get_devices_v1()` automatically resolves the physical electrical hierarchy (linking nested sub-panels and chargers via `device.children` and `device.parent_device_id`), populates device names, and sets `channel.has_data` to easily distinguish active CTs from unpopulated ports.

### Get sites (locations)

```python
sites = vue.get_sites()
for site in sites:
    print(f'Site {site.site_gid}: {site.display_name} ({site.time_zone}) - Rate: ${site.usage_cents_per_kwh}/kWh')
```

Returns a list of `VueSite` objects from `/v1/customers/sites`, representing configured customer locations, timezone, utility rate schedules, and associated device IDs.

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

### Get usages for devices (V1 multi-device batch)

```python
# Query instantaneous power across multiple monitors in a single batch call
usages = vue.get_device_list_usage_v1(
    device_gids=[1234, 2345],
    instant=None,
    scale='SECOND',
    energy_unit='KILOWATT_HOURS'
)

for gid, device_usage in usages.items():
    mains = device_usage.channels_by_id.get('Mains')
    print(f'Device {gid} Mains: {mains.usage} kWh (Raw: {mains.raw_usage})')
```

Queries `GET /v1/customers/devices/usages` to retrieve power or energy for multiple devices in a single HTTP request. Channels can be indexed by channel number (`device_usage.channels['1']`) or by channel ID (`device_usage.channels_by_id['Branch_1']`).

### Get split-phase voltage

```python
# Query instantaneous line voltage for split-phase services
voltages = vue.get_device_list_usage(
    deviceGids=[1234],
    instant=None,
    scale=Scale.SECOND.value,
    unit=Unit.VOLTS.value
)

device = voltages[1234]
print(f"Mains A: {device.channels['Mains_A'].usage} V")
print(f"Mains B: {device.channels['Mains_B'].usage} V")
```

Returns instantaneous voltage readings using `Unit.VOLTS = "Voltage"`. On North American split-phase panels, `Mains_A` and `Mains_B` provide individual leg voltages (~120V) and combined line-to-line 240V circuits. On 3-phase installations (e.g. European/Australian 230V/400V wye or commercial delta), `Mains_A`, `Mains_B`, and `Mains_C` provide individual phase voltages.

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

### Control EV Charger (EVSE)

Emporia EV Chargers can be controlled via modern V1 endpoints:

```python
vue = PyEmVue()
vue.login(username='you@email.com', password='password')

# Query live charging session telemetry
status = vue.get_evse_control(device_id='<evse_id>')
if status:
    print(f'Status: {status.charger_status}, Active: {status.session_active}')
    print(f'Energy Delivered: {status.energy_delivered} kWh, Cost: ${status.cost}')
    print(f'Active Minutes: {status.active_charging_minutes}, Pilot Limit: {status.offered_amps} A')

# Turn charger on/off via V1 control endpoint
vue.set_evse_state(device_id='<evse_id>', enabled=True)

# Set charging current limit in amps
vue.set_evse_settings(device_id='<evse_id>', charge_rate_amps=32)
```

`get_evse_control()` queries `GET /v1/customers/evse/control` for live session metrics (accumulated kWh, session duration, utility billing cost, and pilot offered current). `set_evse_state()` and `set_evse_settings()` dispatch to `/v1/customers/evse/control` and `/v1/devices/evses/settings`.

Legacy methods `update_charger()` and `get_chargers()` remain fully supported for backward compatibility:

```python
chargers = vue.get_chargers()
for charger in chargers:
    charger.charger_on = not charger.charger_on
    charger.charging_rate = 16
    vue.update_charger(charger)
```

The `get_chargers` call returns a list of chargers directly, but it is also possible to get a full `VueDevice` for the charger through the `get_devices` or `get_devices_v1` call and access a `ChargerDevice` through the `ev_charger` attribute off of the `VueDevice` (ie `device.ev_charger`).

### Excess Solar Energy Management

Manage Emporia's native surplus solar EV charging:

```python
# Discover monitors with solar CTs eligible for excess generation control
eg_monitors = vue.get_excess_generation_monitors()
print('Eligible monitors:', [m.device_id for m in eg_monitors.monitors])
print('Non-solar monitors:', eg_monitors.unavailable_monitors)

# Query current excess solar configuration for a monitor
config = vue.get_excess_generation(device_id='<monitor_id>')
print('Active loads:', config.loads)
print('Solar window:', config.solar_window)
print('Sunrise / Sunset:', config.sunrise, config.sunset)

# Configure controllable loads under excess solar
vue.set_excess_generation(
    device_id='<monitor_id>',
    loads=[{'load_gid': 1001, 'enabled': True}],
    solar_window=None
)

# Immediately override solar or scheduled throttling to charge at full power
vue.post_evse_control(device_id='<evse_id>', command='CHARGE_AT_FULL_POWER')
```

Queries `GET /v1/customers/excess-generation` and `GET`/`POST /v1/customers/energy-monitor/excess-generation` to inspect eligible solar monitors, toggle surplus charging on assigned loads, and dispatch immediate `CHARGE_AT_FULL_POWER` overrides.

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
