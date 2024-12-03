import zlib
import base64
import cv2
from pyzbar import pyzbar
import qrcode
from qrcode import QRCode


# 压缩文件
def file2str_encoder(input_data):
    # 1.压缩
    compressed_data = zlib.compress(input_data)
    # 2.base64编码转字符串
    encoded_str = base64.b64encode(compressed_data)
    return encoded_str


def make_qrcode_img(input_str):
    qr = QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=1,
    )
    qr.add_data(input_str)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


if __name__ == '__main__':
    # 添加数据到二维码中
    with open('test_file', 'rb') as f:
        data = f.read()

    str = file2str_encoder(data)
    #
    qrcode_img = make_qrcode_img(str)
    # 保存二维码图像
    qrcode_img.save("qrcode.png")
    print("二维码已生成并保存为 qrcode.png")
