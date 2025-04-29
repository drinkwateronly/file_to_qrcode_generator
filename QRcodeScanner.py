import re
import time

from pyzbar.pyzbar import decode
from numpy import array
from PIL import ImageGrab
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QTextEdit, QVBoxLayout, QApplication, QFormLayout, QLineEdit
import sys
import cv2


def detectQRcodeFromScreenshot(pltImage):
    # ImageGrab类型转为np.array才能被处理
    gray = cv2.cvtColor(array(pltImage), cv2.COLOR_BGR2GRAY)
    decoded_objects = decode(gray)
    return decoded_objects


def genFixLengthList(length):
    return ['' for i in range(length)]


class QRCodeScanner(QThread):
    """ 扫描屏幕二维码，完成后返回，不对内部数据做任何处理"""
    scanner_done_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(QRCodeScanner, self).__init__()

    def run(self):
        try:
            # 用于存放一帧二维码内的base64数据，每次扫描有6个二维码
            qrcode_data_list = []
            # 截屏
            screenshot = ImageGrab.grab()
            # 检测二维码对象
            decoded_objects = detectQRcodeFromScreenshot(screenshot)
            # 遍历所有二维码对象
            for obj in decoded_objects:
                # 提取二维码的数据
                data = obj.data.decode('utf-8')
                qrcode_data_list.append(data)
            self.scanner_done_signal.emit(qrcode_data_list)
        except Exception as e:
            self.error_signal.emit(e)


class QRCodeDetector(QThread):
    """ 监控屏幕上有无二维码 """
    detect_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(QRCodeDetector, self).__init__()

    def run(self):
        try:
            # 截屏
            screenshot = ImageGrab.grab()
            # 检测二维码对象
            decoded_objects = detectQRcodeFromScreenshot(screenshot)
            if len(decoded_objects) != 0:
                data = decoded_objects[0].data.decode('utf-8')
                print(f"Detected QR Code: {data}")
                # 尝试获取其中的所需扫描二维码数量
                match = re.search(r'##(\d+)##', data)
                if not match:
                    # 检测到二维码，但是二维码里没有数字
                    self.error_signal.emit("探测出二维码，但未能获取所需扫描次数")
                    return
                # 所需扫描次数
                scan_num  = int(match.group(1))
                self.detect_signal.emit(scan_num)
        except Exception as e:
            self.error_signal.emit(e)


class QRcode2File(QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.detector_timer = QTimer(self)
        self.scanner_timer = QTimer(self)

        self.setWindowTitle("QRcode2File")
        self.setGeometry(100, 100, 400, 300)

        # 输入框
        # form_layout = QFormLayout()
        # input_field = QLineEdit(self)
        # form_layout.addRow("输入二维码数量：", input_field)

        # 创建一个按钮
        self.button = QPushButton("开始扫描", self)
        self.button.clicked.connect(self.on_button_clicked)  # 绑定按钮点击事件

        # 创建一个日志框
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)  # 设置为只读

        # 设置布局
        layout = QVBoxLayout()
        # layout.addLayout(form_layout)
        layout.addWidget(self.button)
        layout.addWidget(self.log_box)
        self.setLayout(layout)

        self.qrcode_detector = QRCodeDetector()
        self.qrcode_detector.detect_signal.connect(self.code_first_show)

        self.qrcode_scanner = None

        ## 指定qrcode数量
        self.qrcode_num = 0
        self.scan_num = 3
        self.data_list = []

    def on_button_clicked(self):
        """按钮点击事件处理函数"""
        self.log("开始扫描!")  # 记录日志
        self.detector_timer.timeout.connect(self.detector_timer_do)
        self.detector_timer.start(250)  # 每0.25秒触发一次二维码检测

    def detector_timer_do(self):
        """ 开启二维码检测器线程 """
        self.log("检测二维码...")
        self.qrcode_detector.start()

    def code_first_show(self, scan_num):
        """ 二维码首次出现了，开始扫描二维码 """
        self.log(f"二维码出现，即将扫描{scan_num}次")
        self.scan_num = scan_num
        # 停止检测器
        self.detector_timer.stop()
        # 新建一个scanner
        self.qrcode_scanner = QRCodeScanner()
        self.qrcode_scanner.scanner_done_signal.connect(self.scanner_done)

        self.scanner_timer.timeout.connect(self.scanner_timer_do)
        self.scanner_timer.start(1000)  # 每秒触发一次二维码扫描

    def scanner_timer_do(self):
        # 新建一个scanner
        self.qrcode_scanner.start()

    def scanner_done(self, qrcode_data_list):
        """ 扫描完一帧二维码 """
        if self.scan_num == 0:
            """ 扫描次数完成，停止扫描 """
            self.scanner_timer.stop()
            self.log("完成所有二维码扫描，开始合成文件")
            for i in self.data_list:
                print(i)
            return
        else:
            """ 扫描未完成 """
            self.data_list.append(qrcode_data_list)
            self.scan_num -= 1

    def log(self, message):
        """向日志框中添加日志"""
        self.log_box.append(f"> {message}")  # 追加日志信息


# 运行应用程序
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRcode2File()
    window.show()
    sys.exit(app.exec_())
