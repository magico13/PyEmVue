from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import datetime
import json
import logging
import random
from typing import Any, AsyncIterator, Callable, Optional, Union

import aiohttp

from pyemvue.auth import Auth
from pyemvue.device import ChargerDevice, OutletDevice

_LOGGER = logging.getLogger(__name__)

DEFAULT_STREAM_URL = "https://api.emporiaenergy.com/v1/customers/stream"
DEFAULT_EVENT_TYPES = "DEVICE_STATUS"


@dataclass
class DeviceStatusDelta:
    """Normalized device status delta or snapshot emitted by the Emporia SSE stream."""

    event_type: str
    raw_data: dict[str, Any] = field(default_factory=dict)
    device_id: Optional[str] = None
    device_gid: Optional[int] = None
    load_gid: Optional[int] = None
    status: Optional[str] = None
    charger_on: Optional[bool] = None
    outlet_on: Optional[bool] = None
    charging_rate: Optional[int] = None
    vehicle_connected: Optional[bool] = None
    vehicle_charging: Optional[bool] = None
    charging_rate_kw: Optional[float] = None
    charging_rate_amps: Optional[float] = None
    offered_amps: Optional[float] = None
    energy_delivered: Optional[float] = None
    active_charging_minutes: Optional[int] = None
    cost: Optional[float] = None
    plug_in: Optional[Union[str, datetime.datetime]] = None
    connected: Optional[bool] = None
    devices_connected: list[dict[str, Any]] = field(default_factory=list)
    evses: list[ChargerDevice] = field(default_factory=list)
    outlets: list[OutletDevice] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Return True if this event represents an initial full state snapshot."""
        return self.event_type == "DEVICE_STATUS.COMPLETE"

    @property
    def is_delta(self) -> bool:
        """Return True if this event represents an incremental state delta."""
        return self.event_type == "DEVICE_STATUS.DELTA"

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dictionary-style access with default fallback."""
        if hasattr(self, key) and getattr(self, key) is not None:
            return getattr(self, key)
        return self.raw_data.get(key, default)

    @classmethod
    def from_json_dictionary(
        cls, event_type: str, js: dict[str, Any]
    ) -> DeviceStatusDelta:
        """Parse structured device status delta from JSON payload."""
        delta = cls(event_type=event_type, raw_data=js)
        if not isinstance(js, dict):
            return delta

        # Live cloud SSE frames wrap contents in {"event_type": "...", "data": {...}}
        payload = js.get("data") if isinstance(js.get("data"), dict) else js

        def _get(key: str, default: Any = None) -> Any:
            if isinstance(payload, dict) and key in payload:
                return payload[key]
            return js.get(key, default) if isinstance(js, dict) else default

        def _has(key: str) -> bool:
            return (isinstance(payload, dict) and key in payload) or (
                isinstance(js, dict) and key in js
            )

        # Parse devices_connected if present
        devices_connected = _get("devices_connected")
        if isinstance(devices_connected, list):
            delta.devices_connected = devices_connected

        # Parse evses if present
        evses_raw = _get("evses") or _get("evChargers")
        if evses_raw and isinstance(evses_raw, list):
            for raw_charger in evses_raw:
                if isinstance(raw_charger, dict):
                    delta.evses.append(ChargerDevice().from_json_dictionary(raw_charger))

        # Parse outlets if present
        outlets_raw = _get("outlets")
        if outlets_raw and isinstance(outlets_raw, list):
            for raw_outlet in outlets_raw:
                if isinstance(raw_outlet, dict):
                    delta.outlets.append(OutletDevice().from_json_dictionary(raw_outlet))

        # Top-level / single-device attributes
        delta.device_id = _get("device_id") or _get("deviceId")
        delta.device_gid = _get("device_gid") or _get("deviceGid")
        delta.load_gid = _get("load_gid") or _get("loadGid")
        delta.status = _get("status")
        delta.charger_on = (
            _get("charger_on") if _has("charger_on") else _get("chargerOn")
        )
        delta.outlet_on = (
            _get("outlet_on") if _has("outlet_on") else _get("outletOn")
        )
        delta.charging_rate = _get("charging_rate") or _get("chargingRate")
        delta.vehicle_connected = (
            _get("vehicle_connected")
            if _has("vehicle_connected")
            else _get("vehicleConnected")
        )
        delta.vehicle_charging = (
            _get("vehicle_charging")
            if _has("vehicle_charging")
            else _get("vehicleCharging")
        )
        delta.charging_rate_kw = (
            _get("charging_rate_kw")
            if _has("charging_rate_kw")
            else _get("chargingRateKw")
        )
        delta.charging_rate_amps = (
            _get("charging_rate_amps")
            if _has("charging_rate_amps")
            else _get("chargingRateAmps")
        )
        delta.offered_amps = _get("offered_amps") or _get("offeredAmps")
        delta.energy_delivered = (
            _get("energy_delivered")
            if _has("energy_delivered")
            else _get("energyDelivered")
        )
        delta.active_charging_minutes = (
            _get("active_charging_minutes")
            if _has("active_charging_minutes")
            else _get("activeChargingMinutes")
        )
        delta.cost = _get("cost")
        delta.plug_in = _get("plug_in") if _has("plug_in") else _get("plugIn")
        delta.connected = _get("connected")

        # Synthesize single EVSE device model if delta contains EVSE status but evses list is empty
        if (
            (delta.device_gid or delta.device_id)
            and (
                delta.charger_on is not None
                or delta.vehicle_connected is not None
                or delta.status is not None
                or delta.charging_rate is not None
            )
            and not delta.evses
        ):
            charger_dict = payload if isinstance(payload, dict) else js
            charger = ChargerDevice().from_json_dictionary(charger_dict)
            delta.evses.append(charger)

        # Synthesize single outlet device model if delta contains outlet status but outlets list is empty
        if (
            (delta.device_gid or delta.device_id)
            and delta.outlet_on is not None
            and not delta.outlets
        ):
            outlet_dict = payload if isinstance(payload, dict) else js
            outlet = OutletDevice().from_json_dictionary(outlet_dict)
            delta.outlets.append(outlet)

        return delta


