from __future__ import annotations

import datetime
from typing import Any, Optional, Union
from typing_extensions import Self
from dateutil.parser import parse
from dateutil import tz


class VueDevice(object):
    def __init__(self, gid=0, manId="", modelNum="", firmwareVersion=""):
        self.device_id: str = ""
        self.device_gid: int = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.parent_device_gid: int = 0
        self.parent_channel_num: str = ""
        self.parent_device_id: Optional[str] = None
        self.parent_channel_id: Optional[str] = None
        self.site_gid: Optional[int] = None
        self.device_type: str = ""
        self.load_gid: Optional[int] = None
        self.combined_vue: bool = False
        self.primary_vue_device_id: Optional[str] = None
        self.buyback_rate_cents_per_kwh: Optional[float] = None
        self.net_metering: Optional[str] = None
        self.supported_energy_managements: list[str] = []
        self.energy_managements_configured: list[str] = []
        self.children: list[VueDevice] = []
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
        if "device_id" in js:
            self.device_id = js["device_id"]
        elif "deviceId" in js:
            self.device_id = js["deviceId"]

        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        elif "device_gid" in js:
            self.device_gid = js["device_gid"]

        if "manufacturerDeviceId" in js:
            self.manufacturer_id = js["manufacturerDeviceId"]
        elif "manufacturer_id" in js:
            self.manufacturer_id = js["manufacturer_id"]
        elif self.device_id and not self.manufacturer_id:
            self.manufacturer_id = self.device_id

        if "model" in js:
            self.model = js["model"]
        if "firmware" in js:
            self.firmware = js["firmware"]

        if "parentDeviceGid" in js:
            self.parent_device_gid = js["parentDeviceGid"]
        elif "parent_device_gid" in js:
            self.parent_device_gid = js["parent_device_gid"]

        if "parentChannelNum" in js:
            self.parent_channel_num = js["parentChannelNum"]
        elif "parent_channel_num" in js:
            self.parent_channel_num = js["parent_channel_num"]

        if "parent_device_id" in js:
            self.parent_device_id = js["parent_device_id"]
        elif "parentDeviceId" in js:
            self.parent_device_id = js["parentDeviceId"]

        if "parent_channel_id" in js:
            self.parent_channel_id = js["parent_channel_id"]
        elif "parentChannelId" in js:
            self.parent_channel_id = js["parentChannelId"]

        if "site_gid" in js:
            self.site_gid = js["site_gid"]
        elif "siteGid" in js:
            self.site_gid = js["siteGid"]

        if "device_type" in js:
            self.device_type = js["device_type"]
        elif "deviceType" in js:
            self.device_type = js["deviceType"]

        if "load_gid" in js:
            self.load_gid = js["load_gid"]
        elif "loadGid" in js:
            self.load_gid = js["loadGid"]

        if "combined_vue" in js:
            self.combined_vue = bool(js["combined_vue"])
        elif "combinedVue" in js:
            self.combined_vue = bool(js["combinedVue"])

        if "primary_vue_device_id" in js:
            self.primary_vue_device_id = js["primary_vue_device_id"]
        elif "primaryVueDeviceId" in js:
            self.primary_vue_device_id = js["primaryVueDeviceId"]

        if "supported_energy_managements" in js and js["supported_energy_managements"]:
            self.supported_energy_managements = list(js["supported_energy_managements"])
        if (
            "energy_managements_configured" in js
            and js["energy_managements_configured"]
        ):
            self.energy_managements_configured = list(
                js["energy_managements_configured"]
            )

        if "displayName" in js:
            self.display_name = js["displayName"]
        elif "display_name" in js:
            self.display_name = js["display_name"]

        if "deviceName" in js:
            self.device_name = js["deviceName"]
        elif "device_name" in js:
            self.device_name = js["device_name"]

        if "timeZone" in js:
            self.time_zone = js["timeZone"]
        elif "time_zone" in js:
            self.time_zone = js["time_zone"]

        if "latitude" in js and js["latitude"] is not None:
            self.latitude = js["latitude"]
        if "longitude" in js and js["longitude"] is not None:
            self.longitude = js["longitude"]

        if "usageCentPerKwHour" in js:
            self.usage_cent_per_kw_hour = js["usageCentPerKwHour"]
        elif "usage_cent_per_kw_hour" in js:
            self.usage_cent_per_kw_hour = js["usage_cent_per_kw_hour"]

        if "buyback_rate_cents_per_kwh" in js:
            self.buyback_rate_cents_per_kwh = js["buyback_rate_cents_per_kwh"]
        if "net_metering" in js:
            self.net_metering = js["net_metering"]
        if "billing_cycle_start_day" in js:
            self.billing_cycle_start_day = js["billing_cycle_start_day"]
        if "utility_rate_gid" in js:
            self.utility_rate_gid = js["utility_rate_gid"]

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
        if (
            "evCharger" in js
            or js.get("category") == "EVSE"
            or js.get("model") == "VVDN01"
        ):
            if "evCharger" in js and js["evCharger"]:
                self.ev_charger = ChargerDevice().from_json_dictionary(js["evCharger"])
            else:
                self.ev_charger = ChargerDevice().from_json_dictionary(js)

        # Fallback naming: if not self.device_name, use display_name or 'EV Charger'
        if not self.device_name:
            self.device_name = self.display_name or (
                "EV Charger" if self.ev_charger else ""
            )
        if not self.display_name and self.device_name:
            self.display_name = self.device_name

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
        self.parent_channel_num = None
        self.channel_id: str = ""
        self.channel_classification: str = ""
        self.has_data: Optional[bool] = None
        self.parent_channel_id: Optional[str] = None
        self.direction: str = ""
        self.sub_type: Optional[str] = None
        self.appliance_type: Optional[str] = None

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        """Populate device channel data from a dictionary extracted from the response json."""
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        elif "device_gid" in js:
            self.device_gid = js["device_gid"]

        if "name" in js:
            self.name = js["name"]
        elif "display_name" in js:
            self.name = js["display_name"]

        if "channelNum" in js and js["channelNum"] is not None:
            self.channel_num = str(js["channelNum"])
        elif "channel_num" in js and js["channel_num"] is not None:
            self.channel_num = str(js["channel_num"])

        if "channelMultiplier" in js:
            self.channel_multiplier = js["channelMultiplier"]
        elif "multiplier" in js:
            self.channel_multiplier = js["multiplier"]

        if "channelTypeGid" in js:
            self.channel_type_gid = js["channelTypeGid"]
        elif "channel_type_gid" in js:
            self.channel_type_gid = js["channel_type_gid"]

        if "type" in js:
            self.type = js["type"]
        elif "channel_classification" in js:
            self.type = js["channel_classification"]

        if "channel_id" in js:
            self.channel_id = js["channel_id"]
        elif "channelId" in js:
            self.channel_id = js["channelId"]

        if "channel_classification" in js:
            self.channel_classification = js["channel_classification"]
        elif "channelClassification" in js:
            self.channel_classification = js["channelClassification"]

        if "has_data" in js:
            self.has_data = js["has_data"]
        elif "hasData" in js:
            self.has_data = js["hasData"]

        if "parentChannelNum" in js:
            self.parent_channel_num = js["parentChannelNum"]
        elif "parent_channel_num" in js:
            self.parent_channel_num = js["parent_channel_num"]

        if "parent_channel_id" in js:
            self.parent_channel_id = js["parent_channel_id"]
        elif "parentChannelId" in js:
            self.parent_channel_id = js["parentChannelId"]

        if "direction" in js:
            self.direction = js["direction"]
        if "sub_type" in js:
            self.sub_type = js["sub_type"]
        if "appliance_type" in js:
            self.appliance_type = js["appliance_type"]

        # Channel number normalization from channel_id if explicit channel_num not in json
        if "channelNum" not in js and "channel_num" not in js and self.channel_id:
            if self.channel_id == "Mains":
                self.channel_num = "1,2,3"
            elif self.channel_id.startswith("Branch_"):
                self.channel_num = self.channel_id.split("_")[1]
            else:
                self.channel_num = self.channel_id

        return self

    # Known types: Main, FiftyAmp, FiftyAmpBidirectional

    def as_dictionary(self) -> "dict[str, Any]":
        """Returns a dictionary of the device channel data."""
        d = {
            "deviceGid": self.device_gid,
            "name": self.name,
            "channelNum": self.channel_num,
            "channelMultiplier": self.channel_multiplier,
            "channelTypeGid": self.channel_type_gid,
            "type": self.type,
            "parentChannelNum": self.parent_channel_num,
        }
        if self.channel_id:
            d["channelId"] = self.channel_id
        if self.has_data is not None:
            d["hasData"] = self.has_data
        return d


