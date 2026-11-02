from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from pyemvue.device import (
    EnergyMonitorExcessGeneration,
    ExcessGenerationLoad,
    ExcessGenerationMonitor,
    ExcessGenerationMonitors,
)
from pyemvue.pyemvue import PyEmVue


def test_excess_generation_monitor_direct() -> None:
    """Validate ExcessGenerationMonitor direct instantiation and serialization."""
    mon = ExcessGenerationMonitor(device_id="DEV_123", enabled=True)
    assert mon.device_id == "DEV_123"
    assert mon.enabled is True
    assert mon.as_dictionary() == {"device_id": "DEV_123", "enabled": True}

    roundtrip = ExcessGenerationMonitor().from_json_dictionary(
        {"deviceId": "DEV_456", "enabled": False}
    )
    assert roundtrip.device_id == "DEV_456"
    assert roundtrip.enabled is False


def test_excess_generation_monitors_deserialization(
    excess_generation_v1_json: dict[str, Any],
) -> None:
    """Validate ExcessGenerationMonitors deserializes monitors list and unavailable monitors."""
    raw = excess_generation_v1_json["monitors_response"]
    monitors_data = ExcessGenerationMonitors().from_json_dictionary(raw)

    assert len(monitors_data.monitors) == 2
    assert monitors_data.monitors[0].device_id == "A2237A0000000000000001"
    assert monitors_data.monitors[0].enabled is False
    assert monitors_data.monitors[1].device_id == "F2410A0000000000000002"
    assert monitors_data.monitors[1].enabled is True
    assert monitors_data.unavailable_monitors == ["A2304A0000000000000004"]

    # Roundtrip serialization
    as_dict = monitors_data.as_dictionary()
    assert as_dict == raw
    roundtrip = ExcessGenerationMonitors().from_json_dictionary(as_dict)
    assert len(roundtrip.monitors) == 2
    assert roundtrip.monitors[0].device_id == monitors_data.monitors[0].device_id
    assert roundtrip.monitors[0].enabled == monitors_data.monitors[0].enabled
    assert roundtrip.monitors[1].device_id == monitors_data.monitors[1].device_id
    assert roundtrip.monitors[1].enabled == monitors_data.monitors[1].enabled
    assert roundtrip.unavailable_monitors == monitors_data.unavailable_monitors


def test_energy_monitor_excess_generation_without_window(
    excess_generation_v1_json: dict[str, Any],
) -> None:
    """Validate EnergyMonitorExcessGeneration without solar_window."""
    raw = excess_generation_v1_json["energy_monitor_without_window"]
    config = EnergyMonitorExcessGeneration().from_json_dictionary(raw)

    assert config.device_id == "F2410A0000000000000002"
    assert len(config.loads) == 1
    assert config.loads[0].load_gid == 138878
    assert config.loads[0].enabled is True
    assert config.solar_window is None
    assert config.sunrise == "2026-11-01T14:29:49Z"
    assert config.sunset == "2026-11-02T00:10:38Z"

    # Roundtrip check
    as_dict = config.as_dictionary()
    assert as_dict == raw
    roundtrip = EnergyMonitorExcessGeneration().from_json_dictionary(as_dict)
    assert roundtrip.device_id == config.device_id
    assert len(roundtrip.loads) == len(config.loads)
    assert roundtrip.loads[0].load_gid == config.loads[0].load_gid
    assert roundtrip.loads[0].enabled == config.loads[0].enabled
    assert roundtrip.solar_window is None
    assert roundtrip.sunrise == config.sunrise
    assert roundtrip.sunset == config.sunset


def test_energy_monitor_excess_generation_with_window(
    excess_generation_v1_json: dict[str, Any],
) -> None:
    """Validate EnergyMonitorExcessGeneration with custom solar_window."""
    raw = excess_generation_v1_json["energy_monitor_with_window"]
    config = EnergyMonitorExcessGeneration().from_json_dictionary(raw)

    assert config.device_id == "F2410A0000000000000002"
    assert len(config.loads) == 1
    assert config.loads[0].load_gid == 138878
    assert config.loads[0].enabled is True
    assert config.solar_window is not None
    assert config.solar_window["start"]["anchor"] == "SUNRISE"
    assert config.solar_window["start"]["offset_seconds"] == 3600
    assert config.solar_window["end"]["anchor"] == "SUNSET"
    assert config.solar_window["end"]["offset_seconds"] == -3600
    assert config.sunrise == "2026-11-01T14:29:49Z"
    assert config.sunset == "2026-11-02T00:10:38Z"

    # Roundtrip check
    as_dict = config.as_dictionary()
    assert as_dict == raw
    roundtrip = EnergyMonitorExcessGeneration().from_json_dictionary(as_dict)
    assert roundtrip.solar_window == config.solar_window


