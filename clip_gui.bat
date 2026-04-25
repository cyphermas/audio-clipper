@echo off
chcp 65001 >nul
REM 音频剪辑图形界面
REM 双击运行即可

cd /d "%~dp0"
python "audio_clip_gui.py"
