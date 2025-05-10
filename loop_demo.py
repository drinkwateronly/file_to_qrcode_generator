import io
import math
import os
import sys
import tkinter
from tkinter import messagebox

import win32con
import win32gui
import win32print
from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QVBoxLayout, QWidget, QTextEdit, QPushButton, \
    QHBoxLayout, QSplitter, QGridLayout, QLineEdit, QFormLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from file_to_qrcode import file2str_encoder, make_qrcode_img


class qrcodeGenerator(QThread):
    images_ready = pyqtSignal()
    single_image_ready = pyqtSignal()

    def __init__(self, *args, **kwargs):
        self.encoded_str = None
        self.patch_index = 0
        self.qrcode_list = []
        self.patch_size = 0
        super(qrcodeGenerator, self).__init__()

    def set_params(self, encoded_str, patch_size, total_count):
        """动态设置数据列表"""
        self.encoded_str = encoded_str
        self.patch_size = patch_size
        self.total_count_count = total_count

    def run(self):
        try:
            self.qrcode_list = []
            for self.patch_index in range(self.total_count_count):
                # print(f"第{self.patch_index}张二维码生成")
                right_index = min((self.patch_index + 1) * self.patch_size, len(self.encoded_str))
                patch = self.encoded_str[self.patch_index * self.patch_size: right_index]
                qr_code_img = make_qrcode_img(f"##{self.total_count_count}##{self.patch_index}@@{patch}")
                byte_array = io.BytesIO()
                qr_code_img.save(byte_array)
                byte_array.seek(0)
                q_img = QImage.fromData(byte_array.getvalue())
                self.qrcode_list.append(q_img)

                self.single_image_ready.emit()
            self.images_ready.emit()
        except Exception as e:
            print(e)


def get_real_resolution():
    """获取真实的分辨率"""
    hDC = win32gui.GetDC(0)
    # 横向分辨率
    w = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    # 纵向分辨率
    h = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    return w, h


class QRCodeGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.qrcode_generator = qrcodeGenerator()
        self.qrcode_generator.images_ready.connect(self.qrcode_ready)  # 二维码处理完成，开始倒计时
        self.qrcode_generator.single_image_ready.connect(self.single_image_ready_log)  # 二维码处理完成，开始倒计时

        self.confirm_button = None
        self.screen_w, self.screen_h = get_real_resolution()

        self.reset_button = None
        self.image_labels = None
        self.total_count = None
        self.encoded_str = None
        self.file = None

        self.max_size_mb = 5  # 最大文件MB大小
        self.patch_size = 2 * 1024  # 每个二维码存放的字节数量,默认2kB
        self.patch_index = 0
        self.count_down_second = 3  # 点击开始后等待的秒数
        self.count_down_second_tmp = self.count_down_second
        self.qrcode_gen_second = 1
        self.input_labels = ["二维码字节数(kB)", "等待时长(秒)", "二维码生成频率(秒)"]

        self.file_button = None
        self.log_text_edit = None
        self.file_2_qrcode_button = None
        self.label = None
        self.count_down_timer = None
        self.qr_code_timer = None
        self.initUI()

    def initUI(self):
        # 左侧布局
        self.file_button = QPushButton('选择文件', self)
        self.file_button.clicked.connect(self.click_open_file)

        self.file_2_qrcode_button = QPushButton('文件转二维码', self)
        self.file_2_qrcode_button.clicked.connect(self.click_file_2_qrcode_button)
        self.file_2_qrcode_button.setEnabled(False)

        self.reset_button = QPushButton('重置', self)
        self.reset_button.clicked.connect(self.click_reset_button)

        self.start_button = QPushButton('开始传输二维码', self)
        self.start_button.clicked.connect(self.click_start_button)
        self.start_button.setEnabled(False)

        self.confirm_button = QPushButton('确认参数(建议默认)', self)
        self.confirm_button.clicked.connect(self.confirm_inputs)



        # 上半部分按钮布局
        button_layout1 = QHBoxLayout()
        button_layout1.addWidget(self.file_button)
        button_layout1.addWidget(self.confirm_button)

        button_layout2 = QHBoxLayout()
        button_layout2.addWidget(self.file_2_qrcode_button)
        button_layout2.addWidget(self.reset_button)

        # 下半部分输入框和确认按钮
        self.input_fields = []
        form_layout = QFormLayout()

        for label in self.input_labels:
            input_field = QLineEdit(self)
            self.input_fields.append(input_field)
            form_layout.addRow(label, input_field)

        input_layout = QVBoxLayout()
        input_layout.addLayout(form_layout)

        # 日志文本框
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)

        # 左侧整体布局
        left_layout = QVBoxLayout()
        left_layout.addLayout(button_layout1)
        left_layout.addLayout(button_layout2)
        left_layout.addWidget(self.start_button)

        left_layout.addLayout(input_layout)
        left_layout.addWidget(self.log_text_edit)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        # 右侧布局
        self.image_labels = [QLabel(self) for _ in range(6)]  # 创建9个QLabel
        for label in self.image_labels:
            label.setAlignment(Qt.AlignCenter)  # 居中对齐
            label.setScaledContents(True)  # 自动缩放内容以适应标签大小
            label.setFixedSize((self.screen_w - 100) / 4, (self.screen_w - 100) / 4)  # 设置固定大小，可以根据需要调整

        grid_layout = QGridLayout()  # 使用QGridLayout进行3x3布局
        for i, label in enumerate(self.image_labels):
            row = i // 3
            col = i % 3
            grid_layout.addWidget(label, row, col)

        right_widget = QWidget()
        right_widget.setLayout(grid_layout)

        # 分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)

        # 设置主窗口的中心部件
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.splitter)
        container.setLayout(container_layout)
        self.setLayout(container_layout)

        # 窗口显示后调整分割器大小
        # self.resize(self.screen_w, self.screen_h)  # 设置初始窗口大小
        self.showMaximized()  # 全屏显示
        self.splitter.setSizes([(self.screen_w - 100) / 4, (self.screen_w - 100) * 3 / 4])  # 左侧300，右侧700


    def is_file_size_within_limit(self, file_path):
        max_size_bytes = self.max_size_mb * 1024 * 1024
        return os.path.getsize(file_path) <= max_size_bytes

    def confirm_inputs(self):
        _

    def click_open_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*);;文本文件 (*.txt)",
                                                   options=options)
        if file_path:
            if not self.is_file_size_within_limit(file_path):
                messagebox.showwarning("note", "所选文件大小超过5MB")
                self.log("> 文件大于5MB，不允许传输，请重新选择文件")
            else:
                # 处理文件
                self.log(f"> 选择了文件: {file_path}")
                file = open(file_path, 'rb').read()
                self.encoded_str = file2str_encoder(file)
                self.total_count = math.ceil(len(self.encoded_str) / self.patch_size)

                self.log(f"> 需要生成{self.total_count}张二维码, 点击开始按钮生成")
                self.file_2_qrcode_button.setEnabled(True)

    def log(self, message):
        self.log_text_edit.append(message)

    def click_file_2_qrcode_button(self):
        self.patch_index = 0
        # 二维码生成器开始生成二维码
        self.qrcode_generator.set_params(encoded_str=self.encoded_str, patch_size=self.patch_size,
                                         total_count=self.total_count)
        self.qrcode_generator.start()
        # 进度条
        self.log("> 开始生成二维码，请等待：")
        self.log("  0 %[.....................]")

    def single_image_ready_log(self):
        ratio = (self.qrcode_generator.patch_index + 1) / self.total_count
        a = '*' * int(ratio * 20)
        b = '.' * int((1 - ratio) * 20)
        c = ratio * 100 # 输入与输出的百分比
        self.repeat_log(" {:^3.0f}%[{}>{}]".format(c, a, b))


    def repeat_log(self, message):
        current_text = self.log_text_edit.toPlainText()
        processed_text = current_text[:len(current_text) - len(message)]
        self.log_text_edit.setPlainText(processed_text + message)

    def click_reset_button(self):
        self.initUI()
        # # 点击停止生产二维码
        # self.count_down_timer.stop()
        # self.qr_code_timer.stop()
        # self.start_button.setEnabled(False)  # 重置开始按钮
        # self.reset_button.setEnabled(False)  # 重置停止按钮
        # for label in self.labels:
        #     label.setPixmap(QPixmap())
        self.log("> 已重置")


    def qrcode_ready(self):
        # 二维码生成器生成完成后，开始按钮可点击
        self.log("> 完成二维码生成，预计需要展示{:^3.0f}秒".format(self.total_count / len(self.image_labels) * self.qrcode_gen_second))
        self.log(f"> 点击开始按钮后{self.count_down_second_tmp}秒开始展示二维码")
        self.start_button.setEnabled(True)

    def click_start_button(self):
        # 点击开始按钮，开始倒计时
        self.count_down_timer = QTimer(self)
        self.count_down_timer.timeout.connect(self.countdown_done)
        self.count_down_timer.start(1000)  # 每秒触发一次


    def countdown_done(self):
        # 等待倒计时结束后开始展示二维码
        if self.count_down_second_tmp > 0:
            self.log(f"> 倒计时{self.count_down_second_tmp}秒")
            self.count_down_second_tmp -= 1
        else:
            # 倒计时结束
            self.count_down_timer.stop()
            self.log("> 倒计时结束，开始生成二维码")
            self.count_down_second_tmp = self.count_down_second # 重置秒数

            # 设置二维码生成Timer
            self.qr_code_timer = QTimer(self)
            self.qr_code_timer.timeout.connect(self.show_qrcode)
            self.qr_code_timer.start(self.qrcode_gen_second * 1000)  # 每秒生成一个二维码

    def show_qrcode(self):
        for label_index, q_image in enumerate(self.image_labels):
            self.image_labels[label_index].clear()
        if self.patch_index > self.total_count - 1:
            # 已经完成所有二维码的生成，停止生成二维码计时器
            self.qr_code_timer.stop()
            self.start_button.setEnabled(False)
            self.file_2_qrcode_button.setEnabled(False)
            self.log("")
        else:
            target_qrcode_imgs = self.qrcode_generator.qrcode_list[
                                 self.patch_index: min(self.patch_index + len(self.image_labels), self.total_count)]
            for label_index, q_image in enumerate(target_qrcode_imgs):
                self.image_labels[label_index].setPixmap(QPixmap.fromImage(q_image))
        self.patch_index += len(self.image_labels)



if __name__ == '__main__':
    root = tkinter.Tk()
    root.withdraw()

    app = QApplication(sys.argv)
    ex = QRCodeGenerator()
    ex.show()
    sys.exit(app.exec_())