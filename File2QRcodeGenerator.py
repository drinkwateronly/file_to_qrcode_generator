import io
import math
import os
import sys
from tkinter import Tk, messagebox
from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QVBoxLayout, QWidget, QTextEdit, QPushButton, \
    QHBoxLayout, QSplitter, QGridLayout, QLineEdit, QFormLayout, QComboBox
from PyQt5.QtGui import QPixmap, QImage, QTextCursor
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from tools import get_real_resolution, makeQRcodeImg, file2strEncode, getMd5


class Str2QRcodeGenerator(QThread):
    """
    字符串切片转二维码生成器，
    """
    images_ready = pyqtSignal()
    single_image_ready = pyqtSignal(int)
    error_signal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        self.encoded_str = None
        self.patch_byte_len = 0
        self.total_count = None
        self.qrcode_list = []

        self.show_interval = 1000
        self.version = 40
        self.error_correction_lvl = 'L'
        self.box_size = 5
        self.border = 1
        super(Str2QRcodeGenerator, self).__init__()

    def setParams(self,
                  encoded_str,
                  patch_size,
                  total_count,
                  show_interval,
                  version=40,
                  error_correction_lvl='L',
                  box_size=5,
                  border=1,
                  ):
        """
        :param encoded_str: 待转为二维码的字符串（文件压缩并转码后的字符串）
        :param patch_size: 每张二维码的存放字符串的比特长度
        :param total_count: 总二维码数量
        :param show_interval: 二维码展示的间隔
        :param version: 二维码版本
        :param error_correction_lvl: 纠错版本，可选L/M/Q/H
        :param box_size: 二维码尺寸
        :param border: 二维码边缘空白尺寸
        :return:
        """
        self.encoded_str, self.patch_byte_len, self.total_count, self.show_interval \
            = encoded_str, patch_size, total_count, show_interval
        self.version = version
        self.error_correction_lvl = error_correction_lvl
        self.box_size = box_size
        self.border = border

    def run(self):
        try:
            self.qrcode_list = []
            # 循环所有二维码，不断切割字符串，生成二维码
            for patch_index in range(self.total_count):
                # 切割字符串右侧位置是否超过字符串长度
                right_pos = min((patch_index + 1) * self.patch_byte_len, len(self.encoded_str))
                patch_str = self.encoded_str[patch_index * self.patch_byte_len: right_pos]
                # 加入前缀提供二维码数量信息
                patch_str = f"##{self.total_count}##{patch_index}##{self.show_interval}@@{patch_str}"
                # 字符串转二维码图片
                qr_code_img = makeQRcodeImg(input_str=patch_str,
                                            version=self.version,
                                            error_correction_lvl=self.error_correction_lvl,
                                            box_size=self.box_size,
                                            border=self.border
                                            )
                if qr_code_img is None:
                    raise Exception('二维码图片生成失败')
                # 图片转为QImage格式
                byte_array = io.BytesIO()
                qr_code_img.save(byte_array)
                byte_array.seek(0)
                q_img = QImage.fromData(byte_array.getvalue())
                self.qrcode_list.append(q_img)
                # 单张图片完成，发送信号给主线程
                self.single_image_ready.emit(patch_index)
            # 所有二维码已生成，发送信号给主线程
            self.images_ready.emit()
        except Exception as e:
            print(e)
            self.error_signal.emit(e)
            raise e


