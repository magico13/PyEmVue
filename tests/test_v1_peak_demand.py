from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest
from dateutil import tz

from pyemvue.device import (
    EnergyMonitorPeakDemand,
    MonthlyPeakDemand,
    PeakDemandLoad,
)
from pyemvue.pyemvue import (
    API_CURRENT_MONTH_PEAK_DEMAND,
    API_ENERGY_MONITOR_PEAK_DEMAND,
    API_PEAK_DEMAND,
    PyEmVue,
)


def test_monthly_peak_demand_deserialization_nested_and_flat() -> None:
    """Validate MonthlyPeakDemand parses nested peakDemand and flat/snake_case payloads."""
    nested = MonthlyPeakDemand().from_json_dictionary(
        {
            "deviceGid": 427903,
            "peakDemand": {
                "value": 7.108,
                "instant": "2026-11-10T18:15:00Z",
            },
        }
    )
    assert nested.device_gid == 427903
    assert nested.peak_demand_kw == pytest.approx(7.108)
    assert nested.peak_timestamp == datetime.datetime(
        2026, 11, 10, 18, 15, tzinfo=tz.tzutc()
    )
    assert nested.as_dictionary() == {
        "device_gid": 427903,
        "peak_demand_kw": 7.108,
        "peak_timestamp": "2026-11-10T18:15:00+00:00",
    }

    flat = MonthlyPeakDemand().from_json_dictionary(
        {
            "device_gid": 1001,
            "peak_demand_kw": 12.5,
            "peak_timestamp": "2026-11-05T12:00:00Z",
        }
    )
    assert flat.device_gid == 1001
    assert flat.peak_demand_kw == pytest.approx(12.5)
    assert flat.peak_timestamp == datetime.datetime(
        2026, 11, 5, 12, 0, tzinfo=tz.tzutc()
    )

    epoch_nested = MonthlyPeakDemand().from_json_dictionary(
        {
            "device_gid": None,
            "deviceGid": 427903,
            "peakDemand": {
                "value": 7.5,
                "timestamp": {"epochSecond": 1762800900},
            },
        }
    )
    assert epoch_nested.device_gid == 427903
    assert epoch_nested.peak_demand_kw == pytest.approx(7.5)
    assert epoch_nested.peak_timestamp == datetime.datetime(
        2025, 11, 10, 18, 55, tzinfo=datetime.timezone.utc
    )


def test_monthly_peak_demand_empty_or_invalid_timestamp() -> None:
    """Validate MonthlyPeakDemand handles missing/invalid values gracefully."""
    empty = MonthlyPeakDemand().from_json_dictionary(
        {"peakDemand": {"value": None, "instant": "not-a-date"}}
    )
    assert empty.peak_demand_kw is None
    assert empty.peak_timestamp is None


def test_energy_monitor_peak_demand_round_trip() -> None:
    """Validate EnergyMonitorPeakDemand and PeakDemandLoad parsing and serialization."""
    payload = {
        "device_id": "MON_427903",
        "enabled": True,
        "demand_goal_kwatts": 10.5,
        "loads": [
            {"load_gid": 138878, "enabled": False},
            {"loadGid": 138879, "enabled": True},
        ],
    }
    config = EnergyMonitorPeakDemand().from_json_dictionary(payload)
    assert config.device_id == "MON_427903"
    assert config.enabled is True
    assert config.demand_goal_kwatts == pytest.approx(10.5)
    assert len(config.loads) == 2
    assert config.loads[0].load_gid == 138878
    assert config.loads[0].enabled is False
    assert config.loads[1].load_gid == 138879
    assert config.loads[1].enabled is True

    serialized = config.as_dictionary()
    assert serialized == {
        "device_id": "MON_427903",
        "enabled": True,
        "demand_goal_kwatts": 10.5,
        "loads": [
            {"load_gid": 138878, "enabled": False},
            {"load_gid": 138879, "enabled": True},
        ],
    }


