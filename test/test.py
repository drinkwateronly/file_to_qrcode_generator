import time
import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, pyqtSignal


class PictureOCR(QThread):
    """
    对图片进行 OCR 识别，功能服务，可单独放一个文件
    """
    image_ready = pyqtSignal()  # 定义一个信号，通知主线程显示图片

    def __init__(self, *args, **kwargs):
        super(PictureOCR, self).__init__()

    def run(self):
        time.sleep(2)  # 模拟耗时操作
        print('任务执行中')
        self.image_ready.emit()  # 任务完成后发出信号


class MainWindow(QtWidgets.QMainWindow):
    """PyQt主界面"""
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.resize(500, 300)

        # 初始化图片线程
        self.p = PictureOCR()
        self.p.image_ready.connect(self.show_image)  # 连接信号到槽函数

        # 按钮
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setText('开始异步任务')
        self.pushButton.clicked.connect(self.click_event)
        self.pushButton.move(200, 50)

        # 图片显示标签
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setGeometry(150, 100, 200, 200)
        self.image_label.setScaledContents(True)

    def click_event(self):
        self.p.start()  # 启动线程

    def show_image(self):
        # 设置图片路径（可以替换为实际图片路径）
        pixmap = QtGui.QPixmap("example.png")  # 请确保图片文件在当前目录下或提供完整路径
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap)
        else:
            print("图片加载失败")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