def test_excess_generation_models_camelcase_compatibility() -> None:
    """Validate models gracefully handle camelCase API response keys."""
    mon_raw = {
        "monitors": [{"deviceId": "MONITOR_1", "enabled": True}],
        "unavailableMonitors": ["MONITOR_2"],
    }
    monitors = ExcessGenerationMonitors().from_json_dictionary(mon_raw)
    assert len(monitors.monitors) == 1
    assert monitors.monitors[0].device_id == "MONITOR_1"
    assert monitors.monitors[0].enabled is True
    assert monitors.unavailable_monitors == ["MONITOR_2"]

    load_raw = {"loadGid": 9999, "enabled": False}
    load = ExcessGenerationLoad().from_json_dictionary(load_raw)
    assert load.load_gid == 9999
    assert load.enabled is False

    em_raw = {
        "deviceId": "MONITOR_1",
        "loads": [{"loadGid": 9999, "enabled": True}],
        "solarWindow": {"start": {"anchor": "SUNRISE", "offset_seconds": 0}},
        "sunrise": "2026-11-01T12:00:00Z",
        "sunset": "2026-11-01T22:00:00Z",
    }
    em = EnergyMonitorExcessGeneration().from_json_dictionary(em_raw)
    assert em.device_id == "MONITOR_1"
    assert len(em.loads) == 1
    assert em.loads[0].load_gid == 9999
    assert em.loads[0].enabled is True
    assert em.solar_window == {"start": {"anchor": "SUNRISE", "offset_seconds": 0}}


def test_get_excess_generation_monitors(
    excess_generation_v1_json: dict[str, Any],
) -> None:
    """Validate get_excess_generation_monitors queries GET customers/excess-generation."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'
    mock_response.json.return_value = excess_generation_v1_json["monitors_response"]
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    result = vue.get_excess_generation_monitors()
    assert result is not None
    assert len(result.monitors) == 2
    assert result.monitors[0].device_id == "A2237A0000000000000001"
    assert result.unavailable_monitors == ["A2304A0000000000000004"]

    mock_auth.request.assert_called_with("get", "customers/excess-generation")


def test_get_excess_generation_monitors_empty_response() -> None:
    """Validate get_excess_generation_monitors handles empty response body."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    assert vue.get_excess_generation_monitors() is None


def test_get_excess_generation(excess_generation_v1_json: dict[str, Any]) -> None:
    """Validate get_excess_generation queries GET customers/energy-monitor/excess-generation?device_id=..."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'
    mock_response.json.return_value = excess_generation_v1_json[
        "energy_monitor_with_window"
    ]
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    result = vue.get_excess_generation("F2410A0000000000000002")
    assert result is not None
    assert result.device_id == "F2410A0000000000000002"
    assert len(result.loads) == 1
    assert result.solar_window is not None

    mock_auth.request.assert_called_with(
        "get",
        "customers/energy-monitor/excess-generation?device_id=F2410A0000000000000002",
    )


def test_get_excess_generation_empty_response() -> None:
    """Validate get_excess_generation handles empty response body."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    assert vue.get_excess_generation("F2410A0000000000000002") is None


def test_set_excess_generation_with_model_objects() -> None:
    """Validate set_excess_generation serializes ExcessGenerationLoad instances in POST payload."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    loads = [ExcessGenerationLoad(load_gid=138878, enabled=True)]
    solar_window = {
        "start": {"anchor": "SUNRISE", "offset_seconds": 3600},
        "end": {"anchor": "SUNSET", "offset_seconds": -3600},
    }

    result = vue.set_excess_generation(
        device_id="F2410A0000000000000002",
        loads=loads,
        solar_window=solar_window,
        sunrise="2026-11-01T14:29:49Z",
        sunset="2026-11-02T00:10:38Z",
    )
    assert result is True

    mock_auth.request.assert_called_with(
        "post",
        "customers/energy-monitor/excess-generation",
        json={
            "device_id": "F2410A0000000000000002",
            "loads": [{"load_gid": 138878, "enabled": True}],
            "solar_window": solar_window,
            "sunrise": "2026-11-01T14:29:49Z",
            "sunset": "2026-11-02T00:10:38Z",
        },
    )


def test_set_excess_generation_with_raw_dicts() -> None:
    """Validate set_excess_generation accepts raw dict loads."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    loads = [{"load_gid": 138878, "enabled": False}]
    result = vue.set_excess_generation(
        device_id="F2410A0000000000000002",
        loads=loads,
    )
    assert result is True

    mock_auth.request.assert_called_with(
        "post",
        "customers/energy-monitor/excess-generation",
        json={
            "device_id": "F2410A0000000000000002",
            "loads": [{"load_gid": 138878, "enabled": False}],
            "solar_window": None,
            "sunrise": None,
            "sunset": None,
        },
    )


def test_post_evse_control_full_power_override() -> None:
    """Validate post_evse_control dispatches CHARGE_AT_FULL_POWER command via POST."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    result = vue.post_evse_control(
        device_id="D2301A0000000000000003", command="CHARGE_AT_FULL_POWER"
    )
    assert result is True

    mock_auth.request.assert_called_with(
        "post",
        "customers/evse/control",
        json={
            "device_id": "D2301A0000000000000003",
            "command": "CHARGE_AT_FULL_POWER",
        },
    )


def test_set_evse_state_backward_compatibility() -> None:
    """Validate set_evse_state delegates to post_evse_control with TURN_ON and TURN_OFF."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    assert vue.set_evse_state("D2301A0000000000000003", enabled=True) is True
    mock_auth.request.assert_called_with(
        "post",
        "customers/evse/control",
        json={"device_id": "D2301A0000000000000003", "command": "TURN_ON"},
    )

    assert vue.set_evse_state("D2301A0000000000000003", enabled=False) is True
    mock_auth.request.assert_called_with(
        "post",
        "customers/evse/control",
        json={"device_id": "D2301A0000000000000003", "command": "TURN_OFF"},
    )
