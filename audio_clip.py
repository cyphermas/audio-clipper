#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的音频剪辑脚本
依赖: pydub, ffmpeg
安装: pip install pydub
"""

import sys
import os
from pathlib import Path

try:
    from pydub import AudioSegment
except ImportError:
    print("错误: 未安装 pydub，请先运行: pip install pydub")
    sys.exit(1)


def parse_time(time_str):
    """
    解析时间字符串，支持:
    - 纯数字（秒）: 10, 10.5
    - mm:ss 格式: 1:30, 01:30
    - hh:mm:ss 格式: 1:02:30
    """
    time_str = str(time_str).strip()
    
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            # mm:ss
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 3:
            # hh:mm:ss
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
    else:
        return float(time_str)
    
    raise ValueError(f"无法解析时间格式: {time_str}")


def clip_audio(input_path, start_time, end_time, output_path=None):
    """
    剪辑音频文件
    
    Args:
        input_path: 输入音频文件路径
        start_time: 开始时间（支持秒或 mm:ss 格式）
        end_time: 结束时间（支持秒或 mm:ss 格式，或负数为倒数）
        output_path: 输出文件路径，默认在原文件名后加 _clipped
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        print(f"错误: 文件不存在 - {input_path}")
        return False
    
    # 解析时间
    start_ms = int(parse_time(start_time) * 1000)
    end_ms = int(parse_time(end_time) * 1000)
    
    print(f"正在加载音频: {input_path}")
    audio = AudioSegment.from_file(str(input_path))
    total_ms = len(audio)
    
    print(f"音频总时长: {total_ms / 1000:.2f} 秒")
    
    # 处理负数结束时间（倒数）
    if end_ms < 0:
        end_ms = total_ms + end_ms
    
    # 边界检查
    if start_ms < 0:
        start_ms = 0
    if end_ms > total_ms:
        end_ms = total_ms
    if start_ms >= end_ms:
        print("错误: 开始时间必须小于结束时间")
        return False
    
    print(f"剪辑区间: {start_ms/1000:.2f}s ~ {end_ms/1000:.2f}s")
    
    # 剪辑
    clipped = audio[start_ms:end_ms]
    
    # 确定输出路径
    if output_path is None:
        output_path = input_path.with_stem(input_path.stem + "_clipped")
    else:
        output_path = Path(output_path)
    
    # 根据输出后缀确定格式
    format_map = {
        '.mp3': 'mp3',
        '.wav': 'wav',
        '.m4a': 'mp4',
        '.flac': 'flac',
        '.ogg': 'ogg',
        '.aac': 'aac',
        '.wma': 'wma',
    }
    fmt = format_map.get(output_path.suffix.lower(), 'mp3')
    
    print(f"正在保存: {output_path} (格式: {fmt})")
    clipped.export(str(output_path), format=fmt)
    
    print(f"完成! 输出文件: {output_path}")
    return True


def interactive_mode():
    """交互模式"""
    print("=" * 50)
    print("        简单音频剪辑工具")
    print("=" * 50)
    print("支持格式: mp3, wav, m4a, flac, ogg 等")
    print("时间格式: 秒(10.5) 或 mm:ss(1:30) 或 hh:mm:ss")
    print("=" * 50)
    
    input_path = input("\n请输入音频文件路径: ").strip().strip('"')
    
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return
    
    start_time = input("开始时间 (如 0 或 1:30): ").strip()
    end_time = input("结束时间 (如 60 或 2:30，留空表示到末尾): ").strip()
    
    if not end_time:
        # 获取音频总时长
        try:
            audio = AudioSegment.from_file(input_path)
            end_time = len(audio) / 1000
            print(f"未指定结束时间，自动设为末尾: {end_time:.2f}秒")
        except Exception as e:
            print(f"无法读取音频: {e}")
            return
    
    output_path = input("输出文件路径 (留空自动命名): ").strip().strip('"')
    if not output_path:
        output_path = None
    
    clip_audio(input_path, start_time, end_time, output_path)


def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("用法:")
        print("  python audio_clip.py <输入文件> <开始时间> <结束时间> [输出文件]")
        print()
        print("示例:")
        print('  python audio_clip.py song.mp3 10 60')
        print('  python audio_clip.py song.mp3 1:30 2:45 out.mp3')
        print('  python audio_clip.py song.mp3 0 -10  (去掉末尾10秒)')
        print()
        
        # 如果没有参数，进入交互模式
        if len(sys.argv) == 1:
            interactive_mode()
        else:
            print("参数不足，进入交互模式...")
            interactive_mode()
    else:
        input_path = sys.argv[1]
        start_time = sys.argv[2]
        end_time = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        clip_audio(input_path, start_time, end_time, output_path)


if __name__ == "__main__":
    main()
