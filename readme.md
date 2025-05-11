Base64 的内容是有 0 ～ 9，a ～ z，A ～ Z，+，/ 组成，正好 64 个字符

 pyinstaller --windowed --upx-dir=C:\Users\chen\Downloads\upx-5.0.0-win64\upx-5.0.0-win64 --onefile --exclude-module PyQt5.QtWebEngine --exclude-module PyQt5.QtNetwork --exclude-module PyQt5.QtSql QRcodeScanner.py 

https://blog.csdn.net/jzwalliser/article/details/136010089
 pyinstaller --windowed --upx-dir=C:\Users\chen\Downloads\upx-5.0.0-win64\upx-5.0.0-win64 --onefile --exclude-module PyQt5.QtWebEngine --exclude-module PyQt5.QtNetwork --exclude-module PyQt5.QtSql --add-data "libzbar-64.dll;pyzbar" --add-data "libiconv.dll;pyzbar" QRcodeScanner.py  
File2QRcodeGenerator.py


--add-data=libiconv.dll:./pyzbar/ --add-data=libzbar-64.dll:./pyzbar/

   pyinstaller --windowed --onefile \
       --add-data "e:\\_code\\file_to_qrcode_generator\\venv\\lib\\site-packages\\libiconv.dll;pyzbar" \
       --add-data "e:\\_code\\file_to_qrcode_generator\\venv\\lib\\site-packages\\libzbar-0.dll;pyzbar" \
       QRcodeScanner.py