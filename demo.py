import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGridLayout


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 创建grid layout
        grid = QGridLayout(self)

        # 创建一个标签，让它跨2行
        label = QLabel('这是一个标签', self)
        # 参数分别是：widget, 行起始位置, 列起始位置, 跨越的行数, 跨越的列数
        grid.addWidget(label, 0, 0, 2, 1)  # 让label从第0行第0列开始，跨越2行，1列

        # 创建一个按钮，让它跨2行
        button = QPushButton('点击我', self)
        grid.addWidget(button, 2, 0, 2, 1)  # 让button从第2行第0列开始，跨越2行，1列

        # 设置窗口的其他属性
        self.setLayout(grid)
        self.setWindowTitle('Grid Layout Example')
        self.setGeometry(300, 300, 300, 200)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())