import unittest
from types import SimpleNamespace
import pulsectl

from bt_audio_manager.audio.pulse import PulseAudioManager


class FakePulse:
    def __init__(self, sinks, sink_inputs, event_stream):
        self._sinks = sinks
        self._sink_inputs = sink_inputs
        self._event_stream = event_stream
        self.volume_calls = []

    async def sink_input_info(self, index):
        return self._event_stream

    async def sink_info(self, index):
        return next(sink for sink in self._sinks if sink.index == index)

    async def volume_set_all_chans(self, sink_input, volume):
        self.volume_calls.append((sink_input.index, volume))


class TestMpdStreamNormalization(unittest.IsolatedAsyncioTestCase):
    async def test_normalizes_exact_new_mpd_stream_when_another_mpd_stream_exists(self):
        sink = SimpleNamespace(index=7, name="bluez_sink.6C_0D_C4_30_50_F6.a2dp_sink")
        old_mpd_stream = SimpleNamespace(
            index=101,
            sink=7,
            proplist={
                "application.name": "Music Player Daemon",
                "application.process.binary": "mpd",
            },
        )
        new_mpd_stream = SimpleNamespace(
            index=102,
            sink=7,
            proplist={
                "application.name": "Music Player Daemon",
                "application.process.binary": "mpd",
            },
        )
        pulse = PulseAudioManager()
        pulse._pulse = FakePulse([sink], [old_mpd_stream, new_mpd_stream], new_mpd_stream)

        updated = await pulse._normalize_new_mpd_stream(new_mpd_stream.index)

        self.assertTrue(updated)
        self.assertEqual(pulse._pulse.volume_calls, [(new_mpd_stream.index, 1.0)])

    async def test_skips_mpd_stream_on_non_bluetooth_sink(self):
        sink = SimpleNamespace(index=7, name="alsa_output.pci-0000_00_1f.3.analog-stereo")
        mpd_stream = SimpleNamespace(
            index=101,
            sink=7,
            proplist={
                "application.name": "Music Player Daemon",
                "application.process.binary": "mpd",
            },
        )
        pulse = PulseAudioManager()
        pulse._pulse = FakePulse([sink], [mpd_stream], mpd_stream)

        updated = await pulse._normalize_new_mpd_stream(mpd_stream.index)

        self.assertFalse(updated)
        self.assertEqual(pulse._pulse.volume_calls, [])

    async def test_skips_sink_with_bluez_only_in_its_name(self):
        sink = SimpleNamespace(index=7, name="combined_bluez_sink")
        mpd_stream = SimpleNamespace(
            index=101,
            sink=7,
            proplist={
                "application.name": "Music Player Daemon",
                "application.process.binary": "mpd",
            },
        )
        pulse = PulseAudioManager()
        pulse._pulse = FakePulse([sink], [mpd_stream], mpd_stream)

        updated = await pulse._normalize_new_mpd_stream(mpd_stream.index)

        self.assertFalse(updated)
        self.assertEqual(pulse._pulse.volume_calls, [])

    async def test_skips_non_mpd_stream_on_bluetooth_sink(self):
        sink = SimpleNamespace(index=7, name="bluez_sink.6C_0D_C4_30_50_F6.a2dp_sink")
        music_stream = SimpleNamespace(
            index=101,
            sink=7,
            proplist={
                "application.name": "Another music player",
                "application.process.binary": "other-player",
            },
        )
        pulse = PulseAudioManager()
        pulse._pulse = FakePulse([sink], [music_stream], music_stream)

        updated = await pulse._normalize_new_mpd_stream(music_stream.index)

        self.assertFalse(updated)
        self.assertEqual(pulse._pulse.volume_calls, [])



A = "41:42:00:00:08:75"
B = "41:42:00:00:10:59"
C = "41:42:00:00:09:70"


def _sink(index, mac):
    return SimpleNamespace(index=index, name=f"bluez_sink.{mac.replace(':', '_')}.a2dp_sink")


def _mpd_stream(index, sink, mac=None, pid=None):
    props = {"application.name": "Music Player Daemon", "application.process.binary": "mpd"}
    if mac:
        props["module-stream-restore.id"] = f"bt-audio-manager:{mac}"
    if pid:
        props["application.process.id"] = str(pid)
    return SimpleNamespace(index=index, sink=sink, proplist=props,
                           volume=SimpleNamespace(values=[1.0, 1.0]),
                           channel_list=["front-left", "front-right"], mute=0)


class FakePinPulse:
    def __init__(self, sinks, streams, entries=(), default_sink=None):
        self.sinks = sinks
        self.streams = {s.index: s for s in streams}
        self.moves = []
        self.mutes = []
        self.entries = list(entries)
        self.writes = []
        self.default_sink = default_sink

    async def stream_restore_read(self):
        return list(self.entries)

    async def stream_restore_write(self, entry, mode="merge", apply_immediately=False):
        self.writes.append((entry.name, entry.device, mode, apply_immediately))

    async def server_info(self):
        return SimpleNamespace(default_sink_name=self.default_sink)

    async def sink_input_info(self, index):
        return self.streams[index]

    async def sink_input_list(self):
        return list(self.streams.values())

    async def sink_info(self, index):
        return next(s for s in self.sinks if s.index == index)

    async def sink_list(self):
        return list(self.sinks)

    async def sink_input_move(self, stream_index, sink_index):
        self.moves.append((stream_index, sink_index))
        self.streams[stream_index].sink = sink_index

    async def sink_input_mute(self, stream_index, mute=True):
        self.mutes.append((stream_index, bool(mute)))
        self.streams[stream_index].mute = bool(mute)


