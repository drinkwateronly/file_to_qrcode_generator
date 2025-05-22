import time

from PIL import ImageGrab

while 1:
    screenshot = ImageGrab.grab()
    print(time.time())
