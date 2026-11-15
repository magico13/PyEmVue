# API Documentation

## Authorization through AWS idp

Emporia uses the AWS cognito idp for authentication, getting an access token, refresh token, and most importantly an id token from there. The id token is provided to calls to the Emporia api via the `authtoken` header and expires after some time, at which point the refresh token is passed to the cognito idp to get a new set of access, refresh, and id tokens.

## Detection of maintenance

The check for if the servers are down for maintenance is rather simple in that it just checks the contents of a json file on Amazon S3. During normal operation this check returns an access denied error but during maintenance periods the content of the file is downloaded and checked. An example of this file during maintenance is below.

`https://s3.amazonaws.com/com.emporiaenergy.manual.ota/maintenance/maintenance.json`

```json
{"msg":"down"}
```

# Emporia Specific API

Root url for the api server is `https://api.emporiaenergy.com`

Authorization is provided through "authtoken" key in the header, not by a standard bearer token. The authtoken and corresponding refresh and id tokens are gotten from authenticating with AWS, currently done through the [Warrant](https://github.com/capless/warrant) library in this library.

## Get customer details

GET `/customers?email=you%40email.com`

### Response

```json
{
    "customerGid": 1234,
    "email": "you@email.com",
    "firstName": "First",
    "lastName": "Last",
    "createdAt": "2020-01-01T12:34:56.789Z"
}
```

## Get all devices for an account

GET `/customers/devices`

### Response

```json
{
    "customerGid": 1234,
    "email": "you@email.com",
    "firstName": "First",
    "lastName": "Last",
    "createdAt": "2020-01-01T12:34:56.789Z",
    "devices": [
        {
            "deviceGid": 2345,
            "manufacturerDeviceId": "{hex_device_id}",
            "model": "VUE001",
            "firmware": "Vue-1587661391",
            "locationProperties": {
                "deviceGid": 2345,
                "deviceName": "MyHome",
                "zipCode": "12345",
                "timeZone": "America/New_York",
                "billingCycleStartDay": 15,
                "usageCentPerKwHour": 15.0,
                "peakDemandDollarPerKw": 0.0,
                "locationInformation": {
                    "airConditioning": "true",
                    "heatSource": "electricSpaceHeater",
                    "locationSqFt": "1200",
                    "numElectricCars": "1",
                    "locationType": "houseMultiLevel",
                    "numPeople": "2",
                    "swimmingPool": "false",
                    "hotTub": "false"
                },
                "latitudeLongitude": null
            },
            "outlet": null,
            "devices": [],
            "channels": [
                {
                    "deviceGid": 2345,
                    "name": null,
                    "channelNum": "1,2,3",
                    "channelMultiplier": 1.0,
                    "channelTypeGid": null
                }
            ]
        },
        {
            "deviceGid": 3456,
            "manufacturerDeviceId": "{hex_device_id}",
            "model": "SSO001",
            "firmware": "Outlet-1594685591",
            "locationProperties": {
                "deviceGid": 3456,
                "deviceName": "myplug",
                "zipCode": "12345",
                "timeZone": "America/New_York",
                "billingCycleStartDay": 15,
                "usageCentPerKwHour": 15.0,
                "peakDemandDollarPerKw": 0.0,
                "locationInformation": null,
                "latitudeLongitude": null
            },
            "outlet": {
                "deviceGid": 3456,
                "outletOn": false,
                "parentDeviceGid": 1234,
                "parentChannelNum": "1,2,3",
                "schedules": []
            },
            "devices": [],
            "channels": [
                {
                    "deviceGid": 3456,
                    "name": null,
                    "channelNum": "1,2,3",
                    "channelMultiplier": 1.0,
                    "channelTypeGid": 23
                }
            ]
        }
    ]
}
```

## Get device location info

GET `/devices/{deviceGid}/locationProperties`

### Response

```json
{
    "deviceGid": 1234,
    "deviceName": "Home",
    "zipCode": "54321",
    "timeZone": "America/New_York",
    "billingCycleStartDay": 15,
    "usageCentPerKwHour": 15.0,
    "peakDemandDollarPerKw": 0.0,
    "locationInformation": {
        "airConditioning": "true",
        "heatSource": "naturalGasFurnace",
        "locationSqFt": "1200",
        "numElectricCars": "1",
        "locationType": "houseMultiLevel",
        "numPeople": "2",
        "swimmingPool": "false",
        "hotTub": "false"
    },
    "latitudeLongitude": null
}
```

## getDeviceListUsages - Instantaneous device usage

GET `/AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGid1}+{deviceGid2}&instant=2021-02-09T21:18:50.278474Z&scale=1S&energyUnit=KilowattHours`

Valid energy units: `[KilowattHours, Dollars, AmpHours, Trees, GallonsOfGas, MilesDriven, Carbon]`

Valid scales: `[1S, 1MIN, 1H, 1D, 1W, 1MON, 1Y]`

### Response

```json
{
    "deviceListUsages": {
        "instant": "2021-08-18T19:46:19Z",
        "scale": "1D",
        "devices": [
            {
                "deviceGid": 1234,
                "channelUsages": [
                    {
                        "name": "Main",
                        "usage": 10.234881177404192,
                        "deviceGid": 1234,
                        "channelNum": "1,2,3",
                        "percentage": 100.0,
                        "nestedDevices": [
                            {
                                "deviceGid": 2345,
                                "channelUsages": [
                                    {
                                        "name": "Main",
                                        "usage": 2.904190340656776,
                                        "deviceGid": 2345,
                                        "channelNum": "1,2,3",
                                        "percentage": 28.375418241966806,
                                        "nestedDevices": []
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Bar Area",
                        "usage": 0.8640784244209527,
                        "deviceGid": 1234,
                        "channelNum": "1",
                        "percentage": 8.442486135829311,
                        "nestedDevices": []
                    },
                    {
                        "name": "A/C",
                        "usage": 0.0,
                        "deviceGid": 1234,
                        "channelNum": "2",
                        "percentage": 0.0,
                        "nestedDevices": []
                    },
                    {
                        "name": "Balance",
                        "usage": 1.595748729527017,
                        "deviceGid": 1234,
                        "channelNum": "Balance",
                        "percentage": 15.59127753285492,
                        "nestedDevices": []
                    }
                ]
            }
        ],
        "energyUnit": "KilowattHours"
    }
}
```

## getChartUsage - Usage over a range of time

GET `/AppAPI?apiMethod=getChartUsage&deviceGid={deviceGid}&channel=1,2,3&start=2020-12-09T20:00:00.000Z&end=2021-02-09T19:00:00.000Z&scale=1H&energyUnit=KilowattHours`

Valid energy units: `[KilowattHours, Dollars, AmpHours, Trees, GallonsOfGas, MilesDriven, Carbon]`

Valid scales: `[1S, 1MIN, 1H, 1D, 1W, 1MON, 1Y]`

### Response

```json
{
    "usageList": [
        6.317710544808371,
        3.299631271330938,
        6.341609317335783,
    ],
    "firstUsageInstant": "2021-02-08T20:00:00Z"
}
```

## Get list of outlets

GET `/customers/outlets`

Emporia Energy has released their own line of wifi-controlled outlets. This returns the list of outlets owned by the user.

### Response

```json
[
    {
        "deviceGid": 1234,
        "outletOn": false,
        "parentDeviceGid": null,
        "parentChannelNum": null
    }
]
```

## Activate/Deactivate an outlet

Turns an outlet on or off. Presumably can be used to nest an outlet under another device/channel but I haven't tested that yet.

PUT `/devices/outlet`

```json
{
    "deviceGid": 1234,
    "outletOn": true,
    "parentDeviceGid": null,
    "parentChannelNum": null
}
```

### Response

```json
{
    "deviceGid": 1234,
    "outletOn": true,
    "parentDeviceGid": null,
    "parentChannelNum": null
}
```

## Get list of EV chargers

GET `/customers/evchargers`

Returns the list of EV chargers (technically EVSE) linked to the account

### Response

```json
[
    {
        "deviceGid": 1234,
        "message": "Check your EV",
        "status": "Standby",
        "icon": "CarConnected",
        "iconLabel": "Ready",
        "iconDetailText": "Your charger is ready, but your EV is not.  Check your EV for a scheduled charge time.",
        "faultText": null,
        "chargerOn": true,
        "chargingRate": 25,
        "maxChargingRate": 40,
        "offPeakSchedulesEnabled": false
    }
]
```

## Activate/Deactivate a Charger

Enables you to turn the charger on and off, set the current charge rate, and set the maximum charge rate.

PUT `/devices/evcharger`

```json
{
    "deviceGid": 1234,
    "chargerOn": false,
    "chargingRate": 32,
    "maxChargingRate": 40,
    "offPeakSchedulesEnabled": false
}
```

### Response

```json
{
    "deviceGid": 1234,
    "message": "Check your EV",
    "status": "Standby",
    "icon": "CarConnected",
    "iconLabel": "Pausing",
    "iconDetailText": "Please wait a moment.",
    "faultText": null,
    "chargerOn": false,
    "chargingRate": 32,
    "maxChargingRate": 40,
    "offPeakSchedulesEnabled": false
}
```


## Get partner data

GET `/customers/partners?customerGid={customerGid}`

As of right now I do not know what this call will be used for. Guesses include devices made by other companies that work with the Emporia ecosystem (smart switches, power monitors?) or partners of Emporia's that they sell data to?

### Response

```json
[]
```

## Get thermostats

GET `/customers/thermostats?customerGid={customerGid}`

I haven't set up a thermostat with the app yet, will update after I do.

### Response

```json
[]
```

## Get remote config

GET `/remoteconfig?appVersion=2.4.35.2435`

Unsure of the use of this yet.

### Response

```json
{}
```

## Setting up an outlet

This is a WIP but I'd like to be able to set up an outlet without requiring a phone. I have yet to fully sniff the traffic since the setup fails while I'm listening to the traffic. Some basic info though: the outlet appears to also be using an ESP-32 or similar device like the Vue does. When you use hotspot mode the IP is 192.168.4.1 which corresponds to what I've seen with WiFi libraries for the ESP series of microcontrollers. The setup has a few back and forth requests and then presumably makes a call to the main API to register. I actually had it tell me it failed but finished registration.

Known calls:
POST `http://192.168.4.1/prov-config`
BODY (hex characters)

```text
08 02 62 24 0A 0F SSID 12 11 PWD
```

08 is backspace, 02 is "start of text" so I don't know how necessary those are. Then there's "b$" followed by linefeed and "shift in". The second line is the SSID followed by "device control 2" and "device control 1", then the password for the network. Again, I'm not sure how many of these extra characters are necessary.
Reponse:

```text
08 03 6A 00
```

The response is basically just the letter `j`. Technically it's `backspace "end of text" j null`.

I have yet to see a response to the next request:
POST `http://192.168.4.1/prov-config`
BODY

```text
08 04 72 00
```

In this case the request is `backspace "end of transmission" r null`. The app basically hangs at this point waiting for a response that doesn't come while I am listening to the traffic. Since this section is all plain http and not https it might be possible to capture this traffic another way that doesn't prevent it from succeeding.

# V1 API

Root url for the V1 api is `https://api.emporiaenergy.com/v1`. The routes below are called by this library through the `auth_v1` session.

Authorization uses the same Cognito id token as the legacy api, but is sent as a standard header: `Authorization: Bearer <id token>` rather than `authtoken`.

Naming differs from the legacy api: fields are `snake_case`, hardware is identified by a string `device_id` (the serial) in addition to the integer `device_gid`, and enum values are upper case. Example values below are placeholders.

## Units and scales

`/v1/customers/devices/usages` takes upper-case names, unlike `/AppAPI`:

| Parameter | `/AppAPI` | V1 |
| --- | --- | --- |
| `energyUnit` / `energy_unit` | `KilowattHours`, `Voltage`, `AmpHours`, `Dollars` | `KILOWATT_HOURS`, `VOLTAGE`, `AMP_HOURS`, `DOLLARS` |
| `scale` | `1S`, `1MIN`, `1H`, `1D`, ... | `SECOND`, `MINUTE`, `HOUR`, `DAY`, ... |

Only `SECOND` has been observed in captured traffic. Note that the amp-hours unit is `AMP_HOURS` (with an underscore). With `AMP_HOURS` the aggregate `Mains` channel has been observed to return `"usage": null`; the `Mains_A` and `Mains_B` channels return values.

## Get devices

GET `/customers/devices`

Returns monitors and EV chargers. Optional query parameter `device_ids` (repeatable) restricts the result.

### Response

```json
{
    "devices": [
        {
            "device_type": "MONITOR",
            "device_id": "MONITOR_SERIAL",
            "device_gid": 1234,
            "display_name": "Main panel",
            "site_gid": 5678,
            "parent_device_id": null,
            "parent_channel_id": null,
            "time_zone": "America/Denver",
            "billing_cycle_start_day": 1,
            "usage_cent_per_kw_hour": 0.12,
            "buyback_rate_cents_per_kwh": null,
            "net_metering": null,
            "model": "VUE003",
            "firmware": "Vue3-000",
            "category": "MONITOR",
            "energy_managements_configured": ["EXCESS_SOLAR"],
            "supported_energy_managements": ["POWER_SMART", "PEAK_DEMAND", "EXCESS_SOLAR"],
            "channels": [
                {
                    "channel_id": "Mains",
                    "parent_channel_id": null,
                    "name": null,
                    "multiplier": 1.0,
                    "channel_type_gid": null,
                    "channel_classification": "MAIN",
                    "has_data": true
                },
                {
                    "channel_id": "Mains_A",
                    "parent_channel_id": "Mains",
                    "name": null,
                    "multiplier": 1.0,
                    "channel_type_gid": null,
                    "channel_classification": "MAIN",
                    "has_data": true
                }
            ],
            "combined_vue": "NONE",
            "primary_vue_device_id": null
        },
        {
            "device_type": "EV_CHARGER",
            "device_id": "EVSE_SERIAL",
            "device_gid": 2345,
            "display_name": "EV charger",
            "site_gid": 5678,
            "parent_device_id": "MONITOR_SERIAL",
            "parent_channel_id": "Mains",
            "model": "VVDN01",
            "firmware": "EVCharger-000",
            "category": "EVSE",
            "load_gid": 3456,
            "evse_model": "Classic",
            "evse_branding": "EMPORIA",
            "evse_power_source": "NEMA",
            "evse_color": "WHITE",
            "evse_gun_type": "J1772",
            "energy_managements_configured": ["EXCESS_SOLAR"],
            "supported_energy_managements": ["LOAD_SHARING", "PEAK_DEMAND", "POWER_SMART"],
            "power_smart_upgraded": false
        }
    ]
}
```

EV charger entries share the common fields above (latitude, longitude, utility rate fields and so on, omitted here) and add the `evse_*` and `load_gid` fields. The captured EV charger entry had no `channels` key.

## Get channels

GET `/customers/devices/channels`

Returns a list of devices with their channels, including nested devices.

## Get sites

GET `/customers/sites`

Sites are optional, user-defined groupings of devices. An account without sites returns an empty list, and a device not assigned to a site has a `null` `site_gid`.

### Response

```json
{
    "sites": [
        {
            "site_gid": 5678,
            "display_name": "Home",
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": "America/Denver",
            "service_address": {
                "address": "123 Example St",
                "address2": null,
                "city": "Denver",
                "state": "CO",
                "postal": "80202",
                "country_code": "US"
            },
            "utility_provider": null,
            "utility_rate_gid": null,
            "utility_rate_mods": null,
            "usage_cents_per_kwh": 0.12,
            "buyback_rate_cents_per_kwh": null,
            "net_metering": null,
            "billing_cycle_start_day": 1,
            "device_ids": ["MONITOR_SERIAL", "EVSE_SERIAL"],
            "customer_emails": ["user@example.com"]
        }
    ]
}
```

## Get device status

GET `/customers/devices/status`

Optional query parameter `device_ids` (repeatable). Returns connectivity for all devices and live state for EV chargers.

### Response

```json
{
    "command_acknowledged": null,
    "devices_connected": [
        {"device_id": "EVSE_SERIAL", "device_gid": 2345, "connected": true, "offline_since": null}
    ],
    "monitors": [
        {"device_id": "MONITOR_SERIAL", "device_gid": 1234, "connected": true, "offline_since": null}
    ],
    "evses": [
        {
            "device_id": "EVSE_SERIAL",
            "device_gid": 2345,
            "load_gid": 3456,
            "connected": true,
            "offline_since": null,
            "charger_status": "CHARGING",
            "charging_rate": 13,
            "max_charging_rate": 48,
            "temperature_derated": false,
            "active_energy_managements": [
                {"type": "EXCESS_SOLAR", "active_since": "2026-01-01T12:00:00.000000Z"}
            ],
            "overridden_energy_managements": [],
            "next_scheduled_event": null,
            "override": null
        }
    ],
    "batteries": [],
    "outlets": [],
    "thermostats": [],
    "appliances": [],
    "vehicles": []
}
```

## Get device usages

GET `/customers/devices/usages?device_gids=1234,2345&instant=2026-01-01T12:00:00.000Z&scale=SECOND&energy_unit=KILOWATT_HOURS`

`device_gids` is a comma-separated list. See [Units and scales](#units-and-scales) for accepted values.

### Response

```json
{
    "instant": "2026-01-01T12:00:00.000Z",
    "scale": "SECOND",
    "energy_unit": "KILOWATT_HOURS",
    "device_usages": [
        {
            "device_gid": 1234,
            "channel_usages": [
                {
                    "device_gid": 1234,
                    "channel_id": "Mains",
                    "usage": 0.0001,
                    "percentage": 100.0,
                    "raw_usage": null,
                    "included_in_total_usage": null,
                    "nested_devices": []
                },
                {
                    "device_gid": 1234,
                    "channel_id": "Branch_3",
                    "usage": 0.00005,
                    "percentage": 50.0,
                    "raw_usage": null,
                    "included_in_total_usage": null,
                    "nested_devices": []
                }
            ]
        }
    ]
}
```

Channels are named `Mains`, `Mains_A`, `Mains_B`, `Branch_<n>` and `Balance`. A `nested_devices` entry has the same shape as a `device_usages` entry.

## Get EV chargers

GET `/devices/evses?device_ids=EVSE_SERIAL`

`device_ids` is a comma-separated list of serials. The library reads the charger list from the `success` key (falling back to `evses`).

## Get EV charger session status

GET `/customers/evse/control?device_id=EVSE_SERIAL`

### Response

```json
{
    "status": {
        "charger_status": "CHARGING",
        "subtext_type": null,
        "subtext_parameters": []
    },
    "fault_code": null,
    "next_event": null,
    "button_info": {"text": "MANAGE", "behavior": "OVERRIDE_EXCESS_SOLAR"},
    "session_active": true,
    "active_charging_minutes": 228,
    "cost": 0.02,
    "energy_delivered": 18.05,
    "charging_rate_kw": 3.24,
    "charging_rate_amps": 13,
    "offered_amps": 13,
    "charging_rate_controller": "EXCESS_SOLAR",
    "charging_rate_controller_warning": null,
    "charge_rate_controller": {
        "controller_type": "EXCESS_SOLAR",
        "status": "WORKING_CORRECTLY",
        "offline_device_name": null,
        "additional_amps": null,
        "guaranteed_amps": null
    },
    "plug_in": "2026-01-01T10:00:00.000Z"
}
```

`charger_status` values include `DISCONNECTED_OFF`, `DISCONNECTED_ON`, `CONNECTED_OFF`, `CONNECTED_ON`, `CHARGING`, `FAULTING` and `OFFLINE`.

## Send an EV charger command

POST `/customers/evse/control`

```json
{
    "device_id": "EVSE_SERIAL",
    "command": "TURN_ON"
}
```

Accepted commands are `TURN_ON`, `TURN_OFF` and `CHARGE_AT_FULL_POWER`. `CHARGE_AT_FULL_POWER` applies while the charger is being throttled by an energy management feature such as excess solar. Other values, including `PAUSE` and `RESUME`, are not commands.

## Set the EV charger charge rate

PUT `/devices/evses/settings`

```json
{
    "settings": [
        {"device_id": "EVSE_SERIAL", "charge_rate_amps": 32}
    ]
}
```

The library treats the update as successful when the serial appears in the `success` list of the response.

## Excess solar

GET `/customers/excess-generation` lists the monitors that support excess solar management, as `monitors` (each with `device_id` and `enabled`) and `unavailable_monitors` (a list of serials).

GET `/customers/energy-monitor/excess-generation?device_id=MONITOR_SERIAL` returns the configuration of one monitor.

POST `/customers/energy-monitor/excess-generation` sets it:

```json
{
    "device_id": "MONITOR_SERIAL",
    "loads": [
        {"load_gid": 3456, "enabled": true}
    ],
    "solar_window": null,
    "sunrise": null,
    "sunset": null
}
```

`loads[].load_gid` is the `load_gid` of an EV charger from the devices response. The `solar_window`, `sunrise` and `sunset` fields are passed through unchanged by the library.
