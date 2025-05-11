import zipfile
import os

# 生成一个约 4MB 的文本文件内容
def generate_large_text_file(filename, target_size_mb):
    target_size_bytes = target_size_mb * 1024 * 1024
    chunk = "A" * 1024 * 1024 * 1024 * 4  # 1MB per line


    with open(filename, 'w') as f:
        for _ in range(target_size_mb):
            f.write(chunk)
            if os.path.getsize(filename) >= target_size_bytes:
                break
    print(f"已生成 {target_size_mb}MB 的测试文件: {filename}")

# 压缩为 ZIP 文件
def create_zip_with_large_file(input_filename, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(input_filename)
    print(f"已生成 ZIP 文件: {zip_filename}")

if __name__ == "__main__":
    txt_file = "test_4mb.txt"
    zip_file = "test_4mb.zip"

    # 生成 4MB 文本文件
    generate_large_text_file(txt_file, 4)

    # 创建 ZIP 文件
    create_zip_with_large_file(txt_file, zip_file)

    # 删除原始文本文件（可选）
    os.remove(txt_file)