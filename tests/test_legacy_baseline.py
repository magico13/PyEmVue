from __future__ import annotations

import datetime
from typing import Any

from pyemvue.customer import Customer
from pyemvue.device import (
    ChannelType,
    ChargerDevice,
    OutletDevice,
    Vehicle,
    VehicleStatus,
    VueDevice,
    VueDeviceChannel,
    VueDeviceChannelUsage,
    VueUsageDevice,
)


def test_vue_device_legacy_parsing(devices_legacy_json: dict[str, Any]) -> None:
    """Validate that VueDevice correctly deserializes legacy devices payload."""
    raw_devices = devices_legacy_json["devices"]
    assert len(raw_devices) == 3

    # Main Vue 3 monitor (root)
    dev0 = VueDevice().from_json_dictionary(raw_devices[0])
    assert dev0.device_gid == 1001
    assert dev0.manufacturer_id == "F2410A0000000000000001"
    assert dev0.model == "VUE003"
    assert dev0.firmware == "1.0.0"
    assert dev0.parent_device_gid == 0
    assert dev0.parent_channel_num == ""
    assert dev0.connected is True
    assert dev0.offline_since.year == 2026

    # Location properties
    assert dev0.device_name == "Main Panel"
    assert dev0.display_name == "Home"
    assert dev0.zip_code == "80202"
    assert dev0.time_zone == "America/Denver"
    assert dev0.usage_cent_per_kw_hour == 12.0
    assert dev0.peak_demand_dollar_per_kw == 0.0
    assert dev0.billing_cycle_start_day == 1
    assert dev0.solar is True
    assert dev0.utility_rate_gid == 1234
    assert dev0.air_conditioning == "true"
    assert dev0.heat_source == "heatPump"
    assert dev0.location_sqft == "2500"
    assert dev0.num_electric_cars == "1"
    assert dev0.location_type == "houseSingleFamily"
    assert dev0.num_people == "3"
    assert dev0.swimming_pool == "false"
    assert dev0.hot_tub == "false"
    assert dev0.latitude == 39.7392
    assert dev0.longitude == -104.9903

    # Channels
    assert len(dev0.channels) == 3
    mains = dev0.channels[0]
    assert isinstance(mains, VueDeviceChannel)
    assert mains.device_gid == 1001
    assert mains.name == "Main"
    assert mains.channel_num == "1,2,3"
    assert mains.channel_multiplier == 1.0
    assert mains.channel_type_gid == 0
    assert mains.type == "Main"
    assert mains.parent_channel_num is None

    solar = dev0.channels[1]
    assert solar.name == "Solar"
    assert solar.channel_num == "1"
    assert solar.channel_multiplier == 1.0
    assert solar.channel_type_gid == 13
    assert solar.type == "FiftyAmpBidirectional"

    heat_pump = dev0.channels[2]
    assert heat_pump.name == "Heat Pump"
    assert heat_pump.channel_num == "2"
    assert heat_pump.channel_multiplier == 2.0
    assert heat_pump.channel_type_gid == 24
    assert heat_pump.type == "FiftyAmp"

    # VueDeviceChannel.as_dictionary
    mains_dict = mains.as_dictionary()
    assert mains_dict["deviceGid"] == 1001
    assert mains_dict["channelNum"] == "1,2,3"
    assert mains_dict["type"] == "Main"


def test_subdevice_legacy_parsing(devices_legacy_json: dict[str, Any]) -> None:
    """Validate that nested subdevices parse correctly."""
    raw_devices = devices_legacy_json["devices"]
    root_dev = raw_devices[0]
    assert "devices" in root_dev
    assert len(root_dev["devices"]) == 1

    subdev = VueDevice().from_json_dictionary(root_dev["devices"][0])
    assert subdev.device_gid == 1002
    assert subdev.manufacturer_id == "A2237A0000000000000002"
    assert subdev.model == "VUE002"
    assert subdev.parent_device_gid == 1001
    assert subdev.parent_channel_num == "1,2,3"
    assert subdev.display_name == "Garage"
    assert len(subdev.channels) == 1
    assert subdev.channels[0].name == "Sub Mains"


def test_charger_device_legacy_parsing(devices_legacy_json: dict[str, Any]) -> None:
    """Validate ChargerDevice parsing from legacy payload."""
    raw_devices = devices_legacy_json["devices"]
    ev_raw = raw_devices[1]
    dev = VueDevice().from_json_dictionary(ev_raw)

    assert dev.device_gid == 1003
    assert dev.ev_charger is not None
    ev = dev.ev_charger
    assert isinstance(ev, ChargerDevice)
    assert ev.device_gid == 1003
    assert ev.load_gid == 9001
    assert ev.charger_on is True
    assert ev.message == "Charging normally"
    assert ev.status == "CHARGING"
    assert ev.charging_rate == 40
    assert ev.max_charging_rate == 48
    assert ev.off_peak_schedules_enabled is False
    assert ev.breaker_pin == "1234"
    assert ev.debug_code == "DEBUG01"
    assert ev.pro_control_code == "PRO01"

    # as_dictionary
    ev_dict = ev.as_dictionary()
    assert ev_dict["deviceGid"] == 1003
    assert ev_dict["loadGid"] == 9001
    assert ev_dict["chargerOn"] is True
    assert ev_dict["chargingRate"] == 40
    assert ev_dict["maxChargingRate"] == 48
    assert ev_dict["breakerPIN"] == "1234"


