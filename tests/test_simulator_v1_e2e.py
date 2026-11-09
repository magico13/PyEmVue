from __future__ import annotations

import datetime
from typing import Generator
from unittest.mock import patch
from urllib.parse import urlparse
import pytest
import requests
from fastapi.testclient import TestClient

from pyemvue.enums import Unit
from pyemvue.device import ChargerDevice, OutletDevice, VueDevice
from pyemvue.pyemvue import PyEmVue
from simulator.main import app


@pytest.fixture
def simulated_vue() -> Generator[PyEmVue, None, None]:
    """Provide a PyEmVue client connected to the FastAPI simulator via TestClient."""
    client = TestClient(app)

    def forward_to_client(method: str, url: str, **kwargs) -> requests.Response:
        parsed = urlparse(url)
        path = parsed.path
        if parsed.query:
            path += "?" + parsed.query
        json_data = kwargs.get("json")
        headers = kwargs.get("headers")
        params = kwargs.get("params")
        h_resp = client.request(
            method, path, json=json_data, headers=headers, params=params
        )
        r_resp = requests.Response()
        r_resp.status_code = h_resp.status_code
        r_resp._content = h_resp.content
        r_resp.headers = requests.structures.CaseInsensitiveDict(h_resp.headers)
        r_resp.url = url
        return r_resp

    with patch("requests.request", side_effect=forward_to_client):
        vue = PyEmVue()
        assert vue.login_simulator(
            "http://simulator.local", "simulator@simulator.sim", "password"
        ) is True
        yield vue


def test_simulator_v1_login_and_customer(simulated_vue: PyEmVue) -> None:
    """Validate customer details are retrieved and populated upon simulator login."""
    assert simulated_vue.customer is not None
    assert simulated_vue.customer.customer_gid == 1234
    assert simulated_vue.customer.email == "simulator@simulator.sim"
    assert simulated_vue.customer.first_name == "Sim"
    assert simulated_vue.customer.last_name == "Ulator"


def test_simulator_v1_get_devices_hierarchy_and_pruning(
    simulated_vue: PyEmVue,
) -> None:
    """Validate get_devices_v1 retrieves multi-device topology, builds tree hierarchy, and parses CT data."""
    devices = simulated_vue.get_devices_v1()
    assert len(devices) == 6

    dev_by_gid = {d.device_gid: d for d in devices}
    home = dev_by_gid[1000]
    plug1 = dev_by_gid[1001]
    plug2 = dev_by_gid[1002]
    plug3 = dev_by_gid[1003]
    plug4 = dev_by_gid[1004]
    evse = dev_by_gid[1005]

    # Verify root monitor hierarchy
    assert home.device_name == "Home"
    assert home.model == "VUE002"
    assert home.parent_device_id is None
    assert len(home.children) == 5
    assert set(home.children) == {plug1, plug2, plug3, plug4, evse}

    # Verify child devices parent linkage
    for child in (plug1, plug2, plug3, plug4, evse):
        assert child.parent_device_gid == 1000
        assert child.parent_device_id == home.device_id

    # Verify parent channels
    assert plug1.parent_channel_num == "1"
    assert plug1.parent_channel_id == "Branch_1"
    assert plug4.parent_channel_num == "1,2,3"
    assert plug4.parent_channel_id == "Mains"
    assert evse.parent_channel_num == "1,2,3"
    assert evse.parent_channel_id == "Mains"

    # Verify channel pruning capabilities on Vue 1000
    channels_by_id = {ch.channel_id: ch for ch in home.channels}
    assert channels_by_id["Mains"].has_data is True
    assert channels_by_id["Mains_A"].has_data is True
    assert channels_by_id["Mains_B"].has_data is True
    assert channels_by_id["Mains_C"].has_data is False

    active_branches = [
        channels_by_id[f"Branch_{i}"] for i in range(1, 9) if channels_by_id[f"Branch_{i}"].has_data
    ]
    empty_branches = [
        channels_by_id[f"Branch_{i}"] for i in range(9, 17) if not channels_by_id[f"Branch_{i}"].has_data
    ]
    assert len(active_branches) == 8
    assert len(empty_branches) == 8

    # Verify EVSE device representation
    assert evse.device_type == "EV_CHARGER"
    assert evse.ev_charger is not None
    assert isinstance(evse.ev_charger, ChargerDevice)
    assert evse.ev_charger.category == "EVSE"
    assert evse.ev_charger.charger_on is True
    assert evse.ev_charger.max_charging_rate == 40


