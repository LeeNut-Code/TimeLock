# 定点锁定息屏
import ctypes
import time
import sys

class PointLocker:
    def __init__(self):
        pass
    
    def lock_screen(self):
        """锁定屏幕 - Windows 11专用"""
        try:
            # 方法1: 使用Windows API锁定
            ctypes.windll.user32.LockWorkStation()
            print("屏幕已锁定")
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
    
    def execute_lock(self):
        """执行锁定和息屏"""
        print("执行定点锁定和息屏...")
        
        # 先锁定屏幕
        self.lock_screen()
        
        # 等待1秒确保锁定完成
        time.sleep(1)
        
        # 然后关闭显示器
        self.turn_off_display()
        
        # 任务完成，退出程序
        sys.exit(0)

def main():
    locker = PointLocker()
    locker.execute_lock()

if __name__ == "__main__":
    main()
