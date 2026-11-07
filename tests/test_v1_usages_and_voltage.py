from __future__ import annotations

import datetime
from typing import Any
from unittest.mock import MagicMock
import pytest

from pyemvue.enums import Scale, Unit
from pyemvue.device import VueDeviceChannelUsage, VueUsageDevice
from pyemvue.pyemvue import PyEmVue


def test_get_device_list_usage_v1_power(usages_v1_json: dict[str, Any]) -> None:
    """Validate get_device_list_usage_v1 fetches and deserializes multi-device power/energy data."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'
    mock_response.json.return_value = usages_v1_json
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    test_instant = datetime.datetime(
        2026, 11, 1, 20, 10, 20, 657000, tzinfo=datetime.timezone.utc
    )
    devices = vue.get_device_list_usage_v1(
        device_gids=[1001, 1002, 1004],
        instant=test_instant,
        scale="SECOND",
        energy_unit="KILOWATT_HOURS",
    )

    # Verify query parameters passed to V1 auth endpoint
    mock_auth.request.assert_called_once()
    method, endpoint = mock_auth.request.call_args[0]
    assert method == "get"
    assert endpoint == "customers/devices/usages"

    kwargs = mock_auth.request.call_args[1]
    params = kwargs["params"]
    assert params["device_gids"] == "1001,1002,1004"
    assert params["instant"] == "2026-11-01T20:10:20.657000Z"
    assert params["scale"] == "SECOND"
    assert params["energy_unit"] == "KILOWATT_HOURS"

    # Verify returned devices
    assert set(devices.keys()) == {1001, 1002, 1004}

    # Verify Home (1001) channels
    dev_1001 = devices[1001]
    assert dev_1001.device_gid == 1001
    assert "1,2,3" in dev_1001.channels
    mains = dev_1001.channels["1,2,3"]
    assert mains.channel_id == "Mains"
    assert mains.usage == pytest.approx(0.0020296568)
    assert mains.raw_usage == pytest.approx(2.0296568)
    assert mains.percentage == 100.0

    # Verify nested subpanel device under Mains
    assert 1002 in mains.nested_devices
    nested_garage = mains.nested_devices[1002]
    assert nested_garage.device_gid == 1002
    assert "1,2,3" in nested_garage.channels
    assert nested_garage.channels["1,2,3"].channel_id == "Mains"
    assert nested_garage.channels["1,2,3"].usage == pytest.approx(0.000591986)

    # Verify split-phase and branch channels on 1001
    assert "Mains_A" in dev_1001.channels
    assert dev_1001.channels["Mains_A"].channel_id == "Mains_A"
    assert dev_1001.channels["Mains_A"].usage == pytest.approx(0.001015)
    assert dev_1001.channels["Mains_B"].channel_id == "Mains_B"
    assert dev_1001.channels["Mains_B"].usage == pytest.approx(0.0010146568)

    assert "1" in dev_1001.channels
    assert dev_1001.channels["1"].channel_id == "Branch_1"
    assert dev_1001.channels["1"].usage == pytest.approx(0.00025)
    assert dev_1001.channels["1"].included_in_total_usage is True

    assert "16" in dev_1001.channels
    assert dev_1001.channels["16"].channel_id == "Branch_16"
    assert dev_1001.channels["16"].usage == pytest.approx(0.00005)

    assert "Balance" in dev_1001.channels
    assert dev_1001.channels["Balance"].channel_id == "Balance"
    assert dev_1001.channels["Balance"].percentage == pytest.approx(44.33)

    assert "TotalUsage" in dev_1001.channels
    assert dev_1001.channels["TotalUsage"].channel_id == "TotalUsage"

    # Verify Kelwood (1004) merged circuit
    dev_1004 = devices[1004]
    assert "Merged_100" in dev_1004.channels
    assert dev_1004.channels["Merged_100"].channel_id == "Merged_100"
    assert dev_1004.channels["Merged_100"].usage == pytest.approx(0.0003)
    assert dev_1004.channels["Merged_100"].percentage == pytest.approx(20.0)


def test_get_device_list_usage_v1_voltage(usages_v1_json: dict[str, Any]) -> None:
    """Validate get_device_list_usage_v1 parses split-phase voltages correctly."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"dummy": true}'
    mock_response.json.return_value = usages_v1_json["voltage"]
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    # Test passing Unit.VOLTS enum
    devices = vue.get_device_list_usage_v1(
        device_gids=[1001, 1002, 1004],
        energy_unit=Unit.VOLTS,
    )

    # Verify parameter formatting for Unit.VOLTS -> VOLTAGE
    mock_auth.request.assert_called_once()
    kwargs = mock_auth.request.call_args[1]
    assert kwargs["params"]["energy_unit"] == "VOLTAGE"

    # Verify Home (1001) split-phase voltages
    home = devices[1001]
    assert home.channels["1,2,3"].usage == pytest.approx(120.75)
    assert home.channels_by_id["Mains"].usage == pytest.approx(120.75)
    assert home.channels["Mains_A"].usage == pytest.approx(120.4)
    assert home.channels["Mains_A"].channel_id == "Mains_A"
    assert home.channels["Mains_A"].raw_usage == pytest.approx(120.4)

    assert home.channels["Mains_B"].usage == pytest.approx(121.1)
    assert home.channels["Mains_B"].channel_id == "Mains_B"
    assert home.channels["Mains_B"].raw_usage == pytest.approx(121.1)

    assert home.channels["Mains_C"].usage == pytest.approx(0.0)

    # Verify Garage (1002) and Kelwood (1004) voltages
    assert devices[1002].channels["Mains_A"].usage == pytest.approx(120.2)
    assert devices[1002].channels["Mains_B"].usage == pytest.approx(120.8)
    assert devices[1004].channels["Mains_A"].usage == pytest.approx(120.9)
    assert devices[1004].channels["Mains_B"].usage == pytest.approx(121.5)


