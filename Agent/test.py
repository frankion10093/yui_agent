# pip install pillow

import os
from pathlib import Path
from PIL import Image

# 根目录为当前脚本所在目录
root = Path.cwd() / "output"

# 遍历 output 目录下的所有子文件夹
for folder in root.iterdir():
    if folder.is_dir():
        # 收集该文件夹下所有以 .png 结尾的文件，按文件名排序
        png_files = sorted(folder.glob("*.png"))
        if not png_files:
            continue

        # 打开所有图片并转换为 RGB（Pillow 需要 RGB 或 CMYK 才能保存为 PDF）
        images = [Image.open(p).convert("RGB") for p in png_files]

        # PDF 文件名为原文件夹名
        pdf_path = folder / f"{folder.name}.pdf"

        # 第一个图像保存为 PDF，后续图像作为附加页
        images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])

        # 关闭所有打开的图片文件
        for img in images:
            img.close()

print("转换完成！")