# Micro Python UART API
## UART 類別
### 初始化
```python
UART(1, baudrate=115200, bits=8, parity=None, stop=1, timeout=2000, timeout_char=2, read_buf_len=64)
```
- 包含識別名稱的參數可以忽略 有初始值，並且順序可以對調。ex. baudrate 等

最簡易使用方法
```python
>>>from machine import UART
>>>uart1 = UART(1,9600)
>>>uart1
UART(1, baudrate=9600, bits=8, parity=None, stop=1, timeout=2000, timeout_char=3, read_buf_len=64)
```
- 第一個參數 可帶入 0-3 ，代表使用版上 TX0/RX0~TX3-RX3
- baudrate : 輸入對接UART裝置的傳輸速度 (內建 RL62M 為115200 )
- bit : 每一筆數據量為幾位元 (通用 8bit)
- parity : 同位檢查None(無), 0 (even) or 1 (odd).
- stop : 停止位元 ，1 或 2 (通常使用 1)
- timeout (ms): 等待第一個字元進來的時間
- timeout_char(ms):每一個字元與字元間的等待時間
- read_buf_len (byte) :UART 一次可接收的暫存容量

### 關閉
UART.deinit()

### 讀取
- UART.read(n) : 由UART暫存Buffer 讀出n 個 byte，未讀出的有可能會被之後進入的資料覆蓋
- UART.readline() : 讀取單行 ，判斷到換行字元
- UART.readinto(buf[,n bytes]) : 讀出UART n個 byte 放置到 buf裡面 
-  UART.readchar() : 讀出單一字元的ASCII code
### 寫入
- UART.write(buf) : 將 buf寫到 UART Port , buf 為字串 或 bytearray
- UART.writechar(ASCII code) : 寫出一個ASCII Code的字元



