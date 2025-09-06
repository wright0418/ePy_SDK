## 簡單計時器 Timer
定時使用，固定時間會回call 使用回調函數，可使用 None 函數將 Timer 中斷關閉  
###初始化
tim = Timer (0,freq=xx)
- freq = 次 /Sec (整數 >=1 )
```python
from machine import Timer
def cb_func(t_no):
    print ('have a timer interrupt')
    tim0.callback(None) # Close the timer interrupt
   
tim0 = Timer(0,freq=1)
tim0.callback(cb_func) # enable the timer interrupt
```
#回調使用 (CallBack)
Timer.callback( CallbackFunc )
- CallBackFunc : Timer 時間到會進入此 Function執行
- CallBackFunc = None : 關閉此中斷

# 中止 Timer
Timer.deinit()

# duty

# counter

# channel

