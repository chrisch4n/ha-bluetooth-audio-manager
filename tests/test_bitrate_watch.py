"""Reconnect a playing speaker that sat at PulseAudio's lowest SBC step too long."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from bt_audio_manager.config import AppConfig
    from bt_audio_manager.manager import BluetoothAudioManager
except OSError as exc:  # libpulse.so.0 is absent on non-Linux dev machines
    raise unittest.SkipTest(f"libpulse not available: {exc}") from exc

A = "41:42:00:00:08:75"
B = "41:42:00:00:09:70"
SINK_A = "bluez_sink.41_42_00_00_08_75.a2dp_sink"
SINK_B = "bluez_sink.41_42_00_00_09_70.a2dp_sink"


def sink(name, lowest):
    return {"sink": name, "rate": 44100, "sbc_frames_per_packet": 15 if lowest else 5,
            "at_lowest_step": lowest}


def build(sinks, *, minutes=5, playing=True):
    m = BluetoothAudioManager.__new__(BluetoothAudioManager)
    m.config = AppConfig()
    m.config.lowest_bitrate_reconnect_minutes = minutes
    m._lowest_since = {}
    m._bitrate_reconnects = {}
    m._bitrate_fix_running = set()
    m._rate_fix_running = set()
    m._device_connect_time = {A: 1.0, B: 1.0}
    m.pulse = MagicMock(bt_sink_encoder_estimates=AsyncMock(return_value=sinks))
    mpd = MagicMock(is_running=True, handle_command=AsyncMock(), resume=AsyncMock(return_value=True),
                    playback_snapshot=AsyncMock(return_value={"uri": "http://radio/bob", "playing": playing}))
    m._mpd_instances = {A: mpd, B: mpd}
    m.force_reconnect_device = AsyncMock(return_value=True)
    m._resume_state = MagicMock(return_value={})
    m._save_resume_state = MagicMock()
    return m, mpd


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class BitrateWatchTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.clock = Clock()
        self._p = patch("bt_audio_manager.manager.time.monotonic", self.clock)
        self._p.start()

    async def asyncTearDown(self):
        self._p.stop()

    def test_address_from_sink(self):
        f = BluetoothAudioManager.address_from_bt_sink
        self.assertEqual(f(SINK_A), A)
        self.assertIsNone(f("alsa_output.pci.analog-stereo"))
        self.assertIsNone(f(""))

    async def test_reconnects_after_the_set_time_and_keeps_the_station(self):
        m, mpd = build([sink(SINK_A, True), sink(SINK_B, False)])
        self.assertEqual(await m.check_lowest_bitrate(), [])  # first seen now
        self.clock.now += 4 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [])  # not yet 5 min
        self.clock.now += 61
        self.assertEqual(await m.check_lowest_bitrate(), [A])
        m.force_reconnect_device.assert_awaited_once_with(A)
        self.assertEqual([c.args[0] for c in mpd.handle_command.await_args_list], ["Stop"])
        mpd.resume.assert_awaited_once_with("http://radio/bob")

    async def test_recovering_bitrate_resets_the_time(self):
        m, _ = build([sink(SINK_A, True)])
        await m.check_lowest_bitrate()
        self.clock.now += 4 * 60
        m.pulse.bt_sink_encoder_estimates.return_value = [sink(SINK_A, False)]
        await m.check_lowest_bitrate()
        m.pulse.bt_sink_encoder_estimates.return_value = [sink(SINK_A, True)]
        self.clock.now += 2 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [])  # counting starts again
        m.force_reconnect_device.assert_not_awaited()

    async def test_at_most_once_in_the_cooldown(self):
        m, _ = build([sink(SINK_A, True)])
        await m.check_lowest_bitrate()
        self.clock.now += 6 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [A])
        self.clock.now += 1
        await m.check_lowest_bitrate()  # still low: counting again
        self.clock.now += 10 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [])  # within 30 min
        self.clock.now += 25 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [A])
        self.assertEqual(m.force_reconnect_device.await_count, 2)

    async def test_idle_speaker_is_left_alone(self):
        m, _ = build([sink(SINK_A, True)], playing=False)
        await m.check_lowest_bitrate()
        self.clock.now += 10 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [])
        m.force_reconnect_device.assert_not_awaited()

    async def test_off_when_zero(self):
        m, _ = build([sink(SINK_A, True)], minutes=0)
        await m.check_lowest_bitrate()
        self.clock.now += 60 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [])
        m.pulse.bt_sink_encoder_estimates.assert_not_awaited()

    async def test_not_while_the_44k_fix_reconnects_it(self):
        m, _ = build([sink(SINK_A, True)])
        await m.check_lowest_bitrate()
        self.clock.now += 6 * 60
        m._rate_fix_running.add(A)
        self.assertEqual(await m.check_lowest_bitrate(), [])
        m.force_reconnect_device.assert_not_awaited()

    async def test_station_noted_when_speaker_not_back_yet(self):
        m, mpd = build([sink(SINK_A, True)])
        state = {}
        m._resume_state = MagicMock(return_value=state)

        async def reconnect(address):
            m._mpd_instances[address] = MagicMock(is_running=False)
            return False

        m.force_reconnect_device = AsyncMock(side_effect=reconnect)
        await m.check_lowest_bitrate()
        self.clock.now += 6 * 60
        self.assertEqual(await m.check_lowest_bitrate(), [A])
        self.assertEqual(state[A]["uri"], "http://radio/bob")
        m._save_resume_state.assert_called_once()


class SettingTest(unittest.TestCase):

    def test_default_and_runtime_settings(self):
        c = AppConfig()
        self.assertEqual(c.lowest_bitrate_reconnect_minutes, 5)
        self.assertEqual(c.runtime_settings["lowest_bitrate_reconnect_minutes"], 5)


if __name__ == "__main__":
    unittest.main()