def test_simulator_v1_get_channels_topology(simulated_vue: PyEmVue) -> None:
    """Validate get_channels queries V1 channel topology with nested devices."""
    channel_devices = simulated_vue.get_channels()
    assert len(channel_devices) == 1

    root_dev = channel_devices[0]
    assert root_dev.device_gid == 1000

    channels_by_id = {ch.channel_id: ch for ch in root_dev.channels}
    mains = channels_by_id["Mains"]
    assert len(mains.nested_devices) == 2
    nested_gids = {nd.device_gid for nd in mains.nested_devices}
    assert nested_gids == {1004, 1005}

    branch_1 = channels_by_id["Branch_1"]
    assert len(branch_1.nested_devices) == 2
    b1_gids = {nd.device_gid for nd in branch_1.nested_devices}
    assert b1_gids == {1001, 1002}

    branch_4 = channels_by_id["Branch_4"]
    assert len(branch_4.nested_devices) == 1
    assert branch_4.nested_devices[0].device_gid == 1003


def test_simulator_v1_get_sites(simulated_vue: PyEmVue) -> None:
    """Validate get_sites deserializes simulated VueSite models."""
    sites = simulated_vue.get_sites()
    assert len(sites) == 1

    site = sites[0]
    assert site.site_gid == 5001
    assert site.display_name == "Home"
    assert site.time_zone == "America/New_York"
    assert site.latitude == pytest.approx(40.0)
    assert site.longitude == pytest.approx(-74.0)
    assert len(site.device_ids) == 6
    assert site.service_address is not None
    assert site.service_address["city"] == "Denver"


def test_simulator_v1_usages_power_and_split_phase_voltage(
    simulated_vue: PyEmVue,
) -> None:
    """Validate get_device_list_usage_v1 parses instantaneous power and split-phase voltage."""
    # 1. Power usages (KILOWATT_HOURS)
    devices_kwh = simulated_vue.get_device_list_usage_v1(
        device_gids=[1000, 1005], energy_unit=Unit.KWH
    )
    assert 1000 in devices_kwh
    home_kwh = devices_kwh[1000]
    assert "1,2,3" in home_kwh.channels
    assert home_kwh.channels["1,2,3"].channel_id == "Mains"
    assert home_kwh.channels["1,2,3"].usage > 0
    assert "Mains_A" in home_kwh.channels
    assert "Mains_B" in home_kwh.channels
    assert "1" in home_kwh.channels
    assert "2" in home_kwh.channels
    assert "Balance" in home_kwh.channels
    assert "TotalUsage" in home_kwh.channels

    # 2. Voltage telemetry (Unit.VOLTS -> VOLTAGE)
    devices_volts = simulated_vue.get_device_list_usage_v1(
        device_gids=[1000, 1005], energy_unit=Unit.VOLTS
    )
    assert 1000 in devices_volts
    home_volts = devices_volts[1000]
    assert home_volts.channels["1,2,3"].usage == pytest.approx(120.75)
    assert home_volts.channels["Mains_A"].usage == pytest.approx(120.4)
    assert home_volts.channels["Mains_B"].usage == pytest.approx(121.1)
    assert home_volts.channels["Mains_C"].usage == pytest.approx(0.0)

    # EVSE 240V
    assert 1005 in devices_volts
    evse_volts = devices_volts[1005]
    assert evse_volts.channels["1,2,3"].usage == pytest.approx(240.0)


def test_simulator_v1_devices_status_dual_schema_and_bearer_auth(
    simulated_vue: PyEmVue,
) -> None:
    """Validate get_devices_status dual schema compatibility and Bearer token verification."""
    dev_list = [VueDevice(gid=1000), VueDevice(gid=1005)]
    outlets, chargers = simulated_vue.get_devices_status(device_list=dev_list)

    assert len(outlets) == 4
    assert all(isinstance(o, OutletDevice) for o in outlets)
    assert len(chargers) == 1
    assert isinstance(chargers[0], ChargerDevice)
    assert chargers[0].charger_on is True

    # Connected status updated on device objects
    assert dev_list[0].connected is True
    assert dev_list[1].connected is True

    # Test Bearer auth rejection for malformed authorization header
    client = TestClient(app)
    bad_resp = client.get(
        "/v1/customers/devices/status", headers={"Authorization": "InvalidTokenFormat"}
    )
    assert bad_resp.status_code == 401
    assert "Invalid Bearer token" in bad_resp.json()["message"]


