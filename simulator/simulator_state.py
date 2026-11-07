# SimulatorState of the Emporia API. Holds all the state needed to simulate the API.
from __future__ import annotations

import datetime
import json
import os
from typing import Any, Optional

from simulator.models import (
    ChannelType,
    CustomerDevicesResponse,
    DeviceListUsage,
    DeviceUsage,
    DeviceUsageResponse,
    ChannelUsage,
    SimulatorChannel,
    SimulatorCharger,
    SimulatorCustomer,
    SimulatorDevice,
    SimulatorDeviceConnected,
    SimulatorLatitudeLongitude,
    SimulatorLocationInformation,
    SimulatorLocationProperties,
    SimulatorOutlet,
    SimulatorSubDevice,
    StatusResponse,
    _format_time,
)


class SimulatorState(object):
    def __init__(self):
        self.customer = SimulatorCustomer(
            customerGid=1234,
            email="simulator@simulator.sim",
            firstName="Sim",
            lastName="Ulator",
            createdAt=datetime.datetime.now(datetime.timezone.utc),
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

        # V1 excess generation & EVSE telemetry state
        self.evse_session_active: bool = True
        self.evse_active_charging_minutes: int = 42
        self.evse_energy_delivered: float = 12.35
        self.evse_cost: float = 1.48
        self.evse_plug_in: datetime.datetime = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(minutes=42)
        self.evse_controller: str = "EXCESS_SOLAR"
        self.evse_override_excess_solar: bool = False

        self.excess_generation_loads: list[dict[str, Any]] = [
            {"load_gid": 1005, "enabled": True}
        ]
        self.excess_solar_window: Optional[dict[str, Any]] = {
            "start": {"anchor": "SUNRISE", "offset_seconds": 3600},
            "end": {"anchor": "SUNSET", "offset_seconds": -3600},
        }
        self.excess_sunrise: str = "2026-11-01T14:29:49Z"
        self.excess_sunset: str = "2026-11-02T00:10:38Z"

        script_dir = os.path.dirname(__file__)
        channel_types_file = script_dir + "/channel_types.json"
        self.load_channel_types(channel_types_file)

    def load_channel_types(self, channel_types_file: str):
        with open(channel_types_file, "r") as f:
            self.channel_types = json.load(f)

    def get_device_by_gid(self, gid: Optional[int]) -> Optional[SimulatorDevice]:
        if gid is None:
            return None
        for d in self.devices:
            if d.deviceGid == gid:
                return d
        return None

    def get_device_by_id(self, dev_id: str) -> Optional[SimulatorDevice]:
        for d in self.devices:
            if d.manufacturerDeviceId == dev_id or str(d.deviceGid) == str(dev_id):
                return d
        return None

    def get_customers_devices(self) -> CustomerDevicesResponse:
        return CustomerDevicesResponse(
            customerGid=self.customer.customerGid,
            email=self.customer.email,
            firstName=self.customer.firstName,
            lastName=self.customer.lastName,
            createdAt=self.customer.createdAt,
            devices=self.devices,
        )

    def get_customers_devices_v1(self) -> dict[str, Any]:
        dev_list = []
        for dev in self.devices:
            parent_dev = self.get_device_by_gid(dev.parentDeviceGid)
            parent_dev_id = parent_dev.manufacturerDeviceId if parent_dev else None
            parent_channel_num = dev.parentChannelNum
            if parent_channel_num:
                if parent_channel_num == "1,2,3":
                    parent_channel_id = "Mains"
                elif parent_channel_num.isdigit():
                    parent_channel_id = f"Branch_{parent_channel_num}"
                else:
                    parent_channel_id = parent_channel_num
            else:
                parent_channel_id = None

            if dev.evCharger is not None:
                dev_type = "EV_CHARGER"
                cat = "EVSE"
                charger = dev.evCharger
                ev_charger_dict = {
                    "device_id": dev.manufacturerDeviceId,
                    "device_gid": dev.deviceGid,
                    "category": "EVSE",
                    "name": dev.locationProperties.deviceName or "EV",
                    "connected": dev.deviceConnected.connected,
                    "charger_on": charger.chargerOn,
                    "charging_rate": charger.chargingRate,
                    "max_charging_rate": charger.maxChargingRate,
                    "charge_rate_amps": charger.chargingRate,
                    "max_charge_rate_amps": charger.maxChargingRate,
                    "charger_status": "CHARGING" if charger.chargerOn else "DISCONNECTED_OFF",
                    "status": "CHARGING" if charger.chargerOn else "DISCONNECTED_OFF",
                    "load_gid": charger.loadGid,
                }
                outlet_dict = None
                channels = [
                    {
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": 25,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "parent_channel_id": None,
                        "channel_classification": "FIFTY_AMP",
                        "has_data": True,
                    }
                ]
            elif dev.outlet is not None:
                dev_type = "OUTLET"
                cat = "OUTLET"
                ev_charger_dict = None
                outlet_dict = {
                    "device_id": dev.manufacturerDeviceId,
                    "device_gid": dev.deviceGid,
                    "load_gid": dev.outlet.loadGid,
                    "outlet_on": dev.outlet.outletOn,
                }
                channels = [
                    {
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": 23,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "parent_channel_id": None,
                        "channel_classification": "FIFTY_AMP",
                        "has_data": True,
                    }
                ]
            else:
                # Vue monitor
                dev_type = "MONITOR"
                cat = "MONITOR"
                ev_charger_dict = None
                outlet_dict = None
                channels = [
                    {
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": None,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "parent_channel_id": None,
                        "channel_classification": "MAIN",
                        "has_data": True,
                    },
                    {
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": None,
                        "channel_id": "Mains_A",
                        "channel_num": "Mains_A",
                        "parent_channel_id": "Mains",
                        "channel_classification": "MAIN",
                        "has_data": True,
                    },
                    {
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": None,
                        "channel_id": "Mains_B",
                        "channel_num": "Mains_B",
                        "parent_channel_id": "Mains",
                        "channel_classification": "MAIN",
                        "has_data": True,
                    },
                    {
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": None,
                        "channel_id": "Mains_C",
                        "channel_num": "Mains_C",
                        "parent_channel_id": "Mains",
                        "channel_classification": "MAIN",
                        "has_data": False,
                    },
                ]
                # Branch CTs
                for i in range(1, 9):
                    is_solar = (i == 2)
                    channels.append({
                        "name": "Solar" if is_solar else f"Channel {i}",
                        "multiplier": 1.0,
                        "channel_type_gid": 13 if is_solar else 18,
                        "channel_id": f"Branch_{i}",
                        "channel_num": str(i),
                        "parent_channel_id": None,
                        "channel_classification": "FIFTY_AMP",
                        "has_data": True,
                    })
                # Unpopulated CT ports
                for i in range(9, 17):
                    channels.append({
                        "name": None,
                        "multiplier": 1.0,
                        "channel_type_gid": None,
                        "channel_id": f"Branch_{i}",
                        "channel_num": str(i),
                        "parent_channel_id": None,
                        "channel_classification": "FIFTY_AMP",
                        "has_data": False,
                    })

            device_item = {
                "device_id": dev.manufacturerDeviceId,
                "device_gid": dev.deviceGid,
                "manufacturer_id": dev.manufacturerDeviceId,
                "model": dev.model,
                "firmware": dev.firmware,
                "device_type": dev_type,
                "category": cat,
                "display_name": dev.locationProperties.displayName,
                "device_name": dev.locationProperties.deviceName,
                "site_gid": 5001,
                "parent_device_id": parent_dev_id,
                "parent_device_gid": dev.parentDeviceGid,
                "parent_channel_id": parent_channel_id,
                "parent_channel_num": parent_channel_num,
                "time_zone": dev.locationProperties.timeZone,
                "latitude": dev.locationProperties.latitudeLongitude.latitude,
                "longitude": dev.locationProperties.latitudeLongitude.longitude,
                "billing_cycle_start_day": dev.locationProperties.billingCycleStartDay,
                "usage_cent_per_kw_hour": dev.locationProperties.usageCentPerKwHour,
                "energy_managements_configured": ["EXCESS_SOLAR"] if dev_type in ("MONITOR", "EV_CHARGER") else [],
                "supported_energy_managements": ["PEAK_DEMAND", "POWER_SMART", "EXCESS_SOLAR"] if dev_type == "MONITOR" else (["LOAD_SHARING", "EXCESS_SOLAR", "POWER_SMART", "PEAK_DEMAND"] if dev_type == "EV_CHARGER" else []),
                "channels": channels,
            }
            if outlet_dict:
                device_item["outlet"] = outlet_dict
            if ev_charger_dict:
                device_item["evCharger"] = ev_charger_dict
                device_item["ev_charger"] = ev_charger_dict
                device_item["charger_on"] = charger.chargerOn
                device_item["charging_rate"] = charger.chargingRate
                device_item["max_charging_rate"] = charger.maxChargingRate
                device_item["charge_rate_amps"] = charger.chargingRate
                device_item["max_charge_rate_amps"] = charger.maxChargingRate
            dev_list.append(device_item)

        return {"devices": dev_list}

    def get_channels_v1(self) -> list[dict[str, Any]]:
        # Builds V1 channel topology for root devices
        channel_devices = []
        for dev in self.devices:
            if dev.parentDeviceGid is None:
                channel_devices.append(self._build_channel_device(dev))
        return channel_devices

    def _build_channel_device(self, dev: SimulatorDevice) -> dict[str, Any]:
        channels = []
        if dev.model.startswith("VUE"):
            nested_under_mains = [
                self._build_channel_device(child)
                for child in self.devices
                if child.parentDeviceGid == dev.deviceGid and child.parentChannelNum == "1,2,3"
            ]
            channels.append({
                "display_name": "Main",
                "channel_id": "Mains",
                "parent_channel_id": None,
                "channel_num": "1,2,3",
                "sub_type": None,
                "has_data": True,
                "nested_devices": nested_under_mains,
            })
            channels.append({
                "display_name": "Main_A",
                "channel_id": "Mains_A",
                "parent_channel_id": "Mains",
                "channel_num": "Mains_A",
                "sub_type": None,
                "has_data": True,
                "nested_devices": [],
            })
            channels.append({
                "display_name": "Main_B",
                "channel_id": "Mains_B",
                "parent_channel_id": "Mains",
                "channel_num": "Mains_B",
                "sub_type": None,
                "has_data": True,
                "nested_devices": [],
            })
            channels.append({
                "display_name": "Main_C",
                "channel_id": "Mains_C",
                "parent_channel_id": "Mains",
                "channel_num": "Mains_C",
                "sub_type": None,
                "has_data": False,
                "nested_devices": [],
            })
            for i in range(1, 9):
                is_solar = (i == 2)
                nested = [
                    self._build_channel_device(child)
                    for child in self.devices
                    if child.parentDeviceGid == dev.deviceGid and child.parentChannelNum == str(i)
                ]
                channels.append({
                    "display_name": "Solar" if is_solar else f"Channel {i}",
                    "channel_id": f"Branch_{i}",
                    "parent_channel_id": None,
                    "channel_num": str(i),
                    "sub_type": "Solar" if is_solar else None,
                    "has_data": True,
                    "nested_devices": nested,
                })
            for i in range(9, 17):
                channels.append({
                    "display_name": f"Channel {i}",
                    "channel_id": f"Branch_{i}",
                    "parent_channel_id": None,
                    "channel_num": str(i),
                    "sub_type": None,
                    "has_data": False,
                    "nested_devices": [],
                })
        else:
            channels.append({
                "display_name": dev.locationProperties.deviceName or "Main",
                "channel_id": "Mains",
                "parent_channel_id": None,
                "channel_num": "1,2,3",
                "sub_type": None,
                "has_data": True,
                "nested_devices": [],
            })

        return {
            "device_gid": dev.deviceGid,
            "device_id": dev.manufacturerDeviceId,
            "channels": channels,
        }

    def get_sites_v1(self) -> dict[str, Any]:
        return {
            "sites": [
                {
                    "site_gid": 5001,
                    "display_name": "Home",
                    "latitude": self.default_location_props.latitudeLongitude.latitude,
                    "longitude": self.default_location_props.latitudeLongitude.longitude,
                    "time_zone": self.default_location_props.timeZone,
                    "timezone": self.default_location_props.timeZone,
                    "device_ids": [d.manufacturerDeviceId for d in self.devices],
                    "customer_emails": [self.customer.email],
                    "service_address": {
                        "address": "123 Energy Way",
                        "address2": None,
                        "city": "Denver",
                        "state": "CO",
                        "postal": "80202",
                        "country_code": "USA",
                    },
                    "billing_cycle_start_day": 1,
                    "usage_cents_per_kwh": self.default_location_props.usageCentPerKwHour,
                    "buyback_rate_cents_per_kwh": None,
                    "net_metering": None,
                    "utility_provider": None,
                    "utility_rate_gid": None,
                    "utility_rate_mods": None,
                }
            ]
        }

    def get_usages_v1(
        self,
        device_gids: Optional[str] = None,
        instant: Optional[datetime.datetime] = None,
        scale: str = "SECOND",
        energy_unit: str = "KILOWATT_HOURS",
    ) -> dict[str, Any]:
        if not instant:
            instant = datetime.datetime.now(datetime.timezone.utc)

        target_gids = set()
        if device_gids:
            for g in device_gids.split(","):
                g = g.strip()
                if g.isdigit():
                    target_gids.add(int(g))

        device_usages = []
        is_voltage = (energy_unit.upper() in ("VOLTAGE", "VOLTS"))

        for dev in self.devices:
            if target_gids and dev.deviceGid not in target_gids:
                continue

            channel_usages = []
            if dev.model.startswith("VUE"):
                if is_voltage:
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "name": "Main",
                        "usage": 120.75,
                        "percentage": 100.0,
                        "raw_usage": 120.75,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_A",
                        "channel_num": "Mains_A",
                        "name": "Main_A",
                        "usage": 120.4,
                        "percentage": None,
                        "raw_usage": 120.4,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_B",
                        "channel_num": "Mains_B",
                        "name": "Main_B",
                        "usage": 121.1,
                        "percentage": None,
                        "raw_usage": 121.1,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_C",
                        "channel_num": "Mains_C",
                        "name": "Main_C",
                        "usage": 0.0,
                        "percentage": None,
                        "raw_usage": 0.0,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                else:
                    mains_usage = self.usage_dict_1min.get(f"{dev.deviceGid}_1,2,3", 85 * 240 / 60000) or 0.0
                    mains_raw = mains_usage * 1000.0

                    nested_mains = [
                        self._build_usage_device(child, is_voltage)
                        for child in self.devices
                        if child.parentDeviceGid == dev.deviceGid and child.parentChannelNum == "1,2,3"
                    ]
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "name": "Main",
                        "usage": mains_usage,
                        "percentage": 100.0,
                        "raw_usage": mains_raw,
                        "included_in_total_usage": None,
                        "nested_devices": nested_mains,
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_A",
                        "channel_num": "Mains_A",
                        "name": "Main_A",
                        "usage": mains_usage * 0.501,
                        "percentage": 50.01,
                        "raw_usage": mains_raw * 0.501,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_B",
                        "channel_num": "Mains_B",
                        "name": "Main_B",
                        "usage": mains_usage * 0.499,
                        "percentage": 49.99,
                        "raw_usage": mains_raw * 0.499,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    for i in range(1, 9):
                        ch_usage = self.usage_dict_1min.get(f"{dev.deviceGid}_{i}", 0.0) or 0.0
                        ch_raw = ch_usage * 1000.0
                        pct = (ch_usage / mains_usage * 100.0) if mains_usage else 0.0
                        nested_ch = [
                            self._build_usage_device(child, is_voltage)
                            for child in self.devices
                            if child.parentDeviceGid == dev.deviceGid and child.parentChannelNum == str(i)
                        ]
                        channel_usages.append({
                            "device_gid": dev.deviceGid,
                            "channel_id": f"Branch_{i}",
                            "channel_num": str(i),
                            "name": f"Channel {i}",
                            "usage": ch_usage,
                            "percentage": pct,
                            "raw_usage": ch_raw,
                            "included_in_total_usage": True,
                            "nested_devices": nested_ch,
                        })
                    bal_usage = self.usage_dict_1min.get(f"{dev.deviceGid}_Balance", 42.5 * 240 / 60000) or 0.0
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Balance",
                        "channel_num": "Balance",
                        "name": "Balance",
                        "usage": bal_usage,
                        "percentage": (bal_usage / mains_usage * 100.0) if mains_usage else 0.0,
                        "raw_usage": bal_usage * 1000.0,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "TotalUsage",
                        "channel_num": "TotalUsage",
                        "name": "TotalUsage",
                        "usage": mains_usage,
                        "percentage": 100.0,
                        "raw_usage": mains_raw,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
            else:
                if is_voltage:
                    volts = 240.0 if dev.evCharger is not None else 120.0
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "name": dev.locationProperties.deviceName or "Main",
                        "usage": volts,
                        "percentage": 100.0,
                        "raw_usage": volts,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_A",
                        "channel_num": "Mains_A",
                        "name": "Main_A",
                        "usage": 120.0,
                        "percentage": None,
                        "raw_usage": 120.0,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains_B",
                        "channel_num": "Mains_B",
                        "name": "Main_B",
                        "usage": 120.0 if dev.evCharger is not None else 0.0,
                        "percentage": None,
                        "raw_usage": 120.0 if dev.evCharger is not None else 0.0,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })
                else:
                    usage = self.usage_dict_1min.get(f"{dev.deviceGid}_1,2,3", 0.0) or 0.0
                    channel_usages.append({
                        "device_gid": dev.deviceGid,
                        "channel_id": "Mains",
                        "channel_num": "1,2,3",
                        "name": dev.locationProperties.deviceName or "Main",
                        "usage": usage,
                        "percentage": 100.0,
                        "raw_usage": usage * 1000.0,
                        "included_in_total_usage": None,
                        "nested_devices": [],
                    })

            device_usages.append({
                "device_gid": dev.deviceGid,
                "channel_usages": channel_usages,
            })

        return {
            "instant": _format_time(instant),
            "scale": scale,
            "energy_unit": "VOLTAGE" if is_voltage else energy_unit,
            "device_usages": device_usages,
        }

    def _build_usage_device(self, dev: SimulatorDevice, is_voltage: bool) -> dict[str, Any]:
        if is_voltage:
            volts = 240.0 if dev.evCharger is not None else 120.0
            usages = [
                {
                    "device_gid": dev.deviceGid,
                    "channel_id": "Mains",
                    "channel_num": "1,2,3",
                    "name": dev.locationProperties.deviceName or "Main",
                    "usage": volts,
                    "percentage": 100.0,
                    "raw_usage": volts,
                    "included_in_total_usage": None,
                    "nested_devices": [],
                }
            ]
        else:
            u = self.usage_dict_1min.get(f"{dev.deviceGid}_1,2,3", 0.0) or 0.0
            usages = [
                {
                    "device_gid": dev.deviceGid,
                    "channel_id": "Mains",
                    "channel_num": "1,2,3",
                    "name": dev.locationProperties.deviceName or "Main",
                    "usage": u,
                    "percentage": 100.0,
                    "raw_usage": u * 1000.0,
                    "included_in_total_usage": None,
                    "nested_devices": [],
                }
            ]
        return {
            "device_gid": dev.deviceGid,
            "channel_usages": usages,
        }

    def get_status(self) -> StatusResponse:
        return StatusResponse(
            devicesConnected=[device.deviceConnected for device in self.devices],
            evChargers=self.chargers,
            loads=[],
            batteries=[],
            outlets=self.outlets,
        )

    def get_status_v1(self) -> dict[str, Any]:
        evses = []
        for d in self.devices:
            if d.evCharger is not None:
                charger = d.evCharger
                evses.append({
                    "device_id": d.manufacturerDeviceId,
                    "deviceId": d.manufacturerDeviceId,
                    "device_gid": d.deviceGid,
                    "deviceGid": d.deviceGid,
                    "load_gid": charger.loadGid,
                    "loadGid": charger.loadGid,
                    "category": "EVSE",
                    "name": d.locationProperties.deviceName or "EV",
                    "connected": d.deviceConnected.connected,
                    "charger_on": charger.chargerOn,
                    "chargerOn": charger.chargerOn,
                    "charging_rate": charger.chargingRate,
                    "chargingRate": charger.chargingRate,
                    "max_charging_rate": charger.maxChargingRate,
                    "maxChargingRate": charger.maxChargingRate,
                    "charge_rate_amps": charger.chargingRate,
                    "max_charge_rate_amps": charger.maxChargingRate,
                    "charger_status": "CHARGING" if charger.chargerOn else "DISCONNECTED_OFF",
                    "status": "CHARGING" if charger.chargerOn else "DISCONNECTED_OFF",
                })
        outlets = []
        for d in self.devices:
            if d.outlet is not None:
                outlets.append({
                    "device_id": d.manufacturerDeviceId,
                    "deviceId": d.manufacturerDeviceId,
                    "device_gid": d.deviceGid,
                    "deviceGid": d.deviceGid,
                    "load_gid": d.outlet.loadGid,
                    "loadGid": d.outlet.loadGid,
                    "outlet_on": d.outlet.outletOn,
                    "outletOn": d.outlet.outletOn,
                })
        devices_conn = []
        for d in self.devices:
            offline_str = _format_time(d.deviceConnected.offlineSince) if d.deviceConnected.offlineSince else None
            devices_conn.append({
                "device_id": d.manufacturerDeviceId,
                "deviceId": d.manufacturerDeviceId,
                "device_gid": d.deviceGid,
                "deviceGid": d.deviceGid,
                "connected": d.deviceConnected.connected,
                "offline_since": offline_str,
                "offlineSince": offline_str,
            })

        return {
            "evses": evses,
            "evChargers": evses,
            "outlets": outlets,
            "devices_connected": devices_conn,
            "devicesConnected": devices_conn,
            "loads": [],
            "batteries": [],
        }

    def get_evse_control(self, device_id: Optional[str] = None) -> dict[str, Any]:
        charger_dev = None
        for d in self.devices:
            if d.evCharger is not None:
                if not device_id or d.manufacturerDeviceId == device_id or str(d.deviceGid) == str(device_id):
                    charger_dev = d
                    break
        if not charger_dev:
            for d in self.devices:
                if d.evCharger is not None:
                    charger_dev = d
                    break

        dev_id = charger_dev.manufacturerDeviceId if charger_dev else (device_id or "D2112A04B4AC6C4523421")
        charger = charger_dev.evCharger if charger_dev else (self.chargers[0] if self.chargers else None)
        is_on = charger.chargerOn if charger else True
        rate_amps = float(charger.chargingRate) if charger else 40.0
        max_amps = float(charger.maxChargingRate) if charger else 40.0
        kw = (rate_amps * 240.0 / 1000.0) if is_on else 0.0

        plug_in_str = _format_time(self.evse_plug_in) if is_on else None
        next_event_time_str = "2026-11-02T14:00:00Z"

        status_str = "CHARGING" if is_on else "DISCONNECTED_OFF"
        button_act = "MANAGE" if is_on else "TURN_ON"
        button_beh = "OVERRIDE_EXCESS_SOLAR" if is_on else None
        subtext = "EXCESS_SOLAR_PAUSED" if self.evse_override_excess_solar else None
        subtext_params = ["2026-11-01T20:00:00Z"]

        return {
            "device_id": dev_id,
            "session_active": self.evse_session_active and is_on,
            "energy_delivered": self.evse_energy_delivered if is_on else None,
            "cost": self.evse_cost if is_on else None,
            "active_charging_minutes": self.evse_active_charging_minutes if is_on else None,
            "charging_rate_kw": kw if is_on else None,
            "charging_rate_amps": rate_amps if is_on else None,
            "offered_amps": max_amps if is_on else None,
            "plug_in": plug_in_str,
            "fault_code": None,
            "charger_status": status_str,
            "button_action": button_act,
            "subtext_type": subtext,
            "subtext_parameters": subtext_params,
            "button_behavior": button_beh,
            "charging_rate_controller": self.evse_controller if is_on else None,
            "charging_rate_controller_warning": None,
            "charge_rate_controller_type": "EXCESS_SOLAR",
            "charge_rate_controller_status": "WORKING_CORRECTLY",
            "charge_rate_controller_offline_device_name": None,
            "charge_rate_controller_additional_amps": 6.0,
            "charge_rate_controller_guaranteed_amps": 12.0,
            "next_event_type": "START",
            "next_event_time": next_event_time_str,
            "next_event_actor": "SOLAR_WINDOW",
            "next_event_subtext_parameters": ["UtilityPartner"],
            "status": {
                "charger_status": status_str,
                "subtext_type": subtext,
                "subtext_parameters": subtext_params,
            },
            "button_info": {
                "text": button_act,
                "behavior": button_beh,
            },
            "charge_rate_controller": {
                "controller_type": "EXCESS_SOLAR",
                "status": "WORKING_CORRECTLY",
                "offline_device_name": None,
                "additional_amps": 6.0,
                "guaranteed_amps": 12.0,
            },
            "next_event": {
                "event_type": "START",
                "event_time": next_event_time_str,
                "event_actor": "SOLAR_WINDOW",
                "subtext_parameters": ["UtilityPartner"],
            },
        }

    def post_evse_control(self, device_id: str, command: str) -> bool:
        cmd = command.strip().upper()
        charger_dev = self.get_device_by_id(device_id)
        charger = charger_dev.evCharger if charger_dev and charger_dev.evCharger else (self.chargers[0] if self.chargers else None)
        if not charger:
            return False

        if cmd == "TURN_ON":
            charger.chargerOn = True
            self.evse_session_active = True
            self.set_channel_1min_watts(charger.deviceGid, "1,2,3", charger.chargingRate * 240)
        elif cmd == "TURN_OFF":
            charger.chargerOn = False
            self.evse_session_active = False
            self.set_channel_1min_watts(charger.deviceGid, "1,2,3", 0.0)
        elif cmd == "CHARGE_AT_FULL_POWER":
            charger.chargerOn = True
            charger.chargingRate = charger.maxChargingRate
            self.evse_session_active = True
            self.evse_controller = "MANUAL"
            self.evse_override_excess_solar = True
            self.set_channel_1min_watts(charger.deviceGid, "1,2,3", charger.maxChargingRate * 240)
        else:
            raise ValueError(f"Unknown EVSE control command: {command}")
        return True

    def get_evses_v1(self, device_ids: Optional[list[str]] = None) -> dict[str, Any]:
        success_list = []
        for d in self.devices:
            if d.evCharger is not None:
                if not device_ids or d.manufacturerDeviceId in device_ids or str(d.deviceGid) in device_ids:
                    c = d.evCharger
                    success_list.append({
                        "device_id": d.manufacturerDeviceId,
                        "category": "EVSE",
                        "name": d.locationProperties.deviceName or "EV",
                        "connected": d.deviceConnected.connected,
                        "charger_on": c.chargerOn,
                        "charging_rate": c.chargingRate,
                        "max_charging_rate": c.maxChargingRate,
                        "charge_rate_amps": c.chargingRate,
                        "max_charge_rate_amps": c.maxChargingRate,
                    })
        return {"success": success_list}

    def set_evse_settings_v1(self, settings: list[dict[str, Any]]) -> dict[str, Any]:
        success_ids = []
        for item in settings:
            dev_id = str(item.get("device_id", ""))
            rate = int(item.get("charge_rate_amps", 40))
            dev = self.get_device_by_id(dev_id)
            if dev and dev.evCharger:
                dev.evCharger.chargingRate = rate
                if dev.evCharger.chargerOn:
                    self.set_channel_1min_watts(dev.deviceGid, "1,2,3", rate * 240)
                success_ids.append(dev_id)
            elif not dev and self.chargers:
                self.chargers[0].chargingRate = rate
                success_ids.append(dev_id)
        return {"success": success_ids}

    def get_excess_generation_monitors(self) -> dict[str, Any]:
        monitors = []
        unavailable = []
        for d in self.devices:
            if d.model.startswith("VUE"):
                monitors.append({
                    "device_id": d.manufacturerDeviceId,
                    "enabled": True,
                })
        return {
            "monitors": monitors,
            "unavailable_monitors": unavailable,
        }

    def get_excess_generation(self, device_id: str) -> dict[str, Any]:
        return {
            "device_id": device_id,
            "loads": self.excess_generation_loads,
            "solar_window": self.excess_solar_window,
            "sunrise": self.excess_sunrise,
            "sunset": self.excess_sunset,
        }

    def set_excess_generation(
        self,
        device_id: str,
        loads: list[dict[str, Any]],
        solar_window: Optional[dict[str, Any]] = None,
        sunrise: Optional[str] = None,
        sunset: Optional[str] = None,
    ) -> bool:
        self.excess_generation_loads = loads
        if solar_window is not None:
            self.excess_solar_window = solar_window
        if sunrise is not None:
            self.excess_sunrise = sunrise
        if sunset is not None:
            self.excess_sunset = sunset
        return True

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
        root = self.build_tree(None, None)
        deviceListUsage.devices = root
        return response

    def build_tree(
        self, parentDeviceGid: Optional[int], parentChannelNum: Optional[str]
    ) -> list[DeviceUsage]:
        devices_at_level: list[DeviceUsage] = []
        for device in self.devices:
            if (
                device.parentDeviceGid == parentDeviceGid
                and device.parentChannelNum == parentChannelNum
            ):
                device_usage = DeviceUsage(deviceGid=device.deviceGid, channelUsages=[])
                channel_usages: list[ChannelUsage] = []
                for channel in device.channels:
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
                device_name = device.locationProperties.deviceName
                device.locationProperties = location_properties.model_copy()
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
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        outlet = SimulatorOutlet(deviceGid=gid, outletOn=on, loadGid=gid)
        self.outlets.append(outlet)
        outlet_device = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId=f"B0000C89109103c{gid}",
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
                    type="FiftyAmp",
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
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        charger = SimulatorCharger(
            deviceGid=gid,
            loadGid=gid,
            chargerOn=on,
            chargingRate=4 * breakerSize // 5,
            maxChargingRate=4 * breakerSize // 5,
        )
        self.chargers.append(charger)
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
                    type="FiftyAmp",
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
        for device in self.devices:
            if device.deviceGid == gid:
                raise Exception(f"Device gid {gid} already exists")
        vue = SimulatorDevice(
            deviceGid=gid,
            manufacturerDeviceId="A2112A04B4AC67B2B548201",
            model="VUE002",
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
                        type="FiftyAmp",
                    )
                )
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
        if watts is None:
            usage = None
        else:
            scaler = 60 * 1000
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