class VueUsageDevice(VueDevice):
    def __init__(self, gid=0, timestamp: Optional[datetime.datetime] = None):
        super().__init__(gid=gid)
        self.timestamp = timestamp
        self.channels: dict[str, VueDeviceChannelUsage] = {}

    @property
    def channels_by_id(self) -> dict[str, VueDeviceChannelUsage]:
        """Return channel usages indexed by channel_id."""
        return {ch.channel_id: ch for ch in self.channels.values() if ch.channel_id}

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if not js:
            return self
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        elif "device_gid" in js:
            self.device_gid = js["device_gid"]

        channel_usages = js.get("channelUsages") or js.get("channel_usages") or []
        for channel in channel_usages:
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
        channel_id: str = "",
        raw_usage: Optional[float] = None,
        percentage: Optional[float] = 0.0,
        included_in_total_usage: Optional[bool] = None,
        **kwargs: Any,
    ):
        super().__init__(gid=gid, name=name, channelNum=channelNum)
        self.name = name
        self.device_gid: int = gid
        self.usage: float = usage
        self.channel_num = channelNum
        self.channel_id: str = channel_id or kwargs.get("channelId", "")
        self.raw_usage: Optional[float] = raw_usage
        self.percentage: Optional[float] = percentage
        self.included_in_total_usage: Optional[bool] = included_in_total_usage
        self.timestamp = timestamp
        self.nested_devices: dict[int, VueUsageDevice] = {}

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        """Populate device channel usage data from a dictionary extracted from the response json."""
        if not js:
            return self
        if "channelUsages" in js:
            js = js[
                "channelUsages"
            ]  # were given "device" level and we want to work off "channel" level
        elif "channel_usages" in js:
            js = js["channel_usages"]

        if "name" in js:
            self.name = js["name"]
        elif "display_name" in js:
            self.name = js["display_name"]

        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        elif "device_gid" in js:
            self.device_gid = js["device_gid"]

        if "channel_id" in js:
            self.channel_id = js["channel_id"]
        elif "channelId" in js:
            self.channel_id = js["channelId"]

        if "channelNum" in js and js["channelNum"] is not None:
            self.channel_num = str(js["channelNum"])
        elif "channel_num" in js and js["channel_num"] is not None:
            self.channel_num = str(js["channel_num"])
        elif self.channel_id:
            if self.channel_id == "Mains":
                self.channel_num = "1,2,3"
            elif self.channel_id.startswith("Branch_"):
                self.channel_num = self.channel_id.split("_")[1]
            else:
                self.channel_num = self.channel_id

        if "usage" in js:
            self.usage = js["usage"]

        if "raw_usage" in js:
            self.raw_usage = js["raw_usage"]
        elif "rawUsage" in js:
            self.raw_usage = js["rawUsage"]

        if "percentage" in js:
            self.percentage = js["percentage"]

        if "included_in_total_usage" in js:
            self.included_in_total_usage = js["included_in_total_usage"]
        elif "includedInTotalUsage" in js:
            self.included_in_total_usage = js["includedInTotalUsage"]

        # Nested device handling
        nested = js.get("nestedDevices") or js.get("nested_devices")
        if nested:
            for device in nested:
                if device:
                    populated = VueUsageDevice(
                        timestamp=self.timestamp
                    ).from_json_dictionary(device)
                    self.nested_devices[populated.device_gid] = populated
        return self

    def as_dictionary(self) -> "dict[str, Any]":
        """Returns a dictionary of the device channel usage data."""
        d = super().as_dictionary()
        d["usage"] = self.usage
        d["percentage"] = self.percentage
        if self.raw_usage is not None:
            d["raw_usage"] = self.raw_usage
        if self.included_in_total_usage is not None:
            d["included_in_total_usage"] = self.included_in_total_usage
        return d


