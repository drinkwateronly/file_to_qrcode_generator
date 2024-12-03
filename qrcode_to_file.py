import zlib
import base64
import cv2
from pyzbar import pyzbar


def str2file_decoder(input_str):
    # 1.base64解码，转为压缩后的文件
    compressed_data = base64.b64decode(input_str)
    # 2.解压缩
    decompressed_data = zlib.decompress(compressed_data)
    return decompressed_data


def qrcode_scan(input_image):
    data = pyzbar.decode(input_image)
    output_str = data[0].data.decode('utf-8')
    return output_str


if __name__ == '__main__':
    # 1、读取二维码图片
    qrcode_image = cv2.imread('qrcode.png')
    decoded_str = str2file_decoder(qrcode_scan(qrcode_image))

    with open('data_decoded', 'wb') as f:
        f.write(decoded_str)
