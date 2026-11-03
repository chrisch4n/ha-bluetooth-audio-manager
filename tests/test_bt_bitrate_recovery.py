"""Bluetooth bitrate recovery: PulseAudio's output_rate_refresh_interval_ms.

After an overload PulseAudio drops audio and lowers the A2DP bitrate, then
raises it again every 500 ms by default.  With three speakers on one
adapter that climbs straight back into the next overload (a dropout about
once a minute).  The app can make PulseAudio wait longer.
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

try:
    from bt_audio_manager.audio.pulse import PulseAudioManager
    from bt_audio_manager.config import AppConfig
    from bt_audio_manager.manager import BluetoothAudioManager
except OSError as exc:  # libpulse.so.0 is absent on non-Linux dev machines
    raise unittest.SkipTest(f"libpulse not available: {exc}") from exc

A = "41:42:E8:96:EE:34"
B = "41:42:86:95:15:12"


class ArgsTest(unittest.TestCase):

    def test_read_interval(self):
        f = PulseAudioManager.rate_refresh_from_args
        self.assertIsNone(f(""))
        self.assertIsNone(f(None))
        self.assertEqual(f("output_rate_refresh_interval_ms=600000"), 600000)
        self.assertEqual(f("headset=native output_rate_refresh_interval_ms=5000"), 5000)
        self.assertIsNone(f("xoutput_rate_refresh_interval_ms=5"))

    def test_set_and_remove_keeps_other_args(self):
        f = PulseAudioManager.args_with_rate_refresh
        self.assertEqual(f("", 600000), "output_rate_refresh_interval_ms=600000")
        self.assertEqual(
            f("headset=native output_rate_refresh_interval_ms=500", 600000),
            "headset=native output_rate_refresh_interval_ms=600000",
        )
        self.assertEqual(f("headset=native output_rate_refresh_interval_ms=500", None), "headset=native")


def module(index, args):
    return SimpleNamespace(index=index, name="module-bluez5-discover", argument=args)


class ReloadTest(unittest.IsolatedAsyncioTestCase):

    def build(self, load_side_effect=None):
        pa = PulseAudioManager()
        pa._pulse = MagicMock()
        pa._pulse.module_list = AsyncMock(return_value=[
            SimpleNamespace(index=3, name="module-bluetooth-discover", argument=""),
            module(29, ""),
        ])
        pa._pulse.module_unload = AsyncMock()
        pa._pulse.module_load = AsyncMock(side_effect=load_side_effect)
        return pa

    async def test_reload_with_new_args(self):
        pa = self.build()
        pa_sleep = asyncio.sleep
        try:
            asyncio.sleep = AsyncMock()
            ok = await pa.reload_bt_discover_module("output_rate_refresh_interval_ms=600000", "")
        finally:
            asyncio.sleep = pa_sleep
        self.assertTrue(ok)
        pa._pulse.module_unload.assert_awaited_once_with(29)
        pa._pulse.module_load.assert_awaited_once_with(
            "module-bluez5-discover", "output_rate_refresh_interval_ms=600000")

    async def test_failed_load_restores_the_old_args(self):
        pa = self.build(load_side_effect=[RuntimeError("refused"), None])
        pa_sleep = asyncio.sleep
        try:
            asyncio.sleep = AsyncMock()
            ok = await pa.reload_bt_discover_module("output_rate_refresh_interval_ms=600000", "")
        finally:
            asyncio.sleep = pa_sleep
        self.assertFalse(ok)
        self.assertEqual(
            [c.args for c in pa._pulse.module_load.await_args_list],
            [("module-bluez5-discover", "output_rate_refresh_interval_ms=600000"),
             ("module-bluez5-discover", "")],
        )


def manager_with(seconds, module_args, *, connected=(A, B), sinks_back=()):
    m = BluetoothAudioManager.__new__(BluetoothAudioManager)
    m.config = AppConfig()
    m.config.bt_bitrate_recovery_seconds = seconds
    m._bt_rate_lock = asyncio.Lock()
    m._bt_rate_failed_for = None
    m.BT_RATE_RESTORE_STAGGER = 0
    m.pulse = MagicMock()
    m.pulse.bt_discover_module = AsyncMock(return_value=(29, module_args))
    m.pulse.rate_refresh_from_args = PulseAudioManager.rate_refresh_from_args
    m.pulse.args_with_rate_refresh = PulseAudioManager.args_with_rate_refresh
    m.pulse.reload_bt_discover_module = AsyncMock(return_value=True)
    m.pulse.get_sink_for_address = AsyncMock(
        side_effect=lambda addr: f"bluez_sink.{addr}" if addr in sinks_back else None)
    m.pulse.wait_for_bt_sink = AsyncMock(return_value="bluez_sink.x")
    m._device_connect_time = {a: 1.0 for a in connected}
    m.managed_devices = {
        a: MagicMock(is_connected=AsyncMock(return_value=True), connect_profile=AsyncMock())
        for a in connected
    }
    m.force_reconnect_device = AsyncMock(return_value=True)
    m._restart_audio_service = AsyncMock()
    return m


class EnsureTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self._sleep = asyncio.sleep
        asyncio.sleep = AsyncMock()

    async def asyncTearDown(self):
        asyncio.sleep = self._sleep

    async def test_nothing_to_do_when_already_in_effect(self):
        for seconds, args in ((0, ""), (600, "output_rate_refresh_interval_ms=600000")):
            with self.subTest(seconds=seconds):
                m = manager_with(seconds, args)
                result = await m.ensure_bt_bitrate_recovery()
                self.assertFalse(result["applied"])
                m.pulse.reload_bt_discover_module.assert_not_called()

    async def test_apply_reloads_and_restores_a2dp(self):
        m = manager_with(600, "", sinks_back=(B,))
        result = await m.ensure_bt_bitrate_recovery()
        self.assertTrue(result["applied"])
        m.pulse.reload_bt_discover_module.assert_awaited_once_with(
            "output_rate_refresh_interval_ms=600000", restore_args="")
        m.managed_devices[A].connect_profile.assert_awaited_once()
        m.managed_devices[B].connect_profile.assert_not_called()  # came back by itself
        self.assertEqual(result["speakers"][A], "A2DP restored")
        m.force_reconnect_device.assert_not_called()

    async def test_back_to_default_removes_the_argument(self):
        m = manager_with(0, "output_rate_refresh_interval_ms=600000")
        await m.ensure_bt_bitrate_recovery()
        m.pulse.reload_bt_discover_module.assert_awaited_once_with(
            "", restore_args="output_rate_refresh_interval_ms=600000")

    async def test_missing_stream_gets_a_forced_reconnect(self):
        m = manager_with(600, "", connected=(A,))
        m.pulse.wait_for_bt_sink = AsyncMock(return_value=None)
        result = await m.ensure_bt_bitrate_recovery()
        m.force_reconnect_device.assert_awaited_once_with(A)
        self.assertEqual(result["speakers"][A], "forced reconnect")

    async def test_failed_value_is_not_retried_automatically(self):
        m = manager_with(600, "")
        m.pulse.reload_bt_discover_module = AsyncMock(return_value=False)
        await m.ensure_bt_bitrate_recovery()
        self.assertEqual(m.pulse.reload_bt_discover_module.await_count, 1)
        result = await m.ensure_bt_bitrate_recovery()  # e.g. after a PA reconnect
        self.assertEqual(result["reason"], "failed before")
        self.assertEqual(m.pulse.reload_bt_discover_module.await_count, 1)
        await m.ensure_bt_bitrate_recovery(force=True)  # settings changed
        self.assertEqual(m.pulse.reload_bt_discover_module.await_count, 2)

    async def test_module_lost_restarts_audio_service(self):
        m = manager_with(600, "")
        m.pulse.reload_bt_discover_module = AsyncMock(return_value=False)
        m.pulse.bt_discover_module = AsyncMock(side_effect=[(29, ""), None])
        await m.ensure_bt_bitrate_recovery()
        m._restart_audio_service.assert_awaited_once()


from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from bt_audio_manager.web.api import create_api_routes


class SettingsApiTest(AioHTTPTestCase):

    async def get_application(self):
        self.manager = MagicMock()
        self.manager.config = AppConfig()
        self.manager.config.save_settings = MagicMock()
        self.manager.volume_lock_summary.return_value = {}
        self.manager.ensure_bt_bitrate_recovery = MagicMock(return_value="coro")
        app = web.Application()
        app.router.add_routes(create_api_routes(self.manager))
        return app

    async def test_change_applies_in_background(self):
        resp = await self.client.put("/api/settings", json={"bt_bitrate_recovery_seconds": 600})
        self.assertEqual(resp.status, 200)
        self.assertEqual((await resp.json())["bt_bitrate_recovery_seconds"], 600)
        self.manager.ensure_bt_bitrate_recovery.assert_called_once_with(force=True)
        self.manager._fire_and_forget.assert_called_once_with("coro")

    async def test_unchanged_value_does_not_reload(self):
        resp = await self.client.put("/api/settings", json={"bt_bitrate_recovery_seconds": 0})
        self.assertEqual(resp.status, 200)
        self.manager._fire_and_forget.assert_not_called()

    async def test_invalid_values_rejected(self):
        for value in (-1, 86401, "600", True, 1.5):
            with self.subTest(value=value):
                resp = await self.client.put("/api/settings", json={"bt_bitrate_recovery_seconds": value})
                self.assertEqual(resp.status, 400)


if __name__ == "__main__":
    unittest.main()