class TestMpdStreamPinning(unittest.IsolatedAsyncioTestCase):
    """#318: a running MPD stream moved onto another speaker goes back home.

    Seen when a speaker reconnects while others play: PulseAudio drags the
    running streams onto the new sink and two stations mix on one speaker,
    while Home Assistant still shows both as playing correctly.
    """

    def build(self, sinks, streams):
        manager = PulseAudioManager()
        manager._pulse = FakePinPulse(sinks, streams)
        return manager

    async def test_stray_stream_is_moved_back(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=3, mac=A)])
        self.assertTrue(await manager._pin_mpd_stream(10))
        self.assertEqual(manager._pulse.moves, [(10, 1)])

    async def test_stream_on_its_own_sink_is_left_alone(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=1, mac=A)])
        self.assertFalse(await manager._pin_mpd_stream(10))
        self.assertEqual(manager._pulse.moves, [])

    async def test_foreign_streams_are_left_alone(self):
        foreign = SimpleNamespace(index=20, sink=3, proplist={"application.name": "Music Assistant"})
        manager = self.build([_sink(1, A), _sink(3, C)], [foreign])
        self.assertFalse(await manager._pin_mpd_stream(20))
        self.assertEqual(manager._pulse.moves, [])

    async def test_nothing_happens_while_the_own_sink_is_missing(self):
        manager = self.build([_sink(3, C)], [_mpd_stream(10, sink=3, mac=A)])
        self.assertFalse(await manager._pin_mpd_stream(10))
        self.assertEqual(manager._pulse.moves, [])

    async def test_new_sink_brings_every_stray_home(self):
        # C reconnected and both running streams were dragged onto it.
        manager = self.build(
            [_sink(1, A), _sink(2, B), _sink(3, C)],
            [_mpd_stream(10, sink=3, mac=A), _mpd_stream(11, sink=3, mac=B),
             _mpd_stream(12, sink=3, mac=C)],
        )
        self.assertEqual(await manager._pin_all_mpd_streams(), 2)
        self.assertEqual(sorted(manager._pulse.moves), [(10, 1), (11, 2)])

    async def test_mac_case_does_not_matter(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=3, mac=A.lower())])
        self.assertTrue(await manager._pin_mpd_stream(10))

    async def test_pid_resolver_identifies_streams_without_restore_id(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=3, pid=4242)])
        manager.set_stream_owner_resolver(
            lambda props: A if props.get("application.process.id") == "4242" else None
        )
        self.assertTrue(await manager._pin_mpd_stream(10))
        self.assertEqual(manager._pulse.moves, [(10, 1)])

    async def test_move_back_is_reported_with_the_owner(self):
        """A moved stream can stay silent (13.11.2026) — the owner must hear of it."""
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=3, mac=A)])
        moved = []
        manager.on_stream_moved_back(moved.append)
        await manager._pin_mpd_stream(10)
        self.assertEqual(moved, [A.upper()])

    async def test_no_report_when_nothing_moved(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=1, mac=A)])
        moved = []
        manager.on_stream_moved_back(moved.append)
        await manager._pin_mpd_stream(10)
        self.assertEqual(moved, [])

    async def test_gives_up_when_something_keeps_moving_the_stream(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=3, mac=A)])
        for _ in range(manager.PIN_MAX_MOVES):
            self.assertTrue(await manager._pin_mpd_stream(10))
            manager._pulse.streams[10].sink = 3  # moved away again
        self.assertFalse(await manager._pin_mpd_stream(10))
        self.assertEqual(len(manager._pulse.moves), manager.PIN_MAX_MOVES)


