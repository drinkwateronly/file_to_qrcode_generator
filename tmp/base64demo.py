import base64
import zlib

import file_to_qrcode as ff


# 1.压缩
compressed_data = zlib.compress(b"123")
# 2.base64编码转字符串
encoded_str = str(base64.b64encode(compressed_data))

print(encoded_str)

# 2. Base64 解码（还原字节数据）
compressed_data = base64.b64decode('eJwzNDIGAAEtAJc=')
# 3. Zlib 解压缩（还原原始数据）
original_data = zlib.decompress(compressed_data)

print(original_data)