class OutletDevice(object):
    def __init__(self, gid: int = 0, on: bool = False):
        self.device_id: str = ""
        self.device_gid = gid
        self.outlet_on = on
        self.load_gid: int = 0
        self.schedules = []

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if "device_id" in js:
            self.device_id = js["device_id"]
        elif "deviceId" in js:
            self.device_id = js["deviceId"]
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        elif "device_gid" in js:
            self.device_gid = js["device_gid"]
        if "outletOn" in js:
            self.outlet_on = js["outletOn"]
        elif "outlet_on" in js:
            self.outlet_on = js["outlet_on"]
        if "loadGid" in js:
            self.load_gid = js["loadGid"]
        elif "load_gid" in js:
            self.load_gid = js["load_gid"]
        # don't have support for schedules yet
        return self

    def as_dictionary(self) -> "dict[str, Any]":
        d = {
            "deviceGid": self.device_gid,
            "outletOn": self.outlet_on,
            "loadGid": self.load_gid,
        }
        if self.device_id:
            d["deviceId"] = self.device_id
        return d


class EvseControlStatus(object):
    """Live charging session telemetry and control status for an EVSE."""

    def __init__(
        self,
        device_id: str = "",
        session_active: bool = False,
        energy_delivered: Optional[float] = None,
        cost: Optional[float] = None,
        active_charging_minutes: Optional[int] = None,
        charging_rate_kw: Optional[float] = None,
        charging_rate_amps: Optional[float] = None,
        offered_amps: Optional[float] = None,
        plug_in: Optional[datetime.datetime] = None,
        fault_code: Optional[Union[int, str]] = None,
        charger_status: Optional[str] = None,
        button_action: Optional[str] = None,
        subtext_type: Optional[str] = None,
        subtext_parameters: Optional[list[str]] = None,
        button_behavior: Optional[str] = None,
        charging_rate_controller: Optional[str] = None,
        charging_rate_controller_warning: Optional[str] = None,
        charge_rate_controller_type: Optional[str] = None,
        charge_rate_controller_status: Optional[str] = None,
        charge_rate_controller_offline_device_name: Optional[str] = None,
        charge_rate_controller_additional_amps: Optional[float] = None,
        charge_rate_controller_guaranteed_amps: Optional[float] = None,
        next_event_type: Optional[str] = None,
        next_event_time: Optional[datetime.datetime] = None,
        next_event_actor: Optional[str] = None,
        next_event_subtext_parameters: Optional[list[str]] = None,
    ) -> None:
        self.device_id = device_id
        self.session_active = session_active
        self.energy_delivered = energy_delivered
        self.cost = cost
        self.active_charging_minutes = active_charging_minutes
        self.charging_rate_kw = charging_rate_kw
        self.charging_rate_amps = charging_rate_amps
        self.offered_amps = offered_amps
        self.plug_in = plug_in
        self.fault_code = fault_code
        self.charger_status = charger_status
        self.button_action = button_action
        self.subtext_type = subtext_type
        self.subtext_parameters: list[str] = (
            list(subtext_parameters) if subtext_parameters is not None else []
        )
        self.button_behavior = button_behavior
        self.charging_rate_controller = charging_rate_controller
        self.charging_rate_controller_warning = charging_rate_controller_warning
        self.charge_rate_controller_type = charge_rate_controller_type
        self.charge_rate_controller_status = charge_rate_controller_status
        self.charge_rate_controller_offline_device_name = (
            charge_rate_controller_offline_device_name
        )
        self.charge_rate_controller_additional_amps = (
            charge_rate_controller_additional_amps
        )
        self.charge_rate_controller_guaranteed_amps = (
            charge_rate_controller_guaranteed_amps
        )
        self.next_event_type = next_event_type
        self.next_event_time = next_event_time
        self.next_event_actor = next_event_actor
        self.next_event_subtext_parameters: list[str] = (
            list(next_event_subtext_parameters)
            if next_event_subtext_parameters is not None
            else []
        )

    def from_json_dictionary(self, js: dict[str, Any]) -> Self:
        if "device_id" in js:
            self.device_id = str(js["device_id"])
        elif "deviceId" in js:
            self.device_id = str(js["deviceId"])

        if "session_active" in js:
            self.session_active = bool(js["session_active"])
        elif "sessionActive" in js:
            self.session_active = bool(js["sessionActive"])

        if "energy_delivered" in js and js["energy_delivered"] is not None:
            self.energy_delivered = float(js["energy_delivered"])
        elif "energyDelivered" in js and js["energyDelivered"] is not None:
            self.energy_delivered = float(js["energyDelivered"])

        if "cost" in js and js["cost"] is not None:
            self.cost = float(js["cost"])
        elif "estimated_cost" in js and js["estimated_cost"] is not None:
            self.cost = float(js["estimated_cost"])
        elif "estimatedCost" in js and js["estimatedCost"] is not None:
            self.cost = float(js["estimatedCost"])

        if (
            "active_charging_minutes" in js
            and js["active_charging_minutes"] is not None
        ):
            self.active_charging_minutes = int(js["active_charging_minutes"])
        elif "activeChargingMinutes" in js and js["activeChargingMinutes"] is not None:
            self.active_charging_minutes = int(js["activeChargingMinutes"])

        if "charging_rate_kw" in js and js["charging_rate_kw"] is not None:
            self.charging_rate_kw = float(js["charging_rate_kw"])
        elif "chargingRateKw" in js and js["chargingRateKw"] is not None:
            self.charging_rate_kw = float(js["chargingRateKw"])

        if "charging_rate_amps" in js and js["charging_rate_amps"] is not None:
            self.charging_rate_amps = float(js["charging_rate_amps"])
        elif "chargingRateAmps" in js and js["chargingRateAmps"] is not None:
            self.charging_rate_amps = float(js["chargingRateAmps"])

        if "offered_amps" in js and js["offered_amps"] is not None:
            self.offered_amps = float(js["offered_amps"])
        elif "offeredAmps" in js and js["offeredAmps"] is not None:
            self.offered_amps = float(js["offeredAmps"])

        plug_in_val = js.get("plug_in") if "plug_in" in js else js.get("plugIn")
        if plug_in_val:
            if isinstance(plug_in_val, datetime.datetime):
                self.plug_in = plug_in_val
            else:
                try:
                    self.plug_in = parse(plug_in_val)
                except Exception:
                    self.plug_in = None
        else:
            self.plug_in = None

        fault_code_val = (
            js.get("fault_code") if "fault_code" in js else js.get("faultCode")
        )
        if isinstance(fault_code_val, int) or (
            isinstance(fault_code_val, str) and fault_code_val.strip()
        ):
            self.fault_code = fault_code_val
        else:
            self.fault_code = None

        status_obj = js.get("status")
        if isinstance(status_obj, dict):
            self.charger_status = status_obj.get("charger_status") or status_obj.get(
                "chargerStatus"
            )
            self.subtext_type = status_obj.get("subtext_type") or status_obj.get(
                "subtextType"
            )
            raw_params = status_obj.get("subtext_parameters") or status_obj.get(
                "subtextParameters"
            )
            if isinstance(raw_params, list):
                self.subtext_parameters = [str(x) for x in raw_params if x is not None]
        else:
            if "charger_status" in js or "chargerStatus" in js:
                self.charger_status = js.get("charger_status") or js.get(
                    "chargerStatus"
                )
            if "subtext_type" in js or "subtextType" in js:
                self.subtext_type = js.get("subtext_type") or js.get("subtextType")
            raw_params = js.get("subtext_parameters") or js.get("subtextParameters")
            if isinstance(raw_params, list):
                self.subtext_parameters = [str(x) for x in raw_params if x is not None]

        btn_obj = js.get("button_info") or js.get("buttonInfo")
        if isinstance(btn_obj, dict):
            self.button_action = btn_obj.get("text")
            self.button_behavior = btn_obj.get("behavior")
        else:
            if "button_action" in js or "buttonAction" in js:
                self.button_action = js.get("button_action") or js.get("buttonAction")
            if "button_behavior" in js or "buttonBehavior" in js:
                self.button_behavior = js.get("button_behavior") or js.get(
                    "buttonBehavior"
                )

        if "charging_rate_controller" in js:
            self.charging_rate_controller = js["charging_rate_controller"]
        elif "chargingRateController" in js:
            self.charging_rate_controller = js["chargingRateController"]

        if "charging_rate_controller_warning" in js:
            self.charging_rate_controller_warning = js[
                "charging_rate_controller_warning"
            ]
        elif "chargingRateControllerWarning" in js:
            self.charging_rate_controller_warning = js["chargingRateControllerWarning"]

        crc_obj = js.get("charge_rate_controller") or js.get("chargeRateController")
        if isinstance(crc_obj, dict):
            self.charge_rate_controller_type = crc_obj.get(
                "controller_type"
            ) or crc_obj.get("controllerType")
            self.charge_rate_controller_status = crc_obj.get("status")
            self.charge_rate_controller_offline_device_name = crc_obj.get(
                "offline_device_name"
            ) or crc_obj.get("offlineDeviceName")
            if crc_obj.get("additional_amps") is not None:
                self.charge_rate_controller_additional_amps = float(
                    crc_obj["additional_amps"]
                )
            elif crc_obj.get("additionalAmps") is not None:
                self.charge_rate_controller_additional_amps = float(
                    crc_obj["additionalAmps"]
                )
            if crc_obj.get("guaranteed_amps") is not None:
                self.charge_rate_controller_guaranteed_amps = float(
                    crc_obj["guaranteed_amps"]
                )
            elif crc_obj.get("guaranteedAmps") is not None:
                self.charge_rate_controller_guaranteed_amps = float(
                    crc_obj["guaranteedAmps"]
                )
        else:
            if "charge_rate_controller_type" in js:
                self.charge_rate_controller_type = js["charge_rate_controller_type"]
            elif "chargeRateControllerType" in js:
                self.charge_rate_controller_type = js["chargeRateControllerType"]
            if "charge_rate_controller_status" in js:
                self.charge_rate_controller_status = js["charge_rate_controller_status"]
            elif "chargeRateControllerStatus" in js:
                self.charge_rate_controller_status = js["chargeRateControllerStatus"]
            if "charge_rate_controller_offline_device_name" in js:
                self.charge_rate_controller_offline_device_name = js[
                    "charge_rate_controller_offline_device_name"
                ]
            elif "chargeRateControllerOfflineDeviceName" in js:
                self.charge_rate_controller_offline_device_name = js[
                    "chargeRateControllerOfflineDeviceName"
                ]
            if js.get("charge_rate_controller_additional_amps") is not None:
                self.charge_rate_controller_additional_amps = float(
                    js["charge_rate_controller_additional_amps"]
                )
            elif js.get("chargeRateControllerAdditionalAmps") is not None:
                self.charge_rate_controller_additional_amps = float(
                    js["chargeRateControllerAdditionalAmps"]
                )
            if js.get("charge_rate_controller_guaranteed_amps") is not None:
                self.charge_rate_controller_guaranteed_amps = float(
                    js["charge_rate_controller_guaranteed_amps"]
                )
            elif js.get("chargeRateControllerGuaranteedAmps") is not None:
                self.charge_rate_controller_guaranteed_amps = float(
                    js["chargeRateControllerGuaranteedAmps"]
                )

        ne_obj = js.get("next_event") or js.get("nextEvent")
        if isinstance(ne_obj, dict):
            self.next_event_type = ne_obj.get("event_type") or ne_obj.get("eventType")
            time_val = ne_obj.get("event_time") or ne_obj.get("eventTime")
            if time_val:
                if isinstance(time_val, datetime.datetime):
                    self.next_event_time = time_val
                else:
                    try:
                        self.next_event_time = parse(time_val)
                    except Exception:
                        self.next_event_time = None
            self.next_event_actor = ne_obj.get("event_actor") or ne_obj.get(
                "eventActor"
            )
            raw_ne_params = ne_obj.get("subtext_parameters") or ne_obj.get(
                "subtextParameters"
            )
            if isinstance(raw_ne_params, list):
                self.next_event_subtext_parameters = [
                    str(x) for x in raw_ne_params if x is not None
                ]
        else:
            if "next_event_type" in js:
                self.next_event_type = js["next_event_type"]
            elif "nextEventType" in js:
                self.next_event_type = js["nextEventType"]
            time_val = js.get("next_event_time") or js.get("nextEventTime")
            if time_val:
                if isinstance(time_val, datetime.datetime):
                    self.next_event_time = time_val
                else:
                    try:
                        self.next_event_time = parse(time_val)
                    except Exception:
                        self.next_event_time = None
            if "next_event_actor" in js:
                self.next_event_actor = js["next_event_actor"]
            elif "nextEventActor" in js:
                self.next_event_actor = js["nextEventActor"]
            raw_ne_params = js.get("next_event_subtext_parameters") or js.get(
                "nextEventSubtextParameters"
            )
            if isinstance(raw_ne_params, list):
                self.next_event_subtext_parameters = [
                    str(x) for x in raw_ne_params if x is not None
                ]

        return self

    def as_dictionary(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "session_active": self.session_active,
            "energy_delivered": self.energy_delivered,
            "cost": self.cost,
            "active_charging_minutes": self.active_charging_minutes,
            "charging_rate_kw": self.charging_rate_kw,
            "charging_rate_amps": self.charging_rate_amps,
            "offered_amps": self.offered_amps,
            "plug_in": self.plug_in.isoformat() if self.plug_in else None,
            "fault_code": self.fault_code,
            "charger_status": self.charger_status,
            "subtext_type": self.subtext_type,
            "subtext_parameters": self.subtext_parameters,
            "button_action": self.button_action,
            "button_behavior": self.button_behavior,
            "charging_rate_controller": self.charging_rate_controller,
            "charging_rate_controller_warning": self.charging_rate_controller_warning,
            "charge_rate_controller_type": self.charge_rate_controller_type,
            "charge_rate_controller_status": self.charge_rate_controller_status,
            "charge_rate_controller_offline_device_name": (
                self.charge_rate_controller_offline_device_name
            ),
            "charge_rate_controller_additional_amps": (
                self.charge_rate_controller_additional_amps
            ),
            "charge_rate_controller_guaranteed_amps": (
                self.charge_rate_controller_guaranteed_amps
            ),
            "next_event_type": self.next_event_type,
            "next_event_time": (
                self.next_event_time.isoformat() if self.next_event_time else None
            ),
            "next_event_actor": self.next_event_actor,
            "next_event_subtext_parameters": self.next_event_subtext_parameters,
        }


