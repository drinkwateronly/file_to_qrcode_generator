from math import ceil
import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QFileDialog, QVBoxLayout,
                             QWidget, QTextEdit, QPushButton, QGridLayout,
                             QLineEdit, QComboBox, QMessageBox)
from PyQt5.QtGui import QPixmap, QTextCursor
from PyQt5.QtCore import Qt, QTimer
from tools import file2strEncode, getMd5, is_integer, checkFileSize
from Str2QRcodeGenerator import Str2QRcodeGenerator


class File2QRcodeGenerator(QWidget):
    # 按钮
    file_select_button: QPushButton
    file_2_qrcode_button: QPushButton
    matrix_start_button: QPushButton
    stop_button: QPushButton
    log_clear_button: QPushButton
    # 下拉
    qr_ver_combo_box: QComboBox
    qr_lvl_combo_box: QComboBox
    matrix_size_combo_box: QComboBox
    wait_sec_combo_box: QComboBox
    # 输入框
    byte_per_code_input: QLineEdit
    show_interval_input: QLineEdit
    # 日志
    log_text_edit: QTextEdit
    # 矩阵
    matrix_labels: list
    # 矩阵布局
    matrix_grid_layout: QGridLayout
    # 文件转二维码生成器
    str2qrcode_generator: Str2QRcodeGenerator
    # timer
    count_down_timer: QTimer
    qrcode_timer: QTimer

    def __init__(self):
        super().__init__()
        # 参数
        self.max_size_mb = 5  # 最大文件MB大小
        self.patch_size = 1500  # 每个二维码存放的字节数量,默认1500B

        self.patch_size_limit = 2 * 1024  # 最多2000B
        self.qr_show_interval = 1000  # 每轮二维码展示的间隔（秒）
        self.qr_show_interval_limit = 199  # 每轮二维码展示的间隔（秒）
        self.version = 20  #

        self.error_correction_lvl = 'M (15%)'
        self.error_correction_opt = ['L (7%)', 'M (15%)', 'Q (25%)', 'H (30%)']

        self.matrix_size_opt = ['2×3', '3×4', '4×5']
        self.max_qrcode_per_matrix = 20  # 单个矩阵最多展示20个二维码，4×5
        self.qrcode_per_matrix = 6  # 单个矩阵默认值
        self.qr_show_matrix_col = 3

        # 初始化
        self.total_count = None
        self.encoded_str = ''
        self.file = None
        self.first_img_ready = True
        self.patch_index = 0
        self.wait_sec = 0

        # UI初始化
        self.initUI()

    def initUI(self):
        """
        :return:
        """
        # 选择文件按钮
        self.file_select_button = QPushButton('选择文件', self)
        self.file_select_button.clicked.connect(self.clickOpenFile)

        # 文件转二维码按钮
        self.file_2_qrcode_button = QPushButton('文件转二维码', self)
        self.file_2_qrcode_button.clicked.connect(self.clickFile2QRcode)
        self.file_2_qrcode_button.setEnabled(False)

        # 重置按钮
        self.stop_button = QPushButton('停止', self)
        self.stop_button.clicked.connect(self.clickStop)
        self.stop_button.setEnabled(False)

        # 开始传输按钮
        self.matrix_start_button = QPushButton('开始传输二维码', self)
        self.matrix_start_button.clicked.connect(self.clickStart)
        self.matrix_start_button.setEnabled(False)

        # 清空日志按钮
        self.log_clear_button = QPushButton('清空日志', self)
        self.log_clear_button.clicked.connect(self.clearLog)
        self.log_clear_button.setEnabled(True)

        # 二维码版本选项
        self.qr_ver_combo_box = QComboBox()
        # 填充 1~40 的选项
        for i in range(1, 41):
            self.qr_ver_combo_box.addItem(str(i))
        # 设置默认值20，即index为19的选项
        self.qr_ver_combo_box.setCurrentText(str(self.version))

        # 纠错级别选项
        self.qr_lvl_combo_box = QComboBox()
        # 填充选项
        self.qr_lvl_combo_box.addItems(self.error_correction_opt)
        # 设置默认值（例如：40）
        self.qr_lvl_combo_box.setCurrentText(self.error_correction_lvl)

        # 二维码矩阵尺寸选项
        self.matrix_size_combo_box = QComboBox()
        self.matrix_size_combo_box.addItems(self.matrix_size_opt)
        self.matrix_size_combo_box.setCurrentIndex(0)  # 设置默认值
        self.matrix_size_combo_box.currentIndexChanged.connect(self.onMatrixSizeChanged)

        # 等待时间选项
        self.wait_sec_combo_box = QComboBox()
        # 填充选项
        self.wait_sec_combo_box.addItems(['0s', '1s', '2s', '3s'])
        # 设置默认值（例如：40）
        self.wait_sec_combo_box.setCurrentIndex(self.wait_sec)
        self.wait_sec_combo_box.currentIndexChanged.connect(self.onWaitSecChanged)

        # 输入框
        self.byte_per_code_input = QLineEdit(self)
        self.byte_per_code_input.setText(str(self.patch_size))

        self.show_interval_input = QLineEdit(self)
        self.show_interval_input.setText(str(self.qr_show_interval))

        # 日志文本框
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)

        # 左侧操作面板布局
        panel_grid_layout = QGridLayout()
        # 0
        panel_grid_layout.addWidget(self.file_select_button, 0, 0, 1, 4)
        # 1
        panel_grid_layout.addWidget(QLabel("二维码版本"), 1, 0)
        panel_grid_layout.addWidget(self.qr_ver_combo_box, 1, 1)
        panel_grid_layout.addWidget(QLabel("纠错级别"), 1, 2)
        panel_grid_layout.addWidget(self.qr_lvl_combo_box, 1, 3)
        # 2
        panel_grid_layout.addWidget(QLabel("二维码容量"), 2, 0)
        panel_grid_layout.addWidget(self.byte_per_code_input, 2, 1)
        panel_grid_layout.addWidget(QLabel("矩阵频率"), 2, 2)
        panel_grid_layout.addWidget(self.show_interval_input, 2, 3)
        # 3
        panel_grid_layout.addWidget(self.file_2_qrcode_button, 3, 0, 1, 4)
        # 4
        panel_grid_layout.addWidget(QLabel("矩阵尺寸"), 4, 0)
        panel_grid_layout.addWidget(self.matrix_size_combo_box, 4, 1)
        panel_grid_layout.addWidget(QLabel("等待时间"), 4, 2)
        panel_grid_layout.addWidget(self.wait_sec_combo_box, 4, 3)
        # 5
        panel_grid_layout.addWidget(self.matrix_start_button, 5, 0, 1, 4)
        # 6
        panel_grid_layout.addWidget(self.stop_button, 6, 0, 1, 2)
        panel_grid_layout.addWidget(self.log_clear_button, 6, 2, 1, 2)

        # 左侧整体布局
        left_layout = QVBoxLayout()
        left_layout.addLayout(panel_grid_layout)
        left_layout.addWidget(self.log_text_edit)

        # 二维码展示布局
        # 仅创建，不布局
        self.matrix_labels = [QLabel(self) for _ in range(self.max_qrcode_per_matrix)]  # 创建20个QLabel
        self.matrix_grid_layout = QGridLayout()  # 使用QGridLayout，创建12个占用
        self.matrix_grid_layout.setSpacing(self.max_qrcode_per_matrix)
        # 初始化布局
        self.updateMatrixLayout()

        # 主窗口
        main_grid_layout = QGridLayout()
        main_grid_layout.addLayout(left_layout, 0, 0)
        main_grid_layout.addLayout(self.matrix_grid_layout, 0, 1)
        main_grid_layout.setColumnStretch(0, 1)
        main_grid_layout.setColumnStretch(1, 4)

        self.setLayout(main_grid_layout)
        self.count_down_timer = QTimer()
        self.qrcode_timer = QTimer()
        self.showMaximized()  # 全屏显示

    def onMatrixSizeChanged(self, index):
        """当选择项改变时触发（通过索引）"""
        selected_text = self.matrix_size_combo_box.currentText()
        # 根据选择执行不同的操作
        if index == 0:  # 2×3
            self.qrcode_per_matrix = 6
            self.qr_show_matrix_col = 3
        elif index == 1:  # 3×4
            self.qrcode_per_matrix = 12
            self.qr_show_matrix_col = 4
        elif index == 2:  # 4×5
            self.qrcode_per_matrix = 20
            self.qr_show_matrix_col = 5
        self.updateMatrixLayout()
        self.log(f"> [矩阵尺寸]切换为{selected_text}")

    def onWaitSecChanged(self, index):
        """
        等待时间控件选项改变
        :param index: 改变后的index
        :return:
        """
        self.wait_sec = index
        self.log(f"> [等待时间]切换为{self.wait_sec}秒")

    def updateMatrixLayout(self):
        """
        动态更新矩阵布局
        :return:
        """
        # 清除现有布局项
        for i in reversed(range(self.matrix_grid_layout.count())):
            item = self.matrix_grid_layout.itemAt(i)
            if item.widget():
                self.matrix_grid_layout.removeWidget(item.widget())

        # 重新排列，只显示指定数量的label
        display_labels = self.matrix_labels[:self.qrcode_per_matrix]
        for i, label in enumerate(display_labels):
            row = i // self.qr_show_matrix_col
            col = i % self.qr_show_matrix_col
            self.matrix_grid_layout.addWidget(label, row, col)
            # 显示所有label，但通过布局控制可见性
            label.show()

        # 隐藏超出数量的label
        for i in range(self.qrcode_per_matrix, len(self.matrix_labels)):
            self.matrix_labels[i].hide()

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
                # 点击文件后，检查文件大小
                if not checkFileSize(file_path, self.max_size_mb):
                    QMessageBox.warning(None, "提示", f"所选文件大小不允许超过{self.max_size_mb}MB")
                    self.log(f"> 文件大于{self.max_size_mb}MB，传输时间过长，请重新选择文件")
                else:
                    # 处理文件
                    self.log(f"> 选择文件[{file_path}]")
                    file_data = open(file_path, 'rb').read()
                    self.encoded_str = file2strEncode(file_data)
                    self.total_count = ceil(len(self.encoded_str) / self.patch_size)
                    self.log(f"> md5校验码[{getMd5(file_data)}]")
                    self.log("> 请点击【文件转二维码】按钮生成二维码")

                    # 选择文件后，只允许点击【文件转二维码】及【日志清空】按钮
                    self.file_2_qrcode_button.setEnabled(True)
                    self.log_clear_button.setEnabled(True)
                    self.matrix_start_button.setEnabled(False)
                    self.stop_button.setEnabled(False)

        except Exception as e:
            self.log(f"> 打开文件出错：{e}")

    def clickFile2QRcode(self):
        """
        点击文件转二维码按钮，确认各种参数，新建Str2QRcodeGenerator实例进行处理
        :return:
        """
        try:
            # interval
            if not is_integer(self.show_interval_input.text()):
                QMessageBox.warning(None, "提示", "二维码生成频非整数，请修改")
                return
            else:
                self.qr_show_interval = int(self.show_interval_input.text())
                if self.qr_show_interval < self.qr_show_interval_limit:
                    QMessageBox.warning(None, "提示", f"生成频率应该大于{self.qr_show_interval_limit}ms，请修改")
                    return
            # byte
            if not is_integer(self.byte_per_code_input.text()):
                QMessageBox.warning(None, "提示", "二维码生成频非整数，请修改")
                return
            else:
                self.patch_size = int(self.byte_per_code_input.text())
                if self.patch_size > self.patch_size_limit:
                    QMessageBox.warning(None, "提示", f"二维码字节数应小于{self.patch_size_limit}，请修改")
                    return

            self.version = int(self.qr_ver_combo_box.currentText())
            self.error_correction_lvl = self.qr_lvl_combo_box.currentText()

            # 参数展示
            self.log("> 二维码参数：")
            log_str1 = f"{self.version}"
            log_str2 = f"{self.error_correction_lvl}"
            log_str3 = f"{self.patch_size} (bytes)"
            log_str4 = f"{self.qr_show_interval} (ms)"
            max_len = max(len(log_str1), len(log_str2), len(log_str3), len(log_str4))
            self.log('  丨二维码版本丨' + log_str1.ljust(max_len) + "|")
            self.log('  丨纠错级别  丨' + log_str2.ljust(max_len) + "|")
            self.log('  丨二维码容量丨' + log_str3.ljust(max_len) + "|")
            self.log('  丨矩阵频率  丨' + log_str4.ljust(max_len) + "|")

            # 按钮可用性设置
            self.file_select_button.setEnabled(False)
            self.file_2_qrcode_button.setEnabled(False)
            self.matrix_start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.log_clear_button.setEnabled(False)

            # 字符串转二维码生成器
            self.str2qrcode_generator = Str2QRcodeGenerator()
            # 单个二维码处理完成信号，用于日志展示
            self.str2qrcode_generator.single_image_ready.connect(self.singleImgReadyLog)
            # 二维码处理完成，开始倒计时
            self.str2qrcode_generator.images_ready.connect(self.allImgReady)
            # 错误处理
            self.str2qrcode_generator.error_signal.connect(self.errorLog)

            self.str2qrcode_generator.setParams(encoded_str=self.encoded_str,
                                                patch_size=self.patch_size,
                                                show_interval=self.qr_show_interval,
                                                version=self.version,
                                                error_correction_lvl=self.error_correction_lvl[0]  # 取第0个字符
                                                )
            # 初始化
            self.patch_index = 0
            self.first_img_ready = True
            # 线程开始
            self.str2qrcode_generator.start()

        except Exception as e:
            self.log(f"> 文件转二维码出错：{e}")

    def singleImgReadyLog(self, sig_img_list):
        """
        该方法接收Str2QRcodeGenerator每个二维码生成的信号，仅用于日志中进度的展示
        :param sig_img_list: [二维码index, 二维码总数量]
        :return:
        """
        try:
            patch_index = sig_img_list[0]
            if self.first_img_ready:
                # 仅展示一次
                self.total_count = sig_img_list[1]
                self.log(f"> 共需生成{self.total_count}张二维码")
                self.log(f"  进度： 0 %[.....................]")
                self.first_img_ready = False

            # 进度条
            ratio = (patch_index + 1) / self.total_count
            a = '*' * int(ratio * 20)
            b = '.' * int((1 - ratio) * 20)
            c = ratio * 100  # 输入与输出的百分比
            self.repeatLog("  进度：{:^3.0f}%[{}>{}]".format(c, a, b))
        except Exception as e:
            self.log(f"> {e}")

    def allImgReady(self):
        """
        所有二维码生成完毕，信号到达，
        """
        try:
            self.matrix_start_button.setEnabled(True)
            # 二维码生成器生成完成后，开始按钮可点击
            self.log("> 完成{:^d}张二维码生成，预计需要展示{:^3.0f}秒".format(
                self.total_count,
                self.total_count / self.qrcode_per_matrix * self.qr_show_interval / 1000))
            self.log(f"> 请点击【开始传输二维码】按钮，倒计时{self.wait_sec}秒开始")

            self.file_select_button.setEnabled(True)
            self.file_2_qrcode_button.setEnabled(True)
            self.matrix_start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.log_clear_button.setEnabled(True)

        except Exception as e:
            self.log(f"> {e}")

    def clickStart(self):
        """
        点击开始传输二维码按钮
        :return:
        """
        # 禁用按钮
        self.file_select_button.setEnabled(False)
        self.matrix_start_button.setEnabled(False)
        self.file_2_qrcode_button.setEnabled(False)
        self.log_clear_button.setEnabled(False)

        # 禁止调整矩阵尺寸
        self.matrix_size_combo_box.setEnabled(False)

        # 仅放开停止按钮进行终止，避免其他按钮点击产生干扰
        self.stop_button.setEnabled(True)

        # 开始倒计时
        self.count_down_timer = QTimer(self)
        self.count_down_timer.timeout.connect(self.countdownDone)
        self.count_down_timer.start(1000)  # 每秒触发一次

    def countdownDone(self):
        self.patch_index = 0
        # 等待倒计时结束后开始展示二维码
        if self.wait_sec > 0:
            self.log(f"> 倒计时{self.wait_sec}秒")
            self.wait_sec -= 1
        else:
            # 倒计时结束
            self.count_down_timer.stop()
            self.log("> 倒计时结束，开始传输矩阵")
            self.wait_sec = self.wait_sec_combo_box.currentIndex()  # 重置秒数
            # 设置二维码生成Timer
            self.qrcode_timer = QTimer(self)
            self.qrcode_timer.timeout.connect(self.showQRcode)
            self.qrcode_timer.start(self.qr_show_interval)  # 每秒生成一个二维码

    def showQRcode(self):
        try:
            # 清除已有图片
            for label_index, q_image in enumerate(self.matrix_labels):
                self.matrix_labels[label_index].clear()

            if self.patch_index > self.total_count - 1:
                # 已经完成所有二维码的生成，停止生成二维码计时器
                self.qrcode_timer.stop()
                self.file_select_button.setEnabled(True)
                self.matrix_start_button.setEnabled(True)
                self.file_2_qrcode_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.matrix_size_combo_box.setEnabled(True)
                self.log("> 传输已完成")
                self.log("--------------------------------------")
            else:
                # 取得当前需要展示的二维码
                target_qrcode_imgs = self.str2qrcode_generator.qrcode_list[
                                     self.patch_index: min(self.patch_index + self.qrcode_per_matrix,
                                                           self.total_count)]
                for label_index, q_image in enumerate(target_qrcode_imgs):
                    label_size = self.matrix_labels[label_index].size()
                    margin = 1  # 边距
                    available_width = label_size.width() - 2 * margin
                    available_height = label_size.height() - 2 * margin
                    pixmap = QPixmap.fromImage(q_image)
                    # 缩放图片，保持宽高比
                    scaled_pixmap = pixmap.scaled(
                        available_width,
                        available_height,
                        Qt.KeepAspectRatio,  # 保持宽高比
                        Qt.SmoothTransformation  # 平滑缩放
                    )
                    self.matrix_labels[label_index].setPixmap(scaled_pixmap)

                    # self.qrcode_img_labels[label_index].setPixmap(QPixmap.fromImage(q_image))
            self.patch_index += self.qrcode_per_matrix
        except Exception as e:
            self.log(e)

    def clickStop(self):
        try:
            # 生成器重置
            # self.str2qrcode_generator = Str2QRcodeGenerator()
            # 各种计时器重置
            if self.count_down_timer is not None:
                self.count_down_timer.stop()
            if self.qrcode_timer is not None:
                self.qrcode_timer.stop()
            self.str2qrcode_generator.exit_thread()

            self.patch_index = 0
            # 按钮重置
            self.file_select_button.setEnabled(True)
            self.matrix_start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.file_2_qrcode_button.setEnabled(False)

            for label_index, q_image in enumerate(self.matrix_labels):
                # 清除已有图片
                self.matrix_labels[label_index].clear()

            QTimer.singleShot(500, lambda: self.log("> 已重置"))
        except Exception as e:
            print(e)
            self.log(e)

    def log(self, message):
        self.log_text_edit.append(message)
        self.log_text_edit.moveCursor(QTextCursor.End)

    def errorLog(self, err_message):
        try:
            print(err_message)
            self.log(err_message)
        except Exception as e:
            self.log(f"> {e}")

    def repeatLog(self, message):
        current_text = self.log_text_edit.toPlainText()
        processed_text = current_text[:len(current_text) - len(message)]
        self.log_text_edit.setPlainText(processed_text + message)

    def clearLog(self):
        self.log_text_edit.setPlainText('')


if __name__ == '__main__':
    # 创建应用程序
    app = QApplication(sys.argv)
    # 创建并显示窗口
    window = File2QRcodeGenerator()
    window.setWindowTitle('QRMatrixGenerator v1.2')
    window.show()
    # 运行应用程序
    sys.exit(app.exec_())
