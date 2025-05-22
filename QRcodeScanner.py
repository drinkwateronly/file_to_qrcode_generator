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


class QRCodeDetector(QThread):
    """ 监控屏幕上有无二维码，若有则发送二维码数量信号 """
    detect_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(QRCodeDetector, self).__init__()

    def run(self):
        try:
            # 截屏
            start = time.time()
            screenshot = ImageGrab.grab()
            # 检测二维码对象
            detected_objs = decode(screenshot)
            if len(detected_objs) != 0:
                data = detected_objs[0].data.decode('utf-8')
                print(f"Detected QR Code: {data}")
                # 尝试获取其中的所需扫描二维码数量
                match = re.search(r'^##(\d+)##(-?\d+)##(\d+)@@', data)
                if not match:
                    # 检测到二维码，但是二维码里没有数字
                    self.error_signal.emit("探测出二维码，但未能获取所需扫描次数")
                    return
                # 二维码总数
                total_qrcode_cnt = int(match.group(1))
                # 二维码的index
                patch_index = int(match.group(2))
                # 二维码的发送间隔
                qrcode_show_interval = int(match.group(3))
                self.detect_signal.emit([total_qrcode_cnt, qrcode_show_interval])
            end = time.time()
            print(f"截屏用时：{(end - start) * 1000}")
        except Exception as e:
            self.log(f"QRCodeDetector: {e}")
            self.error_signal.emit(e)


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
        self.qrcode_num = 0
        self.scan_num = 3
        self.data_list = []
        self.qrcode_show_interval = 1000
        self.detect_interval = 50

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
        try:
            self.patch_cnt, self.qrcode_show_interval = signal_list[0], int(signal_list[1] / 2)
            """ 二维码首次出现了，开始扫描二维码 """
            self.scan_num = ceil(self.patch_cnt / 6) * 2
            self.log(f"二维码出现，即将扫描{self.scan_num}次")
            # 停止检测器
            self.detector_timer.stop()

            # 开启截图器
            self.screenshot_grabber = ScreenshotGrabber()
            # 截图器信号完成动作
            self.screenshot_grabber.grabber_done.connect(self.screenshotDone)
            # 先扫描一次
            self.screenshot_grabber.start()

            # 设置一个计时器
            self.scanner_timer.timeout.connect(self.screenshot_grabber.start)
            # 每秒触发一次二维码扫描
            self.scanner_timer.start(self.qrcode_show_interval)
        except Exception as e:
            self.log(e)

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
                for qrcode_data in qrcode_data_list:
                    self.data_list.append(qrcode_data)
                self.scan_num -= 1

                # if
                # self.log(f'剩余{self.scan_num}')
            else:
                """ 扫描次数完成，停止扫描 """
                self.scanner_timer.stop()
                self.log("完成所有二维码扫描，开始合成文件")

                data_mapped = {}
                print(len(self.data_list))
                for data in self.data_list:
                    print(data)
                    pattern = r"^##(\d+)##(-?\d+)##(\d+)@@"  # 匹配开头到第一个 ##数字1##数字2@@‘
                    # 提取所有匹配的数字对
                    try:
                        matches = re.search(pattern, data)
                        index = int(matches.group(2))
                    except Exception as e:
                        print(e)
                        continue
                    if index == -1:
                        continue
                    # 移除所有匹配的模式
                    patch = re.sub(pattern, "", data, count=1)  # count=1 表示只替换第一个匹配项

                    data_mapped[index] = patch

                sorted_values = ''
                for i in range(self.patch_cnt - 18):
                    if not data_mapped.get(i):

                        self.log(f"缺少索引{i}对应二维码！")
                        print(f"缺少索引{i}对应二维码！")
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
    sys.exit(app.exec_())