def test_get_current_month_peak_demand_client() -> None:
    """Validate PyEmVue.get_current_month_peak_demand() HTTP call and parsing."""
    vue = PyEmVue()
    mock_auth = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = (
        '{"peakDemand": {"value": 8.42, "instant": "2026-11-12T19:30:00Z"}}'
    )
    mock_resp.json.return_value = {
        "peakDemand": {"value": 8.42, "instant": "2026-11-12T19:30:00Z"}
    }
    mock_auth.request.return_value = mock_resp
    vue.auth = mock_auth

    peak = vue.get_current_month_peak_demand(427903)
    assert peak is not None
    assert peak.device_gid == 427903
    assert peak.peak_demand_kw == pytest.approx(8.42)
    assert peak.peak_timestamp == datetime.datetime(
        2026, 11, 12, 19, 30, tzinfo=tz.tzutc()
    )
    mock_auth.request.assert_called_once_with(
        "get", API_CURRENT_MONTH_PEAK_DEMAND.format(deviceGid=427903)
    )

    mock_resp.text = ""
    assert vue.get_current_month_peak_demand(427903) is None


def test_get_and_set_peak_demand_config_client() -> None:
    """Validate get_peak_demand_monitors(), get_peak_demand_config(), and set_peak_demand_config()."""
    vue = PyEmVue()
    mock_auth_v1 = MagicMock()
    vue.auth = MagicMock()
    vue.auth_v1 = mock_auth_v1

    # 1. Customer-level peak demand monitors
    monitors_resp = MagicMock()
    monitors_resp.text = '{"monitors": [{"device_id": "MON_1", "enabled": true}]}'
    monitors_resp.json.return_value = {
        "monitors": [{"device_id": "MON_1", "enabled": True}]
    }
    mock_auth_v1.request.return_value = monitors_resp

    monitors = vue.get_peak_demand_monitors()
    assert monitors == {"monitors": [{"device_id": "MON_1", "enabled": True}]}
    mock_auth_v1.request.assert_called_once_with("get", API_PEAK_DEMAND)

    # 2. Per-monitor peak demand config
    mock_auth_v1.request.reset_mock()
    cfg_resp = MagicMock()
    cfg_resp.text = '{"enabled": true, "demand_goal_kwatts": 9.0, "loads": [{"load_gid": 138878, "enabled": true}]}'
    cfg_resp.json.return_value = {
        "enabled": True,
        "demand_goal_kwatts": 9.0,
        "loads": [{"load_gid": 138878, "enabled": True}],
    }
    mock_auth_v1.request.return_value = cfg_resp

    cfg = vue.get_peak_demand_config("MON_1")
    assert cfg is not None
    assert cfg.device_id == "MON_1"
    assert cfg.enabled is True
    assert cfg.demand_goal_kwatts == pytest.approx(9.0)
    assert len(cfg.loads) == 1
    mock_auth_v1.request.assert_called_once_with(
        "get", f"{API_ENERGY_MONITOR_PEAK_DEMAND}?device_id=MON_1"
    )

    # 3. Set peak demand config with mixed PeakDemandLoad and dict loads
    mock_auth_v1.request.reset_mock()
    post_resp = MagicMock()
    mock_auth_v1.request.return_value = post_resp

    ok = vue.set_peak_demand_config(
        device_id="MON_1",
        enabled=False,
        demand_goal_kwatts=11.2,
        loads=[
            PeakDemandLoad(load_gid=138878, enabled=False),
            {"load_gid": 138879, "enabled": True},
        ],
    )
    assert ok is True
    mock_auth_v1.request.assert_called_once_with(
        "post",
        API_ENERGY_MONITOR_PEAK_DEMAND,
        json={
            "device_id": "MON_1",
            "enabled": False,
            "demand_goal_kwatts": 11.2,
            "loads": [
                {"load_gid": 138878, "enabled": False},
                {"load_gid": 138879, "enabled": True},
            ],
        },
    )
    post_resp.raise_for_status.assert_called_once()
