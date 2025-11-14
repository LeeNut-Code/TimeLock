#!/usr/bin/env python3
import sys
import os
import json
import random
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QGraphicsBlurEffect
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPixmap

class TransparentWindow(QMainWindow):
    def __init__(self, break_minutes=0.5):
        super().__init__()
        try:
            self.break_minutes = float(break_minutes)
        except Exception:
            self.break_minutes = 0.5
        if self.break_minutes <= 0:
            self.break_minutes = 0.5
        self.remaining_seconds = int(self.break_minutes * 60)
        self.config = self.load_config()
        self.bg_label = None
        self.central_widget = None
        self.init_ui()
        self.init_timers()

# ---------------- 配置读取 ----------------
    def load_config(self):
        config_paths = [
            os.path.join(os.path.dirname(__file__), "..", "config.json"),
            os.path.join(os.path.dirname(__file__), "config.json"),
            os.path.join(os.path.dirname(__file__), "..", "配置", "settings_config.json"),
            os.path.join(os.path.dirname(__file__), "config", "settings_config.json"),
            os.path.join(os.getcwd(), "config.json"),
        ]
        for path in config_paths:
            path = os.path.abspath(path)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        print(f"加载配置文件： {path}")
                        return cfg
                except Exception as e:
                    print(f"读取配置 {path} 失败： {e}")
                    continue
        return {"break_ui": {"wallpaper_path": "壁纸", "opacity": 0.85, "blur_effect": True, "blur_radius": 20}}

# ---------------- 壁纸相关 ----------------
    def get_wallpaper_path(self):
        wp = self.config.get("break_ui", {}).get("wallpaper_path", "壁纸")
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        candidates = [
            wp,
            os.path.join(base_dir, wp),
            os.path.join(os.path.dirname(__file__), wp),
            os.path.abspath(wp)
        ]
        for candidate in candidates:
            if not candidate:
                continue
            if os.path.exists(candidate):
                if os.path.isdir(candidate):
                    exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif')
                    files = [os.path.join(candidate, f) for f in os.listdir(candidate)
                             if f.lower().endswith(exts)]
                    if files:
                        choice = random.choice(files)
                        print(f"从目录 {candidate} 随机选择壁纸： {choice}")
                        return choice
                elif os.path.isfile(candidate):
                    print(f"使用指定壁纸文件： {candidate}")
                    return candidate
        print(f"未找到壁纸路径（尝试过： {candidates}）")
        return None

    def set_wallpaper_background(self):
        """使用QLabel设置背景图片，应用模糊效果和透明度"""
        wp_path = self.get_wallpaper_path()
        if not wp_path:
            self.set_fallback_background()
            return
        
        pixmap = QPixmap(wp_path)
        if pixmap.isNull():
            print(f"无法加载图片： {wp_path}")
            self.set_fallback_background()
            return
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen()
        if screen is None:
            self.set_fallback_background()
            return
        
        rect = screen.availableGeometry()
        w, h = rect.width(), rect.height()
        
        # 缩放图片以适应屏幕
        scaled_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        # 创建背景标签
        if self.bg_label is None:
            self.bg_label = QLabel(self)
        
        self.bg_label.setPixmap(scaled_pixmap)
        self.bg_label.setGeometry(0, 0, w, h)
        self.bg_label.setScaledContents(True)
        
        # 从配置读取模糊效果参数
        blur_effect = self.config.get("break_ui", {}).get("blur_effect", True)
        blur_radius = self.config.get("break_ui", {}).get("blur_radius", 20)
        
        # 应用模糊效果
        if blur_effect:
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(blur_radius)
            self.bg_label.setGraphicsEffect(blur)
        
        # 应用透明度
        opacity = self.config.get("break_ui", {}).get("opacity", 0.85)
        try:
            self.setWindowOpacity(float(opacity))
        except Exception:
            pass
            
        self.bg_label.lower()  # 确保背景在底层
        self.bg_label.show()

    def set_fallback_background(self):
        """备用背景设置"""
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")

# ---------------- UI 初始化 ----------------
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)

        self.set_wallpaper_background()
        self.create_labels(self.central_widget)

# ---------------- 标签创建（按 0 版风格） ----------------
    def create_labels(self, parent):
        rect = QApplication.primaryScreen().availableGeometry()
        sw, sh = rect.width(), rect.height()

        time_px = int(sw / 31)
        date_px = int(time_px * 0.48)
        count_px = int(sw / 48)

        time_font = QFont("Segoe UI", time_px, QFont.Light)
        date_font = QFont("Segoe UI", date_px, QFont.Normal)
        count_font = QFont("Segoe UI", count_px, QFont.Normal)

        # 时间
        self.time_label = QLabel(parent)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #fff; background: transparent;")
        self.time_label.setFont(time_font)

        # 日期
        self.date_label = QLabel(parent)
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("color: #fff; background: transparent;")
        self.date_label.setFont(date_font)

        # 倒计时
        self.count_label = QLabel(parent)
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.count_label.setStyleSheet("color: #fff; background: transparent;")
        self.count_label.setFont(count_font)

        self.place_labels(sw, sh)

# ---------------- 标签定位（按 0 版风格） ----------------
    def place_labels(self, sw, sh):
        center_y = sh // 2 - 300

        # 时间
        self.time_label.setText(QDateTime.currentDateTime().toString("hh:mm"))
        self.time_label.adjustSize()
        self.time_label.move((sw - self.time_label.width()) // 2,
                             center_y - self.time_label.height() // 2)

        # 日期
        self.date_label.setText(QDateTime.currentDateTime().toString("yyyy/MM/dd"))
        self.date_label.adjustSize()
        self.date_label.move((sw - self.date_label.width()) // 2,
                             center_y + self.time_label.height() // 2 + 10)

        # 倒计时
        self.count_label.setText(f"{self.remaining_seconds // 60:02d}:{self.remaining_seconds % 60:02d}")
        self.count_label.adjustSize()
        self.count_label.move(sw - self.count_label.width() - 60,
                              sh - self.count_label.height() - 60)

# ---------------- 定时器 ----------------
    def init_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

        self.top_timer = QTimer(self)
        self.top_timer.timeout.connect(self.keep_on_top)
        self.top_timer.start(500)

    def tick(self):
        self.remaining_seconds -= 1
        self.time_label.setText(QDateTime.currentDateTime().toString("hh:mm"))
        self.date_label.setText(QDateTime.currentDateTime().toString("yyyy/MM/dd"))
        self.count_label.setText(f"{self.remaining_seconds // 60:02d}:{self.remaining_seconds % 60:02d}")
        if self.remaining_seconds <= 0:
            self.close_break()

    def keep_on_top(self):
        try:
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

# ---------------- 退出清理 ----------------
    def close_break(self):
        print("倒计时结束，关闭锁屏窗口")
        try:
            self.timer.stop()
            self.top_timer.stop()
        except Exception:
            pass
        self.close()
        QApplication.quit()

# ---------------- 事件过滤 ----------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_break()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

# ----------------主要----------------
def main():
    minutes = 0.5
    if len(sys.argv) > 1:
        try:
            minutes = float(sys.argv[1])
        except Exception:
            print("无法解析参数为数字，使用默认 0.5（30 秒）")
            minutes = 0.5

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    win = TransparentWindow(minutes)
    win.show()
    app.aboutToQuit.connect(lambda: print("应用程序即将退出"))
    result = app.exec_()
    print(f"应用程序退出，返回码： {result}")
    sys.exit(result)

if __name__ == "__main__":
    main()