class TestOrphanedStreamMuting(unittest.IsolatedAsyncioTestCase):
    """25.11.2026: when a speaker dropped, PulseAudio put its stream on the
    default sink and ~2 s of its station played over another speaker."""

    def build(self, sinks, streams):
        manager = PulseAudioManager()
        manager._pulse = FakePinPulse(sinks, streams)
        return manager

    async def test_stream_of_a_gone_speaker_is_muted_once(self):
        manager = self.build([_sink(3, C)], [_mpd_stream(10, sink=3, mac=A)])
        self.assertFalse(await manager._pin_mpd_stream(10))
        await manager._pin_mpd_stream(10)  # the "change" event of the mute itself
        self.assertEqual(manager._pulse.mutes, [(10, True)])
        self.assertEqual(manager._pulse.moves, [])

    async def test_moved_home_stream_is_unmuted(self):
        manager = self.build([_sink(3, C)], [_mpd_stream(10, sink=3, mac=A)])
        await manager._pin_mpd_stream(10)
        manager._pulse.sinks.append(_sink(1, A))  # the speaker is back
        self.assertEqual(await manager._pin_all_mpd_streams(), 1)
        self.assertEqual(manager._pulse.moves, [(10, 1)])
        self.assertEqual(manager._pulse.mutes, [(10, True), (10, False)])

    async def test_muted_stream_on_its_own_sink_is_unmuted(self):
        stream = _mpd_stream(10, sink=1, mac=A)
        stream.mute = 1  # muted from outside (test on 25.11.2026)
        manager = self.build([_sink(1, A)], [stream])
        await manager._pin_mpd_stream(10)
        self.assertEqual(manager._pulse.mutes, [(10, False)])

    async def test_unmuted_stream_on_its_own_sink_is_not_touched(self):
        manager = self.build([_sink(1, A)], [_mpd_stream(10, sink=1, mac=A)])
        await manager._pin_mpd_stream(10)
        self.assertEqual(manager._pulse.mutes, [])

    async def test_foreign_streams_are_never_muted(self):
        foreign = SimpleNamespace(index=20, sink=3, proplist={"application.name": "Music Assistant"},
                                  mute=0)
        manager = self.build([_sink(3, C)], [foreign])
        await manager._pin_mpd_stream(20)
        self.assertEqual(manager._pulse.mutes, [])


class TestMpdStreamBinding(unittest.IsolatedAsyncioTestCase):
    """23.11.2026: a stream that names its sink gets no preferred sink in
    PulseAudio 17 and follows the default sink — bind it to its speaker."""

    def build(self, sinks, streams, entries=(), default_sink=None):
        manager = PulseAudioManager()
        manager._pulse = FakePinPulse(sinks, streams, entries, default_sink)
        return manager

    async def test_stream_on_its_own_sink_is_bound_once(self):
        manager = self.build([_sink(1, A)], [_mpd_stream(10, sink=1, mac=A)])
        await manager._pin_mpd_stream(10)
        await manager._pin_mpd_stream(10)  # a later "change" event
        self.assertEqual(manager._pulse.writes, [
            (f"bt-audio-manager:{A}", _sink(1, A).name, "replace", True),
        ])
        self.assertEqual(manager._pulse.moves, [])

    async def test_existing_entry_keeps_its_volume_and_gets_the_device(self):
        entry = pulsectl.PulseExtStreamRestoreInfo(
            f"bt-audio-manager:{A}", volume=[0.5, 0.5],
            channel_list=["front-left", "front-right"], mute=False, device=None)
        manager = self.build([_sink(1, A)], [_mpd_stream(10, sink=1, mac=A)], entries=[entry])
        await manager._pin_mpd_stream(10)
        self.assertEqual(entry.device, _sink(1, A).name)
        self.assertEqual([round(v, 2) for v in entry.volume.values], [0.5, 0.5])

    async def test_moved_back_stream_is_bound_too(self):
        manager = self.build([_sink(1, A), _sink(3, C)], [_mpd_stream(10, sink=3, mac=A)],
                             default_sink=_sink(3, C).name)
        self.assertTrue(await manager._pin_mpd_stream(10))
        self.assertEqual([w[1] for w in manager._pulse.writes], [_sink(1, A).name])

    async def test_foreign_stream_is_not_bound(self):
        foreign = SimpleNamespace(index=20, sink=1, proplist={"application.name": "Music Assistant"})
        manager = self.build([_sink(1, A)], [foreign])
        await manager._pin_mpd_stream(20)
        self.assertEqual(manager._pulse.writes, [])

    async def test_a_failing_write_is_not_retried_on_every_event(self):
        manager = self.build([_sink(1, A)], [_mpd_stream(10, sink=1, mac=A)])
        calls = []

        async def broken(*a, **kw):
            calls.append(1)
            raise RuntimeError("no stream-restore")
        manager._pulse.stream_restore_write = broken
        await manager._pin_mpd_stream(10)
        await manager._pin_mpd_stream(10)
        self.assertEqual(len(calls), 1)

    async def test_a_new_stream_index_is_bound_again(self):
        manager = self.build([_sink(1, A)], [_mpd_stream(10, sink=1, mac=A)])
        await manager._pin_mpd_stream(10)
        manager._bound_streams.discard(10)  # "remove" event
        manager._pulse.streams[11] = _mpd_stream(11, sink=1, mac=A)
        await manager._pin_mpd_stream(11)
        self.assertEqual(len(manager._pulse.writes), 2)

    async def test_routing_shows_default_sink_and_streams(self):
        manager = self.build([_sink(1, A), _sink(3, C)],
                             [_mpd_stream(10, sink=1, mac=A), _mpd_stream(12, sink=1, mac=C)],
                             default_sink=_sink(1, A).name)
        await manager._pin_mpd_stream(10)
        routing = await manager.mpd_stream_routing()
        self.assertEqual(routing["default_sink"], _sink(1, A).name)
        self.assertEqual(
            [(s["speaker"], s["on_own_sink"], s["bound"]) for s in routing["mpd_streams"]],
            [(A, True, True), (C, False, False)],
        )


if __name__ == "__main__":
    unittest.main()
