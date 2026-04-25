@echo off
chcp 65001 >nul
REM 简单的音频剪辑批处理入口
REM 用法: clip.bat <输入文件> <开始时间> <结束时间> [输出文件]

python "%~dp0audio_clip.py" %*

pause
