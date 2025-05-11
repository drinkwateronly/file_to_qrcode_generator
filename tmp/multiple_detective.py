import cv2
import numpy as np
from pyzbar.pyzbar import decode


def detect_qrcodes(image_path):
    # 读取图像
    image = cv2.imread(image_path)

    # 转换为灰度图像
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 检测二维码
    decoded_objects = decode(gray)

    # 遍历检测到的二维码
    for obj in decoded_objects:
        # 提取二维码的数据
        data = obj.data.decode('utf-8')
        print(f"Detected QR Code: {data}")

        # 绘制二维码的边界框
        points = obj.polygon
        if len(points) > 4:
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else:
            hull = points

        # 绘制边界框
        n = len(hull)
        for j in range(0, n):
            cv2.line(image, hull[j], hull[(j + 1) % n], (0, 255, 0), 3)

    # # 显示图像
    # cv2.imshow("QR Code Detection", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


# 调用函数检测图像中的二维码
detect_qrcodes('test1.png')
