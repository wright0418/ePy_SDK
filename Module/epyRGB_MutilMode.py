from machine import LED
from utime import sleep_ms, ticks_ms, ticks_diff
import urandom as random  # MicroPython urandom

# --- Configuration (centralized constants) ---
NUM_LEDS = 64
BRIGHTNESS = 50  # 0~100
DEFAULT_UPDATE_HZ = 30  # buffer update frequency (Hz) (1/30s)
DEFAULT_WRITE_HZ = 30  # hardware write frequency (Hz)
DEFAULT_SPEED = 8  # how many wheel-steps to advance each buffer update
MAIN_LOOP_SLEEP_MS = 1


class RGBModeDisplay:
    def __init__(self, num_leds=NUM_LEDS, brightness=BRIGHTNESS,
                 update_hz=DEFAULT_UPDATE_HZ, write_hz=DEFAULT_WRITE_HZ,
                 speed=DEFAULT_SPEED):
        self.num_leds = num_leds
        self.brightness = brightness
        self.update_hz = update_hz
        self.write_hz = write_hz
        self.speed = speed
        self.led = LED(LED.RGB)
        self.led.lightness(self.brightness)
        # core runtime state
        self.led_buffer = [(0, 0, 0) for _ in range(self.num_leds)]
        self.phase = 0
        self.write_request = False
        # state for original modes
        self.chase_pos = 0
        self.twinkle_counters = [0] * self.num_leds
        self.twinkle_colors = [(0, 0, 0)] * self.num_leds
        # additional state for extra modes
        self.sparkle_counters = [0] * self.num_leds
        self.sparkle_colors = [(0, 0, 0)] * self.num_leds
        self.meteor_pos = 0
        self.meteor_size = max(3, self.num_leds // 8)
        self.scanner_pos = 0
        self.scanner_dir = 1
        self.strobe_on = False
        self.fire_heat = [0] * self.num_leds
        self.confetti_decay = 20
        self.color_chase_offset = 0
        # intervals in ms
        self.fill_interval_ms = max(1, int(1000.0 / self.update_hz))
        self.update_interval_ms = max(1, int(1000.0 / self.write_hz))

        self.last_fill_time = ticks_ms()
        self.last_update_time = ticks_ms()

        # mode can be a callable or a name mapping. register available modes
        self.mode = self.rainbow_mode
        self._modes = {
            'rainbow': self.rainbow_mode,
            'solid': self.solid_color_mode,
            'primary_cycle': self.primary_cycle_mode,
            'random_flash': self.random_flash_mode,
            'chase': self.chase_mode,
            'breathing': self.breathing_mode,
            'color_wipe': self.color_wipe_mode,
            'gradient': self.gradient_mode,
            'theater_chase': self.theater_chase_mode,
            'twinkle': self.twinkle_mode,
            # extra modes
            'sparkle': self.sparkle_mode,
            'meteor': self.meteor_mode,
            'strobe': self.strobe_mode,
            'scanner': self.scanner_mode,
            'confetti': self.confetti_mode,
            'fire': self.fire_mode,
            'rainbow_cycle': self.rainbow_cycle_mode,
            'color_chase': self.color_chase_mode,
            'pulse': self.pulse_mode,
            'gradient_shift': self.gradient_shift_mode,
        }
        # precompute a 256-entry palette to avoid repeated wheel calculations
        self.palette = [self.wheel(i) for i in range(256)]
        self.running = False

    # color wheel helper
    def wheel(self, pos):
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return (r, g, b)

    # small helpers to reduce duplicated code
    def set_all(self, color):
        """Set entire led_buffer to a single color (uses same tuple repeatedly)."""
        self.led_buffer = [color] * self.num_leds

    def fade_all(self, factor):
        """Fade current buffer by factor (0..1)."""
        for i in range(self.num_leds):
            v = self.led_buffer[i]
            self.led_buffer[i] = (int(v[0] * factor),
                                  int(v[1] * factor), int(v[2] * factor))

    def rainbow_mode(self):
        for i in range(self.num_leds):
            rc_index = (i * 255 // self.num_leds) + self.phase
            self.led_buffer[i] = self.palette[rc_index & 255]

    def solid_color_mode(self, color=None):
        # fill with a single color from wheel if not provided
        c = color if color is not None else self.palette[self.phase & 255]
        for i in range(self.num_leds):
            self.led_buffer[i] = c

    def primary_cycle_mode(self):
        # cycle R,G,B every ~85 steps
        idx = (self.phase // 85) % 3
        if idx == 0:
            c = (255, 0, 0)
        elif idx == 1:
            c = (0, 255, 0)
        else:
            c = (0, 0, 255)
        for i in range(self.num_leds):
            self.led_buffer[i] = c

    def random_flash_mode(self):
        # entire strip random color each update
        c = (random.getrandbits(8), random.getrandbits(8), random.getrandbits(8))
        for i in range(self.num_leds):
            self.led_buffer[i] = c

    def chase_mode(self):
        # single dot chasing
        for i in range(self.num_leds):
            self.led_buffer[i] = (0, 0, 0)
        pos = self.chase_pos % self.num_leds
        self.led_buffer[pos] = self.palette[self.phase & 255]
        self.chase_pos = (self.chase_pos + 1) % self.num_leds

    def breathing_mode(self):
        # simple triangle-wave breathing for intensity on a base color
        base = self.palette[self.phase & 255]
        t = (self.phase % 256) / 255.0
        intensity = 1.0 - abs(2.0 * t - 1.0)
        for i in range(self.num_leds):
            self.led_buffer[i] = (
                int(base[0] * intensity), int(base[1] * intensity), int(base[2] * intensity))

    def color_wipe_mode(self):
        # progressively fill from 0..n
        n = (self.phase * self.num_leds) // 256
        c = self.palette[self.phase & 255]
        for i in range(self.num_leds):
            self.led_buffer[i] = c if i <= n else (0, 0, 0)

    def gradient_mode(self):
        # gradient along strip using wheel
        for i in range(self.num_leds):
            self.led_buffer[i] = self.palette[(
                (i * 255) // max(1, self.num_leds) + self.phase) & 255]

    def theater_chase_mode(self):
        # on, off, off pattern shifting
        for i in range(self.num_leds):
            if (i + self.phase) % 3 == 0:
                self.led_buffer[i] = self.palette[self.phase & 255]
            else:
                self.led_buffer[i] = (0, 0, 0)

    def twinkle_mode(self):
        # random twinkles with decay counters
        for i in range(self.num_leds):
            if self.twinkle_counters[i] > 0:
                # decay
                self.twinkle_counters[i] -= 1
                self.led_buffer[i] = self.twinkle_colors[i]
            else:
                # small chance to start a twinkle
                if (random.getrandbits(8) % 50) == 0:
                    col = self.palette[random.getrandbits(8) & 255]
                    self.twinkle_colors[i] = col
                    self.twinkle_counters[i] = random.getrandbits(5) % 20 + 5
                    self.led_buffer[i] = col
                else:
                    self.led_buffer[i] = (0, 0, 0)

    # --- Additional 10 modes ---
    def sparkle_mode(self):
        # sporadic single-pixel sparkles
        for i in range(self.num_leds):
            if self.sparkle_counters[i] > 0:
                self.sparkle_counters[i] -= 1
                self.led_buffer[i] = self.sparkle_colors[i]
            else:
                if random.getrandbits(8) % 60 == 0:
                    c = self.palette[random.getrandbits(8) & 255]
                    self.sparkle_colors[i] = c
                    self.sparkle_counters[i] = random.getrandbits(5) % 10 + 3
                    self.led_buffer[i] = c
                else:
                    self.led_buffer[i] = (0, 0, 0)

    def meteor_mode(self):
        # moving meteor with fading tail
        tail_fade = 0.7
        for i in range(self.num_leds):
            v = self.led_buffer[i]
            self.led_buffer[i] = (
                int(v[0] * 0.3), int(v[1] * 0.3), int(v[2] * 0.3))
        pos = self.meteor_pos % self.num_leds
        for t in range(self.meteor_size):
            idx = (pos - t) % self.num_leds
            intensity = max(0.0, 1.0 - (t / max(1, self.meteor_size)))
            w = self.palette[self.phase & 255]
            self.led_buffer[idx] = (
                int(w[0] * intensity), int(w[1] * intensity), int(w[2] * intensity))
        self.meteor_pos = (self.meteor_pos + 1) % self.num_leds

    def strobe_mode(self):
        # flash whole strip on/off
        if random.getrandbits(8) % 10 == 0:
            self.strobe_on = not self.strobe_on
        c = self.palette[self.phase & 255] if self.strobe_on else (0, 0, 0)
        for i in range(self.num_leds):
            self.led_buffer[i] = c

    def scanner_mode(self):
        # single pixel scanner back and forth
        for i in range(self.num_leds):
            self.led_buffer[i] = (0, 0, 0)
        self.led_buffer[self.scanner_pos] = self.palette[self.phase & 255]
        self.scanner_pos += self.scanner_dir
        if self.scanner_pos >= self.num_leds or self.scanner_pos < 0:
            self.scanner_dir *= -1
            self.scanner_pos = max(0, min(self.scanner_pos, self.num_leds - 1))

    def confetti_mode(self):
        # random small colored dots with decay
        for i in range(self.num_leds):
            # decay existing
            if self.sparkle_counters[i] > 0:
                self.sparkle_counters[i] -= 1
                self.led_buffer[i] = self.sparkle_colors[i]
            else:
                if random.getrandbits(8) % 30 == 0:
                    c = self.palette[random.getrandbits(8) & 255]
                    self.sparkle_colors[i] = c
                    self.sparkle_counters[i] = self.confetti_decay
                    self.led_buffer[i] = c
                else:
                    self.led_buffer[i] = (0, 0, 0)

    def fire_mode(self):
        # simple fire-like effect using 'heat' array
        # cool down
        for i in range(self.num_leds):
            cooldown = random.getrandbits(5) % 3
            self.fire_heat[i] = max(0, self.fire_heat[i] - cooldown)
        # heat up randomly near bottom
        if random.getrandbits(8) % 2 == 0:
            idx = random.getrandbits(8) % self.num_leds
            self.fire_heat[idx] = min(
                255, self.fire_heat[idx] + random.getrandbits(6))
        # map heat to color
        for i in range(self.num_leds):
            h = self.fire_heat[i]
            # simple gradient: red to yellow to white
            r = min(255, h)
            g = min(255, int(h * 0.6))
            b = max(0, int(h * 0.2) - 10)
            self.led_buffer[i] = (r, g, b)

    def rainbow_cycle_mode(self):
        # full-strip rainbow that shifts along the strip
        for i in range(self.num_leds):
            self.led_buffer[i] = self.palette[(
                (i * 256 // self.num_leds) + self.color_chase_offset) & 255]
        self.color_chase_offset = (self.color_chase_offset + self.speed) % 256

    def color_chase_mode(self):
        # several color blocks chasing each other
        seg = max(1, self.num_leds // 8)
        for i in range(self.num_leds):
            if ((i + self.color_chase_offset) // seg) % 2 == 0:
                self.led_buffer[i] = self.palette[self.phase & 255]
            else:
                self.led_buffer[i] = (0, 0, 0)
        self.color_chase_offset = (self.color_chase_offset + 1) % 256

    def pulse_mode(self):
        # global pulse (fade in/out)
        t = (self.phase % 256) / 255.0
        intensity = 0.5 + 0.5 * (1.0 - abs(2.0 * t - 1.0))
        c = self.palette[self.phase & 255]
        for i in range(self.num_leds):
            self.led_buffer[i] = (int(c[0] * intensity),
                                  int(c[1] * intensity), int(c[2] * intensity))

    def gradient_shift_mode(self):
        # gradient that slowly shifts hue
        for i in range(self.num_leds):
            self.led_buffer[i] = self.palette[(
                (i * 255 // max(1, self.num_leds)) + self.phase) & 255]

    def set_mode(self, mode):
        """Set display mode. mode can be a callable or the name of a registered mode."""
        if callable(mode):
            self.mode = mode
        elif isinstance(mode, str):
            # lookup named modes from the registry
            if mode in self._modes:
                self.mode = self._modes[mode]
            else:
                # unknown string -> default to rainbow
                self.mode = self.rainbow_mode
        else:
            self.mode = self.rainbow_mode

    def set_speed(self, speed):
        self.speed = int(speed)

    def set_update_hz(self, hz):
        self.update_hz = hz
        self.fill_interval_ms = max(1, int(1000.0 / self.update_hz))

    def set_write_hz(self, hz):
        self.write_hz = hz
        self.update_interval_ms = max(1, int(1000.0 / self.write_hz))

    def fill_if_due(self):
        now = ticks_ms()
        if ticks_diff(now, self.last_fill_time) >= self.fill_interval_ms:
            # call current mode to fill buffer
            try:
                self.mode()
            except Exception:
                # fallback to rainbow
                self.rainbow_mode()
            # advance phase
            self.phase = (self.phase + self.speed) % 256
            self.last_fill_time = now

    def update_if_due(self):
        now = ticks_ms()
        if ticks_diff(now, self.last_update_time) >= self.update_interval_ms:
            self.write_request = True
            self.update_leds()
            self.last_update_time = now

    def update_leds(self):
        # only write when requested; safe to call from main loop
        if not self.write_request:
            return
        try:
            self.led.rgb_write(tuple(self.led_buffer))
        except Exception:
            try:
                self.led.rgb_write(self.led_buffer)
            except Exception:
                pass
        self.write_request = False

    def run(self):
        self.running = True
        while self.running:
            self.fill_if_due()
            self.update_if_due()
            sleep_ms(MAIN_LOOP_SLEEP_MS)

    def stop(self):
        self.running = False


if __name__ == '__main__':
    disp = RGBModeDisplay()
    mode_names = list(disp._modes.keys())
    show_seconds = 10
    try:
        for name in mode_names:
            print('Mode:', name)
            try:
                disp.set_mode(name)
            except Exception:
                disp.set_mode(disp.rainbow_mode)

            start = ticks_ms()
            duration_ms = int(show_seconds * 1000)
            while ticks_diff(ticks_ms(), start) < duration_ms:
                disp.fill_if_due()
                disp.update_if_due()
                sleep_ms(MAIN_LOOP_SLEEP_MS)
    except KeyboardInterrupt:
        # user interrupted; stop cleanly
        disp.stop()
    finally:
        # optional: turn off LEDs or leave them as-is
        try:
            disp.led.rgb_write([(0, 0, 0)] * disp.num_leds)
        except Exception:
            pass