class EvseStatus(object):
    def __init__(self, id: str = "", gid: int = 0, load_gid: int = 0, status: str = ""):
        self.device_id = id
        self.device_gid = gid
        self.load_gid = load_gid
        self.charger_status = status

    def from_json_dictionary(self, js: dict[str, Any]) -> Self:
        self.device_id = js.get("device_id") or js.get("deviceId", "")
        self.device_gid = js.get("device_gid") or js.get("deviceGid", 0)
        self.load_gid = js.get("load_gid") or js.get("loadGid", 0)
        self.charger_status = js.get("charger_status") or js.get("status", "")
        return self

    def as_dictionary(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_gid": self.device_gid,
            "load_gid": self.load_gid,
            "charger_status": self.charger_status,
        }


class ChargerDevice(object):
    def __init__(self, gid: int = 0, on: bool = False, id: str = ""):
        self.device_id: str = id
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
        # V1 attributes
        self.category = ""
        self.name = ""
        self.device_description = ""
        self.connected = False
        self.connected_changed_time: Optional[datetime.datetime] = None
        self.time_zone = datetime.timezone.utc
        self.time_zone_string = "UTC"
        self.billing_cycle_start_day = 0
        self.firmware = ""
        self.latitude = 0.0
        self.longitude = 0.0
        self.excess_solar_configured = False
        self.peak_demand_configured = False
        self.energy_management_active = "NONE"
        self.energy_managements_configured: list[str] = []
        self.energy_managements_active: list[str] = []
        self.evse_product = ""
        self.evse_model = ""
        self.evse_branding = ""
        self.evse_power_source = ""
        self.evse_color = ""
        self.evse_gun_type = ""
        self.power_smart_configuration: Optional[dict[str, Any]] = None
        self.vehicle_connected = False
        self.vehicle_charging = False
        self.partner_schedule_status = ""

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        if "device_id" in js:
            self.device_id = js["device_id"]
        elif "deviceId" in js:
            self.device_id = js["deviceId"]
        if "deviceGid" in js:
            self.device_gid = js["deviceGid"]
        elif "device_gid" in js:
            self.device_gid = js["device_gid"]
        if "loadGid" in js:
            self.load_gid = js["loadGid"]
        elif "load_gid" in js:
            self.load_gid = js["load_gid"]
        if "status" in js:
            self.status = js["status"]
        elif "charger_status" in js:
            self.status = js["charger_status"]
        elif "chargerStatus" in js:
            self.status = js["chargerStatus"]
        if "chargerOn" in js and js["chargerOn"] is not None:
            self.charger_on = bool(js["chargerOn"])
        elif "charger_on" in js and js["charger_on"] is not None:
            self.charger_on = bool(js["charger_on"])
        elif self.status:
            status_upper = self.status.strip().upper()
            if status_upper in (
                "CHARGING",
                "CONNECTED_ON",
                "DISCONNECTED_ON",
                "STANDBY",
                "READY",
            ):
                self.charger_on = True
            elif status_upper in (
                "CONNECTED_OFF",
                "DISCONNECTED_OFF",
                "FAULTING",
                "OFFLINE",
                "DEVICENOTCONNECTED",
                "UNKNOWN_VALUE",
            ):
                self.charger_on = False
            elif status_upper.endswith("_ON"):
                self.charger_on = True
            elif status_upper.endswith("_OFF"):
                self.charger_on = False
            else:
                self.charger_on = True
        else:
            self.charger_on = True
        if "message" in js:
            self.message = js["message"]
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
        elif "charging_rate" in js:
            self.charging_rate = js["charging_rate"]
        elif "charge_rate_amps" in js:
            self.charging_rate = js["charge_rate_amps"]
        elif "charging_rate_amps" in js:
            self.charging_rate = js["charging_rate_amps"]
        if "maxChargingRate" in js:
            self.max_charging_rate = js["maxChargingRate"]
        elif "max_charging_rate" in js:
            self.max_charging_rate = js["max_charging_rate"]
        elif "max_charge_rate_amps" in js:
            self.max_charging_rate = js["max_charge_rate_amps"]
        if not self.max_charging_rate:
            self.max_charging_rate = 48
        if "offPeakSchedulesEnabled" in js:
            self.off_peak_schedules_enabled = js["offPeakSchedulesEnabled"]
        elif "off_peak_schedules_enabled" in js:
            self.off_peak_schedules_enabled = js["off_peak_schedules_enabled"]
        if "debugCode" in js:
            self.debug_code = js["debugCode"]
        if "proControlCode" in js and js["proControlCode"] is not None:
            self.pro_control_code = str(js["proControlCode"])
        elif "pro_control_code" in js and js["pro_control_code"] is not None:
            self.pro_control_code = str(js["pro_control_code"])
        if "breakerPIN" in js:
            self.breaker_pin = js["breakerPIN"]
        elif "breaker_pin" in js:
            self.breaker_pin = js["breaker_pin"]

        # V1 fields
        if "category" in js:
            self.category = js["category"]
        if "name" in js:
            self.name = js["name"]
        if "device_description" in js:
            self.device_description = js["device_description"]
        if "connected" in js:
            self.connected = js["connected"]
        if "connected_changed_time" in js and js["connected_changed_time"]:
            try:
                self.connected_changed_time = parse(js["connected_changed_time"])
            except Exception:
                self.connected_changed_time = None
        timezone_string = js.get("time_zone")
        if timezone_string:
            self.time_zone_string = timezone_string
            try:
                self.time_zone = tz.gettz(timezone_string) or datetime.timezone.utc
            except Exception:
                pass
        if (
            "billing_cycle_start_day" in js
            and js["billing_cycle_start_day"] is not None
        ):
            self.billing_cycle_start_day = js["billing_cycle_start_day"]
        if "firmware" in js:
            self.firmware = js["firmware"]
        if "latitude" in js and js["latitude"] is not None:
            self.latitude = float(js["latitude"])
        if "longitude" in js and js["longitude"] is not None:
            self.longitude = float(js["longitude"])
        if "excess_solar_configured" in js:
            self.excess_solar_configured = js["excess_solar_configured"]
        if "peak_demand_configured" in js:
            self.peak_demand_configured = js["peak_demand_configured"]
        if "energy_management_active" in js:
            self.energy_management_active = js["energy_management_active"]
        if "energy_managements_configured" in js:
            self.energy_managements_configured = js["energy_managements_configured"]
        if "energy_managements_active" in js:
            self.energy_managements_active = js["energy_managements_active"]
        if "evse_product" in js:
            self.evse_product = js["evse_product"]
        if "evse_model" in js:
            self.evse_model = js["evse_model"]
        if "evse_branding" in js:
            self.evse_branding = js["evse_branding"]
        if "evse_power_source" in js:
            self.evse_power_source = js["evse_power_source"]
        if "evse_color" in js:
            self.evse_color = js["evse_color"]
        if "evse_gun_type" in js:
            self.evse_gun_type = js["evse_gun_type"]
        if "power_smart_configuration" in js:
            self.power_smart_configuration = js["power_smart_configuration"]
        if "vehicle_connected" in js:
            self.vehicle_connected = js["vehicle_connected"]
        if "vehicle_charging" in js:
            self.vehicle_charging = js["vehicle_charging"]
        if "partner_schedule_status" in js:
            self.partner_schedule_status = js["partner_schedule_status"]

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
        if self.device_id:
            d["deviceId"] = self.device_id
            d["device_id"] = self.device_id
        if self.breaker_pin:
            d["breakerPIN"] = self.breaker_pin
        if self.pro_control_code:
            d["proControlCode"] = self.pro_control_code
            d["pro_control_code"] = self.pro_control_code
        return d


