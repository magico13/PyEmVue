import datetime
from typing import Any, Optional
from typing_extensions import Self
from dateutil.parser import parse


class VueDevice(object):
    def __init__(self, gid=0, manId="", modelNum="", firmwareVersion=""):
        self.device_gid: int = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.parent_device_gid: int = 0
        self.parent_channel_num: str = ""
        self.channels: list[VueDeviceChannel] = []
        self.outlet: Optional[OutletDevice] = None
        self.ev_charger: Optional[ChargerDevice] = None

        self.connected: bool = False
        self.offline_since = datetime.datetime.min

        # extra info
        self.device_name = ""
        self.display_name = ""
        self.zip_code = "00000"
        self.time_zone = ""
        self.usage_cent_per_kw_hour = 0.0
        self.peak_demand_dollar_per_kw = 0.0
        self.billing_cycle_start_day = 0
        self.solar = False
        self.air_conditioning = "false"
        self.heat_source = ""
        self.location_sqft = "0"
        self.num_electric_cars = "0"
        self.location_type = ""
        self.num_people = ""
        self.swimming_pool = "false"
        self.hot_tub = "false"
        self.latitude = 0
        self.longitude = 0
        self.utility_rate_gid = None

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        """Populate device data from a dictionary extracted from the response json."""
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        if "manufacturerDeviceId" in js:
            self.manufacturer_id = js["manufacturerDeviceId"]
        if "model" in js:
            self.model = js["model"]
        if "firmware" in js:
            self.firmware = js["firmware"]
        if "parentDeviceGid" in js:
            self.parent_device_gid = js["parentDeviceGid"]
        if "parentChannelNum" in js:
            self.parent_channel_num = js["parentChannelNum"]
        if "locationProperties" in js:
            self.populate_location_properties_from_json(js["locationProperties"])
        # 'devices' is empty in my system, will add support later if possible
        if "channels" in js:
            # Channels are another subtype and the channelNum is used in other calls
            self.channels = []
            for chnl in js["channels"]:
                self.channels.append(VueDeviceChannel().from_json_dictionary(chnl))
        # outlets are a special type
        if "outlet" in js and js["outlet"]:
            self.outlet = OutletDevice().from_json_dictionary(js["outlet"])
        # EVSEs are also special
        if "evCharger" in js and js["evCharger"]:
            self.ev_charger = ChargerDevice().from_json_dictionary(js["evCharger"])

        # Online data
        if "deviceConnected" in js and js["deviceConnected"]:
            con = js["deviceConnected"]
            if "connected" in con:
                self.connected = con["connected"]
            try:
                if "offlineSince" in con and con["offlineSince"]:
                    self.offline_since = parse(con["offlineSince"])
            except:
                self.offline_since = datetime.datetime.min
        return self

    def populate_location_properties_from_json(self, js: "dict[str, Any]"):
        """Adds the values from the get_device_properties method."""
        if "deviceName" in js:
            self.device_name = js["deviceName"]
        if "displayName" in js:
            self.display_name = js["displayName"]
        if "zipCode" in js:
            self.zip_code = js["zipCode"]
        if "timeZone" in js:
            self.time_zone = js["timeZone"]
        if "usageCentPerKwHour" in js:
            self.usage_cent_per_kw_hour = js["usageCentPerKwHour"]
        if "peakDemandDollarPerKw" in js:
            self.peak_demand_dollar_per_kw = js["peakDemandDollarPerKw"]
        if "billingCycleStartDay" in js:
            self.billing_cycle_start_day = js["billingCycleStartDay"]
        if "solar" in js:
            self.solar = js["solar"]
        if "utilityRateGid" in js:
            self.utility_rate_gid = js["utilityRateGid"]
        if "locationInformation" in js and js["locationInformation"]:
            li = js["locationInformation"]
            if "airConditioning" in li:
                self.air_conditioning = li["airConditioning"]
            if "heatSource" in li:
                self.heat_source = li["heatSource"]
            if "locationSqFt" in li:
                self.location_sqft = li["locationSqFt"]
            if "numElectricCars" in li:
                self.num_electric_cars = li["numElectricCars"]
            if "locationType" in li:
                self.location_type = li["locationType"]
            if "numPeople" in li:
                self.num_people = li["numPeople"]
            if "swimmingPool" in li:
                self.swimming_pool = li["swimmingPool"]
            if "hotTub" in li:
                self.hot_tub = li["hotTub"]
        if "latitudeLongitude" in js and js["latitudeLongitude"]:
            if "latitude" in js["latitudeLongitude"]:
                self.latitude = js["latitudeLongitude"]["latitude"]
            if "longitude" in js["latitudeLongitude"]:
                self.longitude = js["latitudeLongitude"]["longitude"]


