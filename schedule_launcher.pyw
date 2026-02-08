import os
import sys
import time
import threading
import subprocess
import json
import platform
from datetime import datetime, time as dt_time, timedelta

class ScheduleLauncher:
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
        self.timers = []
        self.current_processes = {}
    
    def parse_time(self, time_str):
        """解析时间字符串"""
        return datetime.strptime(time_str, "%H:%M").time()
    
    def should_start_reminder(self, lock_time):
        """检查是否应该启动提醒"""
        reminder_minutes = self.config['reminder']['show_before_minutes']
        reminder_time = (datetime.combine(datetime.today(), lock_time) - 
                        timedelta(minutes=reminder_minutes)).time()
        current_time = datetime.now().time()
        return current_time <= reminder_time
    
    def schedule_lock_point(self, lock_time_str):
        """安排锁定点任务"""
        lock_time = self.parse_time(lock_time_str)
        current_time = datetime.now().time()
        
        # 计算延迟秒数
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), lock_time)
        
        if current_time < lock_time:
            delay_seconds = (target_datetime - now).total_seconds()
            
            # 安排提醒
            if self.should_start_reminder(lock_time):
                reminder_delay = delay_seconds - (self.config['reminder']['show_before_minutes'] * 60)
                if reminder_delay > 0:
                    timer = threading.Timer(reminder_delay, self.start_reminder, [lock_time_str])
                    timer.start()
                    self.timers.append(timer)
                    print(f"提醒已安排: {lock_time_str}, 延迟: {reminder_delay} 秒")
            
            # 安排锁定
            timer = threading.Timer(delay_seconds, self.start_point_locker)
            timer.start()
            self.timers.append(timer)
            print(f"锁定已安排: {lock_time_str}, 延迟: {delay_seconds} 秒")
        else:
            print(f"锁定时间 {lock_time_str} 已过，跳过")
    
    def schedule_shutdown(self):
        """安排关机任务"""
        shutdown_time = self.parse_time(self.config['shutdown_time'])
        current_time = datetime.now().time()
        
        if current_time < shutdown_time:
            now = datetime.now()
            target_datetime = datetime.combine(now.date(), shutdown_time)
            delay_seconds = (target_datetime - now).total_seconds()
            
            # 安排关机提醒
            reminder_delay = delay_seconds - (self.config['reminder']['show_before_minutes'] * 60)
            if reminder_delay > 0:
                timer = threading.Timer(reminder_delay, self.start_shutdown_reminder)
                timer.start()
                self.timers.append(timer)
                print(f"关机提醒已安排: {self.config['shutdown_time']}, 延迟: {reminder_delay} 秒")
            
            # 安排关机
            timer = threading.Timer(delay_seconds, self.start_shutdown)
            timer.start()
            self.timers.append(timer)
            print(f"关机已安排: {self.config['shutdown_time']}, 延迟: {delay_seconds} 秒")
        else:
            print(f"关机时间 {self.config['shutdown_time']} 已过，跳过")
    
    def start_reminder(self, lock_time_str):
        """启动锁定提醒窗口"""
        try:
            process_kwargs = {}
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, 'reminder.pyw', lock_time_str],
                **process_kwargs
            )
            print(f"锁定提醒已启动: {lock_time_str}")
        except Exception as e:
            print(f"启动锁定提醒失败: {e}")
    
    def start_shutdown_reminder(self):
        """启动关机提醒窗口"""
        try:
            process_kwargs = {}
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, 'reminder.pyw', self.config['shutdown_time'], 'shutdown'],
                **process_kwargs
            )
            print(f"关机提醒已启动: {self.config['shutdown_time']}")
        except Exception as e:
            print(f"启动关机提醒失败: {e}")
    
    def start_point_locker(self):
        """启动点锁定器"""
        try:
            current_os = platform.system()
            
            # 根据平台选择锁定程序
            if current_os == 'Windows':
                lock_script = 'point_locker.pyw'
            else:  # Linux
                lock_script = 'lock_gnome.py'
            
            process_kwargs = {}
            if current_os == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            print(f"为 {current_os} 平台使用 {lock_script}")
            
            self.current_processes['locker'] = subprocess.Popen(
                [sys.executable, lock_script],
                **process_kwargs
            )
            print("锁定已执行")
        except Exception as e:
            print(f"启动锁定失败: {e}")
    
    def start_shutdown(self):
        """启动强制关机"""
        try:
            process_kwargs = {}
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, 'shutdown_force.pyw'],
                **process_kwargs
            )
            print("强制关机已执行")
        except Exception as e:
            print(f"启动强制关机失败: {e}")
    
    def setup_schedules(self):
        """设置所有计划任务"""
        print("正在设置计划任务...")
        
        # 安排所有锁定点
        for lock_time in self.config['lock_points']:
            self.schedule_lock_point(lock_time)
        
        # 安排关机
        self.schedule_shutdown()
        
        # 安排明天的任务
        self.schedule_tomorrow()
        
        print("所有计划任务已设置")
    
    def schedule_tomorrow(self):
        """安排明天的任务"""
        now = datetime.now()
        tomorrow = now.date() + timedelta(days=1)
        first_time = self.parse_time(self.config['lock_points'][0])
        target_datetime = datetime.combine(tomorrow, first_time)
        delay_seconds = (target_datetime - now).total_seconds()
        
        timer = threading.Timer(delay_seconds, self.restart_scheduler)
        timer.start()
        self.timers.append(timer)
        print(f"调度器重启已安排到明天，延迟: {delay_seconds} 秒")
    
    def restart_scheduler(self):
        """重启调度器"""
        print("正在重启调度器...")
        self.cleanup()
        self.setup_schedules()
    
    def cleanup(self):
        """清理所有定时器"""
        print("正在清理定时器...")
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()
        
        # 终止当前进程
        for name, process in self.current_processes.items():
            try:
                process.terminate()
            except:
                pass
        self.current_processes.clear()

def main():
    launcher = ScheduleLauncher()
    
    # 注册退出处理程序
    import atexit
    atexit.register(launcher.cleanup)
    
    try:
        launcher.setup_schedules()
        print("计划启动器准备就绪")
        
        # 保持运行
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print("\n计划启动器退出")
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    main()