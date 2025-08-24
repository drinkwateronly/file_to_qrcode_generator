import json
import time
from datetime import datetime
import re
import sys
from math import ceil
from PIL import ImageGrab
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QTextEdit, QVBoxLayout, QApplication
from tools import str2file_decoder, getMd5
from pyzbar.pyzbar import decode
from random import randint
from QRCodeDetector import QRCodeDetector


class ScreenshotGrabber(QThread):
    """ 扫描屏幕二维码，完成后返回，不对内部数据做任何处理"""
    grabber_done = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(ScreenshotGrabber, self).__init__()

    def run(self):
        try:
            # 截屏
            self.grabber_done.emit(ImageGrab.grab())
        except Exception as e:
            self.error_signal.emit(e)


class QRcode2FileGenerator(QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.patch_cnt = None
        self.detector_timer = QTimer(self)
        self.scanner_timer = QTimer(self)

        self.setWindowTitle("QRcode2File")
        self.setGeometry(100, 100, 400, 300)

        # 按钮
        self.button = QPushButton("开始扫描", self)
        self.button.clicked.connect(self.onButtonClick)  # 绑定按钮点击事件

        # 创建一个日志框
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)  # 设置为只读

        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.log_box)
        self.setLayout(layout)

        self.qrcode_detector = QRCodeDetector()
        self.qrcode_detector.detect_signal.connect(self.qrcodeFirstShow)

        self.screenshot_grabber = None

        ## 指定qrcode数量
        self.scan_num = 0
        self.data_list = []
        self.scan_interval = 1000
        self.detect_interval = 50
        self.qrcode_per_matrix = 6

    def onButtonClick(self):
        """按钮点击事件处理函数"""
        self.detector_timer.timeout.connect(self.detectorTimerDo)
        self.detector_timer.start(self.detect_interval)  # 每0.1秒触发一次二维码检测

    def detectorTimerDo(self):
        """ 开启二维码检测器线程 """
        self.button.setEnabled(False)
        self.qrcode_detector.start()
        self.log_box.setText('')
        self.log(f"检测二维码中{randint(1, 2) * '.'}")

    def qrcodeFirstShow(self, signal_list):
        """ 二维码首次被检测到，开始扫描二维码 """
        try:
            # 停止检测器
            self.detector_timer.stop()

            # 二维码总数量，二维码展示频率
            self.patch_cnt, show_interval, self.qrcode_per_matrix = signal_list[0], signal_list[1], signal_list[2]
            # 二维码扫描间隔 = 二维码展示间隔 / 2
            self.scan_interval = int(show_interval / 2)
            # 扫描次数 = 二维码数量 / 每个矩阵包含二维码数量 * 2
            self.scan_num = ceil(self.patch_cnt / self.qrcode_per_matrix) * 2
            self.log(f"检测到二维码，单次有{self.qrcode_per_matrix}个二维码，需要扫描{self.scan_num}次")

            # 开启截图器
            self.screenshot_grabber = ScreenshotGrabber()
            # 截图器信号完成动作
            self.screenshot_grabber.grabber_done.connect(self.screenshotDone)
            # 先扫描一次
            self.screenshot_grabber.start()

            # 设置一个计时器
            self.scanner_timer.timeout.connect(self.screenshot_grabber.start)
            # 每秒触发一次二维码扫描
            self.scanner_timer.start(self.scan_interval)
        except Exception as e:
            self.log(f"[qrcodeFirstShow]: {e}")

    def screenshotDone(self, screenshot):
        try:
            """ 每次扫描一帧二维码 """
            qrcode_data_list = []
            decoded_objects = decode(screenshot)
            # 遍历所有二维码对象
            for obj in decoded_objects:
                # 提取二维码的数据
                qrcode_data_list.append(obj.data.decode('utf-8'))

            if self.scan_num > 0:
                """ 扫描未完成 """
                self.log(f"正在扫描二维码，还剩{self.scan_num}次")
                for qrcode_data in qrcode_data_list:
                    self.data_list.append(qrcode_data)
                self.scan_num -= 1
            else:
                """ 扫描次数完成，停止扫描 """
                self.scanner_timer.stop()
                self.log("完成所有二维码扫描，开始合成文件")

                data_mapped = {}
                for data in self.data_list:
                    # 提取所有匹配的数字对
                    try:
                        data = json.loads(data)
                        index = int(data['idx'])
                        # print(recv_data)
                    except Exception as e:
                        print(e)
                        continue
                    if index == -1:
                        continue

                    data_mapped[index] = data['info']

                error_flag = False
                sorted_values = ''
                for i in range(self.patch_cnt):
                    if not data_mapped.get(i):
                        self.log(f"缺少索引{i}对应二维码！")
                        print(f"缺少索引{i}对应二维码！")
                        error_flag = True

                if error_flag:
                    self.log("二维码数据不完整，请重新扫描")
                    return

                for i in range(self.patch_cnt):
                    sorted_values += data_mapped.get(i)
                    # print(data_mapped.get(i))
                compressed_data = "".join(sorted_values)
                file_data = str2file_decoder(compressed_data)

                with open('output_file.bin', 'wb') as f:
                    f.write(file_data)
                self.log(f'> 文件MD5值为：{getMd5(file_data)}')
                self.log('> 文件已保存为output_file.bin，请自行修改后缀')
                return
        except Exception as e:
            self.log(e)
            print(e)

        self.button.setEnabled(True)

    def log(self, message):
        """向日志框中添加日志"""
        self.log_box.append(f"> {message}")  # 追加日志信息


# 运行应用程序
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRcode2FileGenerator()
    window.show()
    window.setWindowTitle('QRMatrixScanner v1.2')
    sys.exit(app.exec_())
