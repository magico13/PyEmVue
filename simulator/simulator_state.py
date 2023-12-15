# SimulatorState of the Emporia API. Holds all the state needed to simulate the API.

import json
import os

from simulator.models import *

class SimulatorState(object):
    def __init__(self):
        self.customer = SimulatorCustomer(
            customerGid=1234,
            email='simulator@simulator.sim',
            firstName='Sim',
            lastName='Ulator',
            createdAt=datetime.datetime.utcnow())
        self.devices: list[SimulatorDevice] = []
        self.channel_types: list[ChannelType] = []
        self.outlets: list[SimulatorOutlet] = []
        self.chargers: list[SimulatorCharger] = []
        self.default_location_props = SimulatorLocationProperties(
            timeZone='America/New_York',
            latitudeLongitude=SimulatorLatitudeLongitude(
                latitude=40.0,
                longitude=-74.0),
            utilityRateGid=None,
            deviceName=None,
            deviceGid=1234,
            zipCode='10001',
            billingCycleStartDay=1,
            usageCentPerKwHour=15.0,
            peakDemandDollarPerKw=0.0,
            locationInformation=SimulatorLocationInformation(
                airConditioning='true',
                heatSource='electricFurnace',
                locationSqFt='2000',
                numElectricCars='0',
                locationType='houseMultiLevel',
                numPeople='4'))

        script_dir = os.path.dirname(__file__)
        channel_types_file = script_dir+'/channel_types.json'
        self.load_channel_types(channel_types_file)

    def load_channel_types(self, channel_types_file: str):
        with open(channel_types_file, 'r') as f:
            self.channel_types = json.load(f)

    def get_customers_devices(self) -> CustomerDevicesResponse:
        return CustomerDevicesResponse(
            customerGid=self.customer.customerGid, 
            email=self.customer.email, 
            firstName=self.customer.firstName, 
            lastName=self.customer.lastName,
            createdAt=self.customer.createdAt,
            devices=self.devices)
    
    def get_status(self) -> StatusResponse:
        return StatusResponse(
            devicesConnected=[device.deviceConnected for device in self.devices],
            evChargers=self.chargers,
            loads=[],
            batteries=[],
            outlets=self.outlets)
    
    def set_location_properties(self, location_properties: SimulatorLocationProperties, propagate: bool = True):
        self.default_location_props = location_properties.model_copy()
        if propagate:
            for device in self.devices:
                # get the device name before we overwrite it
                device_name = device.locationProperties.deviceName
                # overwrite the location properties
                device.locationProperties = location_properties.model_copy()
                # fix the device name and gid
                device.locationProperties.deviceGid = device.deviceGid
                device.locationProperties.deviceName = device_name
    
    def add_outlet(self, gid: int, name: Optional[str], on: bool = True, parentDeviceGid: Optional[int] = None, parentChannelNum: Optional[str] = None) -> SimulatorOutlet:
        # if any devices already have this gid, throw an error
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        # Create a basic outlet
        outlet = SimulatorOutlet(
            deviceGid=gid,
            outletOn=on,
            loadGid=0)
        self.outlets.append(outlet)
        # Create a full device for the outlet
        outlet_device = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId='B0000C89109103c1298',
            model='SSO001',
            firmware='Outlet-488',
            parentDeviceGid=parentDeviceGid,
            parentChannelNum=parentChannelNum,
            locationProperties=self.default_location_props.model_copy(),
            outlet=outlet,
            evCharger=None,
            battery=None,
            deviceConnected=SimulatorDeviceConnected(
                deviceGid=gid,
                connected=True,
                offlineSince=None),
            devices=[],
            channels=[
                SimulatorChannel(
                    deviceGid=gid,
                    name=None,
                    channelNum='1,2,3',
                    channelMultiplier=1.0,
                    channelTypeGid=23)])
        
        outlet_device.locationProperties.deviceGid = gid
        outlet_device.locationProperties.deviceName = name
        self.devices.append(outlet_device)
        return outlet
        
    def add_charger(self, gid: int, name: Optional[str], on: bool = True, breakerSize: int = 50, parentDeviceGid: Optional[int] = None, parentChannelNum: Optional[str] = None) -> SimulatorCharger:
        # if any devices already have this gid, throw an error
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        # Create a basic charger
        charger = SimulatorCharger(
            deviceGid=gid,
            loadGid=0,
            chargerOn=on,
            chargingRate=4*breakerSize//5,
            maxChargingRate=4*breakerSize//5)
        self.chargers.append(charger)
        # Create a full device for the charger
        charger_device = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId='D2112A04B4AC6C4523421',
            model='VVDN01',
            firmware='EVCharger-467',
            parentDeviceGid=parentDeviceGid,
            parentChannelNum=parentChannelNum,
            locationProperties=self.default_location_props.model_copy(),
            outlet=None,
            evCharger=charger,
            battery=None,
            deviceConnected=SimulatorDeviceConnected(
                deviceGid=gid,
                connected=True,
                offlineSince=None),
            devices=[],
            channels=[
                SimulatorChannel(
                    deviceGid=gid,
                    name=None,
                    channelNum='1,2,3',
                    channelMultiplier=1.0,
                    channelTypeGid=25)])
        
        charger_device.locationProperties.deviceGid = gid
        charger_device.locationProperties.deviceName = name
        self.devices.append(charger_device)
        return charger
    
    def add_vue(self, gid: int, name: Optional[str], channelCount: int = 8, parentDeviceGid: Optional[int] = None, parentChannelNum: Optional[str] = None) -> SimulatorDevice:
        # if any devices already have this gid, throw an error
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        # Create a basic vue
        vue = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId='A2112A04B4AC67B2B548201',
            model='VUE02',
            firmware='Vue2-434',
            parentDeviceGid=parentDeviceGid,
            parentChannelNum=parentChannelNum,
            locationProperties=self.default_location_props.model_copy(),
            outlet=None,
            evCharger=None,
            battery=None,
            deviceConnected=SimulatorDeviceConnected(
                deviceGid=gid,
                connected=True,
                offlineSince=None),
            devices=[],
            channels=[])
        # Create the main channel
        vue.channels.append(
            SimulatorChannel(
                deviceGid=gid,
                name=None,
                channelNum='1,2,3',
                channelMultiplier=1.0,
                channelTypeGid=None))
        # Create the other channels as children of the "WAT001" device
        if channelCount > 0:
            subDevice = SimulatorSubDevice(
                deviceGid=gid,
                manufacturerDeviceId='SXA2112A04B4AC67B2F12345',
                model='WAT001',
                firmware=None,
                channels=[])
            vue.devices.append(subDevice)
            for i in range(1, channelCount+1):
                subDevice.channels.append(
                    SimulatorChannel(
                        deviceGid=gid,
                        name="Channel "+str(i),
                        channelNum=str(i),
                        channelMultiplier=1.0,
                        channelTypeGid=18))
        # Add the device to the list
        vue.locationProperties.deviceGid = gid
        vue.locationProperties.deviceName = name
        self.devices.append(vue)
        return vue

    def delete_device(self, gid: int) -> Optional[SimulatorDevice]:
        for device in self.devices:
            if device.deviceGid == gid:
                self.devices.remove(device)
                return device
        return None
        