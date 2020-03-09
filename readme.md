# PyEmVue

A Python Library for reading data from the Emporia Vue energy monitoring system.

Currently a WIP in the API documenting phase. Authtoken and customer/device data must be added to a file called keys.json (or likely can be provided during initialization). At a later point the api calls should be made by the app and you will only need to enter credentials.

```json
{
    "customerGid": 1234,
    "authtoken": "your_authtoken"
}
```
