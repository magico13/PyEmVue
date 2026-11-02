from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from pyemvue.auth import Auth, SimulatedAuth
from pyemvue.device import (
    ChannelDevice,
    ChargerDevice,
    VueDevice,
    VueDeviceChannel,
    VueSite,
)
from pyemvue.pyemvue import PyEmVue


def test_v1_device_and_channel_parsing(devices_v1_json: dict[str, Any]) -> None:
    """Validate that VueDevice correctly deserializes V1 snake_case device payloads."""
    raw_devices = devices_v1_json["devices"]
    assert len(raw_devices) == 4

    dev_by_id = {
        d["device_id"]: VueDevice().from_json_dictionary(d) for d in raw_devices
    }

    # Kelwood (standalone Vue 2)
    kelwood = dev_by_id["A2304A0000000000000004"]
    assert kelwood.device_gid == 1004
    assert kelwood.device_id == "A2304A0000000000000004"
    assert kelwood.model == "VUE002"
    assert kelwood.firmware == "Vue2-823"
    assert kelwood.device_type == "MONITOR"
    assert kelwood.display_name == "Kelwood"
    assert kelwood.parent_device_id is None
    assert kelwood.site_gid is None
    assert kelwood.time_zone == "America/Denver"
    assert kelwood.usage_cent_per_kw_hour == 11.75
    assert kelwood.latitude == 39.7392
    assert kelwood.longitude == -104.9903

    # Home (root Vue 3)
    home = dev_by_id["F2410A0000000000000001"]
    assert home.device_gid == 1001
    assert home.device_id == "F2410A0000000000000001"
    assert home.model == "VUE003"
    assert home.firmware == "Vue3-823"
    assert home.parent_device_id is None

    # Garage (child Vue 2 under Home)
    garage = dev_by_id["A2237A0000000000000002"]
    assert garage.device_gid == 1002
    assert garage.device_id == "A2237A0000000000000002"
    assert garage.parent_device_id == "F2410A0000000000000001"
    assert garage.parent_channel_id == "Mains"

    # EV Charger (grandchild EVSE under Garage)
    evse = dev_by_id["D2301A0000000000000003"]
    assert evse.device_gid == 1003
    assert evse.device_id == "D2301A0000000000000003"
    assert evse.model == "VVDN01"
    assert evse.device_type == "EV_CHARGER"
    assert evse.parent_device_id == "A2237A0000000000000002"
    assert evse.parent_channel_id == "Mains"
    assert evse.ev_charger is not None
    assert isinstance(evse.ev_charger, ChargerDevice)
    assert evse.device_name != ""
    assert evse.device_name == "EV Charger"
    assert evse.ev_charger.device_gid == 1003
    assert evse.ev_charger.load_gid == 9001
    assert evse.ev_charger.charger_on is True
    assert evse.ev_charger.max_charging_rate == 48


def test_has_data_channel_pruning(devices_v1_json: dict[str, Any]) -> None:
    """Validate that channels correctly parse the has_data boolean attribute."""
    raw_devices = devices_v1_json["devices"]
    home_raw = next(
        d for d in raw_devices if d["device_id"] == "F2410A0000000000000001"
    )
    home = VueDevice().from_json_dictionary(home_raw)

    channels_by_id = {ch.channel_id: ch for ch in home.channels}

    # Mains and populated CTs have has_data: true
    assert channels_by_id["Mains"].has_data is True
    assert channels_by_id["Mains"].channel_num == "1,2,3"
    assert channels_by_id["Branch_1"].has_data is True
    assert channels_by_id["Branch_1"].name == "Solar main 1"
    assert channels_by_id["Branch_1"].channel_num == "1"

    assert channels_by_id["Branch_5"].has_data is True
    assert channels_by_id["Branch_5"].name == "Heat pump basement"
    assert channels_by_id["Branch_5"].channel_num == "5"

    # Mains_C is unpopulated in split phase (has_data: false)
    assert channels_by_id["Mains_C"].has_data is False

    # Standalone/Subpanel with unpopulated CT branch ports (e.g. Kelwood)
    kelwood_raw = next(
        d for d in raw_devices if d["device_id"] == "A2304A0000000000000004"
    )
    kelwood = VueDevice().from_json_dictionary(kelwood_raw)
    kelwood_channels_by_id = {ch.channel_id: ch for ch in kelwood.channels}

    assert kelwood_channels_by_id["Branch_1"].has_data is True
    assert kelwood_channels_by_id["Branch_6"].has_data is False
    assert kelwood_channels_by_id["Branch_16"].has_data is False

    # Confirm pruning capability: active vs empty CTs
    active_channels = [ch for ch in kelwood.channels if ch.has_data]
    empty_channels = [ch for ch in kelwood.channels if not ch.has_data]
    assert len(active_channels) == 9  # Mains, Mains_A, Mains_B + Branches 1..5
    assert len(empty_channels) == 12  # Mains_C + Branches 6..16


