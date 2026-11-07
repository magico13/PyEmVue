from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import MagicMock
import pytest
from dateutil import tz

from pyemvue.device import (
    ChargerDevice,
    EVSEDevice,
    EvseControlStatus,
    OutletDevice,
    VueDevice,
)
from pyemvue.pyemvue import PyEmVue


def test_evse_control_status_active_deserialization(
    evse_control_v1_json: dict[str, Any],
) -> None:
    """Validate EvseControlStatus deserializes all telemetry metrics from an active session payload."""
    raw_active = evse_control_v1_json["active"]
    status = EvseControlStatus().from_json_dictionary(raw_active)

    assert status.device_id == "D2301A0000000000000003"
    assert status.session_active is True
    assert status.active_charging_minutes == 42
    assert status.cost == pytest.approx(1.48)
    assert status.energy_delivered == pytest.approx(12.35)
    assert status.charging_rate_kw == pytest.approx(7.68)
    assert status.charging_rate_amps == pytest.approx(32.0)
    assert status.offered_amps == pytest.approx(40.0)
    assert status.plug_in == datetime.datetime(2026, 11, 1, 18, 30, tzinfo=tz.tzutc())
    assert status.fault_code is None
    assert status.charger_status == "CHARGING"
    assert status.subtext_type == "EXCESS_SOLAR_PAUSED"
    assert status.subtext_parameters == ["2026-11-01T20:00:00Z"]
    assert status.button_action == "MANAGE"
    assert status.button_behavior == "OVERRIDE_EXCESS_SOLAR"
    assert status.charging_rate_controller == "EXCESS_SOLAR"
    assert status.charging_rate_controller_warning == "CONTROLLER_WARN"
    assert status.charge_rate_controller_type == "EXCESS_SOLAR"
    assert status.charge_rate_controller_status == "WORKING_CORRECTLY"
    assert status.charge_rate_controller_offline_device_name == "Garage Monitor"
    assert status.charge_rate_controller_additional_amps == pytest.approx(6.0)
    assert status.charge_rate_controller_guaranteed_amps == pytest.approx(12.0)
    assert status.next_event_type == "START"
    assert status.next_event_time == datetime.datetime(
        2026, 11, 2, 14, 0, tzinfo=tz.tzutc()
    )
    assert status.next_event_actor == "SOLAR_WINDOW"
    assert status.next_event_subtext_parameters == ["UtilityPartner"]

    # Verify serialization dictionary
    status_dict = status.as_dictionary()
    assert status_dict["device_id"] == "D2301A0000000000000003"
    assert status_dict["session_active"] is True
    assert status_dict["active_charging_minutes"] == 42
    assert status_dict["cost"] == pytest.approx(1.48)
    assert status_dict["energy_delivered"] == pytest.approx(12.35)
    assert status_dict["charging_rate_kw"] == pytest.approx(7.68)
    assert status_dict["charging_rate_amps"] == pytest.approx(32.0)
    assert status_dict["offered_amps"] == pytest.approx(40.0)
    assert status_dict["plug_in"] == "2026-11-01T18:30:00+00:00"
    assert status_dict["fault_code"] is None
    assert status_dict["charger_status"] == "CHARGING"
    assert status_dict["subtext_type"] == "EXCESS_SOLAR_PAUSED"
    assert status_dict["subtext_parameters"] == ["2026-11-01T20:00:00Z"]
    assert status_dict["button_action"] == "MANAGE"
    assert status_dict["button_behavior"] == "OVERRIDE_EXCESS_SOLAR"
    assert status_dict["charging_rate_controller"] == "EXCESS_SOLAR"
    assert status_dict["charging_rate_controller_warning"] == "CONTROLLER_WARN"
    assert status_dict["charge_rate_controller_type"] == "EXCESS_SOLAR"
    assert status_dict["charge_rate_controller_status"] == "WORKING_CORRECTLY"
    assert status_dict["charge_rate_controller_offline_device_name"] == "Garage Monitor"
    assert status_dict["charge_rate_controller_additional_amps"] == pytest.approx(6.0)
    assert status_dict["charge_rate_controller_guaranteed_amps"] == pytest.approx(12.0)
    assert status_dict["next_event_type"] == "START"
    assert status_dict["next_event_time"] == "2026-11-02T14:00:00+00:00"
    assert status_dict["next_event_actor"] == "SOLAR_WINDOW"
    assert status_dict["next_event_subtext_parameters"] == ["UtilityPartner"]

    # Round-trip check
    round_trip = EvseControlStatus().from_json_dictionary(status_dict)
    assert round_trip.device_id == status.device_id
    assert round_trip.session_active == status.session_active
    assert round_trip.energy_delivered == status.energy_delivered
    assert round_trip.charger_status == status.charger_status
    assert round_trip.button_action == status.button_action
    assert round_trip.button_behavior == status.button_behavior
    assert round_trip.subtext_type == status.subtext_type
    assert round_trip.subtext_parameters == status.subtext_parameters
    assert round_trip.next_event_type == status.next_event_type
    assert round_trip.next_event_time == status.next_event_time


