import time

import cv2
import qrcode

from tmp.qrcode_to_file import  qrcode_scan
from qrcode import QRCode

import random
import string

from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap
import sys


def compare_str(str1, str2):
    if str1 != str2:
        return False
    return True

def generate_ascii_string(length, printable_only=True):
    if printable_only:
        # 仅使用可打印字符
        characters = string.printable.strip()  # 移除不可见字符（如换行）
    else:
        # 使用所有 ASCII 字符
        characters = ''.join(chr(i) for i in range(128))  # ASCII 范围 0-127

    return ''.join(random.choice(characters) for _ in range(length))

# 示例：生成长度为 10 的随机 ASCII 字符串

if __name__ == '__main__':
    app = QApplication(sys.argv)
    label = QLabel()
    label.setFixedSize(1000, 1000)
    label.setScaledContents(True)

    for i in range(1000):
        # 生成4296个随机字母
        random_letters = generate_ascii_string(1024, True)
        # 要编码的信息
        data = random_letters
        # 创建二维码对象
        qr = QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=3,
        )
        # 添加数据到二维码中
        qr.add_data(data)
        qr.make(fit=True)

        # 创建二维码图像
        img = qr.make_image(fill_color="black", back_color="white")

        # # 保存二维码图像
        img.save("qrcode.png")

        pixmap = QPixmap('qrcode.png')
        label.setPixmap(pixmap)
        label.show()

        qrcode_image = cv2.imread('qrcode.png')
        decoded_str = qrcode_scan(qrcode_image)
        print(compare_str(random_letters, decoded_str))
        time.sleep(10000)

    sys.exit(app.exec_())