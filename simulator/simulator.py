import json
import os
from typing import Union
import datetime

from fastapi import FastAPI

from simulator.models import *

app = FastAPI()

# All APIs that are supported are:
# API_CHANNELS = 'devices/{deviceGid}/channels'
# API_CHANNEL_TYPES = 'devices/channels/channeltypes'
# API_CHARGER = 'devices/evcharger'
# API_CHART_USAGE = 'AppAPI?apiMethod=getChartUsage&deviceGid={deviceGid}&channel={channel}&start={start}&end={end}&scale={scale}&energyUnit={unit}'
# API_CUSTOMER = 'customers'
# API_CUSTOMER_DEVICES = 'customers/devices'
# API_DEVICES_USAGE = 'AppAPI?apiMethod=getDeviceListUsages&deviceGids={deviceGids}&instant={instant}&scale={scale}&energyUnit={unit}'
# API_DEVICE_PROPERTIES = 'devices/{deviceGid}/locationProperties'
# API_GET_STATUS = 'customers/devices/status'
# API_OUTLET = 'devices/outlet'
# API_VEHICLES = 'customers/vehicles'
# API_VEHICLE_STATUS = 'vehicles/v2/settings?vehicleGid={vehicleGid}'


@app.get("/customers")
def get_customers() -> SimulatorCustomer:
    return SimulatorCustomer(
        customerGid=1234,
        email='simulator@simulator.sim', 
        firstName='Sim', lastName='Ulator', 
        createdAt=datetime.datetime.utcnow())

@app.get("/customers/devices")
def get_customers_devices() -> SimulatorCustomerDevices:
    return SimulatorCustomerDevices(
        customerGid=1234, 
        email='simulator@simulator.sim', 
        firstName='Sim', 
        lastName='Ulator',
        createdAt=datetime.datetime.utcnow(),
        devices=[])

@app.get("/devices/channels/channeltypes")
def get_devices_channels_channelTypes() -> list[ChannelType]:
    # load the file channel_types.json into a list of ChannelType objects
    script_dir = os.path.dirname(__file__)
    channel_types_file = script_dir+'/channel_types.json'
    channel_types = []
    with open(channel_types_file, 'r') as f:
        channel_types = json.load(f)
    return channel_types

