from Module import epyBuzzerMusic as m
import pytest
import sys
import types
import time
import threading
import os

# make sure repo root is importable
repo_root = r"d:\個人資料庫\Github\ePy_SDK"
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# ---- fake utime (ModuleType) ----
fake_utime = types.ModuleType('utime')


def sleep_ms(ms):
    time.sleep(ms / 1000.0)


def ticks_ms():
    return int(time.time() * 1000)


fake_utime.sleep_ms = sleep_ms
fake_utime.ticks_ms = ticks_ms
sys.modules['utime'] = fake_utime

# ---- fake _thread (ModuleType) ----
fake_thread = types.ModuleType('_thread')


def start_new_thread(func, args):
    t = threading.Thread(target=func, args=args, daemon=True)
    t.start()
    return t


fake_thread.start_new_thread = start_new_thread
sys.modules['_thread'] = fake_thread

# ---- fake machine (ModuleType with Pin/Timer classes) ----
machine_mod = types.ModuleType('machine')


class Pin:
    OUT = 0

    class epy:
        P9 = 9
        P22 = 22

    def __init__(self, pin, mode=None):
        self._v = 0

    def value(self, v=None):
        if v is None:
            return int(self._v)
        self._v = int(v) & 0x1
        return self._v


class Timer:
    def __init__(self, id=0):
        self._freq = 0
        self._cb = None
        self._thr = None
        self._stop = threading.Event()

    def init(self, freq=0):
        self._freq = freq

    def callback(self, cb):
        # stop old thread
        if getattr(self, '_thr', None):
            self._stop.set()
            try:
                self._thr.join()
            except Exception:
                pass
            self._stop = threading.Event()
            self._thr = None
        self._cb = cb
        if cb is None:
            return
        if not self._freq:
            return
        interval = 1.0 / float(self._freq)

        def run():
            while not self._stop.is_set():
                try:
                    cb(self)
                except Exception:
                    pass
                time.sleep(interval)

        self._thr = threading.Thread(target=run, daemon=True)
        self._thr.start()


machine_mod.Pin = Pin
machine_mod.Timer = Timer
sys.modules['machine'] = machine_mod

# ---- import module under test (after fake modules injected) ----

# Optional: enable Windows audio output for buzzer simulation when
# running tests locally. Controlled by environment variable ENABLE_AUDIO.
if os.name == 'nt' and os.environ.get('ENABLE_AUDIO'):
    try:
        import winsound
    except Exception:
        winsound = None

    if winsound:
        _orig_playFreq = m.Music._playFreq

        def _playFreq_with_audio(self, playFreq, playtime_ms):
            # rest: delegate to original
            if playFreq <= 0:
                return _orig_playFreq(self, playFreq, playtime_ms)
            try:
                # winsound.Beep blocks until completion
                winsound.Beep(int(playFreq), int(playtime_ms))
                return
            except Exception:
                return _orig_playFreq(self, playFreq, playtime_ms)

        m.Music._playFreq = _playFreq_with_audio


def test_playFreq_sync():
    t = Timer(0)
    muz = m.Music(t, pin=Pin.epy.P9)
    muz.playFreq(440, 150)
    assert muz.getState() == 'STOP'


def test_play_sequence():
    t = Timer(1)
    muz = m.Music(t, pin=Pin.epy.P22)
    muz.tempo(4, 200)
    muz.play(["A4:1", "R:1"], loop=False)
    timeout = time.time() + 5
    while muz.getState() != 'STOP' and time.time() < timeout:
        time.sleep(0.05)
    assert muz.getState() == 'STOP'


@pytest.mark.skipif(not (os.name == 'nt' and os.environ.get('ENABLE_AUDIO')),
                    reason='ENABLE_AUDIO not set or not on Windows')
def test_play_with_audio():
    """Play a short beep using winsound.Beep — only runs when ENABLE_AUDIO=1 on Windows."""
    t = Timer(0)
    muz = m.Music(t, pin=Pin.epy.P9)
    # short beep (300ms) — winsound.Beep will block until finished
    muz.playFreq(440, 300)
    assert muz.getState() == 'STOP'


# (removed manual debug beep — use the pytest audio test which runs when
# ENABLE_AUDIO is set)