EVSEDevice = ChargerDevice


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


class VueSite(object):
    def __init__(self):
        self.site_gid: int = 0
        self.display_name: str = ""
        self.latitude: float = 0.0
        self.longitude: float = 0.0
        self.time_zone: str = ""
        self.device_ids: list[str] = []
        self.customer_emails: list[str] = []
        self.service_address: Optional[dict[str, Any]] = None
        self.billing_cycle_start_day: int = 1
        self.usage_cents_per_kwh: float = 0.0
        self.buyback_rate_cents_per_kwh: Optional[float] = None
        self.net_metering: Optional[str] = None
        self.utility_provider: Optional[str] = None
        self.utility_rate_gid: Optional[int] = None
        self.utility_rate_mods: Optional[Any] = None

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        self.site_gid = js.get("site_gid") or js.get("siteGid", 0)
        self.display_name = js.get("display_name") or js.get("displayName", "")
        self.latitude = js.get("latitude", 0.0)
        self.longitude = js.get("longitude", 0.0)
        self.time_zone = js.get("time_zone") or js.get("timezone", "")
        self.device_ids = js.get("device_ids") or js.get("deviceIds", [])
        self.customer_emails = js.get("customer_emails") or js.get("customerEmails", [])
        self.service_address = js.get("service_address") or js.get("serviceAddress")
        self.billing_cycle_start_day = js.get("billing_cycle_start_day") or js.get(
            "billingCycleStartDay", 1
        )
        self.usage_cents_per_kwh = js.get("usage_cents_per_kwh") or js.get(
            "usageCentsPerKwh", 0.0
        )
        self.buyback_rate_cents_per_kwh = js.get("buyback_rate_cents_per_kwh")
        self.net_metering = js.get("net_metering")
        self.utility_provider = js.get("utility_provider")
        self.utility_rate_gid = js.get("utility_rate_gid")
        self.utility_rate_mods = js.get("utility_rate_mods")
        return self

    def as_dictionary(self) -> "dict[str, Any]":
        return {
            "site_gid": self.site_gid,
            "display_name": self.display_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "time_zone": self.time_zone,
            "device_ids": self.device_ids,
            "customer_emails": self.customer_emails,
            "service_address": self.service_address,
            "billing_cycle_start_day": self.billing_cycle_start_day,
            "usage_cents_per_kwh": self.usage_cents_per_kwh,
            "buyback_rate_cents_per_kwh": self.buyback_rate_cents_per_kwh,
            "net_metering": self.net_metering,
        }