def test_simulator_v1_evse_control_26_metrics(simulated_vue: PyEmVue) -> None:
    """Validate get_evse_control queries live charging session telemetry with all 26 fields."""
    status = simulated_vue.get_evse_control("1005")
    assert status is not None

    # Verify all 26 telemetry metrics
    assert status.device_id == "D2112A04B4AC6C4523421"
    assert status.session_active is True
    assert status.energy_delivered == pytest.approx(12.35)
    assert status.cost == pytest.approx(1.48)
    assert status.active_charging_minutes == 42
    assert status.charging_rate_kw == pytest.approx(9.6)
    assert status.charging_rate_amps == pytest.approx(40.0)
    assert status.offered_amps == pytest.approx(40.0)
    assert status.plug_in is not None
    assert status.fault_code is None
    assert status.charger_status == "CHARGING"
    assert status.button_action == "MANAGE"
    assert status.subtext_type is None
    assert status.subtext_parameters == ["2026-11-01T20:00:00Z"]
    assert status.button_behavior == "OVERRIDE_EXCESS_SOLAR"
    assert status.charging_rate_controller == "EXCESS_SOLAR"
    assert status.charging_rate_controller_warning is None
    assert status.charge_rate_controller_type == "EXCESS_SOLAR"
    assert status.charge_rate_controller_status == "WORKING_CORRECTLY"
    assert status.charge_rate_controller_offline_device_name is None
    assert status.charge_rate_controller_additional_amps == pytest.approx(6.0)
    assert status.charge_rate_controller_guaranteed_amps == pytest.approx(12.0)
    assert status.next_event_type == "START"
    assert status.next_event_time == datetime.datetime(
        2026, 11, 2, 14, 0, tzinfo=datetime.timezone.utc
    )
    assert status.next_event_actor == "SOLAR_WINDOW"
    assert status.next_event_subtext_parameters == ["UtilityPartner"]


def test_simulator_v1_evse_control_commands_and_override(
    simulated_vue: PyEmVue,
) -> None:
    """Validate post_evse_control handles TURN_OFF, TURN_ON, and CHARGE_AT_FULL_POWER."""
    # 1. Turn charger off
    assert simulated_vue.set_evse_state("1005", enabled=False) is True
    off_status = simulated_vue.get_evse_control("1005")
    assert off_status.charger_status == "DISCONNECTED_OFF"
    assert off_status.session_active is False

    # 2. Turn charger on
    assert simulated_vue.set_evse_state("1005", enabled=True) is True
    on_status = simulated_vue.get_evse_control("1005")
    assert on_status.charger_status == "CHARGING"
    assert on_status.session_active is True

    # 3. Full power override
    assert (
        simulated_vue.post_evse_control(
            device_id="1005", command="CHARGE_AT_FULL_POWER"
        )
        is True
    )
    override_status = simulated_vue.get_evse_control("1005")
    assert override_status.charger_status == "CHARGING"
    assert override_status.session_active is True
    assert override_status.charging_rate_controller == "MANUAL"
    assert override_status.subtext_type == "EXCESS_SOLAR_PAUSED"

    # 4. Invalid command validation
    with pytest.raises(ValueError, match="Unsupported EVSE control command"):
        simulated_vue.post_evse_control("1005", command="INVALID_CMD")


def test_simulator_v1_evse_settings_and_rate_adjustment(
    simulated_vue: PyEmVue,
) -> None:
    """Validate get_evses and set_evse_settings update pilot charge rate in simulator state."""
    evses = simulated_vue.get_evses(["D2112A04B4AC6C4523421"])
    assert len(evses) == 1
    assert evses[0].charging_rate == 40
    assert evses[0].max_charging_rate == 40

    # Adjust charge rate to 32 amps
    success = simulated_vue.set_evse_settings("D2112A04B4AC6C4523421", charge_rate_amps=32)
    assert success is True

    # Verify updated pilot current persists in simulator
    updated_evses = simulated_vue.get_evses(["D2112A04B4AC6C4523421"])
    assert updated_evses[0].charging_rate == 32


def test_simulator_v1_excess_solar_discovery_and_configuration(
    simulated_vue: PyEmVue,
) -> None:
    """Validate excess generation monitors discovery and dynamic load configuration."""
    # 1. Discover monitors with solar generation CTs
    eg_monitors = simulated_vue.get_excess_generation_monitors()
    assert eg_monitors is not None
    assert len(eg_monitors.monitors) == 1
    assert eg_monitors.monitors[0].device_id == "A2112A04B4AC67B2B548201"
    assert eg_monitors.monitors[0].enabled is True

    # 2. Query initial excess solar configuration
    config = simulated_vue.get_excess_generation("A2112A04B4AC67B2B548201")
    assert config is not None
    assert config.device_id == "A2112A04B4AC67B2B548201"
    assert len(config.loads) == 1
    assert config.loads[0].load_gid == 1005
    assert config.loads[0].enabled is True
    assert config.solar_window is not None
    assert config.sunrise == "2026-11-01T14:29:49Z"
    assert config.sunset == "2026-11-02T00:10:38Z"

    # 3. Update excess generation configuration (disable EVSE load)
    update_success = simulated_vue.set_excess_generation(
        device_id="A2112A04B4AC67B2B548201",
        loads=[{"load_gid": 1005, "enabled": False}],
    )
    assert update_success is True

    # Verify updated state in simulator
    updated_config = simulated_vue.get_excess_generation("A2112A04B4AC67B2B548201")
    assert updated_config is not None
    assert updated_config.loads[0].enabled is False


def test_simulator_v1_sse_stream_endpoint() -> None:
    """Validate simulator SSE event stream endpoint returns DEVICE_STATUS stream."""
    client = TestClient(app)
    response = client.get("/v1/customers/stream?event_types=DEVICE_STATUS")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "DEVICE_STATUS" in response.text