class EmporiaStreamClient:
    """Asynchronous Server-Sent Events (SSE) stream client for Emporia real-time push events."""

    def __init__(
        self,
        auth: Optional[Any] = None,
        host: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
        event_types: str = DEFAULT_EVENT_TYPES,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        on_connect: Optional[Callable[[], Any]] = None,
        on_disconnect: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._vue = None
        self.auth: Optional[Auth] = None
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        if auth is not None:
            if hasattr(auth, "auth_v1") and auth.auth_v1 is not None:
                self.auth = auth.auth_v1
                self._vue = auth
            elif hasattr(auth, "auth") and auth.auth is not None:
                self.auth = auth.auth
                self._vue = auth
            else:
                self.auth = auth

        # Resolve host URL
        if host is not None:
            self.host = host
        elif self.auth and hasattr(self.auth, "host") and self.auth.host:
            self.host = self.auth.host
        else:
            self.host = "https://api.emporiaenergy.com/v1"

        self.event_types = event_types
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay

        self._session = session
        self._own_session = False
        self._running = False
        self._listeners: list[Callable[[DeviceStatusDelta], Any]] = []

    @property
    def url(self) -> str:
        """Construct the full SSE stream endpoint URL."""
        base = self.host.rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/customers/stream"
        if "/v1/" in base:
            return f"{base}/customers/stream"
        return f"{base}/v1/customers/stream"

    @property
    def is_running(self) -> bool:
        """Return True if the stream client is currently running or reconnecting."""
        return self._running

    def add_listener(
        self, callback: Callable[[DeviceStatusDelta], Any]
    ) -> Callable[[], None]:
        """Register a callback for incoming stream deltas. Returns an unsubscribe callable."""
        self._listeners.append(callback)

        def unsubscribe() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        return unsubscribe

    def _get_headers(self) -> dict[str, str]:
        """Extract Bearer token and construct SSE request headers."""
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }
        token = ""
        if self.auth and hasattr(self.auth, "tokens") and self.auth.tokens:
            token = (
                self.auth.tokens.get("id_token")
                or self.auth.tokens.get("access_token")
                or ""
            )
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _refresh_tokens(self) -> None:
        """Refresh auth tokens via Auth or PyEmVue."""
        if self._vue and hasattr(self._vue, "auth_v1") and self._vue.auth_v1:
            self._vue.auth_v1.refresh_tokens()
        elif self.auth and hasattr(self.auth, "refresh_tokens"):
            self.auth.refresh_tokens()

    @staticmethod
    def parse_sse_lines(lines: list[str]) -> list[DeviceStatusDelta]:
        """Parse raw SSE text lines into a list of DeviceStatusDelta objects."""
        deltas: list[DeviceStatusDelta] = []
        current_event = ""
        data_lines: list[str] = []

        for line in lines:
            line = line.rstrip("\r\n")
            if line.startswith(":"):
                # SSE Comment / heartbeat ping
                continue
            if line.startswith("event:"):
                current_event = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())
            elif not line:
                # Empty line signals end of an SSE message block
                if data_lines or current_event:
                    payload_str = "\n".join(data_lines)
                    try:
                        payload = json.loads(payload_str) if payload_str else {}
                    except Exception:  # noqa: BLE001
                        payload = {"raw": payload_str}
                    deltas.append(
                        DeviceStatusDelta.from_json_dictionary(
                            current_event or "DEVICE_STATUS", payload
                        )
                    )
                    current_event = ""
                    data_lines = []

        if data_lines or current_event:
            payload_str = "\n".join(data_lines)
            try:
                payload = json.loads(payload_str) if payload_str else {}
            except Exception:  # noqa: BLE001
                payload = {"raw": payload_str}
            deltas.append(
                DeviceStatusDelta.from_json_dictionary(
                    current_event or "DEVICE_STATUS", payload
                )
            )

        return deltas

    async def listen(self) -> AsyncIterator[DeviceStatusDelta]:
        """Asynchronously stream status events with automatic reconnect and 401 token refresh."""
        self._running = True
        loop = asyncio.get_running_loop()
        retry_delay = self.initial_retry_delay

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._own_session = True

        stream_url = self.url
        params = {"event_types": self.event_types}

        while self._running:
            try:
                headers = self._get_headers()
                timeout = aiohttp.ClientTimeout(
                    total=None,
                    sock_read=None,
                    sock_connect=30.0,
                )
                async with self._session.get(
                    stream_url,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                ) as response:
                    if response.status == 401:
                        _LOGGER.info(
                            "Emporia stream received 401 Unauthorized; refreshing tokens..."
                        )
                        await loop.run_in_executor(None, self._refresh_tokens)
                        retry_delay = self.initial_retry_delay
                        continue

                    response.raise_for_status()
                    retry_delay = self.initial_retry_delay

                    if self.on_connect:
                        try:
                            connect_res = self.on_connect()
                            if asyncio.iscoroutine(connect_res):
                                await connect_res
                        except Exception as hook_err:  # noqa: BLE001
                            _LOGGER.warning("Error in on_connect hook: %s", hook_err)

                    current_event = ""
                    data_lines: list[str] = []
                    buffer = ""

                    async for raw_chunk in response.content:
                        if not self._running:
                            break
                        buffer += raw_chunk.decode("utf-8")

                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.rstrip("\r")

                            if line.startswith(":"):
                                # SSE comment / heartbeat
                                continue
                            if line.startswith("event:"):
                                current_event = line[len("event:") :].strip()
                            elif line.startswith("data:"):
                                data_lines.append(line[len("data:") :].strip())
                            elif not line:
                                # Empty line dispatches message
                                if data_lines or current_event:
                                    payload_str = "\n".join(data_lines)
                                    try:
                                        payload = (
                                            json.loads(payload_str)
                                            if payload_str
                                            else {}
                                        )
                                    except Exception:  # noqa: BLE001
                                        payload = {"raw": payload_str}
                                    delta = DeviceStatusDelta.from_json_dictionary(
                                        current_event or "DEVICE_STATUS", payload
                                    )
                                    yield delta
                                    current_event = ""
                                    data_lines = []

                    if data_lines or current_event:
                        payload_str = "\n".join(data_lines)
                        try:
                            payload = json.loads(payload_str) if payload_str else {}
                        except Exception:  # noqa: BLE001
                            payload = {"raw": payload_str}
                        yield DeviceStatusDelta.from_json_dictionary(
                            current_event or "DEVICE_STATUS", payload
                        )

            except asyncio.CancelledError:
                _LOGGER.debug("Emporia stream listener cancelled.")
                self._running = False
                raise
            except Exception as err:  # noqa: BLE001
                if not self._running:
                    break

                if self.on_disconnect:
                    try:
                        disconnect_res = self.on_disconnect()
                        if asyncio.iscoroutine(disconnect_res):
                            await disconnect_res
                    except Exception as hook_err:  # noqa: BLE001
                        _LOGGER.warning("Error in on_disconnect hook: %s", hook_err)

                jitter = random.uniform(0.8, 1.2)
                sleep_time = min(retry_delay * jitter, self.max_retry_delay)
                _LOGGER.warning(
                    "Emporia stream connection dropped (%s). Reconnecting in %.2fs...",
                    err,
                    sleep_time,
                )
                await asyncio.sleep(sleep_time)
                retry_delay = min(retry_delay * 2, self.max_retry_delay)

    async def run(self) -> None:
        """Run persistent stream listener, dispatching deltas to registered listeners."""
        async for delta in self.listen():
            for listener in list(self._listeners):
                try:
                    res = listener(delta)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error("Error in stream listener callback: %s", err)

    async def close(self) -> None:
        """Stop listening and cleanly close any internally created session."""
        self._running = False
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._own_session = False