def test_get_devices_v1_tree_linking(devices_v1_json: dict[str, Any]) -> None:
    """Validate that get_devices_v1() constructs the parent-child hierarchy tree."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "non-empty"
    mock_response.json.return_value = devices_v1_json
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    devices = vue.get_devices_v1()
    assert len(devices) == 4

    dev_by_id = {d.device_id: d for d in devices}
    home = dev_by_id["F2410A0000000000000001"]
    garage = dev_by_id["A2237A0000000000000002"]
    evse = dev_by_id["D2301A0000000000000003"]
    kelwood = dev_by_id["A2304A0000000000000004"]

    # Home has Garage as child
    assert len(home.children) == 1
    assert home.children[0] is garage
    assert garage.parent_device_gid == home.device_gid
    assert garage.parent_device_id == home.device_id
    assert garage.parent_channel_id == "Mains"
    assert garage.parent_channel_num == "1,2,3"

    # Garage has EV Charger as child
    assert len(garage.children) == 1
    assert garage.children[0] is evse
    assert evse.parent_device_gid == garage.device_gid
    assert evse.parent_device_id == garage.device_id
    assert evse.parent_channel_id == "Mains"
    assert evse.parent_channel_num == "1,2,3"

    # Leaf and standalone devices have empty children
    assert len(evse.children) == 0
    assert len(kelwood.children) == 0
    assert kelwood.parent_device_id is None


def test_get_devices_v1_include_channels_false(
    devices_v1_json: dict[str, Any],
) -> None:
    """Validate that include_channels=False excludes channel data while preserving hierarchy."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "non-empty"
    mock_response.json.return_value = devices_v1_json
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    devices = vue.get_devices_v1(include_channels=False)
    assert len(devices) == 4
    for d in devices:
        assert len(d.channels) == 0

    dev_by_id = {d.device_id: d for d in devices}
    home = dev_by_id["F2410A0000000000000001"]
    garage = dev_by_id["A2237A0000000000000002"]
    assert len(home.children) == 1
    assert home.children[0] is garage
    assert garage.parent_device_gid == home.device_gid
    assert garage.parent_channel_id == "Mains"
    assert garage.parent_channel_num == "1,2,3"


def test_sites_v1_parsing(sites_v1_json: dict[str, Any]) -> None:
    """Validate that VueSite correctly models customer site properties."""
    raw_sites = sites_v1_json["sites"]
    assert len(raw_sites) == 2

    sites = [VueSite().from_json_dictionary(s) for s in raw_sites]

    site1 = sites[0]
    assert site1.site_gid == 5001
    assert site1.display_name == "Primary Residence"
    assert site1.latitude == 39.7392
    assert site1.longitude == -104.9903
    assert site1.time_zone == "America/Denver"
    assert site1.device_ids == [
        "D2301A0000000000000003",
        "A2237A0000000000000002",
        "F2410A0000000000000001",
    ]
    assert site1.billing_cycle_start_day == 1
    assert site1.usage_cents_per_kwh == 0.12
    assert site1.buyback_rate_cents_per_kwh is None
    assert site1.net_metering is None
    assert site1.service_address is not None
    assert site1.service_address["city"] == "Denver"

    site2 = sites[1]
    assert site2.site_gid == 5002
    assert site2.display_name == "Secondary Property"
    assert site2.device_ids == ["A2304A0000000000000004"]


