# 定点锁定息屏
import ctypes
import time
import sys
import threading

class PointLocker:
    def __init__(self):
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
    
    def monitor_lock(self):
        """持续监控锁定状态，如果解锁则立即重新锁定"""
        print("开始监控锁定状态...")
        consecutive_unlocked_count = 0
        
        while self.should_monitor:
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
