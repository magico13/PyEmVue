# PyEmVue

A Python Library for reading data from the Emporia Vue energy monitoring system.

The library can be invoked directly to pull back some basic info but requires your email and password to be added to a keys.json file, which is then replaced with the access tokens.

API documentation can be [accessed here](https://github.com/magico13/PyEmVue/blob/master/api_docs.md)

keys.json

```json
{
    "email": "you@email.com",
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
vue.login(id_token=data['idToken'],
    access_token=data['accessToken'],
    refresh_token=data['refreshToken'],
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

### Get total usage

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

energy_usage = vue.get_total_usage(channel, timeFrame=TotalTimeFrame.ALL.value, unit=TotalUnit.WATTHOURS.value)
```

Returns the total usage over the time frame for the specified channel as a single float number. Generally energy over all time or month to date.

#### Arguments

- **channel**: A VueDeviceChannel from the `get_devices` call. Key parts are the `device_gid` and `channel_num`.
- **timeFrame**: Any value from the `TotalTimeFrame` enum. Either all time or month to date.
- **unit**: Any value from the `TotalUnit` enum. Currently only watthours.

### Get recent usage

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

channel_usage_list = vue.get_recent_usage(scale=Scale.HOUR.value, unit=Unit.WATTS.value)
for channel in channel_usage_list:
    print(channel.usage)
```

Returns list of `ViewDeviceChannelUsage` objects giving usage over the `scale` timeframe in the `unit` specified. For a scale of under 1 hour this will give the average usage over the time frame (ie kW), for an hour or more it gives the total usage (ie kWh).

#### Arguments

- **scale**: Any value from the `Scale` enum. From 1 second to 1 year.
- **unit**: Any value from the `Unit` enum. Generally watts but there are options for dollars or trees or miles driven, etc.

### Get usage over a time scale

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

channel_usage_list = vue.get_usage_for_time_scale(time=datetime.datetime(2020, 6, 21, 18, 0, 0) scale=Scale.HOUR.value, unit=Unit.WATTS.value)
for channel in channel_usage_list:
    print(channel.usage)
```

Returns list of `ViewDeviceChannelUsage` objects giving usage over the `scale` timeframe in the `unit` specified for the "bucket" containing the time provided. For a scale of under 1 hour this will give the average usage over the time frame (ie kW), for an hour or more it gives the total usage (ie kWh). The start and end times for the bucket will be returned although is not always consistent (month will give only the start of the month but minute gives start/end times one minute apart for instance).

#### Arguments

- **time**: A datetime value to use as the end time.
- **scale**: Any value from the `Scale` enum. From 1 second to 1 year.
- **unit**: Any value from the `Unit` enum. Generally watts but there are options for dollars or trees or miles driven, etc.


### Get usage over time

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

usage_time = vue.get_usage_over_time(channel, start, end, scale=Scale.SECOND.value, unit=Unit.WATTS.value)

# Throw into matplotlib for plotting
```

Returns the energy used by the VueDeviceChannel between the `start` and `end` datetimes for each `scale` timeframe. In other words, if `scale` is seconds and there's a minute between `start` and `end`, you'll get 60 data points in the output.

#### Arguments

- **channel**: A VueDeviceChannel from the `get_devices` call. Key parts are the `device_gid` and `channel_num`.
- **start**: Starting `datetime` given in UTC.
- **end**: Ending `datetime` given in UTC.
- **scale**: Any value of `Scale` enum at HOUR or finer, DAY and higher is not supported. For 1 hour between `start` and `end` you'd get 3600 data points at SECOND, 60 at MINUTE, or 4 at MINUTE_15.
- **unit**: Any value of `Unit` enum, generally watts.

### Get usage over a date range

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

usage_time = vue.get_usage_over_date_range(channel, start, end, scale=Scale.DAY.value, unit=Unit.WATTS.value)

# Throw into matplotlib for plotting
```

Returns the energy used by the VueDeviceChannel between the `start` and `end` datetimes for each `scale` timeframe. In other words, if `scale` is days and there's a week between `start` and `end`, you'll get 7 data points in the output.

**NOTE:** The actual start and end dates for this call are weird. For my timezone of UTC-4 if I pass in 2020-07-09 for the start the first datapoint is for 2020-07-08. Passing the same value for start and end will appear to work but will give incorrect data. To get correct data for a DAY pass the day you want for the start, two days later for the end, and take the second value. I would recommend doing the same with weeks, months, years, etc.

#### Arguments

- **channel**: A VueDeviceChannel from the `get_devices` call. Key parts are the `device_gid` and `channel_num`.
- **start**: Starting `datetime` given in UTC.
- **end**: Ending `datetime` given in UTC.
- **scale**: Any value of `Scale` enum at DAY or higher, HOUR and lower are not supported.
- **unit**: Any value of `Unit` enum, generally watts.

### Toggle outlets

```python
vue = PyEmVue()
vue.login(id_token='id_token',
    access_token='access_token',
    refresh_token='refresh_token')

outlets = vue.get_outlets()
for outlet in outlets:
    vue.update_outlet(outlet, not outlet_on)
    # alternatively it can be set on the outlet object first
    outlet.outlet_on = not outlet.outlet_on
    outlet = vue.update_outlet(outlet)
```

The `get_outlets` call returns a list of the basic outlet structure but it is also possible to get a full `VueDevice` for the outlet first through the `get_devices` call where the `OutletDevice` will be an object off of the `VueDevice` (ie `device.outlet`). The call to `update_outlet` can either take a full `OutletDevice` with updated values or for simplicity can also take a True/False to turn the outlet on/off without separately modifying the initial outlet object.

### Disclaimer

This project is not affiliated with or endorsed by Emporia Energy.
