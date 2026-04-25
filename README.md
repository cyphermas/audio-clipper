# 🎵 简单音频剪辑工具

一个轻量级的音频剪辑工具，支持**图形界面可视化操作**和**命令行快速剪辑**。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ 功能特性

- 🖱️ **波形可视化 + 鼠标框选** — 在波形图上拖拽即可选择剪辑区间
- ▶️ **实时试听** — 播放选中片段，红色虚线指示当前播放位置
- ⌨️ **精确时间输入** — 支持 `秒`、`mm:ss`、`hh:mm:ss` 多种格式
- 💾 **多格式导出** — MP3、WAV、FLAC、OGG、M4A
- ⌨️ **命令行模式** — 适合批处理和脚本自动化

---

## 📦 安装依赖

```bash
pip install pydub pygame matplotlib numpy
```

> ⚠️ **Windows 用户**：本工具需要 [ffmpeg](https://ffmpeg.org) 来处理 MP3/M4A/FLAC 等格式。
>
> 如果你未安装，可以运行仓库中的自动配置脚本：
> ```bash
> python setup_ffmpeg.py
> ```

---

## 🖥️ 图形界面使用

### 快速启动

```bash
python audio_clip_gui.py
```

或双击 `clip_gui.bat`（Windows）。

### 操作步骤

1. 点击 **📂 打开音频**，选择要剪辑的音频文件
2. 在波形图上 **按住鼠标左键拖拽**，框选想要保留的片段
   - 或在底部输入框手动填写开始/结束时间
3. 点击 **▶️ 播放片段** 试听选中部分
4. 满意后点击 **💾 导出剪辑**，保存为新文件

### 界面截图示意

```
┌─────────────────────────────────────────────┐
│ [📂打开音频] [▶️播放片段] [⏹️停止] [💾导出剪辑]    │
├─────────────────────────────────────────────┤
│                                               │
│           ~ 波形可视化区域 ~                    │
│         （拖拽鼠标框选剪辑区间）                 │
│                                               │
├─────────────────────────────────────────────┤
│  开始时间: [ 1:30 ]    结束时间: [ 2:45 ]      │
│           [  应用时间  ]                       │
└─────────────────────────────────────────────┘
```

---

## ⌨️ 命令行使用

```bash
python audio_clip.py <输入文件> <开始时间> <结束时间> [输出文件]
```

### 示例

```bash
# 剪辑第10秒到第60秒
python audio_clip.py song.mp3 10 60

# 使用 mm:ss 格式
python audio_clip.py song.mp3 1:30 2:45 out.mp3

# 去掉末尾10秒（负数表示倒数）
python audio_clip.py song.mp3 0 -10

# 只保留最后30秒
python audio_clip.py song.mp3 -30 0
```

直接运行不加参数会进入**交互模式**：

```bash
python audio_clip.py
```

---

## 📁 项目结构

```
audio-clip/
├── audio_clip_gui.py    # 图形界面主程序
├── audio_clip.py        # 命令行/交互式程序
├── setup_ffmpeg.py      # ffmpeg 自动下载配置脚本
├── clip_gui.bat         # Windows GUI 启动脚本
├── clip.bat             # Windows 命令行启动脚本
├── .gitignore
└── README.md
```

---

## 🛠️ 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.8+ | 必需 |
| pydub | latest | 音频处理 |
| pygame | latest | 音频播放 |
| matplotlib | latest | 波形绘制 |
| numpy | latest | 数据处理 |
| ffmpeg | - | 处理非 WAV 格式（必需） |

---

## 📝 时间格式说明

| 格式 | 示例 | 含义 |
|------|------|------|
| 秒 | `10` / `10.5` | 10秒 / 10.5秒 |
| mm:ss | `1:30` | 1分30秒 |
| hh:mm:ss | `1:02:30` | 1小时2分30秒 |
| 倒数 | `-10` | 从末尾倒数10秒 |

---

## 📄 License

MIT License
