
from zlib import compress, decompress
from base64 import b64encode, b64decode
from qrcode import QRCode, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from hashlib import md5


# def get_real_resolution():
#     """获取真实的分辨率"""
#     hDC = win32gui.GetDC(0)
#     # 横向分辨率
#     w = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
#     # 纵向分辨率
#     h = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
#     return w, h


# 二维码纠错级别
error_correction_options = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H,
}


def makeQRcodeImg(input_str,
                  version=40,
                  error_correction_lvl='L',
                  box_size=5,
                  border=1):
    try:
        qr = QRCode(
            version=version,
            error_correction=error_correction_options[error_correction_lvl],
            box_size=box_size,
            border=border,
        )
        qr.add_data(input_str)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
    except Exception as e:
        print(2, e)


def file2strEncode(input_data):
    # 1.压缩
    compressed_data = compress(input_data)
    # 2.base64编码转字符串，格式为b'??'
    return str(b64encode(compressed_data))


def str2file_decoder(encoded_str):
    try:
        # 1. 去除字符串的 b'' 标记（如果有）
        if encoded_str.startswith("b'") and encoded_str.endswith("'"):
            encoded_str = encoded_str[2:-1]
        # 2. Base64 解码（还原字节数据）
        compressed_data = b64decode(encoded_str)
        # 3. Zlib 解压缩（还原原始数据）
        original_data = decompress(compressed_data)
        return original_data
    except Exception as e:
        print(e)


def getMd5(input_byte):
    return md5(input_byte).hexdigest()
