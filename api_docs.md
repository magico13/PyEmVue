# API Documentation

Root url for the api server is https://api.emporiaenergy.com

Authorization is provided by through "authtoken" key in the header using the auth token provided in keys.json (got by sniffing).

Get total usage for all time:
GET /total?deviceGid={deviceGid}&timeframe=ALLTODATE&unit=WATTHOURS&channels=1%2C2%2C3

RESPONSE

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

Get usage broken down over a time range:
GET /usage/time?start=2020-03-08T22%3A16%3A53.000Z&end=2020-03-08T22%3A17%3A55.000Z&type=INSTANT&deviceGid={deviceGid}&scale=1MIN&unit=WATTS&channels=1%2C2%2C3
Notes: time is provided in UTC ISO8601 format.
Valid Time Scales: [1S, 1MIN, 15MIN, 1H]
Supported units: [USD, WATTS, TREES, GALLONSGAS, MILESDRIVEN, MILESFLOWN]

RESPONSE

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

Get total usage over a time range:
GET /usage/devices?start=2020-03-08T22%3A17%3A56.000Z&end=2020-03-08T22%3A17%3A57.000Z&scale=1S&unit=WATTS&customerGid={customerGid}

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
