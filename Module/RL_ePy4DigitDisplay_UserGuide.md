# RL Four-Digit Display — User Guide

這份文件說明 Richlink-tech（RL）製作的 4 位數字顯示模組的 I2C 通訊協定、常用指令，以及如何在 MicroPython 上使用 `Module/ePy4Digit.py` 驅動程式。

## 硬體與接線

- VCC -> 3.3V (不要接 5V，可能會損壞模組)
- GND -> GND
- SDA -> MCU SDA
- SCL -> MCU SCL

預設 I2C 位址: `0x3D`（7-bit）

## I2C 通訊概要

模組使用非常簡單的字節式命令協定，所有命令都是透過 I2C 的寫入（no register pointer）送到裝置位址。

- I2C 位址: 0x3D
- 傳送型態: 單次寫入，byte array

已知命令:

1. SHOW_FOUR_DIGITAL (0x03)
   - 格式: [0x03, position, value]
   - position: 1..4 （1 = 最左，4 = 最右）
   - value: 顯示代碼（通常 0-9 對應數字），若要點小數點，將 value 與 0x80 做 OR。
   - 範例: 顯示第三位數為 5 -> [0x03, 3, 5]
   - 範例（帶小數點）: [0x03, 2, (4 | 0x80)] 表示第二位顯示 4 且帶小數點

2. SHOW_TIME (0x02)
   - 格式: [0x02, hour, minute]
   - hour, minute: 直接以數值傳送（常見為 0..23 與 0..59）
   - 一般使用該命令會同時顯示時間並啟用冒號（colon），但實際行為依韌體而定
   - 範例: 顯示 09:30 -> [0x02, 9, 30]

3. SHOW_COLON (0x04)
   - 格式: [0x04, on_off]
   - on_off: 0 或 1（0 = 關，1 = 開）
   - 範例: 開啟冒號 -> [0x04, 1]

## 顯示值與特殊符號

- 常用數字: 0-9
- 小數點: 在欲顯示的 digit value 上做 OR 0x80
- 原始程式碼使用 `12` 作為 degree-symbol（溫度符號）佔位值（`DEGREE_SYMBOL = 12`）。不同模組版本可能會用不同代碼，若無法顯示請嘗試其他值或以實驗方式找出對應代碼。

註記: 模組的韌體決定哪些 value 對應到哪些段（segments），若你需要顯示特殊符號（例如空白、破折號或 ℃），可能需要試不同的 value。

## 使用驅動程式（`Module/ePy4Digit.py`）

驅動程式提供較高階的 API，範例如下（MicroPython）：

```python
from machine import I2C
from Module.ePy4Digit import FourDigit

# 初始化 I2C（依平台不同而異）
i2c = I2C(1, I2C.MASTER, baudrate=100000)
# 建立驅動
fd = FourDigit(i2c)

# 顯示數字
fd.show4number(1999)

# 顯示溫度（單一小數位）
fd.show_temper(24.1)

# 顯示時間（會開冒號）
fd.show_time(23, 59)

# 手動設定單一位元與小數點
fd.set_digit(2, 4, dot=True)  # 在第二位顯示 4 並帶小數點

# 開/關冒號
fd.set_colon(True)
fd.set_colon(False)

# 清除顯示
fd.clear()
```

## 直接以 I2C 原始指令操作

若你想直接透過 I2C 發送 raw bytes（例如用自己的韌體或測試），下面示例示範如何在 MicroPython 上直接寫入：

```python
# 使用 writeto
i2c.writeto(0x3D, bytearray([0x03, 1, 1]))  # 將第一位設為 1
# 或使用 send（某些平台）
i2c.send(bytearray([0x04, 1]), 0x3D)        # 開啟冒號
```

## 偵錯建議

- 若沒有顯示，先確認：電源/接地正確、SDA/SCL 接對、I2C 位址是否為 0x3D（你可以用 I2C 掃描工具確認）。
- 若收到 I2C 錯誤（OSError），請確認拉高電阻、線長與頻率（若可，嘗試 100kHz）。
- 若特殊符號（例如 ℃）顯示不正確，可嘗試將 `DEGREE_SYMBOL` 改為其他值並觀察結果。

## 附註與假設

- 本文件根據現有驅動程式（`ePy4Digit.py`）與原始程式行為推斷 I2C 命令結構。實體模組的韌體版本若不同，部分 value 對應可能不同。
- 若你可以提供模組的原廠資料表或韌體說明，我可以將此文件進一步更新為精確的命令對照表。

---

文件由 ePy_SDK 優化與整理，包含使用範例與通訊指南。
