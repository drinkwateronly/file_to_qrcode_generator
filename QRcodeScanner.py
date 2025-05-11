import math
import re
import sys
from cv2 import cvtColor, COLOR_BGR2GRAY
from PIL import ImageGrab
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QTextEdit, QVBoxLayout, QApplication
from numpy import array
from pyzbar.pyzbar import decode

from tools import str2file_decoder


def detectQRcodeFromScreenshot(pltImage):
    # ImageGrab类型转为np.array才能被处理
    gray = cvtColor(array(pltImage), COLOR_BGR2GRAY)
    decoded_objects = decode(gray)
    return decoded_objects


class QRCodeDetector(QThread):
    """ 监控屏幕上有无二维码，若有则发送二维码数量信号 """
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
                match = re.search(r'##(\d+)##(\d+)@@', data)
                if not match:
                    # 检测到二维码，但是二维码里没有数字
                    self.error_signal.emit("探测出二维码，但未能获取所需扫描次数")
                    return
                # 二维码总数
                total_qrcode_cnt = int(match.group(1))
                # 二维码的index
                # patch_index = int(match.group(2))
                self.detect_signal.emit(total_qrcode_cnt)
        except Exception as e:
            self.error_signal.emit(e)

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

    def code_first_show(self, patch_cnt):
        try:
            """ 二维码首次出现了，开始扫描二维码 """
            print("QR Code first show")
            self.scan_num = math.ceil(patch_cnt / 6)
            self.log(f"二维码出现，即将扫描{self.scan_num}次")
            # 停止检测器
            self.detector_timer.stop()


            # 新建一个scanner
            self.qrcode_scanner = QRCodeScanner()
            # scanner信号完成时
            self.qrcode_scanner.scanner_done_signal.connect(self.scanner_done)
            # 先扫描一次
            self.qrcode_scanner.start()

            # 设置一个计时器
            self.scanner_timer.timeout.connect(self.qrcode_scanner.start)
            # 每秒触发一次二维码扫描
            self.scanner_timer.start(1000)
        except Exception as e:
            print(e)


    def scanner_done(self, qrcode_data_list):
        try:
            """ 每次扫描一帧二维码 """
            if self.scan_num > 0:
                """ 扫描未完成 """
                for qrcode_data in qrcode_data_list:
                    self.data_list.append(qrcode_data)
                self.scan_num -= 1
            else:
                """ 扫描次数完成，停止扫描 """
                self.scanner_timer.stop()
                self.log("完成所有二维码扫描，开始合成文件")

                data_mapped = {}
                for data in self.data_list:
                    pattern = r"##(\d+)##(\d+)@@"  # 匹配开头到第一个 ##数字1##数字2@@‘
                    # 提取所有匹配的数字对
                    matches = re.search(pattern, data)
                    index = int(matches.group(2))
                    print(index)
                    # 移除所有匹配的模式
                    patch = re.sub(pattern, "", data, count=1)  # count=1 表示只替换第一个匹配项
                    print(patch)

                    data_mapped[index] = patch
                print(data_mapped)
                sorted_values = [data_mapped[key] for key in sorted(data_mapped.keys())]
                compressed_data = " ".join(sorted_values)
                print("compressed_data:", compressed_data)
                #
                file_data = str2file_decoder(compressed_data)
                print(file_data)

                with open('output_file.bin', 'wb') as f:
                    f.write(file_data)
                return
        except Exception as e:
            print(e)

    def log(self, message):
        """向日志框中添加日志"""
        self.log_box.append(f"> {message}")  # 追加日志信息


# 运行应用程序
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRcode2File()
    window.show()
    sys.exit(app.exec_())