class File2QRcodeGenerator(QWidget):
    def __init__(self):
        super().__init__()

        # 参数
        self.str2qrcode_generator = None
        self.max_size_mb = 5  # 最大文件MB大小
        self.patch_size = 2 * 1024  # 每个二维码存放的字节数量,默认2kB
        self.patch_index = 0
        self.wait_sec = 3  # 点击开始后等待的秒数
        self.wait_sec_tmp = self.wait_sec
        self.qr_show_interval = 1000  # 每轮二维码展示的间隔（秒）
        self.version = 40  #
        self.error_correction_lvl = 'L'

        self.total_count = None
        self.encoded_str = None
        self.file = None

        # 一系列组件
        # 按钮
        self.screen_w, self.screen_h = get_real_resolution()
        self.file_button = None
        self.file_2_qrcode_button = None
        self.start_button = None
        self.stop_button = None
        # 下拉
        self.combo_ver_box = None
        self.combo_lvl_box = None
        # 输入框
        self.byte_input_field = None
        self.interval_input_field = None
        # 日志
        self.log_text_edit = None
        self.qrcode_img_labels = None

        # 一系列timer
        self.count_down_timer = None
        self.qrcode_timer = None
        self.initUI()

    def initUI(self):
        # 左侧布局
        # 选择文件按钮
        self.file_button = QPushButton('选择文件', self)
        self.file_button.clicked.connect(self.clickOpenFile)
        # 文件转二维码按钮
        self.file_2_qrcode_button = QPushButton('文件转二维码', self)
        self.file_2_qrcode_button.clicked.connect(self.clickFile2QRcode)
        self.file_2_qrcode_button.setEnabled(False)
        # todo:重置按钮
        self.stop_button = QPushButton('停止', self)
        self.stop_button.clicked.connect(self.clickStop)
        # 开始传输按钮
        self.start_button = QPushButton('开始传输二维码', self)
        self.start_button.clicked.connect(self.clickStart)
        self.start_button.setEnabled(False)
        # 参数设置按钮
        # self.confirm_button = QPushButton('确认参数(建议默认)', self)
        # self.confirm_button.clicked.connect(self.confirm_inputs)

        # 创建二维码版本标签和下拉框
        combo_ver_label = QLabel("二维码版本 (1-40)")
        self.combo_ver_box = QComboBox()
        # 填充 1~40 的选项
        for i in range(1, 41):
            self.combo_ver_box.addItem(str(i))
        # 设置默认值（例如：40）
        self.combo_ver_box.setCurrentText("40")

        # 创建纠错级别标签和下拉框
        combo_lvl_label = QLabel("纠错级别（L/M/Q/H）")
        self.combo_lvl_box = QComboBox()
        # 填充选项
        self.combo_lvl_box.addItems(['L (7%)', 'M (15%)', 'Q (25%)', 'H (30%)'])
        # 设置默认值（例如：40）
        self.combo_lvl_box.setCurrentText('L (7%)')

        # 输入框
        self.byte_input_field = QLineEdit(self)
        self.byte_input_field.setText(str(self.patch_size))

        self.interval_input_field = QLineEdit(self)
        self.interval_input_field.setText(str(self.qr_show_interval))

        # 日志文本框
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)

        # 左侧整体布局
        # 上半部分按钮布局
        button_layout1 = QHBoxLayout()
        button_layout1.addWidget(self.file_button)
        button_layout1.addWidget(self.file_2_qrcode_button)
        button_layout2 = QHBoxLayout()
        button_layout2.addWidget(self.start_button)
        button_layout2.addWidget(self.stop_button)

        # 下拉布局
        combo_layout = QHBoxLayout()
        combo_ver_layout = QHBoxLayout()
        combo_ver_layout.addWidget(combo_ver_label)
        combo_ver_layout.addWidget(self.combo_ver_box, alignment=Qt.AlignLeft)
        combo_lvl_layout = QHBoxLayout()
        combo_lvl_layout.addWidget(combo_lvl_label)
        combo_lvl_layout.addWidget(self.combo_lvl_box, alignment=Qt.AlignLeft)
        combo_layout.addLayout(combo_ver_layout)
        combo_layout.addLayout(combo_lvl_layout)

        # 输入布局
        input_layout = QHBoxLayout()
        input_layout1 = QHBoxLayout()
        input_layout1.addWidget(QLabel("二维码字节数（B）"))
        input_layout1.addWidget(self.byte_input_field, alignment=Qt.AlignLeft)
        input_layout2 = QHBoxLayout()
        input_layout2.addWidget(QLabel("二维码生成频率（ms）"))
        input_layout2.addWidget(self.interval_input_field, alignment=Qt.AlignLeft)
        input_layout.addLayout(input_layout1)
        input_layout.addLayout(input_layout2)

        # 左侧整体布局
        left_layout = QVBoxLayout()
        left_layout.addLayout(button_layout1)
        left_layout.addLayout(button_layout2)
        left_layout.addLayout(combo_layout)
        left_layout.addLayout(input_layout)
        left_layout.addWidget(self.log_text_edit)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # 二维码展示布局
        self.qrcode_img_labels = [QLabel(self) for _ in range(6)]  # 创建9个QLabel
        for label in self.qrcode_img_labels:
            label.setAlignment(Qt.AlignCenter)  # 居中对齐
            label.setScaledContents(True)  # 自动缩放内容以适应标签大小
            label.setFixedSize((self.screen_w - 100) / 4, (self.screen_w - 100) / 4)  # 设置固定大小，可以根据需要调整

        grid_layout = QGridLayout()  # 使用QGridLayout进行3x3布局
        for i, label in enumerate(self.qrcode_img_labels):
            row = i // 3
            col = i % 3
            grid_layout.addWidget(label, row, col)

        # 左侧整体布局
        right_widget = QWidget()
        right_widget.setLayout(grid_layout)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置主窗口的中心部件
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(splitter)
        container.setLayout(container_layout)
        self.setLayout(container_layout)

        # 窗口显示后调整分割器大小
        # self.resize(self.screen_w, self.screen_h)  # 设置初始窗口大小
        self.showMaximized()  # 全屏显示
        splitter.setSizes([(self.screen_w - 100) / 4, (self.screen_w - 100) * 3 / 4])  # 左侧300，右侧700

    def log(self, message):
        self.log_text_edit.append(message)
        self.log_text_edit.moveCursor(QTextCursor.End)

    def repeatLog(self, message):
        current_text = self.log_text_edit.toPlainText()
        processed_text = current_text[:len(current_text) - len(message)]
        self.log_text_edit.setPlainText(processed_text + message)

    def checkFileSize(self, file_path):
        max_size_bytes = self.max_size_mb * 1024 * 1024
        return os.path.getsize(file_path) <= max_size_bytes

    def clickOpenFile(self):
        """
        点击打开文件按钮
        :return:
        """
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*);;文本文件 (*.txt)",
                                                       options=options)
            if file_path:
                if not self.checkFileSize(file_path):
                    messagebox.showwarning("note", "所选文件大小超过5MB")
                    self.log("> 文件大于5MB，不允许传输，请重新选择文件")
                else:
                    # 处理文件
                    self.log(f"> 选择了文件: {file_path}")
                    file_data = open(file_path, 'rb').read()
                    #
                    self.encoded_str = file2strEncode(file_data)
                    self.total_count = math.ceil(len(self.encoded_str) / self.patch_size)

                    self.log(f"> 需要生成{self.total_count}张二维码, 点击开始按钮生成")
                    self.file_2_qrcode_button.setEnabled(True)
                    self.log(f'文件MD5值为：{getMd5(file_data)}')

        except Exception as e:
            self.log(f"> 打开文件出错：{e}")
            raise e

    def clickFile2QRcode(self):
        try:
            self.version = int(self.combo_ver_box.currentText())
            self.error_correction_lvl = self.combo_lvl_box.currentText()[0]  # 获取第一个输入框的内容
            self.qr_show_interval = int(self.interval_input_field.text())  # 获取第一个输入框的内容
            self.patch_size = int(self.byte_input_field.text())  # 获取第二个输入框的内容
            self.log(f"> ver:{self.version}, lvl:{self.error_correction_lvl}, interval:{self.qr_show_interval}, "
                     f"byte:{self.patch_size}")

            self.patch_index = 0
            # 二维码生成器开始生成二维码
            # 字符串转二维码生成器
            self.str2qrcode_generator = Str2QRcodeGenerator()
            # 单个二维码处理完成，用于日志展示
            self.str2qrcode_generator.single_image_ready.connect(self.singleImgReadyLog)
            # 二维码处理完成，开始倒计时
            self.str2qrcode_generator.images_ready.connect(self.allImgReady)

            self.str2qrcode_generator.setParams(encoded_str=self.encoded_str,
                                                patch_size=self.patch_size,
                                                total_count=self.total_count,
                                                show_interval=self.qr_show_interval,
                                                version=self.version,
                                                error_correction_lvl=self.error_correction_lvl)
            self.str2qrcode_generator.start()
            # 进度条
            self.log("> 开始生成二维码，请等待：")
            self.log("  0 %[.....................]")
        except Exception as e:
            self.log(f"> 文件转二维码出错：{e}")
            raise e

    def singleImgReadyLog(self, patch_index):
        try:
            ratio = (patch_index + 1) / self.total_count
            a = '*' * int(ratio * 20)
            b = '.' * int((1 - ratio) * 20)
            c = ratio * 100  # 输入与输出的百分比
            self.repeatLog(" {:^3.0f}%[{}>{}]".format(c, a, b))
        except Exception as e:
            self.log(f"> {e}")
            raise e

    def allImgReady(self):
        try:
            # 二维码生成器生成完成后，开始按钮可点击
            self.log("> 完成{:^d}张二维码生成，预计需要展示{:^3.0f}秒".format(
                self.total_count,
                self.total_count / len(self.qrcode_img_labels) * self.qr_show_interval / 1000))
            self.log(f"> 点击开始按钮后{self.wait_sec_tmp}秒开始展示二维码")
            self.start_button.setEnabled(True)
        except Exception as e:
            self.log(f"> {e}")
            raise e

    def clickStart(self):
        # 点击开始按钮，
        self.file_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.file_2_qrcode_button.setEnabled(False)
        # 仅放开停止按钮进行终止，避免其他按钮点击产生干扰
        self.stop_button.setEnabled(True)
        # 开始倒计时
        self.count_down_timer = QTimer(self)
        self.count_down_timer.timeout.connect(self.countdownDone)
        self.count_down_timer.start(1000)  # 每秒触发一次

    def countdownDone(self):
        self.patch_index = 0
        # 等待倒计时结束后开始展示二维码
        if self.wait_sec_tmp > 0:
            self.log(f"> 倒计时{self.wait_sec_tmp}秒")
            self.wait_sec_tmp -= 1
        else:
            # 倒计时结束
            self.count_down_timer.stop()
            self.log("> 倒计时结束，开始生成二维码")
            self.wait_sec_tmp = self.wait_sec  # 重置秒数
            # 设置二维码生成Timer
            self.qrcode_timer = QTimer(self)
            self.qrcode_timer.timeout.connect(self.showQRcode)
            self.qrcode_timer.start(self.qr_show_interval)  # 每秒生成一个二维码

    def showQRcode(self):
        try:
            # 清除已有图片
            for label_index, q_image in enumerate(self.qrcode_img_labels):
                self.qrcode_img_labels[label_index].clear()

            if self.patch_index > self.total_count - 1:
                # 已经完成所有二维码的生成，停止生成二维码计时器
                self.qrcode_timer.stop()
                self.file_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.file_2_qrcode_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.log("> 二维码展示完毕")
            else:
                target_qrcode_imgs = self.str2qrcode_generator.qrcode_list[
                                     self.patch_index: min(self.patch_index + len(self.qrcode_img_labels),
                                                           self.total_count)]
                for label_index, q_image in enumerate(target_qrcode_imgs):
                    self.qrcode_img_labels[label_index].setPixmap(QPixmap.fromImage(q_image))
            self.patch_index += len(self.qrcode_img_labels)
        except Exception as e:
            print(e)
            raise e

    def clickStop(self):
        try:
            # 生成器重置
            # self.str2qrcode_generator = Str2QRcodeGenerator()
            # 各种计时器重置
            if self.count_down_timer is not None:
                self.count_down_timer.stop()
            if self.qrcode_timer is not None:
                self.qrcode_timer.stop()

            self.patch_index = 0
            # 按钮重置
            self.file_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.file_2_qrcode_button.setEnabled(False)
            for label_index, q_image in enumerate(self.qrcode_img_labels):
                # 清除已有图片
                self.qrcode_img_labels[label_index].clear()

            self.log("> 已重置")
        except Exception as e:
            print(e)
            raise e


if __name__ == '__main__':
    root = Tk()
    root.withdraw()

    app = QApplication(sys.argv)
    ex = File2QRcodeGenerator()
    ex.show()
    sys.exit(app.exec_())
