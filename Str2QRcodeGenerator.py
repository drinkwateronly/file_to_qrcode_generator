import io
import json
import random

from PyQt5.QtGui import QImage
from PyQt5.QtCore import QThread, pyqtSignal
from tools import makeQRcodeImg


class Str2QRcodeGenerator(QThread):
    """
    字符串切片转二维码生成器，
    """
    images_ready = pyqtSignal()
    single_image_ready = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        self._is_running = True
        self.encoded_str = None
        self.patch_size = 0
        self.tot_cnt = None
        self.qrcode_list = []

        self.show_interval = 1000
        self.version = 20
        self.error_correction_lvl = 'M'
        self.box_size = 5
        self.border = 1
        super(Str2QRcodeGenerator, self).__init__()

    def setParams(self,
                  encoded_str,
                  patch_size,
                  show_interval,
                  version=20,
                  error_correction_lvl='L',
                  box_size=5,
                  border=1,
                  ):
        """
        :param encoded_str: 待转为二维码的字符串（文件压缩并转码后的字符串）
        :param patch_size: 每张二维码的存放字符串的比特长度
        :param show_interval: 二维码展示的间隔
        :param version: 二维码版本
        :param error_correction_lvl: 纠错版本，可选L/M/Q/H
        :param box_size: 二维码尺寸
        :param border: 二维码边缘空白尺寸
        :return:
        """
        self._is_running = True
        self.encoded_str, self.patch_size, self.show_interval \
            = encoded_str, patch_size, show_interval

        # 计算总共需要生成的patch张数
        self.tot_cnt = int((len(self.encoded_str) + self.patch_size - 1) / self.patch_size)

        self.version = version
        self.error_correction_lvl = error_correction_lvl
        self.box_size = box_size
        self.border = border

    def exit_thread(self):
        # 控制Qthread运行
        self._is_running = False

    def run(self):
        try:
            self.qrcode_list = []
            # 每个patch就是一个二维码内容
            for patch_index in range(self.tot_cnt):
                if not self._is_running:
                    return
                # 根据patch_size切割字符串，right_pos指示子串右侧位置
                right_pos = min((patch_index + 1) * self.patch_size, len(self.encoded_str))
                patch_str = self.encoded_str[patch_index * self.patch_size: right_pos]

                info_json = {
                    "idx": patch_index,
                    "cnt": self.tot_cnt,
                    "len": self.patch_size,
                    "itvl": self.show_interval,
                    "info": patch_str,
                    "rand": random.randint(0, 1000)
                }

                patch_str = json.dumps(info_json)

                # 字符串转二维码图片
                qr_code_img = makeQRcodeImg(input_str=patch_str,
                                            version=self.version,
                                            error_correction_lvl=self.error_correction_lvl,
                                            box_size=self.box_size,
                                            border=self.border
                                            )
                # 图片转为QImage格式
                byte_array = io.BytesIO()
                qr_code_img.save(byte_array)
                byte_array.seek(0)
                q_img = QImage.fromData(byte_array.getvalue())
                self.qrcode_list.append(q_img)
                # 单张图片完成，发送信号给主线程
                self.single_image_ready.emit([patch_index, self.tot_cnt])
            # 所有二维码已生成，发送信号给主线程
            self.images_ready.emit()

        except Exception as e:
            self.error_signal.emit(f'二维码生成出错：{e}')
            print(e)