def test_get_sites_api_call(sites_v1_json: dict[str, Any]) -> None:
    """Validate PyEmVue.get_sites() method invocation."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "non-empty"
    mock_response.json.return_value = sites_v1_json
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    sites = vue.get_sites()
    assert len(sites) == 2
    assert sites[0].site_gid == 5001
    assert sites[1].site_gid == 5002
    mock_auth.request.assert_called_once_with("get", "customers/sites")


def test_channels_v1_parsing(channels_v1_json: list[dict[str, Any]]) -> None:
    """Validate ChannelDevice and Channel nested hierarchy models."""
    assert len(channels_v1_json) == 2

    channel_devices = [
        ChannelDevice().from_json_dictionary(d) for d in channels_v1_json
    ]
    assert len(channel_devices) == 2

    # Device 1001 (Home Vue 3)
    home_dev = next(d for d in channel_devices if d.device_gid == 1001)
    assert home_dev.device_id == "F2410A0000000000000001"
    assert len(home_dev.channels) == 19

    # Find the channel containing nested devices
    nested_subpanel = next(ch for ch in home_dev.channels if len(ch.nested_devices) > 0)
    assert len(nested_subpanel.nested_devices) == 1

    garage_dev = nested_subpanel.nested_devices[0]
    assert garage_dev.device_gid == 270955
    assert garage_dev.device_id == "A2237A05B5349454FAA9B0"

    # Garage should contain EV Charger as nested device
    evse_channel = next(ch for ch in garage_dev.channels if len(ch.nested_devices) > 0)
    assert len(evse_channel.nested_devices) == 1
    evse_dev = evse_channel.nested_devices[0]
    assert evse_dev.device_gid == 242715
    assert evse_dev.device_id == "D2301A00090CB8152E3B78"
    assert evse_dev.channels[0].sub_type == "EV Charger"


def test_get_channels_api_call(channels_v1_json: list[dict[str, Any]]) -> None:
    """Validate PyEmVue.get_channels() method invocation."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "non-empty"
    mock_response.json.return_value = channels_v1_json
    mock_auth.request.return_value = mock_response
    vue.auth_v1 = mock_auth

    channels = vue.get_channels()
    assert len(channels) == 2
    mock_auth.request.assert_called_once_with("get", "customers/devices/channels")


def test_auth_bearer_header() -> None:
    """Validate that Auth sets Authorization: Bearer when as_bearer=True, and authtoken when False."""
    dummy_tokens = {
        "access_token": "dummy-access",
        "id_token": "my-mock-id-token",
        "refresh_token": "dummy-refresh",
    }

    # Bearer auth (V1 API)
    auth_bearer = Auth(host="https://api.emporiaenergy.com/v1", as_bearer=True)
    auth_bearer.tokens = dummy_tokens

    with patch("pyemvue.auth.requests.request") as mock_req:
        mock_req.return_value = MagicMock(status_code=200)
        auth_bearer._do_request("get", "customers/devices")
        mock_req.assert_called_once()
        headers = mock_req.call_args[1]["headers"]
        assert headers.get("Authorization") == "Bearer my-mock-id-token"
        assert "authtoken" not in headers

    # Legacy authtoken header
    auth_legacy = Auth(host="https://api.emporiaenergy.com", as_bearer=False)
    auth_legacy.tokens = dummy_tokens

    with patch("pyemvue.auth.requests.request") as mock_req:
        mock_req.return_value = MagicMock(status_code=200)
        auth_legacy._do_request("get", "customers/devices")
        mock_req.assert_called_once()
        headers = mock_req.call_args[1]["headers"]
        assert headers.get("authtoken") == "my-mock-id-token"
        assert "Authorization" not in headers


def test_login_simulator_v1_setup() -> None:
    """Validate login_simulator creates both legacy and V1 SimulatedAuth instances."""
    vue = PyEmVue()
    with patch.object(vue, "get_customer_details") as mock_cust:
        mock_cust.return_value = MagicMock()
        success = vue.login_simulator(
            "https://simulator.local", "TestUser@Example.Com", "password"
        )
        assert success is True
        assert vue.username == "testuser@example.com"
        assert isinstance(vue.auth, SimulatedAuth)
        assert vue.auth.as_bearer is False
        assert vue.auth.host == "https://simulator.local"
        assert isinstance(vue.auth_v1, SimulatedAuth)
        assert vue.auth_v1.as_bearer is True
        assert vue.auth_v1.host == "https://simulator.local/v1"


