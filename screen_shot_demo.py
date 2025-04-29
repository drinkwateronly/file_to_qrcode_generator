import time

import cv2
import numpy as np
from PIL import ImageGrab
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget
from pyzbar.pyzbar import decode


class QRcodeMonitor(QThread):
    qrcode_show_signal = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super(QRcodeMonitor, self).__init__()

    def isCodeShow(self, pltImage):
        # ImageGrab类型转为np.array才能被处理
        gray = cv2.cvtColor(np.array(pltImage), cv2.COLOR_BGR2GRAY)
        decoded_objects = decode(gray)
        print(len(decoded_objects))

    def run(self):
        while 1:
            screenshot = ImageGrab.grab()
            if not self.isCodeShow(screenshot):
                # self.qrcode_show_signal.emit()
                time.sleep(0.25)
                print("screen shot!")


class QRcodeDetector(QWidget):
    def __init__(self):
        super().__init__()
        self.qrcode_monitor = QRcodeMonitor()
        self.qrcode_monitor.run()


if __name__ == '__main__':
    qrcodeDetector = QRcodeDetector()