def test_evse_control_status_disconnected_deserialization(
    evse_control_v1_json: dict[str, Any],
) -> None:
    """Validate EvseControlStatus deserializes idle/disconnected payload with null metrics."""
    raw_idle = evse_control_v1_json["disconnected"]
    status = EvseControlStatus().from_json_dictionary(raw_idle)

    assert status.device_id == "D2301A0000000000000003"
    assert status.session_active is False
    assert status.active_charging_minutes is None
    assert status.cost is None
    assert status.energy_delivered is None
    assert status.charging_rate_kw is None
    assert status.charging_rate_amps is None
    assert status.offered_amps is None
    assert status.plug_in is None
    assert status.fault_code is None
    assert status.charger_status == "DISCONNECTED_OFF"
    assert status.button_action == "TURN_ON"


def test_get_evse_control_api_call(evse_control_v1_json: dict[str, Any]) -> None:
    """Validate get_evse_control makes the correct GET call and populates device_id."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'
    # Remove top-level device_id to assert get_evse_control populates it from query param
    payload = dict(evse_control_v1_json["active"])
    payload.pop("device_id", None)
    mock_response.json.return_value = payload
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    status = vue.get_evse_control("D2301A0000000000000003")

    mock_auth.request.assert_called_once_with(
        "get", "customers/evse/control?device_id=D2301A0000000000000003"
    )
    assert status is not None
    assert status.device_id == "D2301A0000000000000003"
    assert status.session_active is True
    assert status.charger_status == "CHARGING"
    assert status.button_action == "MANAGE"


def test_get_evse_control_empty_response() -> None:
    """Validate get_evse_control handles empty response gracefully."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    assert vue.get_evse_control("D2301A0000000000000003") is None


def test_set_evse_state_enable_and_disable() -> None:
    """Validate set_evse_state sends TURN_ON and TURN_OFF commands via POST."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"success": true}'
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    # Test enable (TURN_ON)
    result_on = vue.set_evse_state("D2301A0000000000000003", enabled=True)
    assert result_on is True
    mock_auth.request.assert_called_with(
        "post",
        "customers/evse/control",
        json={"device_id": "D2301A0000000000000003", "command": "TURN_ON"},
    )

    # Test disable (TURN_OFF)
    result_off = vue.set_evse_state("D2301A0000000000000003", enabled=False)
    assert result_off is True
    mock_auth.request.assert_called_with(
        "post",
        "customers/evse/control",
        json={"device_id": "D2301A0000000000000003", "command": "TURN_OFF"},
    )


def test_set_evse_settings() -> None:
    """Validate set_evse_settings dispatches PUT with charge_rate_amps payload."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"success": ["D2301A0000000000000003"]}'
    mock_response.json.return_value = {"success": ["D2301A0000000000000003"]}
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    # Test success matching device_id
    success = vue.set_evse_settings("D2301A0000000000000003", charge_rate_amps=32)
    assert success is True
    mock_auth.request.assert_called_once_with(
        "put",
        "devices/evses/settings",
        json={
            "settings": [
                {
                    "device_id": "D2301A0000000000000003",
                    "charge_rate_amps": 32,
                }
            ]
        },
    )

    # Test when device_id not in success array
    mock_response.json.return_value = {"success": ["OTHER_DEVICE"]}
    failed = vue.set_evse_settings("D2301A0000000000000003", charge_rate_amps=32)
    assert failed is False

    # Test 204 No Content response
    mock_response.text = ""
    mock_response.status_code = 204
    assert vue.set_evse_settings("D2301A0000000000000003", charge_rate_amps=32) is True