class ChannelDevice(object):
    def __init__(self):
        self.device_gid: int = 0
        self.device_id: str = ""
        self.channels: list[Channel] = []

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        self.device_gid = js.get("device_gid", 0)
        self.device_id = js.get("device_id", "")
        self.channels = []
        for ch in js.get("channels", []):
            if ch:
                populated = Channel().from_json_dictionary(ch)
                self.channels.append(populated)
        return self


class Channel(object):
    def __init__(self):
        self.display_name: str = ""
        self.channel_id: str = ""
        self.parent_channel_id: Optional[str] = None
        self.channel_num: str = ""
        self.sub_type: Optional[str] = None
        self.nested_devices: list[ChannelDevice] = []

    def from_json_dictionary(self, js: "dict[str, Any]") -> Self:
        self.display_name = js.get("display_name", "")
        self.channel_id = js.get("channel_id", "")
        self.parent_channel_id = js.get("parent_channel_id", None)
        self.channel_num = js.get("channel_num", "")
        self.sub_type = js.get("sub_type", "")
        self.nested_devices = []
        for dev in js.get("nested_devices", []):
            if dev:
                populated = ChannelDevice().from_json_dictionary(dev)
                self.nested_devices.append(populated)
        return self


class ExcessGenerationMonitor(object):
    """Represents an energy monitor with excess generation capabilities."""

    def __init__(
        self,
        device_id: str = "",
        enabled: bool = False,
    ) -> None:
        self.device_id: str = device_id
        self.enabled: bool = enabled

    def from_json_dictionary(self, js: dict[str, Any]) -> Self:
        self.device_id = str(js.get("device_id") or js.get("deviceId") or "")
        self.enabled = bool(js.get("enabled", False))
        return self

    def as_dictionary(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "enabled": self.enabled,
        }