class VueDeviceChannel(object):
    def __init__(
        self,
        gid=0,
        name="",
        channelNum="1,2,3",
        channelMultiplier=1.0,
        channelTypeGid=0,
    ):
        self.device_gid: int = gid
        self.name = name
        self.channel_num = channelNum
        self.channel_multiplier = channelMultiplier
        self.channel_type_gid = channelTypeGid
        self.nested_devices = {}
        self.type = ""

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        """Populate device channel data from a dictionary extracted from the response json."""
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        if "name" in js:
            self.name = js["name"]
        if "channelNum" in js:
            self.channel_num = js["channelNum"]
        if "channelMultiplier" in js:
            self.channel_multiplier = js["channelMultiplier"]
        if "channelTypeGid" in js:
            self.channel_type_gid = js["channelTypeGid"]
        if "type" in js:
            self.type = js["type"]
        return self
    
    # Known types: Main, FiftyAmp, FiftyAmpBidirectional

    def as_dictionary(self) -> "dict[str, Any]":
        """Returns a dictionary of the device channel data."""
        return {
            "deviceGid": self.device_gid,
            "name": self.name,
            "channelNum": self.channel_num,
            "channelMultiplier": self.channel_multiplier,
            "channelTypeGid": self.channel_type_gid,
        }


class VueUsageDevice(VueDevice):
    def __init__(self, gid=0, timestamp: Optional[datetime.datetime] = None):
        super().__init__(gid=gid)
        self.timestamp = timestamp
        self.channels: dict[str, VueDeviceChannelUsage] = {}

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if not js:
            return self
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        if "channelUsages" in js and js["channelUsages"]:
            for channel in js["channelUsages"]:
                if channel:
                    populated_channel = VueDeviceChannelUsage(
                        timestamp=self.timestamp
                    ).from_json_dictionary(channel)
                    self.channels[populated_channel.channel_num] = populated_channel
        return self


class VueDeviceChannelUsage(VueDeviceChannel):
    def __init__(
        self,
        gid: int = 0,
        usage: float = 0,
        channelNum="1,2,3",
        name="",
        timestamp: Optional[datetime.datetime] = None,
    ):
        super().__init__(gid=gid, name=name, channelNum=channelNum)
        self.name = name
        self.device_gid: int = gid
        self.usage: float = usage
        self.channel_num = channelNum
        self.percentage = 0.0
        self.timestamp = timestamp
        self.nested_devices = {}

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        """Populate device channel usage data from a dictionary extracted from the response json."""
        if not js:
            return self
        if "channelUsages" in js:
            js = js[
                "channelUsages"
            ]  # were given "device" level and we want to work off "channel" level
        if "name" in js:
            self.name = js["name"]
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        if "channelNum" in js:
            self.channel_num = js["channelNum"]
        if "usage" in js:
            self.usage = js["usage"]
        if "percentage" in js:
            self.percentage = js["percentage"]
        # Nested device handling
        if "nestedDevices" in js and js["nestedDevices"]:
            for device in js["nestedDevices"]:
                if device:
                    populated = VueUsageDevice(
                        timestamp=self.timestamp
                    ).from_json_dictionary(device)
                    self.nested_devices[populated.device_gid] = populated
        return self


class OutletDevice(object):
    def __init__(self, gid: int = 0, on: bool = False):
        self.device_gid = gid
        self.outlet_on = on
        self.load_gid: int = 0
        self.schedules = []

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        if "outletOn" in js:
            self.outlet_on = js["outletOn"]
        if "loadGid" in js:
            self.load_gid = js["loadGid"]
        # don't have support for schedules yet
        return self

    def as_dictionary(self) -> "dict[str, Any]":
        return {
            "deviceGid": self.device_gid,
            "outletOn": self.outlet_on,
            "loadGid": self.load_gid,
        }


class ChargerDevice(object):
    def __init__(self, gid: int = 0, on: bool = False):
        self.device_gid = gid
        self.charger_on = on
        self.message = ""
        self.status = ""
        self.icon = ""
        self.icon_label = ""
        self.icon_detail_text = ""
        self.fault_text = ""
        self.charging_rate = 0
        self.max_charging_rate = 0
        self.off_peak_schedules_enabled = False
        self.custom_schedules = []
        self.load_gid: int = 0
        self.debug_code = ""
        self.pro_control_code = ""
        self.breaker_pin = ""

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        if "loadGid" in js:
            self.load_gid = js["loadGid"]
        if "chargerOn" in js:
            self.charger_on = js["chargerOn"]
        if "message" in js:
            self.message = js["message"]
        if "status" in js:
            self.status = js["status"]
        if "icon" in js:
            self.icon = js["icon"]
        if "iconLabel" in js:
            self.icon_label = js["iconLabel"]
        if "iconDetailText" in js:
            self.icon_detail_text = js["iconDetailText"]
        if "faultText" in js:
            self.fault_text = js["faultText"]
        if "chargingRate" in js:
            self.charging_rate = js["chargingRate"]
        if "maxChargingRate" in js:
            self.max_charging_rate = js["maxChargingRate"]
        if "offPeakSchedulesEnabled" in js:
            self.off_peak_schedules_enabled = js["offPeakSchedulesEnabled"]
        if "debugCode" in js:
            self.debug_code = js["debugCode"]
        if "proControlCode" in js:
            self.pro_control_code = js["proControlCode"]
        if "breakerPIN" in js:
            self.breaker_pin = js["breakerPIN"]
        # don't have support for schedules yet
        return self

    def as_dictionary(self) -> "dict[str, Any]":
        d = {
            "deviceGid": self.device_gid,
            "loadGid": self.load_gid,
            "chargerOn": self.charger_on,
            "chargingRate": self.charging_rate,
            "maxChargingRate": self.max_charging_rate,
        }
        if self.breaker_pin:
            d["breakerPIN"] = self.breaker_pin
        return d