def test_vue_device_channel_usage_dual_schema() -> None:
    """Validate VueDeviceChannelUsage deserializes both legacy and V1 schemas."""
    # 1. Legacy camelCase schema
    legacy_json = {
        "deviceGid": 1001,
        "channelNum": "1,2,3",
        "name": "Main",
        "usage": 2.54,
        "percentage": 100.0,
        "nestedDevices": [
            {
                "deviceGid": 1002,
                "channelUsages": [
                    {
                        "deviceGid": 1002,
                        "channelNum": "1,2,3",
                        "name": "Subpanel Main",
                        "usage": 0.85,
                        "percentage": 33.46,
                    }
                ],
            }
        ],
    }
    ts = datetime.datetime(2026, 11, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    ch_legacy = VueDeviceChannelUsage(timestamp=ts).from_json_dictionary(legacy_json)
    assert ch_legacy.device_gid == 1001
    assert ch_legacy.channel_num == "1,2,3"
    assert ch_legacy.name == "Main"
    assert ch_legacy.usage == 2.54
    assert ch_legacy.percentage == 100.0
    assert ch_legacy.raw_usage is None
    assert ch_legacy.included_in_total_usage is None
    assert 1002 in ch_legacy.nested_devices
    assert ch_legacy.nested_devices[1002].device_gid == 1002
    assert ch_legacy.nested_devices[1002].channels["1,2,3"].usage == 0.85

    # 2. V1 snake_case schema
    v1_json = {
        "device_gid": 1001,
        "channel_id": "Branch_5",
        "display_name": "Heat Pump",
        "usage": 0.45,
        "raw_usage": 450.0,
        "percentage": 17.7,
        "included_in_total_usage": True,
        "nested_devices": [],
    }
    ch_v1 = VueDeviceChannelUsage(timestamp=ts).from_json_dictionary(v1_json)
    assert ch_v1.device_gid == 1001
    assert ch_v1.channel_id == "Branch_5"
    assert ch_v1.channel_num == "5"
    assert ch_v1.name == "Heat Pump"
    assert ch_v1.usage == 0.45
    assert ch_v1.raw_usage == 450.0
    assert ch_v1.percentage == 17.7
    assert ch_v1.included_in_total_usage is True
    assert ch_v1.nested_devices == {}

    # Check as_dictionary preserves all fields
    d = ch_v1.as_dictionary()
    assert d["deviceGid"] == 1001
    assert d["channelNum"] == "5"
    assert d["channelId"] == "Branch_5"
    assert d["usage"] == 0.45
    assert d["raw_usage"] == 450.0
    assert d["percentage"] == 17.7
    assert d["included_in_total_usage"] is True


def test_channel_normalization_and_merged_circuits() -> None:
    """Validate normalization of channel_num from channel_id across all variants."""
    test_cases = [
        ("Mains", "1,2,3"),
        ("Mains_A", "Mains_A"),
        ("Mains_B", "Mains_B"),
        ("Mains_C", "Mains_C"),
        ("Branch_1", "1"),
        ("Branch_7", "7"),
        ("Branch_16", "16"),
        ("Merged_100", "Merged_100"),
        ("Balance", "Balance"),
        ("TotalUsage", "TotalUsage"),
    ]

    for channel_id, expected_num in test_cases:
        ch = VueDeviceChannelUsage().from_json_dictionary({"channel_id": channel_id})
        assert ch.channel_id == channel_id
        assert ch.channel_num == expected_num, f"Failed for {channel_id}"

    # Verify that explicit channel_num overrides normalization
    explicit_ch = VueDeviceChannelUsage().from_json_dictionary(
        {"channel_id": "Merged_100", "channel_num": "97"}
    )
    assert explicit_ch.channel_id == "Merged_100"
    assert explicit_ch.channel_num == "97"


def test_channels_by_id_lookup() -> None:
    """Validate VueUsageDevice.channels_by_id property indexing."""
    dev_json = {
        "device_gid": 1001,
        "channel_usages": [
            {"channel_id": "Mains", "usage": 1.0},
            {"channel_id": "Mains_A", "usage": 0.5},
            {"channel_id": "Mains_B", "usage": 0.5},
            {"channel_id": "Branch_1", "usage": 0.2},
            {"channel_id": "Merged_100", "usage": 0.1},
        ],
    }
    dev = VueUsageDevice().from_json_dictionary(dev_json)

    # Standard channel_num indexing
    assert "1,2,3" in dev.channels
    assert "Mains_A" in dev.channels
    assert "Mains_B" in dev.channels
    assert "1" in dev.channels
    assert "Merged_100" in dev.channels

    # channels_by_id property
    by_id = dev.channels_by_id
    assert "Mains" in by_id
    assert by_id["Mains"].usage == 1.0
    assert by_id["Mains_A"].usage == 0.5
    assert by_id["Mains_B"].usage == 0.5
    assert by_id["Branch_1"].usage == 0.2
    assert by_id["Merged_100"].usage == 0.1


def test_get_device_list_usage_v1_unauthenticated() -> None:
    """Validate get_device_list_usage_v1 raises ValueError when not authenticated."""
    vue = PyEmVue()
    with pytest.raises(ValueError, match="Not authenticated"):
        vue.get_device_list_usage_v1(device_gids=[1001])


def test_get_device_list_usage_v1_scale_and_energy_unit_variants() -> None:
    """Validate that Enum values for Scale and Unit are properly translated to strings."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"instant": "2026-11-01T20:10:20Z", "device_usages": []}'
    mock_response.json.return_value = {
        "instant": "2026-11-01T20:10:20Z",
        "device_usages": [],
    }
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    # Test with Scale.SECOND and Unit.KWH
    vue.get_device_list_usage_v1(
        device_gids=[1001],
        scale=Scale.SECOND,
        energy_unit=Unit.KWH,
    )
    params = mock_auth.request.call_args[1]["params"]
    assert params["scale"] == "SECOND"
    assert params["energy_unit"] == "KILOWATT_HOURS"
    assert params["device_gids"] == "1001"

    # Test with single int GID
    vue.get_device_list_usage_v1(
        device_gids=1004,
        scale="MINUTE",
        energy_unit="VOLTAGE",
    )
    params = mock_auth.request.call_args[1]["params"]
    assert params["scale"] == "MINUTE"
    assert params["energy_unit"] == "VOLTAGE"
    assert params["device_gids"] == "1004"