def test_get_evses(evses_v1_json: dict[str, Any]) -> None:
    """Validate get_evses sends GET with comma-separated IDs and parses ChargerDevice objects."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'
    mock_response.json.return_value = evses_v1_json
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    evses = vue.get_evses(["D2301A0000000000000003", "D2301A0000000000000004"])
    mock_auth.request.assert_called_once_with(
        "get",
        "devices/evses?device_ids=D2301A0000000000000003,D2301A0000000000000004",
    )
    assert len(evses) == 1
    evse = evses[0]
    assert isinstance(evse, ChargerDevice)
    assert evse.device_id == "D2301A0000000000000003"
    assert evse.charging_rate == 40
    assert evse.max_charging_rate == 48
    assert evse.connected is True
    assert evse.charger_on is True


def test_get_devices_status_v1_dual_schema() -> None:
    """Validate get_devices_status compatibility with both V1 snake_case and legacy camelCase schemas."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'

    # 1. Test V1 response schema
    v1_payload = {
        "evses": [
            {
                "device_id": "D2301A0000000000000003",
                "device_gid": 1003,
                "load_gid": 9001,
                "charger_status": "CHARGING",
            }
        ],
        "outlets": [
            {
                "device_id": "D2301A0000000000000002",
                "device_gid": 1002,
                "load_gid": 9002,
                "outlet_on": True,
            }
        ],
        "devices_connected": [
            {
                "device_id": "D2301A0000000000000003",
                "device_gid": 1003,
                "connected": True,
                "offline_since": None,
            }
        ],
    }
    mock_response.json.return_value = v1_payload
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    dev = VueDevice(gid=1003)
    outlets, chargers = vue.get_devices_status(device_list=[dev])
    assert len(outlets) == 1
    assert isinstance(outlets[0], OutletDevice)
    assert outlets[0].device_id == "D2301A0000000000000002"
    assert outlets[0].outlet_on is True

    assert len(chargers) == 1
    assert isinstance(chargers[0], ChargerDevice)
    assert chargers[0].device_id == "D2301A0000000000000003"
    assert chargers[0].status == "CHARGING"

    assert dev.connected is True
    assert dev.device_id == "D2301A0000000000000003"

    # 2. Test legacy response schema
    legacy_payload = {
        "evChargers": [
            {
                "deviceId": "D2301A0000000000000003",
                "deviceGid": 1003,
                "loadGid": 9001,
                "status": "CHARGING",
            }
        ],
        "outlets": [
            {
                "deviceId": "D2301A0000000000000002",
                "deviceGid": 1002,
                "loadGid": 9002,
                "outletOn": False,
            }
        ],
        "devicesConnected": [
            {
                "deviceId": "D2301A0000000000000003",
                "deviceGid": 1003,
                "connected": False,
                "offlineSince": "2026-11-01T12:00:00Z",
            }
        ],
    }
    mock_response.json.return_value = legacy_payload
    outlets, chargers = vue.get_devices_status(device_list=[dev])
    assert len(outlets) == 1
    assert outlets[0].outlet_on is False
    assert len(chargers) == 1
    assert chargers[0].status == "CHARGING"
    assert dev.connected is False
    assert dev.offline_since == "2026-11-01T12:00:00Z"


