import re
import time

import cv2
import numpy as np
from PIL import ImageGrab
from pyzbar.pyzbar import decode


def detectQRcodeFromScreenshot(pltImage):
    # ImageGrab类型转为np.array才能被处理
    gray = cv2.cvtColor(np.array(pltImage), cv2.COLOR_BGR2GRAY)
    decoded_objects = decode(gray)
    return decoded_objects


def genFixLengthList(length):
    return ['' for i in range(length)]


base64_data_list = genFixLengthList(124)
end = False

stage = 1
while 1:
    screenshot = ImageGrab.grab()
    decoded_objects = detectQRcodeFromScreenshot(screenshot)
    if stage == 1:
        # 第一阶段，每k秒截图一次，检测有无二维码出现
        if len(decoded_objects) == 0:
            # 未出现二维码，
            time.sleep(0.25)
            print("screen shot!")
            continue
        else:
            # 二维码首次出现
            stage = 2
            time.sleep(0.25)

    for obj in decoded_objects:
        # 提取二维码的数据
        data = obj.data.decode('utf-8')
        print(f"Detected QR Code: {data}")
        match = re.search(r'###(\d+)###', data)

        if not match:
            # 一个二维码里没取到数字，就G了
            break
        patch_index = match.group(1)
        patch_data = data[len(patch_index) + 6:]
        print(patch_index)  # 输出: 5
        print(patch_data)
        base64_data_list[int(patch_index)] = patch_data
        if int(patch_index) == 123:
            end = True
    if end:
        break

    time.sleep(1)

for index, base64_data in enumerate(base64_data_list):
    print(index, base64_data)