def test_outlet_device_legacy_parsing(devices_legacy_json: dict[str, Any]) -> None:
    """Validate OutletDevice parsing from legacy payload."""
    raw_devices = devices_legacy_json["devices"]
    outlet_raw = raw_devices[2]
    dev = VueDevice().from_json_dictionary(outlet_raw)

    assert dev.device_gid == 1005
    assert dev.outlet is not None
    outlet = dev.outlet
    assert isinstance(outlet, OutletDevice)
    assert outlet.device_gid == 1005
    assert outlet.load_gid == 9002
    assert outlet.outlet_on is True

    outlet_dict = outlet.as_dictionary()
    assert outlet_dict["deviceGid"] == 1005
    assert outlet_dict["loadGid"] == 9002
    assert outlet_dict["outletOn"] is True


def test_customer_legacy_parsing() -> None:
    """Validate Customer model deserialization."""
    customer_data = {
        "customerGid": 12345,
        "email": "test@example.com",
        "firstName": "Emporia",
        "lastName": "Tester",
        "createdAt": "2026-01-01T00:00:00Z",
    }
    cust = Customer().from_json_dictionary(customer_data)
    assert cust.customer_gid == 12345
    assert cust.email == "test@example.com"
    assert cust.first_name == "Emporia"
    assert cust.last_name == "Tester"
    assert cust.created_at == "2026-01-01T00:00:00Z"


def test_channel_type_parsing() -> None:
    """Validate ChannelType deserialization."""
    raw = {
        "channelTypeGid": 13,
        "description": "Solar / Inverter",
        "selectable": True,
    }
    ct = ChannelType().from_json_dictionary(raw)
    assert ct.channel_type_gid == 13
    assert ct.description == "Solar / Inverter"
    assert ct.selectable is True


def test_vehicle_and_status_parsing() -> None:
    """Validate Vehicle and VehicleStatus deserialization."""
    raw_vehicle = {
        "vehicleGid": 7001,
        "vendor": "TestVendor",
        "apiId": "API_123",
        "displayName": "Test EV",
        "loadGid": 9001,
        "make": "Electric",
        "model": "Car",
        "year": 2026,
    }
    v = Vehicle().from_json_dictionary(raw_vehicle)
    assert v.vehicle_gid == 7001
    assert v.vendor == "TestVendor"
    assert v.display_name == "Test EV"
    assert v.year == 2026

    v_dict = v.as_dictionary()
    assert v_dict["vehicleGid"] == 7001
    assert v_dict["make"] == "Electric"

    raw_status = {
        "settings": {
            "vehicleGid": 7001,
            "vehicleState": "PARKED",
            "batteryLevel": 85,
            "batteryRange": 250,
            "chargingState": "CHARGING",
            "chargeLimitPercent": 90,
            "minutesToFullCharge": 45,
            "chargeCurrentRequest": 32,
            "chargeCurrentRequestMax": 48,
        }
    }
    vs = VehicleStatus().from_json_dictionary(raw_status)
    assert vs.vehicle_gid == 7001
    assert vs.vehicle_state == "PARKED"
    assert vs.battery_level == 85
    assert vs.charging_state == "CHARGING"
    assert vs.minutes_to_full_charge == 45
    assert vs.charge_current_request == 32
    assert vs.charge_current_request_max == 48

    vs_dict = vs.as_dictionary()
    assert vs_dict["vehicleGid"] == 7001
    assert vs_dict["batteryLevel"] == 85


def test_vue_usage_device_parsing() -> None:
    """Validate VueUsageDevice and VueDeviceChannelUsage deserialization."""
    ts = datetime.datetime(2026, 11, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    raw_usage = {
        "deviceGid": 1001,
        "channelUsages": [
            {
                "deviceGid": 1001,
                "name": "Main",
                "channelNum": "1,2,3",
                "usage": 2.54,
                "percentage": 100.0,
            },
            {
                "deviceGid": 1001,
                "name": "Solar",
                "channelNum": "1",
                "usage": -1.25,
                "percentage": 49.2,
            },
        ],
    }
    dev_usage = VueUsageDevice(gid=1001, timestamp=ts).from_json_dictionary(raw_usage)
    assert dev_usage.device_gid == 1001
    assert dev_usage.timestamp == ts
    assert len(dev_usage.channels) == 2
    assert "1,2,3" in dev_usage.channels
    assert isinstance(dev_usage.channels["1,2,3"], VueDeviceChannelUsage)
    assert dev_usage.channels["1,2,3"].usage == 2.54
    assert dev_usage.channels["1,2,3"].percentage == 100.0
    assert dev_usage.channels["1,2,3"].timestamp == ts

    assert "1" in dev_usage.channels
    assert dev_usage.channels["1"].usage == -1.25
    assert dev_usage.channels["1"].percentage == 49.2
