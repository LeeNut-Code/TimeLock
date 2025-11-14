# -*- coding: utf-8 -*-
import sys
import os
import time
import json
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, 
                            QVBoxLayout, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont

class FadeLabel(QLabel):
    """支持淡入淡出效果的标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._opacity = 1.0
        
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
        
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setStyleSheet(f"color: rgba(255, 255, 255, {int(value * 255)});")

class ModernReminderWindow(QMainWindow):
    def __init__(self, lock_time_str="", reminder_type="lock", duration=60):
        super().__init__()
        self.lock_time_str = lock_time_str
        self.reminder_type = reminder_type  # "lock" 或 "shutdown"
        self.duration = duration  # 显示持续时间（秒）
        self.remaining_seconds = duration
        self.is_closing = False  # 标记是否正在关闭
        
        self.setup_ui()
        self.setup_animations()
        self.setup_timers()
        
    def setup_ui(self):
        """设置用户界面"""
        # 窗口基本属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool |  # 不在任务栏显示
            Qt.WindowDoesNotAcceptFocus  # 不获取焦点
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 半透明背景
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示但不激活
        
        # 窗口大小和位置
        self.setFixedSize(350, 150)
        self.move_to_bottom_right()
        
        # 创建中央部件
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # 设置样式
        self.setup_styles()
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # 创建标题
        self.title_label = FadeLabel()
        title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # 创建信息标签
        self.info_label = FadeLabel()
        info_font = QFont("Microsoft YaHei", 11)
        self.info_label.setFont(info_font)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        
        # 创建倒计时标签
        self.countdown_label = FadeLabel()
        countdown_font = QFont("Microsoft YaHei", 10)
        self.countdown_label.setFont(countdown_font)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(self.duration)
        self.progress_bar.setValue(self.duration)
        
        # 添加到布局
        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.progress_bar)
        
        # 更新内容
        self.update_content()
        
    def setup_styles(self):
        """设置样式表"""
        style = """
        #centralWidget {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #2c3e50, 
                stop: 1 #34495e
            );
            border-radius: 12px;
            border: 1px solid #1a252f;
        }
        
        QLabel {
            color: white;
        }
        
        QProgressBar {
            border: none;
            background: #1a252f;
            border-radius: 3px;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #e74c3c, 
                stop: 1 #c0392b
            );
            border-radius: 3px;
        }
        """
        self.setStyleSheet(style)
        
    def setup_animations(self):
        """设置动画效果"""
        # 窗口淡入动画
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(0.95)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def setup_timers(self):
        """设置定时器"""
        # 倒计时定时器
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 每秒更新
        
    def move_to_bottom_right(self):
        """移动窗口到右下角"""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_width = self.width()
        window_height = self.height()
        
        x = screen_geometry.width() - window_width - 20  # 右边距20px
        y = screen_geometry.height() - window_height - 60  # 下边距60px（避免遮挡任务栏）
        
        self.move(x, y)
        
    def update_content(self):
        """更新窗口内容"""
        if self.reminder_type == "lock":
            self.title_label.setText("🔒 锁定提醒")
            self.info_label.setText(f"系统将在 {self.lock_time_str} 自动锁定")
        else:  # shutdown
            self.title_label.setText("<span style='color: red;'>●</span> 关机提醒")
            self.info_label.setText(f"系统将在 {self.lock_time_str} 自动关机")
            
        self.update_countdown_display()
        
    def update_countdown(self):
        """更新倒计时"""
        self.remaining_seconds -= 1
        self.update_countdown_display()
        
        # 更新进度条
        self.progress_bar.setValue(self.remaining_seconds)
        
        # 如果倒计时结束，直接关闭窗口
        if self.remaining_seconds <= 0 and not self.is_closing:
            self.force_close()
            
    def update_countdown_display(self):
        """更新倒计时显示"""
        if self.remaining_seconds > 0:
            self.countdown_label.setText(f"{self.remaining_seconds}秒后自动关闭")
        else:
            self.countdown_label.setText("正在关闭...")
            
    def showEvent(self, event):
        """显示事件 - 启动动画"""
        super().showEvent(event)
        self.fade_in_animation.start()
        
    def force_close(self):
        """强制立即关闭窗口并退出应用"""
        if self.is_closing:
            return
            
        self.is_closing = True
        
        # 停止定时器
        self.countdown_timer.stop()
        
        # 直接关闭窗口
        self.close()
        
        # 退出应用
        QApplication.quit()
        
    def mousePressEvent(self, event):
        """鼠标点击事件 - 禁止拖动"""
        # 不调用父类方法，完全禁止拖动
        pass
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 禁止拖动"""
        # 不调用父类方法，完全禁止拖动
        pass

def main():
    # 获取命令行参数
    if len(sys.argv) > 1:
        lock_time = sys.argv[1]
        reminder_type = "lock"
    else:
        lock_time = datetime.now().strftime("%H:%M")
        reminder_type = "lock"
    
    # 如果是关机提醒，第二个参数为 "shutdown"
    if len(sys.argv) > 2 and sys.argv[2] == "shutdown":
        reminder_type = "shutdown"
    
    # 读取配置文件获取提醒时长
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    duration_seconds = 60  # 默认60秒
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 从配置中获取show_before_minutes并转换为秒数
            if 'reminder' in config and 'show_before_minutes' in config['reminder']:
                show_before_minutes = config['reminder']['show_before_minutes']
                duration_seconds = show_before_minutes * 60
                print(f"Loaded reminder duration: {show_before_minutes} minutes ({duration_seconds} seconds)")
    except Exception as e:
        print(f"Failed to load configuration: {e}, using default duration of 60 seconds")
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # 创建并显示窗口
    window = ModernReminderWindow(lock_time, reminder_type, duration=duration_seconds)
    window.show()
    
    # 运行应用
    result = app.exec_()
    
    # 确保应用完全退出
    sys.exit(result)

if __name__ == "__main__":
    main()