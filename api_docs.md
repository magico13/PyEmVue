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

GET `/customers/{customerGid}/devices?detailed=true&hierarchy=true`

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
            "outlet": {
                "deviceGid": 3456,
                "outletOn": false,
                "parentDeviceGid": null,
                "parentChannelNum": null,
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
    "usageCentPerKwHour": 15.0,
    "peakDemandDollarPerKw": 0.0,
    "solar": false,
    "locationInformation": {
        "airConditioning": "true",
        "heatSource": "naturalGasFurnace",
        "numElectricCars": "1",
        "locationType": "houseMultiLevel",
        "numPeople": "2"
    }
}
```

## Get total usage for a time frame

GET `/usage/total?deviceGid={deviceGid}&timeframe=ALLTODATE&unit=WATTHOURS&channels=1%2C2%2C3`

### Response

```json
{
    "timeframeStart": "1970-01-01T00:00:00Z",
    "timeframe": "ALLTODATE",
    "unit": "WATTHOURS",
    "usage": 1234.5678,
    "deviceGid": 1234,
    "channels": [
        "1,2,3"
    ]
}
```

## Get usage broken down over a time range

GET `/usage/time?start=2020-03-08T22%3A16%3A53.000Z&end=2020-03-08T22%3A17%3A55.000Z&type=INSTANT&deviceGid={deviceGid}&scale=1MIN&unit=WATTS&channels=1%2C2%2C3`

Notes: time is provided in UTC ISO8601 format.  
Valid Time Scales: `[1S, 1MIN, 15MIN, 1H]`  
Supported units: `[USD, WATTS, TREES, GALLONSGAS, MILESDRIVEN, MILESFLOWN]`

### Response

```json
{
    "start": "2020-03-08T22:16:00Z",
    "end": "2020-03-08T22:18:00Z",
    "type": "INSTANT",
    "scale": "1MIN",
    "unit": "WATTS",
    "deviceGid": 1234,
    "usage": [
        1234.456,
        345.678
    ]
}
```

## Get usage for a date range

GET `/usage/date?start=2020-07-08&end=2020-07-10&type=INSTANT&deviceGid={deviceGid}&scale=1D&unit=WATTS&channels=1%2C2%2C3`

Returns usage data for the date range provided. Using the time scales provided can return daily, weekly, monthly, or yearly results.

Note that the date ranges for this have strange behavior so I recommend requesting at least a few days range. If you request the same start and end date you'll get basically useless data that won't include all of the day's usage. The start date also appears to be an entire day before the requested start date (at least for my Z-4 timezone), ie requesting a start of 2020-07-08 returns a real start of 2020-07-07T04:00:00Z which is the start of the 7th at midnight. The same problem is true for the end date (requesting the 10th gives midnight of the 9th). I haven't tested with Z+ timezones but I fear they might have the opposite effect.

Valid Time Scales: `[1D, 1MON, 1W, 1Y]`
Supported units: `[USD, WATTS, TREES, GALLONSGAS, MILESDRIVEN, MILESFLOWN]`

### Response

```json
{
    "start": "2020-07-07T04:00:00Z",
    "end": "2020-07-09T04:00:00Z",
    "type": "INSTANT",
    "scale": "1D",
    "unit": "WATTS",
    "deviceGid": 1234,
    "usage": [
        52640.359240884514,
        54803.46804568436,
        51411.2134282075
    ]
}
```

## Get recent total device usage

GET `/usage/devices?start=2020-03-08T22%3A17%3A56.000Z&end=2020-03-08T22%3A17%3A57.000Z&scale=1S&unit=WATTS&customerGid={customerGid}`

~~Note: Start and end time don't matter at all, just set them to a random date/time one second apart. Instead this will give the usage over the last `scale` time.~~
Note: Further testing has proven that the start time does not matter but the end time does. Specify the end time to get the usage for the "bucket" that includes that time, with the bounds of that bucket returned.

Ok, this endpoint is giving me some additional uncertainty about the times. Changing the end time does appear to affect the total energy usage returned even though the start and end times remain fixed in the return. To get data lining up perfectly with the app, I (at UTC-4 at the moment) have to request data for the day after at 3AM to get data that matches. In other words, to get the data for June 10th, I pass June 11 at 03:00:00.

Another update, they appear to have disabled this for getting historical daily usage, just recent usage. See the `/date` api instead for getting daily/weekly/monthly/yearly data.

Valid Scales: `[1S, 1MIN, 15MIN, 1H, 1D, 1MON, 1W, 1Y]`

### Response

```json
{
    "start": "2020-03-08T22:51:54Z",
    "end": "2020-03-08T22:51:55Z",
    "scale": "1S",
    "unit": "WATTS",
    "customerGid": 1234,
    "channels": [
        {
            "deviceGid": 1234,
            "usage": 123.456,
            "channelNum": "1,2,3"
        }
    ]
}
```

## Get list of outlets

GET `/customers/outlets?customerGid={customerGid}`

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

## Get partner data

GET `/customers/partners?customerGid={customerGid}`

As of right now I do not know what this call will be used for. Guesses include devices made by other companies that work with the Emporia ecosystem (smart switches, power monitors?) or partners of Emporia's that they sell data to?

### Response

```json
[]
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
