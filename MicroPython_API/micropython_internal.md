
ePy micropython 提供有限的 Python 內建函式庫，以下為內建函式庫的說明與使用方式。
ePy series board have "epy-lite" and "epy-plus" two version, epy-plus have more function than epy-lite
epy-litesupport I2C, SPI, UART, ADC, PWM, LED (on board R/G/Y mono LED and external WS2812B RGBLED), one Button key ('keya'), RTC, utime , on board BLE use UART1 ,function
epy-plus support more function than epy-lite, such as 8x8 matrix monochrome LED display, 4 keypad,on board buzzer,dual on board microphone use ADC sensor, 3 axis G-sensor , light sensor etc.


# ePy 不支援的函式庫
 - 不支援 f-string ,  使用string.format() 取代

# utime
```python
from utime import time, sleep, sleep_ms, sleep_us, ticks_add, ticks_cpu, ticks_diff, ticks_ms, ticks_us, localtime, mktime
```
## utime module
獲取/設定當前時間、時間等待、量測時間差
### utime.sleep_ms()
- 延迟给定毫秒数，应为Positive或0。
### utime.sleep_us()
- 延迟给定的微秒数，应为Positive或0。
### utime.sleep()
- 休眠给定秒数的时间。秒钟数可为一个表示休眠时间的浮点数。注意：其他端口可能不接受浮点参数，为满足兼容性，使用 sleep_ms() 和 sleep_us() 函数。
### utime.ticks_cpu()
- 与 ticks_ms 和 ticks_us 相似，但有更高的分辨率（通常CPU时钟）。
### utime.ticks_ms()
- 用在某些值（未指定）后结束后的任意引用点返回一个递增的毫秒计数器。该值应被视为不透明的，且仅适用于ticks_diff()。
### utime.ticks_us()
- 正如上述的 ticks_ms ，但以微秒为单位
### utime.ticks_add(ticks, delta)
- 用一个给定数字来抵消ticks值，该数字可为正或负。给定一个 ticks 值，该函数允许计算之前或之后的ticks value  delta  ticks
```python
# Find out what ticks value there was 100ms ago 找到100ms前的ticks值
print(ticks_add(time.ticks_ms(), -100))

# Calculate deadline for operation and test for it 计算操作和测试的截止时间
deadline = ticks_add(time.ticks_ms(), 200)
while ticks_diff(deadline, time.ticks_ms()) > 0:
    do_a_little_of_something()

# Find out TICKS_MAX used by this port 找到该端口使用的TICKS_MAX
print(ticks_add(0, -1))
```
### utime.ticks_diff(ticks1, ticks2)
- 测量连续调用ticks_ms()、ticks_us()、icks_cpu()间的周期。 由这些函数返回的值可能在任何时间停止，因此并不支持直接减去这些值，应使用ticks_diff()。 “旧”值实际上应及时覆盖“新”值，否则结果将未定义。该函数不应用于测量任意周期长的时间（因为ticks_*()函数包括且通常有短周期）。 预期使用模式是使用超时实现事件轮询
  
### utime.localtime((time tuple))
- time tuple : （年,月,日,小时,分钟,秒,一周中第幾天日,一年中第幾天）
### utime.mktime()
-此为局部时间的逆函数，其参数为一个表示本地时间的8元组。返回一个表示2000年1月1日以来的秒钟的整数。
### utime.time()

# LED Class
 - led_index from 1 to 64 , ePy support max 64 pcs rgb led
 - 大量 LED 時記憶體/速度限制 , 使用 DMA 傳輸 , rgb_write() 硬體一次寫出，延遲時間極短
```python
from machine import LED
led = LED('ledy') # create an LED object for yellow LED , LED object have 'ledy', ledg', 'ledr' or LED.RGB support external WS2812B RGB LED
led.on()  # turn the led on
led.off() # turn the led off
led.toggle() # toggle the led status

rgb = LED(LED.RGB) # create an LED object for external WS2812B RGB LED
rgb.off() # turn the rgb led off
rgb.lightness(50) # set the brightness of rgb led (0~100) , must set before write_rgb()
led_index = 1 # set the index of rgb led if you have more than one rgb led

RGB_COLOR = (255,0,0) # set the rgb color to red (R,G,B) clolor value 0~255
rgb.rgb_write(led_index,*RGB_COLOR) # set the rgb led to red color
# other write RGB method
rgb_raw_data = ((0,255,0),(0,0,255)) # set the rgb color to green and blue for 2 rgb led
rgb.rgb_write(rgb_raw_data) # set the rgb led to green and blue color
```

# FILE 
```python
import machine
import uos as os

filelist = os.listdir()
new_file = open ('test.txt','w')
new_file.write('some data')
new_file.close()

f = open ('test.txt',r')
print (f.read())

bin_file = open('test.bin','w+b')
bin_file.write(b'\x01\xff\x90\x04\xae')
bin_file.write(b'abcde')
bin_file.close ()

bin_file = open('test.bin','r+b')
print (bin_file.read())
bin_file.close ()

bin_file = open('test.bin','a+b') #append
bin_file.write(b'1234555')
bin_file.close ()
os.remove('test.bin')
```