class ChannelType(object):
    def __init__(
        self, gid: int = 0, description: str = "", selectable: bool = False
    ) -> None:
        self.channel_type_gid = gid
        self.description = description
        self.selectable = selectable

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if "channelTypeGid" in js:
            self.channel_type_gid = js["channelTypeGid"]
        if "description" in js:
            self.description = js["description"]
        if "selectable" in js:
            self.selectable = js["selectable"]
        return self


class Vehicle(object):
    def __init__(
        self,
        vehicleGid=0,
        vendor="",
        apiId="",
        displayName="",
        loadGid="",
        make="",
        model="",
        year=0,
    ):
        self.vehicle_gid = vehicleGid
        self.vendor = vendor
        self.api_id = apiId
        self.display_name = displayName
        self.load_gid = loadGid
        self.make = make
        self.model = model
        self.year = year

    def from_json_dictionary(self, js):
        if "vehicleGid" in js:
            self.vehicle_gid = js["vehicleGid"]
        if "vendor" in js:
            self.vendor = js["vendor"]
        if "apiId" in js:
            self.api_id = js["apiId"]
        if "displayName" in js:
            self.display_name = js["displayName"]
        if "loadGid" in js:
            self.load_gid = js["loadGid"]
        if "make" in js:
            self.make = js["make"]
        if "model" in js:
            self.model = js["model"]
        if "year" in js:
            self.year = js["year"]
        return self

    def as_dictionary(self) -> "dict[str, Any]":
        return {
            "vehicleGid": self.vehicle_gid,
            "vendor": self.vendor,
            "apiId": self.api_id,
            "displayName": self.display_name,
            "loadGid": self.load_gid,
            "make": self.make,
            "model": self.model,
            "year": self.year,
        }


class VehicleStatus(object):
    def __init__(
        self,
        vehicleGid=0,
        vehicleState="",
        batteryLevel=0,
        batteryRange=0,
        chargingState="",
        chargeLimitPercent=0,
        minutesToFullCharge=0,
        chargeCurrentRequest=0,
        chargeCurrentRequestMax=0,
    ):
        self.vehicle_gid = vehicleGid
        self.vehicle_state = vehicleState
        self.battery_level = batteryLevel
        self.battery_range = batteryRange
        self.charging_state = chargingState
        self.charge_limit_percent = chargeLimitPercent
        self.minutes_to_full_charge = minutesToFullCharge
        self.charge_current_request = chargeCurrentRequest
        self.charge_current_request_max = chargeCurrentRequestMax

    def from_json_dictionary(self, js):
        jsv = {}
        if "settings" in js:
            jsv = js["settings"]

        if "vehicleGid" in jsv:
            self.vehicle_gid = jsv["vehicleGid"]
        if "vehicleState" in jsv:
            self.vehicle_state = jsv["vehicleState"]
        if "batteryLevel" in jsv:
            self.battery_level = jsv["batteryLevel"]
        if "batteryRange" in jsv:
            self.battery_range = jsv["batteryRange"]
        if "chargingState" in jsv:
            self.charging_state = jsv["chargingState"]
        if "chargeLimitPercent" in jsv:
            self.charge_limit_percent = jsv["chargeLimitPercent"]
        if "minutesToFullCharge" in jsv:
            self.minutes_to_full_charge = jsv["minutesToFullCharge"]
        if "chargeCurrentRequest" in jsv:
            self.charge_current_request = jsv["chargeCurrentRequest"]
        if "chargeCurrentRequestMax" in jsv:
            self.charge_current_request_max = jsv["chargeCurrentRequestMax"]

        return self

    def as_dictionary(self) -> "dict[str, Any]":
        return {
            "vehicleGid": self.vehicle_gid,
            "vehicleState": self.vehicle_state,
            "batteryLevel": self.battery_level,
            "batteryRange": self.battery_range,
            "chargingState": self.charging_state,
            "chargeLimitPercent": self.charge_limit_percent,
            "minutesToFullCharge": self.minutes_to_full_charge,
            "chargeCurrentRequest": self.charge_current_request,
            "chargeCurrentRequestMax": self.charge_current_request_max,
        }
