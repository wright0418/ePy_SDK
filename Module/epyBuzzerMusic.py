from machine import Pin, Timer
import utime
try:
    import _thread
except Exception:
    _thread = None


class Music:
    """Play simple note sequences on a buzzer pin using a hardware Timer when
    available. Includes a precomputed note->frequency lookup cache for speed.
    """

    def __init__(self, tim: Timer, pin=Pin.epy.P9):
        # semitone offsets relative to A (A is 0)
        self.tone_idx = {
            'R': 0, 'A': 0, 'Ab': -1, 'G#': -1, 'G': -2, 'Gb': -3,
            'F#': -3, 'F': -4, 'E': -5, 'Eb': -6, 'D#': -6, 'D': -7,
            'Db': -8, 'C#': -8, 'C': -9, 'B': 2, 'Bb': 1, 'A#': 1
        }

        # reference
        self._freqA4 = 440.0
        # ratio per semitone (float)
        self._semitone_ratio = 2 ** (1 / 12)

        self._buzzer_pin = Pin(pin, Pin.OUT)
        self._timer = tim

        # tempo / duration handling
        self.ticks = 4
        self.bpm = 120
        self._lv = 4  # current octave used when omitted
        self._ticks = int(60000 / (self.bpm * self.ticks))

        # playback state
        self._state = 'STOP'
        self.loop = False
        self.music = []

        # frequency cache and prebuild common octaves
        self._freq_cache = {}
        self._build_freq_table(0, 8)

        # try to run playback thread if threading available
        if _thread:
            try:
                _thread.start_new_thread(self.play_music, ())
            except Exception:
                pass

    def play_music(self):
        while True:
            if self._state != 'START':
                utime.sleep_ms(10)
                continue
            for play_t in self.music:  # avoid creating new list
                if self._state == 'STOP':
                    break

                # manual parse to avoid split() creating list
                colon_pos = play_t.find(":")
                if colon_pos != -1:
                    token = play_t[:colon_pos]
                    duration_part = play_t[colon_pos + 1:]
                else:
                    token = play_t
                    duration_part = ""

                # rest
                if token.startswith('R'):
                    playFreq = 0
                else:
                    # parse note name and optional octave digit at end
                    if len(token) >= 2 and token[1] in ('#', 'b'):
                        name = token[0:2]
                        tail = token[2:]
                    else:
                        name = token[0]
                        tail = token[1:]

                    octave = self._lv
                    if tail and tail[-1].isdigit():
                        octave = int(tail[-1])
                        self._lv = octave

                    playFreq = self._get_freq_from_cache(name, octave)

                # duration (ms)
                if duration_part and duration_part.isdigit():
                    duration = int(duration_part) * \
                        int(60000 / (self.bpm * self.ticks))
                else:
                    duration = self._ticks

                self._playFreq(playFreq, int(duration))

            if self.loop and self._state != 'STOP':
                continue
            self._state = 'STOP'
            self.music = []

    def tempo(self, ticks=4, bpm=120):
        self.ticks = ticks
        self.bpm = bpm
        self._ticks = int(60000 / (self.bpm * self.ticks))

    def _build_freq_table(self, min_oct=0, max_oct=8):
        """Precompute note->frequency for a range of octaves."""
        for octv in range(min_oct, max_oct + 1):
            for name, offset in self.tone_idx.items():
                key = "{}{}".format(name, octv)
                if name == 'R':
                    self._freq_cache[key] = 0
                    continue
                steps = offset + 12 * (octv - 4)
                self._freq_cache[key] = self._freqA4 * \
                    (self._semitone_ratio ** steps)

    def _get_freq_from_cache(self, name, octave):
        key = "{}{}".format(name, octave)
        if key in self._freq_cache:
            return self._freq_cache[key]
        # compute and cache
        try:
            steps = self.tone_idx[name] + 12 * (octave - 4)
            freq = self._freqA4 * (self._semitone_ratio ** steps)
            self._freq_cache[key] = freq
            return freq
        except Exception:
            return 0

    def _buzzer_toggle(self, t):
        # toggle 0/1 value
        self._buzzer_pin.value(~self._buzzer_pin.value() & 0x1)

    def stop(self):
        self._state = 'STOP'
        # wait until current playlist cleared
        while self.music:
            utime.sleep_ms(5)

    def getState(self):
        return self._state

    def play(self, music, loop=False):
        if self._state == 'START':
            self.stop()
        self.music = music
        self.loop = loop
        self._state = 'START'

    def playFreq(self, playFreq, playtime_ms):
        # convenience sync play of a single frequency
        if self._state == 'STOP':
            self._state = 'START'
            self._playFreq(playFreq, playtime_ms)
            self._state = 'STOP'

    def _playFreq(self, playFreq, playtime_ms):
        # rest: just sleep
        if playFreq <= 0:
            utime.sleep_ms(playtime_ms)
            return

        # attempt hardware timer approach
        try:
            self._timer.init(freq=int(playFreq * 2))
            self._timer.callback(self._buzzer_toggle)
        except Exception:
            # fallback: toggle pin in software
            start = utime.ticks_ms()
            while (utime.ticks_ms() - start) < playtime_ms:
                self._buzzer_pin.value(1)
                utime.sleep_ms(1)
                self._buzzer_pin.value(0)
                utime.sleep_ms(1)
            return

        # wait duration
        start = utime.ticks_ms()
        while (utime.ticks_ms() - start) < playtime_ms:
            utime.sleep_ms(1)

        # stop timer callback
        try:
            self._timer.callback(None)
        except Exception:
            pass


if __name__ == '__main__':
    # simple demo (only useful on actual hardware)
    timer = Timer(0)
    music = Music(timer, pin=Pin.epy.P22)

    song = ["E4:2", "E", "F", "E", "D", "E", "A3:4", "D4:2",
            "C", "A3", "C4:4", "D", "D:2", "D", "E", "D:2", "C", "D"]

    music.play(song, loop=False)
    utime.sleep_ms(5000)
