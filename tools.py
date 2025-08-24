
from zlib import compress, decompress
from base64 import b64encode, b64decode
from qrcode import QRCode, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from hashlib import md5
from re import fullmatch
from os import path



# 二维码纠错级别
error_correction_options = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H,
}


def makeQRcodeImg(input_str,
                  version=20,
                  error_correction_lvl='M',
                  box_size=5,
                  border=1):
    qr = QRCode(
        version= min(max(version, 1), 40),
        error_correction=error_correction_options[error_correction_lvl],
        box_size=box_size,
        border=border,
    )
    qr.add_data(input_str)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")




def file2strEncode(input_data):
    # 1.压缩
    compressed_data = compress(input_data)
    # 2.base64编码转字符串，格式为b'??'
    # str1 = str(b64encode(compressed_data))
    # print(str1)

    return str(b64encode(compressed_data))


def str2file_decoder(encoded_str):
    print(encoded_str)
    # 1. 去除字符串的 b'' 标记（如果有）
    if encoded_str.startswith("b'") and encoded_str.endswith("'"):
        encoded_str = encoded_str[2:-1]

    # 2. Base64 解码（还原字节数据）
    compressed_data = b64decode(encoded_str)
    # 3. Zlib 解压缩（还原原始数据）
    original_data = decompress(compressed_data)
    return original_data

def checkFileSize(file_path, max_size_mb):
    max_size_bytes = max_size_mb * 1024 * 1024
    return path.getsize(file_path) <= max_size_bytes

def getMd5(input_byte):
    return md5(input_byte).hexdigest()

def is_integer(s):
    pattern = r'^\d+$'  # 匹配可选正负号的整数
    return bool(fullmatch(pattern, s))


def chinese_ljust(s, width, fillchar=' '):
    """
    支持中文字符的左对齐函数
    中文字符算2个宽度，英文字符算1个宽度
    """
    current_width = 0
    for char in s:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            current_width += 2
        else:
            current_width += 1

    # 计算需要填充的空格数
    padding = max(0, width - current_width)
    return s + fillchar * padding
