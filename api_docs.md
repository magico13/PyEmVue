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

PUT `/devices/outlet`

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
