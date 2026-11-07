from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyemvue.auth import Auth
from pyemvue.pyemvue import PyEmVue
from pyemvue.stream import DeviceStatusDelta, EmporiaStreamClient


class MockAsyncStream:
    """Mock aiohttp StreamReader yielding byte chunks."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    def __aiter__(self) -> MockAsyncStream:
        return self

    async def __anext__(self) -> bytes:
        if not self._chunks:
            raise StopAsyncIteration
        return self._chunks.pop(0)


def test_parse_sse_lines_basic() -> None:
    """Test parsing standard SSE lines with comments and event dispatch."""
    lines = [
        ": keepalive heartbeat",
        "event: DEVICE_STATUS.COMPLETE",
        'data: {"evses": [{"device_gid": 12345, "status": "STANDBY"}]}',
        "",
        ": another comment",
        "event: DEVICE_STATUS.DELTA",
        'data: {"device_gid": 12345, "status": "CHARGING", "vehicle_charging": true}',
        "",
    ]
    deltas = EmporiaStreamClient.parse_sse_lines(lines)
    assert len(deltas) == 2

    assert deltas[0].event_type == "DEVICE_STATUS.COMPLETE"
    assert deltas[0].is_complete is True
    assert deltas[0].is_delta is False
    assert len(deltas[0].evses) == 1
    assert deltas[0].evses[0].device_gid == 12345
    assert deltas[0].evses[0].status == "STANDBY"

    assert deltas[1].event_type == "DEVICE_STATUS.DELTA"
    assert deltas[1].is_complete is False
    assert deltas[1].is_delta is True
    assert deltas[1].device_gid == 12345
    assert deltas[1].status == "CHARGING"
    assert deltas[1].vehicle_charging is True


def test_parse_sse_lines_multiline_data() -> None:
    """Test parsing SSE events where JSON data spans multiple data lines."""
    lines = [
        "event: DEVICE_STATUS.DELTA",
        'data: {"device_gid": 998877,',
        'data:  "outlet_on": false}',
        "",
    ]
    deltas = EmporiaStreamClient.parse_sse_lines(lines)
    assert len(deltas) == 1
    assert deltas[0].device_gid == 998877
    assert deltas[0].outlet_on is False
    assert len(deltas[0].outlets) == 1
    assert deltas[0].outlets[0].device_gid == 998877
    assert deltas[0].outlets[0].outlet_on is False


def test_device_status_delta_complete_parsing() -> None:
    """Test comprehensive DEVICE_STATUS.COMPLETE snapshot parsing."""
    raw = {
        "devices_connected": [
            {"device_id": "mon-1", "device_gid": 1111, "connected": True},
            {"device_id": "evse-1", "device_gid": 2222, "connected": True},
        ],
        "evses": [
            {
                "device_id": "evse-1",
                "device_gid": 2222,
                "load_gid": 3333,
                "status": "CHARGING",
                "charger_on": True,
                "charging_rate": 40,
                "vehicle_connected": True,
                "vehicle_charging": True,
            }
        ],
        "outlets": [
            {
                "device_id": "plug-1",
                "device_gid": 4444,
                "load_gid": 5555,
                "outlet_on": True,
            }
        ],
    }
    delta = DeviceStatusDelta.from_json_dictionary("DEVICE_STATUS.COMPLETE", raw)
    assert delta.is_complete is True
    assert len(delta.devices_connected) == 2
    assert len(delta.evses) == 1
    assert delta.evses[0].device_gid == 2222
    assert delta.evses[0].status == "CHARGING"
    assert delta.evses[0].vehicle_connected is True
    assert len(delta.outlets) == 1
    assert delta.outlets[0].device_gid == 4444
    assert delta.outlets[0].outlet_on is True


def test_device_status_delta_single_evse_delta() -> None:
    """Test incremental EVSE delta parsing and attribute normalization."""
    raw = {
        "device_id": "evse-abc",
        "device_gid": 5001,
        "load_gid": 6001,
        "status": "CHARGING",
        "charger_on": True,
        "vehicle_connected": True,
        "vehicle_charging": True,
        "charging_rate": 48,
        "charging_rate_kw": 11.5,
        "charging_rate_amps": 48.0,
        "offered_amps": 48.0,
        "energy_delivered": 14.8,
        "active_charging_minutes": 77,
        "cost": 1.78,
        "plug_in": "2026-11-07T01:30:00Z",
    }
    delta = DeviceStatusDelta.from_json_dictionary("DEVICE_STATUS.DELTA", raw)
    assert delta.is_delta is True
    assert delta.device_id == "evse-abc"
    assert delta.device_gid == 5001
    assert delta.load_gid == 6001
    assert delta.status == "CHARGING"
    assert delta.charger_on is True
    assert delta.vehicle_connected is True
    assert delta.vehicle_charging is True
    assert delta.charging_rate == 48
    assert delta.charging_rate_kw == 11.5
    assert delta.charging_rate_amps == 48.0
    assert delta.offered_amps == 48.0
    assert delta.energy_delivered == 14.8
    assert delta.active_charging_minutes == 77
    assert delta.cost == 1.78
    assert delta.plug_in == "2026-11-07T01:30:00Z"
    assert delta.get("status") == "CHARGING"
    assert delta.get("unknown_key", "default_val") == "default_val"

    # Synthesized EVSE device
    assert len(delta.evses) == 1
    assert delta.evses[0].device_gid == 5001
    assert delta.evses[0].charger_on is True


def test_device_status_delta_wrapped_data_envelope() -> None:
    """Test cloud SSE frames wrapped in {"event_type": "...", "data": {...}}."""
    raw = {
        "event_type": "DEVICE_STATUS",
        "data": {
            "devices_connected": [
                {"device_id": "evse-1", "device_gid": 242715, "connected": True}
            ],
            "evses": [
                {
                    "device_id": "D2301A00090CB8152E3B78",
                    "device_gid": 242715,
                    "status": "CONNECTED_OFF",
                    "charger_on": False,
                    "charger_status": "CONNECTED_OFF",
                    "button_action": "RESUME",
                }
            ],
            "outlets": [],
        },
    }
    delta = DeviceStatusDelta.from_json_dictionary("DEVICE_STATUS", raw)
    assert len(delta.devices_connected) == 1
    assert delta.devices_connected[0]["device_gid"] == 242715
    assert len(delta.evses) == 1
    assert delta.evses[0].device_gid == 242715
    assert delta.evses[0].status == "CONNECTED_OFF"
    assert delta.evses[0].charger_on is False


def test_device_status_delta_wrapped_single_evse() -> None:
    """Test cloud single-device incremental delta wrapped in data envelope."""
    raw = {
        "event_type": "DEVICE_STATUS",
        "data": {
            "device_gid": 242715,
            "status": "CONNECTED_OFF",
            "charger_on": False,
            "charging_rate": 0,
        },
    }
    delta = DeviceStatusDelta.from_json_dictionary("DEVICE_STATUS", raw)
    assert delta.device_gid == 242715
    assert delta.status == "CONNECTED_OFF"
    assert delta.charger_on is False
    assert len(delta.evses) == 1
    assert delta.evses[0].device_gid == 242715
    assert delta.evses[0].status == "CONNECTED_OFF"
    assert delta.evses[0].charger_on is False


def test_device_status_delta_single_outlet_delta() -> None:
    """Test incremental outlet delta parsing."""
    raw = {
        "device_id": "plug-xyz",
        "device_gid": 7001,
        "load_gid": 8001,
        "outlet_on": False,
    }
    delta = DeviceStatusDelta.from_json_dictionary("DEVICE_STATUS.DELTA", raw)
    assert delta.is_delta is True
    assert delta.device_id == "plug-xyz"
    assert delta.device_gid == 7001
    assert delta.outlet_on is False
    assert len(delta.outlets) == 1
    assert delta.outlets[0].outlet_on is False


def test_stream_client_init_and_url_resolution() -> None:
    """Test URL and auth resolution across various constructor formats."""
    # 1. Direct host ending in /v1
    client1 = EmporiaStreamClient(host="https://api.emporiaenergy.com/v1")
    assert client1.url == "https://api.emporiaenergy.com/v1/customers/stream"

    # 2. Host without /v1
    client2 = EmporiaStreamClient(host="https://api.emporiaenergy.com")
    assert client2.url == "https://api.emporiaenergy.com/v1/customers/stream"

    # 3. Host with trailing slash
    client3 = EmporiaStreamClient(host="https://api.emporiaenergy.com/v1/")
    assert client3.url == "https://api.emporiaenergy.com/v1/customers/stream"

    # 4. From Auth object
    mock_auth = MagicMock(spec=Auth)
    mock_auth.host = "https://api.emporiaenergy.com/v1"
    mock_auth.tokens = {"id_token": "valid_token_123"}
    client4 = EmporiaStreamClient(auth=mock_auth)
    assert client4.url == "https://api.emporiaenergy.com/v1/customers/stream"
    headers = client4._get_headers()
    assert headers["Authorization"] == "Bearer valid_token_123"
    assert headers["Accept"] == "text/event-stream"

    # 5. From PyEmVue instance
    vue = PyEmVue()
    vue.auth_v1 = mock_auth
    client5 = EmporiaStreamClient(auth=vue)
    assert client5.auth == mock_auth


def test_stream_client_listeners() -> None:
    """Test adding, invoking, and unsubscribing stream listeners."""
    client = EmporiaStreamClient()
    received: list[DeviceStatusDelta] = []

    def sync_listener(delta: DeviceStatusDelta) -> None:
        received.append(delta)

    unsub = client.add_listener(sync_listener)
    assert sync_listener in client._listeners

    unsub()
    assert sync_listener not in client._listeners


@pytest.mark.asyncio
async def test_stream_client_listen_and_run() -> None:
    """Test async streaming chunk parsing and listener dispatch."""
    raw_sse_bytes = [
        b"event: DEVICE_STATUS.COMPLETE\n",
        b'data: {"evses": [{"device_gid": 100, "status": "STANDBY"}]}\n\n',
        b"event: DEVICE_STATUS.DELTA\n",
        b'data: {"device_gid": 100, "status": "CHARGING"}\n\n',
    ]

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = MockAsyncStream(raw_sse_bytes)

    # Context manager for session.get
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_resp
    mock_cm.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_cm

    client = EmporiaStreamClient(
        host="https://api.emporiaenergy.com/v1",
        session=mock_session,
        initial_retry_delay=0.01,
    )

    received_deltas: list[DeviceStatusDelta] = []

    async def async_cb(delta: DeviceStatusDelta) -> None:
        received_deltas.append(delta)
        if len(received_deltas) >= 2:
            await client.close()

    client.add_listener(async_cb)

    # Run client in background task
    task = asyncio.create_task(client.run())
    await asyncio.wait_for(task, timeout=2.0)

    assert len(received_deltas) == 2
    assert received_deltas[0].is_complete is True
    assert received_deltas[1].is_delta is True
    assert received_deltas[1].status == "CHARGING"


@pytest.mark.asyncio
async def test_stream_client_401_refresh() -> None:
    """Test 401 Unauthorized handling triggers token refresh and reconnects."""
    mock_auth = MagicMock(spec=Auth)
    mock_auth.tokens = {"id_token": "token_v1"}

    def refresh():
        mock_auth.tokens = {"id_token": "token_v2"}

    mock_auth.refresh_tokens.side_effect = refresh

    # First request: 401
    resp_401 = MagicMock()
    resp_401.status = 401

    cm_401 = AsyncMock()
    cm_401.__aenter__.return_value = resp_401
    cm_401.__aexit__.return_value = None

    # Second request: 200 with data
    resp_200 = MagicMock()
    resp_200.status = 200
    resp_200.raise_for_status = MagicMock()
    resp_200.content = MockAsyncStream(
        [b"event: DEVICE_STATUS.DELTA\ndata: {\"device_gid\": 100}\n\n"]
    )

    cm_200 = AsyncMock()
    cm_200.__aenter__.return_value = resp_200
    cm_200.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.side_effect = [cm_401, cm_200]

    client = EmporiaStreamClient(
        auth=mock_auth,
        session=mock_session,
        initial_retry_delay=0.01,
    )

    deltas: list[DeviceStatusDelta] = []
    async for delta in client.listen():
        deltas.append(delta)
        await client.close()
        break

    assert len(deltas) == 1
    assert deltas[0].device_gid == 100
    assert mock_auth.refresh_tokens.call_count == 1
    assert mock_auth.tokens["id_token"] == "token_v2"


@pytest.mark.asyncio
async def test_stream_client_reconnect_on_error() -> None:
    """Test automatic reconnect with backoff when stream connection fails."""
    # First request: network error
    cm_err = AsyncMock()
    cm_err.__aenter__.side_effect = ConnectionResetError("Connection lost")

    # Second request: 200 with data
    resp_200 = MagicMock()
    resp_200.status = 200
    resp_200.raise_for_status = MagicMock()
    resp_200.content = MockAsyncStream(
        [b"event: DEVICE_STATUS.DELTA\ndata: {\"device_gid\": 200}\n\n"]
    )

    cm_200 = AsyncMock()
    cm_200.__aenter__.return_value = resp_200
    cm_200.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.side_effect = [cm_err, cm_200]

    client = EmporiaStreamClient(
        session=mock_session,
        initial_retry_delay=0.01,
        max_retry_delay=0.05,
    )

    deltas: list[DeviceStatusDelta] = []
    async for delta in client.listen():
        deltas.append(delta)
        await client.close()
        break

    assert len(deltas) == 1
    assert deltas[0].device_gid == 200


@pytest.mark.asyncio
async def test_stream_client_close_terminates() -> None:
    """Test client.close() stops loop and closes internally owned session."""
    client = EmporiaStreamClient()
    mock_internal_session = AsyncMock()
    mock_internal_session.closed = False
    client._session = mock_internal_session
    client._own_session = True
    client._running = True

    await client.close()
    assert client.is_running is False
    assert mock_internal_session.close.call_count == 1
    assert client._session is None


@pytest.mark.asyncio
async def test_stream_client_lifecycle_callbacks() -> None:
    """Test on_connect and on_disconnect callbacks invocation during stream events."""
    on_connect_called = 0
    on_disconnect_called = 0

    def handle_connect():
        nonlocal on_connect_called
        on_connect_called += 1

    def handle_disconnect():
        nonlocal on_disconnect_called
        on_disconnect_called += 1

    # First request: drop
    cm_err = AsyncMock()
    cm_err.__aenter__.side_effect = ConnectionResetError("Connection lost")

    # Second request: 200
    resp_200 = MagicMock()
    resp_200.status = 200
    resp_200.raise_for_status = MagicMock()
    resp_200.content = MockAsyncStream(
        [b"event: DEVICE_STATUS.DELTA\ndata: {\"device_gid\": 500}\n\n"]
    )
    cm_200 = AsyncMock()
    cm_200.__aenter__.return_value = resp_200
    cm_200.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.side_effect = [cm_err, cm_200]

    client = EmporiaStreamClient(
        session=mock_session,
        initial_retry_delay=0.01,
        max_retry_delay=0.05,
        on_connect=handle_connect,
        on_disconnect=handle_disconnect,
    )

    deltas: list[DeviceStatusDelta] = []
    async for delta in client.listen():
        deltas.append(delta)
        await client.close()
        break

    assert on_disconnect_called == 1
    assert on_connect_called == 1
    assert len(deltas) == 1
    assert deltas[0].device_gid == 500

