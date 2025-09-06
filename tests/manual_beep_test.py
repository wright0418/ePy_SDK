import sys
import time

try:
    import winsound
except Exception as e:
    print("winsound import failed:", e)
    sys.exit(2)

print("calling winsound.Beep 440Hz 500ms")
try:
    winsound.Beep(440, 500)
    print("beep done")
except Exception as e:
    print("winsound.Beep failed:", e)
    sys.exit(3)

time.sleep(0.1)