def test_evse_device_alias_and_schema_compatibility() -> None:
    """Validate EVSEDevice alias and dual-schema property parsing in ChargerDevice."""
    assert EVSEDevice is ChargerDevice

    # CamelCase (legacy)
    legacy_charger = ChargerDevice().from_json_dictionary(
        {
            "deviceId": "DEV1",
            "deviceGid": 1003,
            "loadGid": 9001,
            "chargerOn": True,
            "chargingRate": 40,
            "maxChargingRate": 48,
            "breakerPIN": "9999",
        }
    )
    assert legacy_charger.device_id == "DEV1"
    assert legacy_charger.device_gid == 1003
    assert legacy_charger.charger_on is True
    assert legacy_charger.charging_rate == 40
    assert legacy_charger.max_charging_rate == 48
    assert legacy_charger.breaker_pin == "9999"

    # Snake_case (V1)
    v1_charger = ChargerDevice().from_json_dictionary(
        {
            "device_id": "DEV2",
            "device_gid": 1004,
            "load_gid": 9002,
            "charger_on": False,
            "charge_rate_amps": 32,
            "max_charge_rate_amps": 40,
            "breaker_pin": "1234",
            "category": "EVSE",
            "name": "Wall Connector",
            "connected": True,
        }
    )
    assert v1_charger.device_id == "DEV2"
    assert v1_charger.device_gid == 1004
    assert v1_charger.charger_on is False
    assert v1_charger.charging_rate == 32
    assert v1_charger.max_charging_rate == 40
    assert v1_charger.breaker_pin == "1234"
    assert v1_charger.category == "EVSE"
    assert v1_charger.name == "Wall Connector"
    assert v1_charger.connected is True


