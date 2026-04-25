#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频剪辑图形界面工具
依赖: pydub, pygame, matplotlib, numpy
安装: pip install pydub pygame matplotlib numpy
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import numpy as np
from pydub import AudioSegment
import pygame
import os
import tempfile
import threading
import shutil
import subprocess
import sys


def _check_ffmpeg():
    """检测 ffmpeg 是否可用"""
    if shutil.which("ffmpeg"):
        return True
    # 检查几个常见本地路径
    for p in [r"C:\ffmpeg\bin\ffmpeg.exe", r"D:\ffmpeg\bin\ffmpeg.exe",
              os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffmpeg.exe"),
              os.path.join(os.path.dirname(__file__), "tools", "ffmpeg", "bin", "ffmpeg.exe")]:
        if os.path.isfile(p):
            # 临时加入环境变量，让 pydub 能找到
            bin_dir = os.path.dirname(p)
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            return True
    return False


def _show_ffmpeg_dialog(parent):
    """显示 ffmpeg 缺失提示对话框"""
    dlg = tk.Toplevel(parent)
    dlg.title("需要安装 ffmpeg")
    dlg.geometry("500x280")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.resizable(False, False)
    
    ttk.Label(dlg, text="⚠️ 未检测到 ffmpeg", font=("Microsoft YaHei", 14, "bold")).pack(pady=(15, 5))
    
    msg = ("本工具需要 ffmpeg 来处理 MP3/M4A/FLAC 等音频格式。\n\n"
           "你可以：\n"
           "1. 点击「自动下载」一键安装（推荐）\n"
           "2. 点击「手动下载」前往官网自行下载\n"
           "3. 如果你已安装 ffmpeg，请确保其在系统 PATH 中")
    ttk.Label(dlg, text=msg, justify=tk.LEFT).pack(padx=20, pady=5)
    
    def auto_download():
        setup_path = os.path.join(os.path.dirname(__file__), "setup_ffmpeg.py")
        if os.path.isfile(setup_path):
            subprocess.Popen([sys.executable, setup_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            messagebox.showinfo("提示", "下载窗口已弹出，完成后请重启本程序。", parent=dlg)
        else:
            messagebox.showerror("错误", "未找到 setup_ffmpeg.py，请使用手动下载。", parent=dlg)
        dlg.destroy()
    
    def manual_download():
        import webbrowser
        webbrowser.open("https://ffmpeg.org/download.html#build-windows")
        messagebox.showinfo("提示", "请下载 Windows build，解压后将 bin 目录加入系统 PATH，然后重启本程序。", parent=dlg)
        dlg.destroy()
    
    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text="🔧 自动下载", command=auto_download).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="🌐 手动下载", command=manual_download).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="关闭", command=dlg.destroy).pack(side=tk.LEFT, padx=5)
    
    parent.wait_window(dlg)


class AudioClipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("音频剪辑工具")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 检测 ffmpeg
        self.has_ffmpeg = _check_ffmpeg()
        
        # 音频数据
        self.audio = None
        self.audio_path = None
        self.duration = 0.0
        self.sample_rate = 44100
        self.waveform_data = None
        self.time_axis = None
        
        # 剪辑区间（秒）
        self.start_time = 0.0
        self.end_time = 0.0
        self.playing = False
        self.temp_dir = tempfile.mkdtemp()
        self.temp_play_file = None
        
        # 初始化 pygame 音频
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error:
            pygame.mixer.init()
        
        self._build_ui()
        self._build_plot()
        
        # 如果没有 ffmpeg，延迟弹窗提示（等窗口渲染完成后）
        if not self.has_ffmpeg:
            self.root.after(500, lambda: _show_ffmpeg_dialog(self.root))
        
        # 定时更新播放进度
        self._schedule_playback_update()
    
    def _build_ui(self):
        """构建用户界面"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="📂 打开音频", command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▶️ 播放片段", command=lambda: self._play(False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏹️ 停止", command=self._stop).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 导出剪辑", command=self._export).pack(side=tk.LEFT, padx=2)
        
        self.lbl_info = ttk.Label(toolbar, text="未加载音频")
        self.lbl_info.pack(side=tk.RIGHT, padx=10)
        
        # matplotlib 画布区域
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 底部控制面板
        ctrl = ttk.LabelFrame(self.root, text="剪辑设置", padding=10)
        ctrl.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # 开始时间
        ttk.Label(ctrl, text="开始时间:").grid(row=0, column=0, sticky=tk.W)
        self.entry_start = ttk.Entry(ctrl, width=12)
        self.entry_start.grid(row=0, column=1, padx=5)
        self.entry_start.insert(0, "0:00")
        ttk.Label(ctrl, text="(秒 或 mm:ss)").grid(row=0, column=2, sticky=tk.W)
        
        # 结束时间
        ttk.Label(ctrl, text="结束时间:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_end = ttk.Entry(ctrl, width=12)
        self.entry_end.grid(row=1, column=1, padx=5)
        self.entry_end.insert(0, "0:00")
        ttk.Label(ctrl, text="(秒 或 mm:ss，留空=结尾)").grid(row=1, column=2, sticky=tk.W)
        
        # 应用按钮
        ttk.Button(ctrl, text="应用时间", command=self._apply_manual_time).grid(row=0, column=3, rowspan=2, padx=15)
        
        # 操作提示
        hint = ttk.Label(ctrl, text="提示: 在波形图上按住鼠标左键拖拽可选择片段", foreground="gray")
        hint.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(5,0))
        
        # 播放进度条
        self.progress = ttk.Scale(self.root, from_=0, to=1000, orient=tk.HORIZONTAL, state=tk.DISABLED)
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=2)
        self.lbl_progress = ttk.Label(self.root, text="00:00 / 00:00")
        self.lbl_progress.pack(side=tk.BOTTOM, anchor=tk.W, padx=10)
    
    def _build_plot(self):
        """构建 matplotlib 波形图"""
        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("时间 (秒)")
        self.ax.set_ylabel("振幅")
        self.ax.set_title("波形预览 (请打开音频文件)")
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.grid(True, alpha=0.3)
        
        # 选区高亮矩形
        self.select_rect = Rectangle((0, -1), 0, 2, facecolor='lightblue', alpha=0.3, edgecolor='blue', linewidth=1)
        self.ax.add_patch(self.select_rect)
        
        # 播放头竖线
        self.play_line = self.ax.axvline(x=0, color='red', linestyle='--', linewidth=1, visible=False)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
        
        # 鼠标拖拽选择
        self._dragging = False
        self._drag_start_x = None
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_drag)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
    
    def _sec_to_str(self, sec):
        """秒转 mm:ss 字符串"""
        sec = max(0, sec)
        m = int(sec // 60)
        s = sec - m * 60
        if s == int(s):
            return f"{m}:{int(s):02d}"
        return f"{m}:{s:05.2f}"
    
    def _str_to_sec(self, s):
        """解析时间字符串为秒"""
        s = str(s).strip()
        if not s:
            return None
        if ':' in s:
            parts = s.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(s)
    
    def _open_file(self):
        """打开音频文件"""
        path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[
                ("音频文件", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.wma"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("M4A", "*.m4a"),
                ("FLAC", "*.flac"),
                ("所有文件", "*.*")
            ]
        )
        if not path:
            return
        self._load_audio(path)
    
    def _load_audio(self, path):
        """加载并解析音频"""
        try:
            self.lbl_info.config(text="正在加载...")
            self.root.update()
            
            self.audio = AudioSegment.from_file(path)
            self.audio_path = path
            self.duration = len(self.audio) / 1000.0
            self.sample_rate = self.audio.frame_rate
            self.start_time = 0.0
            self.end_time = self.duration
            
            # 生成波形数据（降采样）
            self._generate_waveform()
            
            # 更新 UI
            self.lbl_info.config(text=f"{os.path.basename(path)} | 时长: {self._sec_to_str(self.duration)} | {self.sample_rate}Hz")
            self.entry_start.delete(0, tk.END)
            self.entry_start.insert(0, self._sec_to_str(0))
            self.entry_end.delete(0, tk.END)
            self.entry_end.insert(0, self._sec_to_str(self.duration))
            self.progress.config(to=self.duration, state=tk.NORMAL)
            
            self._draw_waveform()
            self._update_selection_rect()
            
            messagebox.showinfo("加载成功", f"已加载: {os.path.basename(path)}\n时长: {self._sec_to_str(self.duration)}")
            
        except Exception as e:
            err_msg = str(e)
            if "winerror 2" in err_msg.lower() or "系统找不到指定的文件" in err_msg:
                if not self.has_ffmpeg:
                    messagebox.showerror(
                        "加载失败",
                        "无法加载该音频格式：未找到 ffmpeg。\n\n"
                        "请运行同目录下的 setup_ffmpeg.py 自动安装，\n"
                        "或手动下载 ffmpeg 并加入系统 PATH。\n\n"
                        "提示：WAV 格式通常不需要 ffmpeg。",
                    )
                else:
                    messagebox.showerror("加载失败", f"无法加载音频文件:\n{e}")
            else:
                messagebox.showerror("加载失败", f"无法加载音频文件:\n{e}")
            self.lbl_info.config(text="加载失败")
    
    def _generate_waveform(self, max_points=5000):
        """生成降采样后的波形数据用于显示"""
        samples = np.array(self.audio.get_array_of_samples())
        
        # 如果是立体声，取平均值
        if self.audio.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)
        
        # 归一化
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val
        
        # 降采样
        if len(samples) > max_points:
            ratio = len(samples) // max_points
            samples = samples[:max_points * ratio].reshape(-1, ratio).mean(axis=1)
        
        self.waveform_data = samples
        self.time_axis = np.linspace(0, self.duration, len(samples))
    
    def _draw_waveform(self):
        """绘制波形图"""
        self.ax.clear()
        self.ax.plot(self.time_axis, self.waveform_data, color='steelblue', linewidth=0.5)
        self.ax.set_xlim(0, self.duration)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.set_xlabel("时间 (秒)")
        self.ax.set_ylabel("振幅")
        self.ax.set_title(f"波形: {os.path.basename(self.audio_path)}")
        self.ax.grid(True, alpha=0.3)
        
        # 重新添加选区矩形和播放线
        self.select_rect = Rectangle((0, -1.1), 0, 2.2, facecolor='lightblue', alpha=0.3, edgecolor='blue', linewidth=1)
        self.ax.add_patch(self.select_rect)
        self.play_line = self.ax.axvline(x=0, color='red', linestyle='--', linewidth=1, visible=False)
        
        self._update_selection_rect()
        self.canvas.draw()
    
    def _update_selection_rect(self):
        """更新选区矩形显示"""
        if self.audio is None:
            return
        x = self.start_time
        width = self.end_time - self.start_time
        self.select_rect.set_x(x)
        self.select_rect.set_width(max(0, width))
        self.canvas.draw_idle()
    
    def _on_mouse_press(self, event):
        """鼠标按下开始拖拽"""
        if self.audio is None or event.inaxes != self.ax:
            return
        self._dragging = True
        self._drag_start_x = max(0, min(event.xdata, self.duration))
        self.start_time = self._drag_start_x
        self.end_time = self._drag_start_x
        self._update_selection_rect()
        self._sync_entries()
    
    def _on_mouse_drag(self, event):
        """鼠标拖拽中"""
        if not self._dragging or self.audio is None or event.inaxes != self.ax:
            return
        x = max(0, min(event.xdata, self.duration))
        self.start_time = min(self._drag_start_x, x)
        self.end_time = max(self._drag_start_x, x)
        self._update_selection_rect()
        self._sync_entries()
    
    def _on_mouse_release(self, event):
        """鼠标释放结束拖拽"""
        self._dragging = False
    
    def _sync_entries(self):
        """同步时间输入框"""
        self.entry_start.delete(0, tk.END)
        self.entry_start.insert(0, self._sec_to_str(self.start_time))
        self.entry_end.delete(0, tk.END)
        self.entry_end.insert(0, self._sec_to_str(self.end_time))
    
    def _apply_manual_time(self):
        """应用手动输入的时间"""
        if self.audio is None:
            messagebox.showwarning("提示", "请先打开音频文件")
            return
        try:
            start = self._str_to_sec(self.entry_start.get())
            end = self._str_to_sec(self.entry_end.get())
            
            if start is None:
                start = 0
            if end is None:
                end = self.duration
            
            start = max(0, min(start, self.duration))
            end = max(0, min(end, self.duration))
            
            if start >= end:
                messagebox.showerror("错误", "开始时间必须小于结束时间")
                return
            
            self.start_time = start
            self.end_time = end
            self._update_selection_rect()
            
        except ValueError as e:
            messagebox.showerror("错误", f"时间格式错误: {e}")
    
    def _play(self, full=False):
        """播放音频（选中片段或完整）"""
        if self.audio is None:
            messagebox.showwarning("提示", "请先打开音频文件")
            return
        
        self._stop()
        
        try:
            if full:
                segment = self.audio
                offset = 0
            else:
                start_ms = int(self.start_time * 1000)
                end_ms = int(self.end_time * 1000)
                segment = self.audio[start_ms:end_ms]
                offset = self.start_time
            
            # 导出临时 wav（pygame 兼容性最好）
            temp_path = os.path.join(self.temp_dir, "temp_play.wav")
            segment.export(temp_path, format="wav")
            self.temp_play_file = temp_path
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            self.playing = True
            self.play_offset = offset
            self.play_start_time = pygame.time.get_ticks()
            self.play_line.set_visible(True)
            
        except Exception as e:
            messagebox.showerror("播放失败", f"{e}")
    
    def _stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.playing = False
        self.play_line.set_visible(False)
        self.canvas.draw_idle()
    
    def _schedule_playback_update(self):
        """定时更新播放进度"""
        if self.playing and pygame.mixer.music.get_busy():
            elapsed = (pygame.time.get_ticks() - self.play_start_time) / 1000.0
            current = self.play_offset + elapsed
            
            self.play_line.set_xdata([current, current])
            self.play_line.set_visible(True)
            self.canvas.draw_idle()
            
            self.progress.set(current)
            self.lbl_progress.config(text=f"{self._sec_to_str(current)} / {self._sec_to_str(self.duration)}")
        elif self.playing and not pygame.mixer.music.get_busy():
            self.playing = False
            self.play_line.set_visible(False)
            self.canvas.draw_idle()
        
        self.root.after(100, self._schedule_playback_update)
    
    def _export(self):
        """导出剪辑后的音频"""
        if self.audio is None:
            messagebox.showwarning("提示", "请先打开音频文件")
            return
        
        self._apply_manual_time()
        
        default_name = os.path.splitext(os.path.basename(self.audio_path))[0] + "_clipped"
        
        path = filedialog.asksaveasfilename(
            title="导出剪辑",
            defaultextension=".mp3",
            initialfile=default_name,
            filetypes=[
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("FLAC", "*.flac"),
                ("OGG", "*.ogg"),
                ("M4A", "*.m4a"),
            ]
        )
        if not path:
            return
        
        try:
            start_ms = int(self.start_time * 1000)
            end_ms = int(self.end_time * 1000)
            clipped = self.audio[start_ms:end_ms]
            
            ext = os.path.splitext(path)[1].lower()
            fmt_map = {'.mp3': 'mp3', '.wav': 'wav', '.flac': 'flac', '.ogg': 'ogg', '.m4a': 'mp4'}
            fmt = fmt_map.get(ext, 'mp3')
            
            clipped.export(path, format=fmt)
            messagebox.showinfo("导出成功", f"已保存到:\n{path}\n时长: {self._sec_to_str(self.end_time - self.start_time)}")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"{e}")
    
    def on_closing(self):
        """关闭窗口时清理"""
        self._stop()
        pygame.mixer.quit()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AudioClipperApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
