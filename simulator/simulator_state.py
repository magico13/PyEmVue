# SimulatorState of the Emporia API. Holds all the state needed to simulate the API.

import json
import os

from simulator.models import *


class SimulatorState(object):
    def __init__(self):
        self.customer = SimulatorCustomer(
            customerGid=1234,
            email="simulator@simulator.sim",
            firstName="Sim",
            lastName="Ulator",
            createdAt=datetime.datetime.utcnow(),
        )
        # Hold the usage for each channel. deviceGid_channelNum : usage
        self.usage_dict_1min: dict[str, Optional[float]] = {}
        self.devices: list[SimulatorDevice] = []
        self.channel_types: list[ChannelType] = []
        self.outlets: list[SimulatorOutlet] = []
        self.chargers: list[SimulatorCharger] = []
        self.default_location_props = SimulatorLocationProperties(
            timeZone="America/New_York",
            latitudeLongitude=SimulatorLatitudeLongitude(
                latitude=40.0, longitude=-74.0
            ),
            utilityRateGid=None,
            deviceName=None,
            displayName=None,
            deviceGid=1234,
            zipCode="10001",
            billingCycleStartDay=1,
            usageCentPerKwHour=15.0,
            peakDemandDollarPerKw=0.0,
            locationInformation=SimulatorLocationInformation(
                airConditioning="true",
                heatSource="electricFurnace",
                locationSqFt="2000",
                numElectricCars="0",
                locationType="houseMultiLevel",
                numPeople="4",
            ),
        )

        script_dir = os.path.dirname(__file__)
        channel_types_file = script_dir + "/channel_types.json"
        self.load_channel_types(channel_types_file)

    def load_channel_types(self, channel_types_file: str):
        with open(channel_types_file, "r") as f:
            self.channel_types = json.load(f)

    def get_customers_devices(self) -> CustomerDevicesResponse:
        return CustomerDevicesResponse(
            customerGid=self.customer.customerGid,
            email=self.customer.email,
            firstName=self.customer.firstName,
            lastName=self.customer.lastName,
            createdAt=self.customer.createdAt,
            devices=self.devices,
        )

    def get_status(self) -> StatusResponse:
        return StatusResponse(
            devicesConnected=[device.deviceConnected for device in self.devices],
            evChargers=self.chargers,
            loads=[],
            batteries=[],
            outlets=self.outlets,
        )

    # state.get_devices_usage(deviceGids, instant, scale, energyUnit)
    def get_devices_usage(
        self,
        deviceGids: Optional[str],
        instant: datetime.datetime,
        scale: str,
        energyUnit: str,
    ) -> DeviceUsageResponse:
        if scale != "1MIN" or energyUnit != "KilowattHours":
            raise Exception(
                f"Scale {scale} or energyUnit {energyUnit} not yet supported"
            )
        deviceListUsage = DeviceListUsage(
            energyUnit=energyUnit, scale=scale, instant=instant, devices=[]
        )
        response = DeviceUsageResponse(deviceListUsages=deviceListUsage)
        # build the usage tree by recursively calling build_tree
        root = self.build_tree(None, None)
        deviceListUsage.devices = root
        return response

    def build_tree(
        self, parentDeviceGid: Optional[int], parentChannelNum: Optional[str]
    ) -> list[DeviceUsage]:
        devices_at_level: list[DeviceUsage] = []
        # We end up looping through all of the devices each time, but that's ok for now
        # we can optimize later if it becomes a performance concern
        for device in self.devices:
            if (
                device.parentDeviceGid == parentDeviceGid
                and device.parentChannelNum == parentChannelNum
            ):
                # handle the main device, then any sub-devices
                device_usage = DeviceUsage(deviceGid=device.deviceGid, channelUsages=[])
                channel_usages: list[ChannelUsage] = []
                for channel in device.channels:
                    # get the usage for this channel
                    usage = self.usage_dict_1min.get(
                        f"{device.deviceGid}_{channel.channelNum}", 0.0
                    )
                    channel_usages.append(
                        ChannelUsage(
                            name=channel.name or "Main",
                            percentage=0.0,
                            usage=usage,
                            deviceGid=device.deviceGid,
                            channelNum=channel.channelNum,
                            nestedDevices=self.build_tree(
                                device.deviceGid, channel.channelNum
                            ),
                        )
                    )
                for sub_device in device.devices:
                    for channel in sub_device.channels:
                        # get the usage for this channel
                        usage = self.usage_dict_1min.get(
                            f"{sub_device.deviceGid}_{channel.channelNum}", 0.0
                        )
                        channel_usages.append(
                            ChannelUsage(
                                name=channel.name or "Main",
                                percentage=0.0,
                                usage=usage,
                                deviceGid=sub_device.deviceGid,
                                channelNum=channel.channelNum,
                                nestedDevices=self.build_tree(
                                    sub_device.deviceGid, channel.channelNum
                                ),
                            )
                        )
                # There is a special Balance channel that appears when there are multiple channels on a device
                if len(channel_usages) > 1:
                    balance_usage = self.usage_dict_1min.get(
                        f"{device.deviceGid}_Balance", 0.0
                    )
                    channel_usages.append(
                        ChannelUsage(
                            name="Balance",
                            percentage=0.0,
                            usage=balance_usage,
                            deviceGid=device.deviceGid,
                            channelNum="Balance",
                            nestedDevices=[],
                        )
                    )
                device_usage.channelUsages = channel_usages
                devices_at_level.append(device_usage)
        return devices_at_level

    def set_location_properties(
        self, location_properties: SimulatorLocationProperties, propagate: bool = True
    ):
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

    def add_outlet(
        self,
        gid: int,
        name: Optional[str],
        on: bool = True,
        parentDeviceGid: Optional[int] = None,
        parentChannelNum: Optional[str] = None,
    ) -> SimulatorOutlet:
        # if any devices already have this gid, throw an error
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        # Create a basic outlet
        outlet = SimulatorOutlet(deviceGid=gid, outletOn=on, loadGid=0)
        self.outlets.append(outlet)
        # Create a full device for the outlet
        outlet_device = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId="B0000C89109103c1298",
            model="SSO001",
            firmware="Outlet-488",
            parentDeviceGid=parentDeviceGid,
            parentChannelNum=parentChannelNum,
            locationProperties=self.default_location_props.model_copy(),
            outlet=outlet,
            evCharger=None,
            battery=None,
            deviceConnected=SimulatorDeviceConnected(
                deviceGid=gid, connected=True, offlineSince=None
            ),
            devices=[],
            channels=[
                SimulatorChannel(
                    deviceGid=gid,
                    name=None,
                    channelNum="1,2,3",
                    channelMultiplier=1.0,
                    channelTypeGid=23,
                    type="FiftyAmp"
                )
            ],
        )

        outlet_device.locationProperties.deviceGid = gid
        outlet_device.locationProperties.deviceName = name
        outlet_device.locationProperties.displayName = name
        self.devices.append(outlet_device)
        return outlet

    def add_charger(
        self,
        gid: int,
        name: Optional[str],
        on: bool = True,
        breakerSize: int = 50,
        parentDeviceGid: Optional[int] = None,
        parentChannelNum: Optional[str] = None,
    ) -> SimulatorCharger:
        # if any devices already have this gid, throw an error
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        # Create a basic charger
        charger = SimulatorCharger(
            deviceGid=gid,
            loadGid=0,
            chargerOn=on,
            chargingRate=4 * breakerSize // 5,
            maxChargingRate=4 * breakerSize // 5,
        )
        self.chargers.append(charger)
        # Create a full device for the charger
        charger_device = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId="D2112A04B4AC6C4523421",
            model="VVDN01",
            firmware="EVCharger-467",
            parentDeviceGid=parentDeviceGid,
            parentChannelNum=parentChannelNum,
            locationProperties=self.default_location_props.model_copy(),
            outlet=None,
            evCharger=charger,
            battery=None,
            deviceConnected=SimulatorDeviceConnected(
                deviceGid=gid, connected=True, offlineSince=None
            ),
            devices=[],
            channels=[
                SimulatorChannel(
                    deviceGid=gid,
                    name=None,
                    channelNum="1,2,3",
                    channelMultiplier=1.0,
                    channelTypeGid=25,
                    type="FiftyAmp"
                )
            ],
        )

        charger_device.locationProperties.deviceGid = gid
        charger_device.locationProperties.deviceName = name
        charger_device.locationProperties.displayName = name
        self.devices.append(charger_device)
        return charger

    def add_vue(
        self,
        gid: int,
        name: Optional[str],
        channelCount: int = 8,
        parentDeviceGid: Optional[int] = None,
        parentChannelNum: Optional[str] = None,
    ) -> SimulatorDevice:
        # if any devices already have this gid, throw an error
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        # Create a basic vue
        vue = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId="A2112A04B4AC67B2B548201",
            model="VUE02",
            firmware="Vue2-434",
            parentDeviceGid=parentDeviceGid,
            parentChannelNum=parentChannelNum,
            locationProperties=self.default_location_props.model_copy(),
            outlet=None,
            evCharger=None,
            battery=None,
            deviceConnected=SimulatorDeviceConnected(
                deviceGid=gid, connected=True, offlineSince=None
            ),
            devices=[],
            channels=[],
        )
        # Create the main channel
        vue.channels.append(
            SimulatorChannel(
                deviceGid=gid,
                name=None,
                channelNum="1,2,3",
                channelMultiplier=1.0,
                channelTypeGid=None,
                type="Main",
            )
        )
        # Create the other channels as children of the "WAT001" device
        if channelCount > 0:
            subDevice = SimulatorSubDevice(
                deviceGid=gid,
                manufacturerDeviceId="SXA2112A04B4AC67B2F12345",
                model="WAT001",
                firmware=None,
                channels=[],
            )
            vue.devices.append(subDevice)
            for i in range(1, channelCount + 1):
                subDevice.channels.append(
                    SimulatorChannel(
                        deviceGid=gid,
                        name="Channel " + str(i),
                        channelNum=str(i),
                        channelMultiplier=1.0,
                        channelTypeGid=18,
                        type="FiftyAmp"
                    )
                )
        # Add the device to the list
        vue.locationProperties.deviceGid = gid
        vue.locationProperties.deviceName = name
        vue.locationProperties.displayName = name
        self.devices.append(vue)
        return vue

    def delete_device(self, gid: int) -> Optional[SimulatorDevice]:
        for device in self.devices:
            if device.deviceGid == gid:
                self.devices.remove(device)
                return device
        return None

    def set_channel_1min_watts(
        self, deviceGid: int, channelNum: str, watts: Optional[float]
    ):
        # convert from watts to kilowatt hours used over a 1 minute period
        if watts is None:
            usage = None
        else:
            scaler = 60 * 1000  # 60 minutes/hr * 1000 watts/kilowatt
            usage = watts / scaler
        self.set_channel_1min_usage(deviceGid, channelNum, usage)

    def set_channel_1min_usage(
        self, deviceGid: int, channelNum: str, usage: Optional[float]
    ):
        self.usage_dict_1min[f"{deviceGid}_{channelNum}"] = usage

    def get_channel_1min_usage(self, deviceGid: int, channelNum: str) -> Optional[float]:
        return self.usage_dict_1min.get(f"{deviceGid}_{channelNum}", 0.0)

    def set_channel_bidirectionality(
            self, deviceGid: int, channelNum: str, bidirectional: bool
    ):
        # this should technically check if a channel type is allowed to be bidirectional
        # but that won't really affect the simulation, even if it results in invalid real states
        new_type = "FiftyAmpBidirectional" if bidirectional else "FiftyAmp"
        for device in self.devices:
            if device.deviceGid == deviceGid:
                for channel in device.channels:
                    if channel.channelNum == channelNum:
                        channel.type = new_type
                        return
                for sub_device in device.devices:
                    for channel in sub_device.channels:
                        if channel.channelNum == channelNum:
                            channel.type = new_type
                            return
        raise Exception(f"Device {deviceGid} or channel {channelNum} not found")