class ExcessGenerationMonitors(object):
    """Collection of excess generation eligible monitors and unavailable monitors."""

    def __init__(
        self,
        monitors: Optional[list[ExcessGenerationMonitor]] = None,
        unavailable_monitors: Optional[list[str]] = None,
    ) -> None:
        self.monitors: list[ExcessGenerationMonitor] = (
            monitors if monitors is not None else []
        )
        self.unavailable_monitors: list[str] = (
            unavailable_monitors if unavailable_monitors is not None else []
        )

    def from_json_dictionary(self, js: dict[str, Any]) -> Self:
        self.monitors = []
        for mon in js.get("monitors", []):
            if isinstance(mon, dict):
                self.monitors.append(
                    ExcessGenerationMonitor().from_json_dictionary(mon)
                )
        self.unavailable_monitors = [
            str(m)
            for m in (
                js.get("unavailable_monitors") or js.get("unavailableMonitors") or []
            )
        ]
        return self

    def as_dictionary(self) -> dict[str, Any]:
        return {
            "monitors": [m.as_dictionary() for m in self.monitors],
            "unavailable_monitors": list(self.unavailable_monitors),
        }


class ExcessGenerationLoad(object):
    """Represents a controllable load assigned to excess solar charging."""

    def __init__(
        self,
        load_gid: int = 0,
        enabled: bool = False,
    ) -> None:
        self.load_gid: int = load_gid
        self.enabled: bool = enabled

    def from_json_dictionary(self, js: dict[str, Any]) -> Self:
        gid = js.get("load_gid") if "load_gid" in js else js.get("loadGid", 0)
        self.load_gid = int(gid or 0)
        self.enabled = bool(js.get("enabled", False))
        return self

    def as_dictionary(self) -> dict[str, Any]:
        return {
            "load_gid": self.load_gid,
            "enabled": self.enabled,
        }


