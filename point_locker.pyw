# 定点锁定息屏
import ctypes
import time
import sys
import threading
import os
import json
from datetime import datetime, time as dt_time

class PointLocker:
    def __init__(self):
        # 从config.json加载配置
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"配置已成功从 {config_path} 加载")
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 回退到默认配置
            self.config = {
                'time_ranges': [
                    {'start': '08:30', 'end': '09:55'},
                    {'start': '10:15', 'end': '11:45'},
                    {'start': '13:10', 'end': '15:55'},
                    {'start': '16:15', 'end': '17:30'},
                    {'start': '18:25', 'end': '21:10'}
                ]
            }
        self.should_monitor = True
        self.lock_count = 0
    
    def lock_screen(self):
        """锁定屏幕 - Windows 11专用"""
        try:
            # 方法1: 使用Windows API锁定
            ctypes.windll.user32.LockWorkStation()
            print(f"屏幕已锁定 (第 {self.lock_count + 1} 次)")
            self.lock_count += 1
        except Exception as e:
            print(f"锁定失败: {e}")
    
    def turn_off_display(self):
        """关闭显示器"""
        try:
            # 发送显示器关闭命令
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
            print("显示器已关闭")
        except Exception as e:
            print(f"关闭显示器失败: {e}")
    
    def is_system_locked(self):
        """检查系统是否被锁定 - 使用简化的检测方法"""
        try:
            # 方法1: 检查前景窗口
            try:
                foreground_window = ctypes.windll.user32.GetForegroundWindow()
                if foreground_window == 0:
                    return True
            except:
                pass
            
            # 方法2: 尝试获取窗口类名
            try:
                GetClassName = ctypes.windll.user32.GetClassNameW
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd != 0:
                    class_name = ctypes.create_unicode_buffer(256)
                    GetClassName(hwnd, class_name, 256)
                    class_name_str = class_name.value
                    
                    # 检查锁定界面的特征类名
                    if 'Lock' in class_name_str or 'Credential' in class_name_str or 'Auth' in class_name_str:
                        return True
            except:
                pass
            
            # 方法3: 检查是否可以获取窗口标题
            try:
                GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd != 0:
                    length = GetWindowTextLength(hwnd)
                    if length == 0:
                        return True
            except:
                pass
            
            # 方法4: 检查会话状态
            try:
                session_id = ctypes.windll.kernel32.WTSGetActiveConsoleSessionId()
                if session_id == 0xFFFFFFFF:
                    return True
            except:
                pass
            
            # 如果以上方法都没有检测到锁定，说明系统已解锁
            return False
        except Exception as e:
            # 出错时假设已解锁，以便重新锁定
            return False
    
    def is_time_in_ranges(self):
        """检查当前时间是否在允许范围内"""
        current_time = datetime.now().time()
        time_ranges = self.config.get('time_ranges', [])
        
        if not time_ranges:
            return False
        
        # 正常检查当天的范围
        for range_config in time_ranges:
            start_time = datetime.strptime(range_config['start'], "%H:%M").time()
            end_time = datetime.strptime(range_config['end'], "%H:%M").time()
            
            # 处理跨午夜的时间范围
            if start_time > end_time:
                # 跨午夜范围（如23:53-00:59）
                if current_time >= start_time or current_time <= end_time:
                    return True
            else:
                # 正常范围
                if start_time <= current_time <= end_time:
                    return True
        
        return False
    
    def monitor_lock(self):
        """持续监控锁定状态，如果解锁则立即重新锁定"""
        print("开始监控锁定状态...")
        consecutive_unlocked_count = 0
        
        while self.should_monitor:
            # 检查当前时间是否在允许范围内
            if self.is_time_in_ranges():
                print("当前时间在允许范围内，停止监控锁定状态")
                self.should_monitor = False
                break
            
            is_locked = self.is_system_locked()
            
            # 每10次检查输出一次状态（避免过多日志）
            if consecutive_unlocked_count % 10 == 0 and consecutive_unlocked_count > 0:
                print(f"检测到解锁，计数: {consecutive_unlocked_count}")
            
            # 如果检测到解锁，增加计数
            if not is_locked:
                consecutive_unlocked_count += 1
            else:
                consecutive_unlocked_count = 0
            
            # 如果连续多次检测到解锁，立即重新锁定
            if consecutive_unlocked_count >= 2:
                print(f"重新锁定系统 (第{self.lock_count + 1}次)")
                self.lock_screen()
                time.sleep(2)
                self.turn_off_display()
                consecutive_unlocked_count = 0
            
            # 每秒检查一次锁定状态
            time.sleep(1)
    
    def execute_lock(self):
        """执行锁定和息屏，然后持续监控"""
        print("执行定点锁定和息屏...")
        
        # 检查当前时间是否在允许范围内
        if self.is_time_in_ranges():
            print("当前时间在允许范围内，不需要锁定")
            sys.exit(0)
        
        # 先锁定屏幕
        self.lock_screen()
        
        # 等待1秒确保锁定完成
        time.sleep(1)
        
        # 然后关闭显示器
        self.turn_off_display()
        
        # 启动监控线程，持续检查锁定状态
        monitor_thread = threading.Thread(target=self.monitor_lock, daemon=True)
        monitor_thread.start()
        
        # 主线程保持运行，直到程序被终止
        try:
            while True:
                # 检查当前时间是否在允许范围内
                if self.is_time_in_ranges():
                    print("当前时间在允许范围内，退出监控")
                    self.should_monitor = False
                    sys.exit(0)
                time.sleep(1)
        except KeyboardInterrupt:
            print("收到终止信号，停止监控")
            self.should_monitor = False
            sys.exit(0)

def main():
    locker = PointLocker()
    locker.execute_lock()

if __name__ == "__main__":
    main()
