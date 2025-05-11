import io

from tools import  makeQRcodeImg

qr_code_img = makeQRcodeImg("hello world")
byte_array = io.BytesIO()
qr_code_img.save(byte_array)
byte_array.seek(0)
