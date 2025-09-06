from machine import LED, Timer
from utime import sleep_ms
import urandom as random  # 導入 urandom 模組用於隨機數

# 全域變數 (部分變為類別屬性)
NUM_LEDS = 64
BRIGHTNESS = 50  # 0~100
UPDATE_FREQ_HZ = 30  # 1/30 秒更新一次

# 輔助函數 (不屬於類別，因為它們是通用的)


def wheel(pos):
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


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class LEDDisplayManager:
    def __init__(self, num_leds, brightness, update_freq_hz):
        self.num_leds = num_leds
        self.brightness = brightness
        self.update_freq_hz = update_freq_hz
        self.led_buffer = [(0, 0, 0)] * self.num_leds  # 初始化 LED 顯示 buffer
        self.global_j = 0  # 用於動畫的步進計數
        self.rgb_led_obj = LED(LED.RGB)
        self.rgb_led_obj.lightness(self.brightness)

        # 用於星空閃爍模式
        self.active_stars = {}  # {led_index: (color, lifetime_steps)}

        self.display_modes = [
            self.rainbow_cycle_mode,
            self.solid_color_mode,
            self.blink_mode,
            self.chase_mode,
            self.fade_mode,
            self.random_color_mode,
            self.sparkle_mode,
            self.wipe_mode,
            self.starry_night_mode  # 新增星空閃爍模式
        ]
        self.current_mode_index = 0
        self.mode_switch_interval = self.update_freq_hz * 10  # 每 10 秒切換一次模式
        self.step_counter = 0

        self.tim = Timer(0, freq=self.update_freq_hz)
        self.tim.callback(self.timer_callback)

    # --- 顯示模式方法 ---
    def rainbow_cycle_mode(self):
        """彩虹滾動模式"""
        for i in range(self.num_leds):
            rc_index = (i * 256 // self.num_leds) + self.global_j
            self.led_buffer[i] = wheel(rc_index & 255)

    def solid_color_mode(self):
        """單一顏色模式"""
        color = wheel(self.global_j)  # 顏色隨時間變化
        for i in range(self.num_leds):
            self.led_buffer[i] = color

    def blink_mode(self):
        """閃爍模式"""
        color1 = (255, 0, 0)  # 紅色
        color2 = (0, 0, 255)  # 藍色

        if (self.global_j // 15) % 2 == 0:  # 每 15 步切換一次
            for i in range(self.num_leds):
                self.led_buffer[i] = color1
        else:
            for i in range(self.num_leds):
                self.led_buffer[i] = color2

    def chase_mode(self):
        """追逐模式"""
        color = (0, 255, 0)  # 綠色
        off_color = (0, 0, 0)

        for i in range(self.num_leds):
            if (i + self.global_j // 5) % 10 == 0:  # 每 5 步移動，追逐間隔為 10
                self.led_buffer[i] = color
            else:
                self.led_buffer[i] = off_color

    def fade_mode(self):
        """漸變模式 (從一種顏色漸變到另一種)"""
        start_color = (255, 0, 0)  # 紅色
        end_color = (0, 255, 0)  # 綠色

        fade_step = self.global_j % 100  # 100 步完成一個漸變週期

        if fade_step < 50:
            ratio = fade_step / 50.0
        else:
            ratio = (100 - fade_step) / 50.0

        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)

        for i in range(self.num_leds):
            self.led_buffer[i] = (r, g, b)

    def random_color_mode(self):
        """隨機顏色模式 (每個 LED 隨機變色)"""
        if self.global_j % 10 == 0:  # 每 10 步隨機生成新顏色
            for i in range(self.num_leds):
                r = random.getrandbits(8)
                g = random.getrandbits(8)
                b = random.getrandbits(8)
                self.led_buffer[i] = (r, g, b)

    def sparkle_mode(self):
        """閃爍點模式"""
        sparkle_color = (255, 255, 255)  # 白色
        off_color = (0, 0, 0)

        # 先清空所有 LED
        for i in range(self.num_leds):
            self.led_buffer[i] = off_color

        if self.global_j % 5 == 0:  # 每 5 步隨機點亮一個 LED
            pixel = random.randrange(self.num_leds)
            self.led_buffer[pixel] = sparkle_color

    def wipe_mode(self):
        """逐點擦拭模式"""
        wipe_color = (0, 0, 255)  # 藍色
        off_color = (0, 0, 0)

        for i in range(self.num_leds):
            self.led_buffer[i] = off_color  # 每次都清空

        # 逐點亮起
        current_pixel = self.global_j % (self.num_leds * 2)
        if current_pixel < self.num_leds:
            for i in range(current_pixel + 1):
                self.led_buffer[i] = wipe_color
        else:
            # 逐點熄滅
            for i in range(self.num_leds - (current_pixel - self.num_leds)):
                self.led_buffer[i] = wipe_color

    def starry_night_mode(self):
        """星空閃爍模式"""
        # 清空所有 LED
        for i in range(self.num_leds):
            self.led_buffer[i] = (0, 0, 0)

        # 更新現有的星星生命週期
        stars_to_remove = []
        for idx, (color, lifetime) in self.active_stars.items():
            lifetime -= 1
            if lifetime <= 0:
                stars_to_remove.append(idx)
            else:
                self.active_stars[idx] = (color, lifetime)
                self.led_buffer[idx] = color

        for idx in stars_to_remove:
            del self.active_stars[idx]

        # 隨機新增星星
        if random.randrange(10) < 3:  # 隨機機率新增星星
            num_new_stars = random.randrange(0, 6)  # 0-5 顆新星
            for _ in range(num_new_stars):
                pixel_idx = random.randrange(self.num_leds)
                if pixel_idx not in self.active_stars:
                    r = random.getrandbits(8)
                    g = random.getrandbits(8)
                    b = random.getrandbits(8)
                    color = (r, g, b)
                    # 每個亮的時間不一樣但小於 0.5sec (即 1到15步)
                    lifetime_steps = random.randrange(
                        1, self.update_freq_hz // 2 + 1)
                    self.active_stars[pixel_idx] = (color, lifetime_steps)
                    self.led_buffer[pixel_idx] = color

    # --- 內部管理方法 ---

    def update_led_buffer_manager(self):
        """由主程式呼叫，根據當前模式更新 LED 緩衝區的內容"""
        current_mode_func = self.display_modes[self.current_mode_index]
        current_mode_func()  # 模式函數現在直接使用類別的 global_j

        self.global_j = (self.global_j + 1) % 256  # 確保 global_j 在 0-255 範圍內循環

    def timer_callback(self, timer):
        """Timer 回調函數，負責將緩衝區的內容寫入 LED"""
        if self.rgb_led_obj is not None:
            self.rgb_led_obj.rgb_write(tuple(self.led_buffer))

    def run(self):
        """啟動 LED 顯示管理"""
        print("Starting LED display with multiple modes...")

        while True:
            self.update_led_buffer_manager()

            self.step_counter += 1
            if self.step_counter >= self.mode_switch_interval:
                self.step_counter = 0
                self.current_mode_index = (
                    self.current_mode_index + 1) % len(self.display_modes)
                print(
                    f"Switching to mode: {self.display_modes[self.current_mode_index].__name__}")

            # 這裡不需要 sleep_ms，因為 timer_callback 會自動在背景更新 LED
            # sleep_ms(1) # 可以根據需要加入少量延遲，以控制主迴圈的執行速度，但通常不需要


if __name__ == '__main__':
    # 實例化 LEDDisplayManager 並運行
    display_manager = LEDDisplayManager(NUM_LEDS, BRIGHTNESS, UPDATE_FREQ_HZ)
    display_manager.run()
