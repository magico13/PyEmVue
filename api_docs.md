# API Documentation

## Authorization through AWS idp

Emporia uses the AWS cognito idp for authentication, getting an auth token and refresh token from there. The auth token is provided to calls to the Emporia api via the `authtoken` header and expires after some time, at which point the refresh token is passed to the cognito idp to get a new set of auth and refresh tokens.

## Detection of maintenance

The check for if the servers are down for maintenance is rather simple in that it just checks the contents of a json file on Amazon S3. During normal operation this check returns an access denied error but during maintenance periods the content of the file is downloaded and checked. An example of this file during maintenance is below.

`https://s3.amazonaws.com/com.emporiaenergy.manual.ota/maintenance/maintenance.json`

```json
{"msg":"down"}
```

# Emporia Specific API

Root url for the api server is https://api.emporiaenergy.com

Authorization is provided through "authtoken" key in the header, not by a standard bearer token, using the auth token provided in keys.json (currently gotten by sniffing).

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
            "firmware": "1578351378",
            "devices": [],
            "channels": [
                {
                    "deviceGid": 2345,
                    "name": null,
                    "channelNum": "1,2,3",
                    "channelMultiplier": 1.0
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

GET `/total?deviceGid={deviceGid}&timeframe=ALLTODATE&unit=WATTHOURS&channels=1%2C2%2C3`

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

## Get total device usage over a time range

GET `/usage/devices?start=2020-03-08T22%3A17%3A56.000Z&end=2020-03-08T22%3A17%3A57.000Z&scale=1S&unit=WATTS&customerGid={customerGid}`

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