def test_token_synchronization_between_auth_instances() -> None:
    """Validate _store_tokens updates tokens on both auth and auth_v1."""
    vue = PyEmVue()
    auth_v0 = Auth(host="https://api.emporiaenergy.com", as_bearer=False)
    auth_v1 = Auth(host="https://api.emporiaenergy.com/v1", as_bearer=True)
    vue.auth = auth_v0
    vue.auth_v1 = auth_v1

    new_tokens = {"id_token": "token-123", "access_token": "access-456"}
    vue._store_tokens(new_tokens)

    assert auth_v0.tokens["id_token"] == "token-123"
    assert auth_v1.tokens["id_token"] == "token-123"


def test_dual_schema_channel_normalization() -> None:
    """Validate VueDeviceChannel parses both camelCase and snake_case and normalizes channel numbers."""
    # V1 snake_case Branch_1
    ch1 = VueDeviceChannel().from_json_dictionary(
        {
            "channel_id": "Branch_1",
            "channel_classification": "FIFTY_AMP",
            "has_data": True,
        }
    )
    assert ch1.channel_id == "Branch_1"
    assert ch1.channel_num == "1"
    assert ch1.type == "FIFTY_AMP"
    assert ch1.has_data is True

    # V1 snake_case Mains
    ch_mains = VueDeviceChannel().from_json_dictionary(
        {
            "channel_id": "Mains",
            "channel_classification": "MAIN",
            "has_data": True,
        }
    )
    assert ch_mains.channel_id == "Mains"
    assert ch_mains.channel_num == "1,2,3"
    assert ch_mains.has_data is True

    # Legacy camelCase
    ch_legacy = VueDeviceChannel().from_json_dictionary(
        {
            "channelNum": "5",
            "name": "Dryer",
            "channelMultiplier": 1.0,
            "channelTypeGid": 2,
            "type": "FiftyAmp",
        }
    )
    assert ch_legacy.channel_num == "5"
    assert ch_legacy.name == "Dryer"
    assert ch_legacy.channel_multiplier == 1.0
    assert ch_legacy.type == "FiftyAmp"
    assert ch_legacy.has_data is None


def test_v1_evse_device_model_parsing_and_fallback_naming() -> None:
    """Validate DEF-PY-1: V1 EVSE device parsing, ChargerDevice attachment, and display naming fallback."""
    # 1. Device with category EVSE and display_name
    evse_payload = {
        "device_id": "D2301A0000000000000003",
        "device_gid": 1003,
        "load_gid": 9001,
        "model": "VVDN01",
        "category": "EVSE",
        "display_name": "Garage EVSE",
        "breaker_pin": "1234",
    }
    dev = VueDevice().from_json_dictionary(evse_payload)
    assert dev.ev_charger is not None
    assert isinstance(dev.ev_charger, ChargerDevice)
    assert dev.ev_charger.device_gid == 1003
    assert dev.ev_charger.load_gid == 9001
    assert dev.ev_charger.charger_on is True
    assert dev.ev_charger.max_charging_rate == 48
    assert dev.device_name == "Garage EVSE"
    assert dev.display_name == "Garage EVSE"

    # 2. Device with model VVDN01 without display_name or deviceName
    unnamed_evse = {
        "device_id": "D2301A0000000000000099",
        "device_gid": 1099,
        "model": "VVDN01",
    }
    dev2 = VueDevice().from_json_dictionary(unnamed_evse)
    assert dev2.ev_charger is not None
    assert dev2.device_name == "EV Charger"
    assert dev2.display_name == "EV Charger"

    # 3. Explicit charger_on=False and max_charging_rate override
    off_evse = {
        "device_id": "D2301A0000000000000055",
        "device_gid": 1055,
        "model": "VVDN01",
        "category": "EVSE",
        "charger_on": False,
        "max_charging_rate": 40,
    }
    dev3 = VueDevice().from_json_dictionary(off_evse)
    assert dev3.ev_charger is not None
    assert dev3.ev_charger.charger_on is False
    assert dev3.ev_charger.max_charging_rate == 40

    # 4. Charger status standby implies charger_on True
    standby_evse = {
        "device_id": "D2301A0000000000000066",
        "device_gid": 1066,
        "model": "VVDN01",
        "charger_status": "STANDBY",
    }
    dev4 = VueDevice().from_json_dictionary(standby_evse)
    assert dev4.ev_charger is not None
    assert dev4.ev_charger.charger_on is True
    assert dev4.ev_charger.status == "STANDBY"
