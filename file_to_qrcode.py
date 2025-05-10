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
    encoded_str = str(base64.b64encode(compressed_data))
    print("encoded_str:", encoded_str)
    return encoded_str


def str2file_decoder(encoded_str):
    print("str2file_decoder: encode_str:", encoded_str)
    try:
        # 1. 去除字符串的 b'' 标记（如果有）
        if encoded_str.startswith("b'") and encoded_str.endswith("'"):
            encoded_str = encoded_str[2:-1]
        print("remove b:", encoded_str)
        # 2. Base64 解码（还原字节数据）
        compressed_data = base64.b64decode(encoded_str)
        # 3. Zlib 解压缩（还原原始数据）
        original_data = zlib.decompress(compressed_data)
        return original_data
    except Exception as e:
        print(e)



def make_qrcode_img(input_str):
    qr = QRCode(
        version=40,
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