# GPIO
ePy GPIO 使用 machine.Pin 類別來操作 GPIO。
- supportr Pin mode : Pin.IN, Pin.OUT, Pin.OPEN_DRAIN
- support pull : Pin.PULL_UP, Pin.PULL_DOWN, Pin.PULL_NONE
- support irq trigger : Pin.IRQ_FALLING, Pin.IRQ_RISING, Pin.IRQ_LOW_LEVEL, Pin.IRQ_HIGH_LEVEL
- support Pin name : Pin.epy.P0.. P0-P24
  
```python
from machine import Pin
p0 = Pin(Pin.epy.P0,Pin.OUT) # P0 Output GPIO
p1 = Pin(Pin.epy.P1,Pin.IN)  #P1 Input GPIO

p1_value = p1.value() # get P1 input value
p0.value(1) # set P0 output high

def pin_irq_handler(pin): # pin interrupt handler
    print('pin irq',pin)

p1.irq(trigger=Pin.IRQ_FALLING, handler=pin_irq_handler)
p1.irq(trigger=Pin.IRQ_RISING, handler=pin_irq_handler)
p1.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=pin_irq_handler) # both edge
```

# PWM
ePy 支援 4 組 PWM，使用 machine.PWM 類別來操作 PWM。
- support Pin name : Pin.epy.PWM0 , Pin.epy.PWM1 , Pin.epy.PWM2 , Pin.epy.PWM3
- 
```python
from machine import PWM,Pin

pwm0 = PWM(Pin.epy.PWM0,freq=50,duty=50) # create a PWM object from Pin PWM0 , set freq=50Hz , duty=50%
pwm0.duty(99)
pwm0.freq(1000)

pwm1 = PWM(Pin.epy.PWM1,freq=200,duty=50) 
pwm1.duty(80)
pwm1.freq(1000)

pwm2 = PWM(Pin.epy.PWM2,freq=100,duty=50) 
pwm2.duty(30)
pwm2.freq(2000)
   
pwm3 = PWM(Pin.epy.PWM3,freq=150,duty=50) 
pwm3.duty(10)
pwm3.freq(500)
```


#  random

```python

import urandom as random

# urandom.getrandbits (nbit)
# 產生取nbit 的亂數 , 2^7 = 0~128

def rand (a,b): # 產生數字a到 b的 亂數 
    return (random.getrandbits(7) %(b-a+1)+ a)

for i in range(0,10):
    print (rand (0,4)) #取 0到 4亂數

for i in range(0,10):
    print (rand (2,4)) #取 2到 4亂數
    
random.randinit(10,100) # get int number 10~100 random number
random.random() # get 0 to <1 float random number
random.randrange (1,7) # get int 1 to 6 random number 

L = [[1,0,0],[0,1,0],[0,0,1],[20,20,0],[30,20,40]]

random.choice (L) # from L list random choice a item
```

# RTC
ePy RTC 使用 machine.RTC 類別來操作 RTC。
```python
from machine import RTC,delay
today = (2021,2,22,1,0,25,18,0) # (year,month,day,weekly,hour,min,sec,sub) 

rtc = RTC() # create RTC object and Start the RTC

rtc.datetime(today)
   
while True:
    print (rtc.datetime()) # get the current date and time
    delay(1000)
``` 

# Servo Motor
ePy 支援 4 組 Servo，使用 machine.Servo 類別來操作 Servo。
- Servo channel : 1~4 , Servo.ALL_SERVO (Ch1~4  對應  Hardware pin PWM0~PWM3 )
```python
from machine import Servo,delay

s1 = Servo(1)  # serve channel 1 is PWM0 , 2 is PWM1....4 is PWM3
s2 = Servo(2)
s3 = Servo(3)
s4 = Servo(4)
s_all = Servo(Servo.ALL_SERVO)
    
s1.calibration(1500,7000,1600,4100,3000) #(min,max,angle(0),angle(90),xxxx)
s2.calibration(1500,7000,1600,4100,3000)
s3.calibration(1500,7000,1600,4100,3000)
s4.calibration(1500,7000,1600,4100,3000)

s1.angle(90) # change to angle 90
delay(1000) #wait servo
s1.angle(180,1000) # change to angle 180 use 1000ms
delay(1000)
s1.angle(0,1000) # change to angle 0 use 1000ms
delay(1000)
s1.angle(180,1000) # change to angle 180 use 1000ms
delay(1000)
s1.angle(90)

for i in range (1,10):
    s_all.angle([180,180,180,180,2000]) # [s1 angle,s2 angle, s3 angle,s4 angle , active time]
    delay(2000)
    s_all.angle([0,0,0,0,5000])
    delay(2000)
    
```

# SWitch Key
ePy 支援一組按鍵，使用 machine.Key 類別來操作按鍵。

```python
from machine import LED
from machine import Switch

ledG = LED('ledg')
keyA = Switch('keya')
   
def KeyA_Function():
    print ('KeyA be pressed')
    ledG.toggle()
   
keyA.callback(KeyA_Function) # set the keyA callback function

# UART

```python
from machine import UART

uart= UART(3,115200,bits=8,parity=None, stop=1)
uart.write('AT\r\n')
ret = uart.readline()

uart.read(10) # read 10 characters, returns a bytes object

buf = bytearray(10)
uart.readinto(buf) # read and store into the given buffer

uart.write('abc') # write the 3 characters
uart.readchar() # read 1 character and returns it as an integer
uart.writechar(42) # write 1 character
uart.any() # returns the number of characters waiting
uart.deinit() # turn off the UART bus
```