def test_post_evse_control_commands_and_validation() -> None:
    """Validate post_evse_control validates commands against VALID_EVSE_CONTROL_COMMANDS."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"success": true}'
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    # Valid commands
    for cmd in ("TURN_ON", "turn_off", "CHARGE_AT_FULL_POWER"):
        assert vue.post_evse_control("DEV1", cmd) is True
        mock_auth.request.assert_called_with(
            "post",
            "customers/evse/control",
            json={"device_id": "DEV1", "command": cmd.strip().upper()},
        )

    # Invalid commands raise ValueError
    for invalid in ("PAUSE", "RESUME", "", "STOP", "INVALID_CMD"):
        with pytest.raises(ValueError, match="Unsupported EVSE control command"):
            vue.post_evse_control("DEV1", invalid)


def test_evse_control_status_camel_case_dual_schema() -> None:
    """Validate EvseControlStatus parses all 26 attributes from camelCase JSON."""
    camel_payload = {
        "deviceId": "DEV_CAMEL_1",
        "sessionActive": True,
        "energyDelivered": 15.5,
        "estimatedCost": 2.10,
        "activeChargingMinutes": 60,
        "chargingRateKw": 9.6,
        "chargingRateAmps": 40.0,
        "offeredAmps": 48.0,
        "plugIn": "2026-11-01T15:00:00Z",
        "faultCode": 3,
        "status": {
            "chargerStatus": "CONNECTED_OFF",
            "subtextType": "MANUALLY_STOPPED",
            "subtextParameters": ["2026-11-01T16:00:00Z"],
        },
        "buttonInfo": {
            "text": "RESUME",
            "behavior": None,
        },
        "chargingRateController": "PEAK_DEMAND",
        "chargingRateControllerWarning": "GRID_STRESS",
        "chargeRateController": {
            "controllerType": "PEAK_DEMAND",
            "status": "WORKING_CORRECTLY",
            "offlineDeviceName": "Home Monitor",
            "additionalAmps": 10.0,
            "guaranteedAmps": 16.0,
        },
        "nextEvent": {
            "eventType": "STOP",
            "eventTime": "2026-11-01T17:00:00Z",
            "eventActor": "SCHEDULE",
            "subtextParameters": ["Utility"],
        },
    }

    status = EvseControlStatus().from_json_dictionary(camel_payload)
    assert status.device_id == "DEV_CAMEL_1"
    assert status.session_active is True
    assert status.energy_delivered == pytest.approx(15.5)
    assert status.cost == pytest.approx(2.10)
    assert status.active_charging_minutes == 60
    assert status.charging_rate_kw == pytest.approx(9.6)
    assert status.charging_rate_amps == pytest.approx(40.0)
    assert status.offered_amps == pytest.approx(48.0)
    assert status.plug_in == datetime.datetime(2026, 11, 1, 15, 0, tzinfo=tz.tzutc())
    assert status.fault_code == 3
    assert status.charger_status == "CONNECTED_OFF"
    assert status.subtext_type == "MANUALLY_STOPPED"
    assert status.subtext_parameters == ["2026-11-01T16:00:00Z"]
    assert status.button_action == "RESUME"
    assert status.button_behavior is None
    assert status.charging_rate_controller == "PEAK_DEMAND"
    assert status.charging_rate_controller_warning == "GRID_STRESS"
    assert status.charge_rate_controller_type == "PEAK_DEMAND"
    assert status.charge_rate_controller_status == "WORKING_CORRECTLY"
    assert status.charge_rate_controller_offline_device_name == "Home Monitor"
    assert status.charge_rate_controller_additional_amps == pytest.approx(10.0)
    assert status.charge_rate_controller_guaranteed_amps == pytest.approx(16.0)
    assert status.next_event_type == "STOP"
    assert status.next_event_time == datetime.datetime(
        2026, 11, 1, 17, 0, tzinfo=tz.tzutc()
    )
    assert status.next_event_actor == "SCHEDULE"
    assert status.next_event_subtext_parameters == ["Utility"]

    d = status.as_dictionary()
    assert d["fault_code"] == 3
    assert d["button_action"] == "RESUME"
    assert d["subtext_type"] == "MANUALLY_STOPPED"


def test_charger_device_v1_status_derivation_and_pro_control_code() -> None:
    """Validate ChargerDevice pro_control_code dual-schema and status suffix derivation."""
    # 1. Dual schema pro_control_code
    c1 = ChargerDevice().from_json_dictionary({"pro_control_code": "PRO123"})
    assert c1.pro_control_code == "PRO123"
    assert c1.as_dictionary()["pro_control_code"] == "PRO123"
    assert c1.as_dictionary()["proControlCode"] == "PRO123"

    c2 = ChargerDevice().from_json_dictionary({"proControlCode": "PARTNER456"})
    assert c2.pro_control_code == "PARTNER456"

    # 2. charger_on derivation from status
    for on_status in (
        "CHARGING",
        "CONNECTED_ON",
        "DISCONNECTED_ON",
        "STANDBY",
        "READY",
        "CUSTOM_ON",
    ):
        dev = ChargerDevice().from_json_dictionary({"status": on_status})
        assert dev.charger_on is True, f"Failed for {on_status}"

    for off_status in (
        "CONNECTED_OFF",
        "DISCONNECTED_OFF",
        "FAULTING",
        "OFFLINE",
        "DEVICENOTCONNECTED",
        "UNKNOWN_VALUE",
        "CUSTOM_OFF",
    ):
        dev = ChargerDevice().from_json_dictionary({"status": off_status})
        assert dev.charger_on is False, f"Failed for {off_status}"

    # 3. Explicit boolean override
    override_on = ChargerDevice().from_json_dictionary(
        {"status": "CONNECTED_OFF", "charger_on": True}
    )
    assert override_on.charger_on is True

    override_off = ChargerDevice().from_json_dictionary(
        {"status": "CHARGING", "chargerOn": False}
    )
    assert override_off.charger_on is False
