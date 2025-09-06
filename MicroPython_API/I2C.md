# Micro Python I2C API
## I2C Class
### epy Lite I2C 分類
    - 主機模式 (I2C.MASTER)
    - 從機模式 (I2C.SLAVE)

### 初始化
```python
from machine import I2C
i2c0 = I2C(0,I2C.MASTER,baudrate=100000)
```
I2C(id ,I2C.MASTER or SLAVE , baudrate=)
- id : Port 號碼 , Lite 支持 0-3，對應版上 SDA0-3 ,SCL0-3
- I2C.MASTER or I2C.SLAVE : 主從模式設定(通用為主機模式)
- baudrate : 數據傳輸速度，(100000 ~ 400000) 100Kbps~400Kbps
  
### 關閉
I2C.deinit()

### 掃描此port上裝置的位置(address)
I2C.scan()
- 回傳在此I2C port 上串接的裝置所有address (十進位表示)

### 檢測裝置是否在線
I2C.is_ready(0x42) :
  - 回傳 True /False
### 傳送
```python
i2c0.send('ABCD',addr=0x40)
i2c0.send(b'\x00\xff',0x40)
```
### 接收
```python
data = bytearray(3)  # create a buffer
i2c.recv(data) 
