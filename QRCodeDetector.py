import json
import time
import re
from PIL import ImageGrab
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from pyzbar.pyzbar import decode


class QRCodeDetector(QThread):
    """ 监控屏幕上有无二维码，若有则发送二维码数量信号 """
    detect_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(QRCodeDetector, self).__init__()

    def run(self):
        try:
            # start = time.time()
            # 截屏
            screenshot = ImageGrab.grab()
            # 检测二维码对象
            detected_objs = decode(screenshot)
            if len(detected_objs) != 0:
                # 选第一个解码出来的二维码，解析内容
                data = detected_objs[0].data.decode('utf-8')
                data = json.loads(data)
                print(f"Detected QR Code: {data}")
                # 二维码总数
                total_cnt = data['cnt']
                # 二维码的发送间隔
                show_interval = data['itvl']

                # 发送信号
                self.detect_signal.emit([total_cnt, show_interval, len(detected_objs)])
            # end = time.time()
            # print(f"截屏用时：{(end - start) * 1000}")
        except json.JSONDecodeError as e:
            # 检测到二维码，但二维码内容无法被json解析
            self.error_signal.emit(f"[detector]二维码内容格式非法：{e}")
        except KeyError as e:
            self.error_signal.emit(f"[detector]二维码内未提供必要字段：{e}")
        except Exception as e:
            self.error_signal.emit(f"[detector]二维码检测出错：{e}")

