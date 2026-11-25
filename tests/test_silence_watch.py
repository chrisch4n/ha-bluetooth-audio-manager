"""Silence watch: a playing speaker that only gets digital silence.

Test on 25.11.2026: an MPD stream muted in PulseAudio kept its speaker
silent for 5 minutes while Home Assistant showed "playing" and nothing
noticed.  The app now samples each playing speaker's sink monitor.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bt_audio_manager.audio import gap_monitor
from bt_audio_manager.manager import BluetoothAudioManager

A = "41:42:00:00:08:75"
SINK = "bluez_sink.41_42_00_00_08_75.a2dp_sink"


def build(peaks):
    m = BluetoothAudioManager.__new__(BluetoothAudioManager)
    m.pulse = MagicMock(get_sink_for_address=AsyncMock(return_value=SINK))
    mpd = MagicMock(is_running=True, restart_playback=AsyncMock(return_value=True))
    mpd.get_status = AsyncMock(return_value={"state": "play"})
    m._mpd_instances = {A: mpd}
    it = iter(peaks)
    patcher = patch.object(gap_monitor, "monitor_peak", lambda sink, seconds: next(it))
    return m, mpd, patcher


class SilenceWatchTest(unittest.IsolatedAsyncioTestCase):

    async def run_checks(self, m, n):
        out = []
        for _ in range(n):
            out.append(await m.check_silence())
        return out

    async def test_three_silent_checks_reopen_the_stream_once(self):
        m, mpd, p = build([0, 0, 0, 0, 0])
        with p:
            results = await self.run_checks(m, 5)
        self.assertEqual(results, [[], [], [A], [], []])
        mpd.restart_playback.assert_awaited_once()
        self.assertEqual([s["address"] for s in m.silent_speakers()], [A])

    async def test_music_resets_the_count(self):
        m, mpd, p = build([0, 0, 1200, 0, 0])
        with p:
            await self.run_checks(m, 5)
        mpd.restart_playback.assert_not_called()
        self.assertEqual(m.silent_speakers(), [])

    async def test_sound_back_clears_the_report(self):
        m, mpd, p = build([0, 0, 0, 900])
        with p:
            await self.run_checks(m, 4)
        self.assertEqual(m.silent_speakers(), [])

    async def test_cooldown_between_reopens(self):
        m, mpd, p = build([0, 0, 0, 800, 0, 0, 0])
        with p:
            await self.run_checks(m, 7)
        mpd.restart_playback.assert_awaited_once()  # second silence within the cooldown

    async def test_unreadable_monitor_gives_no_verdict(self):
        m, mpd, p = build([0, 0, None, 0])
        with p:
            results = await self.run_checks(m, 4)
        self.assertEqual(results[-1], [A])

    async def test_paused_speaker_is_not_sampled(self):
        m, mpd, p = build([])
        mpd.get_status.return_value = {"state": "pause"}
        with p:
            self.assertEqual(await m.check_silence(), [])

    async def test_nothing_without_pulseaudio(self):
        m, mpd, p = build([])
        m.pulse = None
        with p:
            self.assertEqual(await m.check_silence(), [])


class PeakTest(unittest.TestCase):

    def test_peak_of_silence_and_sound(self):
        self.assertEqual(gap_monitor.peak_of(b"\x00\x00" * 100), 0)
        self.assertEqual(gap_monitor.peak_of(b"\x10\x00\xf0\xff"), 16)  # 16 and -16
        self.assertEqual(gap_monitor.peak_of(b""), 0)

    def test_recorders_are_pinned_to_their_sink(self):
        self.assertIn("--no-move", gap_monitor.parec_command(SINK, "x"))
        self.assertIn(f"--device={SINK}.monitor", gap_monitor.parec_command(SINK, "x"))


class GapMonitorRestartTest(unittest.TestCase):
    """25.11.2026: the recorder of a dropped speaker followed onto another
    speaker's monitor and reported that speaker twice."""

    def test_recording_starts_again_after_the_sink_vanished(self):
        mon = gap_monitor.GapMonitor([SINK], minutes=1)
        calls = []

        def once(sink):
            calls.append(sink)
            if len(calls) == 3:
                mon._stopping = True
                return False
            return True  # ended early: sink gone
        mon._read_once = once
        with patch.object(gap_monitor, "RESTART_DELAY_S", 0):
            mon._read_blocking(SINK)
        self.assertEqual(len(calls), 3)
        self.assertEqual(mon.restarts[SINK], 2)


if __name__ == "__main__":
    unittest.main()
