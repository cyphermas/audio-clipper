#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动下载并配置 ffmpeg (Windows)
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path


def download_file(url, dest, chunk_size=8192):
    """带进度条的下载"""
    print(f"正在下载: {url}")
    req = urllib.request.urlopen(url)
    total = int(req.headers.get('content-length', 0))
    downloaded = 0
    
    with open(dest, 'wb') as f:
        while True:
            chunk = req.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded / total * 100
                mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                print(f"\r进度: {pct:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
    print()


def main():
    # 检查是否已有 ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"ffmpeg 已存在于系统 PATH: {ffmpeg_path}")
        return 0
    
    # 检查常用本地路径
    common_paths = [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("D:/ffmpeg/bin/ffmpeg.exe"),
        Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe",
    ]
    for p in common_paths:
        if p.exists():
            print(f"找到本地 ffmpeg: {p}")
            print(f"请将此目录加入系统 PATH: {p.parent}")
            return 0
    
    # 下载目录
    download_dir = Path(__file__).parent / "tools"
    download_dir.mkdir(exist_ok=True)
    
    zip_path = download_dir / "ffmpeg.zip"
    ffmpeg_dir = download_dir / "ffmpeg"
    
    # 如果已经下载解压过，直接配置
    if (ffmpeg_dir / "bin" / "ffmpeg.exe").exists():
        print(f"检测到已下载的 ffmpeg: {ffmpeg_dir}")
        _add_to_path(ffmpeg_dir / "bin")
        return 0
    
    # 下载 ffmpeg (使用 gyanddo 的 Windows build)
    print("未找到 ffmpeg，开始自动下载...")
    print("下载源: https://github.com/BtbN/FFmpeg-Builds/releases")
    
    # 使用一个稳定的 release 链接
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        download_file(url, zip_path)
    except Exception as e:
        print(f"下载失败: {e}")
        print("请手动下载 ffmpeg 并解压: https://ffmpeg.org/download.html#build-windows")
        return 1
    
    print("正在解压...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(download_dir)
    
    # 重命名解压出来的目录
    extracted = list(download_dir.glob("ffmpeg-master*"))
    if extracted:
        if ffmpeg_dir.exists():
            shutil.rmtree(ffmpeg_dir)
        extracted[0].rename(ffmpeg_dir)
    
    # 清理 zip
    zip_path.unlink(missing_ok=True)
    
    bin_dir = ffmpeg_dir / "bin"
    if not (bin_dir / "ffmpeg.exe").exists():
        print("解压后未找到 ffmpeg.exe，可能目录结构有变化")
        return 1
    
    print(f"ffmpeg 已下载到: {ffmpeg_dir}")
    _add_to_path(bin_dir)
    return 0


def _add_to_path(bin_dir):
    """将目录加入用户 PATH 环境变量"""
    bin_str = str(bin_dir.resolve())
    
    # 检查是否已在 PATH
    current_path = os.environ.get("PATH", "")
    if bin_str.lower() in current_path.lower():
        print("该目录已在系统 PATH 中")
        return
    
    # 使用 setx 永久加入用户 PATH
    print(f"\n正在将 {bin_str} 加入用户 PATH...")
    import subprocess
    result = subprocess.run(
        ["setx", "PATH", f"%PATH%;{bin_str}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ 配置成功！")
        print("⚠️  需要重新打开命令行窗口或重启程序，新 PATH 才会生效。")
    else:
        print(f"setx 失败: {result.stderr}")
        print(f"请手动将此目录加入系统 PATH: {bin_str}")


if __name__ == "__main__":
    sys.exit(main())
