'''[#!/usr/bin/env python3]'''
# 强制关机
import os
import time
import subprocess
import ctypes
import sys
import platform

class ForceShutdown:
    def __init__(self):
        pass
    
    def immediate_shutdown(self):
        """立即强制关机，支持Windows和Linux平台"""
        current_os = platform.system()
        
        try:
            if current_os == 'Windows':
                # Windows关机方法
                subprocess.run([
                    "shutdown", "/s", "/f", "/t", "0"
                ], check=True, timeout=5)
            else:  # Linux
                # Linux关机方法
                try:
                    # 方法1: 使用shutdown命令
                    subprocess.run([
                        "shutdown", "-h", "now"
                    ], check=True, timeout=5)
                except Exception:
                    # 方法2: 使用systemctl poweroff
                    subprocess.run([
                        "systemctl", "poweroff"
                    ], check=True, timeout=5)
                    
        except subprocess.TimeoutExpired:
            # 如果超时，尝试备用方法
            self.alternative_shutdown()
        except Exception as e:
            print(f"关机命令失败: {e}")
            self.alternative_shutdown()
    
    def alternative_shutdown(self):
        """备用关机方法，根据平台选择不同策略"""
        current_os = platform.system()
        
        try:
            if current_os == 'Windows':
                # Windows备用关机方法
                try:
                    # 方法2: 使用Windows API强制退出Windows
                    ctypes.windll.ntdll.NtShutdownSystem(0)  # 0 = 关机
                except:
                    try:
                        # 方法3: 直接调用ExitWindowsEx
                        ctypes.windll.user32.ExitWindowsEx(0x00000008, 0)  # EWX_SHUTDOWN
                    except Exception as e:
                        print(f"Windows备用关机方法失败: {e}")
            else:  # Linux
                # Linux备用关机方法
                try:
                    # 尝试使用init 0
                    subprocess.run(["init", "0"], check=True, timeout=5)
                except Exception as e:
                    print(f"Linux备用关机方法失败: {e}")
        except Exception as e:
            print(f"备用关机方法失败: {e}")
    
    def execute_shutdown(self):
        """执行关机"""
        print("执行强制关机...")
        
        # 立即执行关机，不提供任何延迟
        self.immediate_shutdown()
        
        # 如果程序还在运行（说明关机失败），等待1秒后强制退出
        time.sleep(1)
        sys.exit(1)

def main():
    shutdown = ForceShutdown()
    shutdown.execute_shutdown()

if __name__ == "__main__":
    main()