class EnergyMonitorExcessGeneration(object):
    """Configuration of excess generation loads and solar window for a specific monitor."""

    def __init__(
        self,
        device_id: str = "",
        loads: Optional[list[ExcessGenerationLoad]] = None,
        solar_window: Optional[dict[str, Any]] = None,
        sunrise: Optional[str] = None,
        sunset: Optional[str] = None,
    ) -> None:
        self.device_id: str = device_id
        self.loads: list[ExcessGenerationLoad] = loads if loads is not None else []
        self.solar_window: Optional[dict[str, Any]] = solar_window
        self.sunrise: Optional[str] = sunrise
        self.sunset: Optional[str] = sunset

    def from_json_dictionary(self, js: dict[str, Any]) -> Self:
        self.device_id = str(js.get("device_id") or js.get("deviceId") or "")
        self.loads = []
        for load in js.get("loads", []):
            if isinstance(load, dict):
                self.loads.append(ExcessGenerationLoad().from_json_dictionary(load))
        self.solar_window = (
            js.get("solar_window") if "solar_window" in js else js.get("solarWindow")
        )
        self.sunrise = js.get("sunrise")
        self.sunset = js.get("sunset")
        return self

    def as_dictionary(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "loads": [ld.as_dictionary() for ld in self.loads],
            "solar_window": self.solar_window,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
        }
