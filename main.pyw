'''[#!/usr/bin/env python3]'''
import os
import sys
import time
import threading
import subprocess
import json
import platform
from datetime import datetime, time as dt_time

class MainController:
    def __init__(self):
        # 从config.json加载配置
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"配置已成功从 {config_path} 加载")
            
            # 从time_ranges结束时间提取锁定点
            self.config['lock_points'] = [range_item['end'] for range_item in self.config.get('time_ranges', [])]
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
                ],
                'shutdown_time': '21:10',
                'reminder': {'show_before_minutes': 1}
            }
            # 从回退的time_ranges中提取锁定点
            self.config['lock_points'] = [range_item['end'] for range_item in self.config['time_ranges']]
        self.processes = {}
        
    def start_schedule_launcher(self):
        """启动计划启动器"""
        try:
            # 根据平台设置不同的启动参数
            launch_params = [sys.executable, 'schedule_launcher.pyw']
            process_kwargs = {}
            
            # 仅在Windows平台使用CREATE_NO_WINDOW参数
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            self.processes['schedule'] = subprocess.Popen(launch_params, **process_kwargs)
            print("计划启动器已启动")
        except Exception as e:
            print(f"启动计划启动器失败: {e}")
    
    def start_range_monitor(self):
        """启动范围监控器"""
        try:
            # 根据平台设置不同的启动参数
            launch_params = [sys.executable, 'range_monitor.pyw']
            process_kwargs = {}
            
            # 仅在Windows平台使用CREATE_NO_WINDOW参数
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            self.processes['monitor'] = subprocess.Popen(launch_params, **process_kwargs)
            print("范围监控器已启动")
        except Exception as e:
            print(f"启动范围监控器失败: {e}")
    
    def stop_process(self, process_name):
        """停止指定进程"""
        if process_name in self.processes:
            self.processes[process_name].terminate()
            del self.processes[process_name]
            print(f"{process_name} 已停止")
    
    def cleanup(self):
        """清理所有子进程"""
        for name in list(self.processes.keys()):
            self.stop_process(name)
    
    def is_current_time_in_range(self):
        """检查当前时间是否在任何允许的时间范围内，包括跨夜范围"""
        current_time = datetime.now().time()
        time_ranges = self.config.get('time_ranges', [])
        
        # 特殊情况：检查是否在最后一个范围结束后且在第一个范围开始前（跨夜锁定期）
        if time_ranges:
            # 获取最后一个范围的结束时间
            last_range = time_ranges[-1]
            last_end_time = dt_time(*map(int, last_range['end'].split(':')))
            
            # 获取第一个范围的开始时间
            first_range = time_ranges[0]
            first_start_time = dt_time(*map(int, first_range['start'].split(':')))
            
            # 如果当前时间在最后一个范围结束后且在下一天第一个范围开始前
            # 这处理了跨夜锁定期
            if current_time > last_end_time:
                # 在最后一个范围结束后，我们应该被锁定
                return False
            elif current_time < first_start_time:
                # 在第一个范围开始前，检查是否来自前一天最后范围结束后
                # 如果我们在第一个范围开始前，我们应该被锁定
                return False
        
        # 正常检查当天的范围
        for time_range in time_ranges:
            start_time = dt_time(*map(int, time_range['start'].split(':')))
            end_time = dt_time(*map(int, time_range['end'].split(':')))
            
            # 标准时间范围检查
            if start_time <= current_time <= end_time:
                return True
        
        return False
    
    def calculate_lock_duration(self):
        """计算直到下一个允许时间范围开始或结束的持续时间，支持跨夜锁定"""
        from datetime import timedelta
        current_datetime = datetime.now()
        current_time = current_datetime.time()
        current_date = current_datetime.date()
        time_ranges = self.config.get('time_ranges', [])
        
        if not time_ranges:
            return 30.0  # 如果没有时间范围则返回默认值
        
        # 跨夜锁定期的特殊处理
        # 获取最后一个范围的结束时间
        last_range = time_ranges[-1]
        last_end_time = dt_time(*map(int, last_range['end'].split(':')))
        
        # 获取第一个范围的开始时间
        first_range = time_ranges[0]
        first_start_time = dt_time(*map(int, first_range['start'].split(':')))
        
        # 检查我们是否在跨夜锁定期内
        if current_time > last_end_time:
            # 计算直到下一天第一个范围开始的时间
            next_day_start = datetime.combine(current_date + timedelta(days=1), first_start_time)
            minutes_to_next_start = (next_day_start - current_datetime).total_seconds() / 60
            return max(minutes_to_next_start, 0.5)
        elif current_time < first_start_time:
            # 计算直到今天第一个范围开始的时间
            today_start = datetime.combine(current_date, first_start_time)
            minutes_to_start = (today_start - current_datetime).total_seconds() / 60
            return max(minutes_to_start, 0.5)
        
        # 正常情况：找到最早在当前时间之后结束的时间范围
        min_minutes = float('inf')
        
        for time_range in time_ranges:
            # 将字符串时间转换为datetime.time对象
            start_time = dt_time(*map(int, time_range['start'].split(':')))
            end_time = dt_time(*map(int, time_range['end'].split(':')))
            
            # 对于当前活跃或今天将活跃的范围
            if start_time <= current_time <= end_time:
                # 计算直到此范围结束的时间
                end_datetime = datetime.combine(current_date, end_time)
                minutes_diff = (end_datetime - current_datetime).total_seconds() / 60
                if minutes_diff < min_minutes:
                    min_minutes = minutes_diff
            elif start_time > current_time:
                # 计算直到此范围开始的时间
                start_datetime = datetime.combine(current_date, start_time)
                minutes_diff = (start_datetime - current_datetime).total_seconds() / 60
                if minutes_diff < min_minutes:
                    min_minutes = minutes_diff
        
        # 如果没有找到合适的范围，默认为直到下一天第一个范围的时间
        if min_minutes == float('inf'):
            next_day_start = datetime.combine(current_date + timedelta(days=1), first_start_time)
            min_minutes = (next_day_start - current_datetime).total_seconds() / 60
        
        return max(min_minutes, 0.5)
    
    def start_lock(self):
        """立即启动锁定进程"""
        try:
            # 先检查平台，然后根据平台执行相应的锁定命令
            if platform.system() == 'Windows':
                # Windows平台直接调用锁定命令
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], shell=True, check=True)
                print("Windows平台系统已锁定")
            else:
                # Linux平台：优先尝试运行fullscreen_break.pyw
                try:
                    # 计算锁定时间差值（分钟）
                    lock_duration = self.calculate_lock_duration()
                    print(f"计算的锁定持续时间: {lock_duration:.2f} 分钟")
                    
                    # 优先运行fullscreen_break.pyw
                    result = subprocess.run([sys.executable, 'fullscreen_break.pyw', str(lock_duration)],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                    
                    # 如果fullscreen_break.pyw成功运行并退出（返回码为0），则不需要执行后续锁定
                    if result.returncode == 0:
                        print("使用fullscreen_break.pyw锁定系统")
                        return
                    else:
                        print(f"fullscreen_break.pyw以代码{result.returncode}退出，回退到lock_gnome.py")
                        
                except subprocess.TimeoutExpired:
                    print("fullscreen_break.pyw超时，回退到lock_gnome.py")
                except FileNotFoundError:
                    print("找不到fullscreen_break.pyw，回退到lock_gnome.py")
                except Exception as e:
                    print(f"运行fullscreen_break.pyw失败: {e}，回退到lock_gnome.py")
             
                # 如果fullscreen_break.pyw失败，则尝试运行lock_gnome.py
                try:
                    # 计算锁定时间差值（分钟）
                    lock_duration = self.calculate_lock_duration()
                    print(f"计算的锁定持续时间: {lock_duration:.2f} 分钟")
                    
                    # 直接运行lock_gnome.py并传递倒计时参数
                    subprocess.run([sys.executable, 'lock_gnome.py', str(lock_duration)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print("使用带倒计时的lock_gnome.py锁定系统")
                except Exception as e:
                    print(f"运行lock_gnome.py失败: {e}")
                    
                    # 作为备用，尝试标准锁定命令
                    lock_commands = [
                        ['xdg-screensaver', 'lock'],
                        ['gnome-screensaver-command', '-l'],
                        ['cinnamon-screensaver-command', '-l']
                    ]
                    
                    locked = False
                    for cmd in lock_commands:
                        try:
                            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            print(f"使用命令锁定系统: {' '.join(cmd)}")
                            locked = True
                            break
                        except subprocess.CalledProcessError:
                            continue
                        
        except Exception as e:
            print(f"立即锁定系统失败: {e}")

def main():
    controller = MainController()
    
    # 注册退出处理程序
    import atexit
    atexit.register(controller.cleanup)
    
    try:
        # 检查当前时间是否在允许范围外
        if not controller.is_current_time_in_range():
            print("当前时间在允许范围外。立即启动锁定进程...")
            # 立即启动锁定进程
            controller.start_lock()
            
        # 启动必要组件
        controller.start_schedule_launcher()
        controller.start_range_monitor()
        
        print("智能锁定系统已启动。按Ctrl+C退出。")
        
        # 主循环保持运行
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print("\n正在退出...")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()