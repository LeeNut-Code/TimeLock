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
        # Load configuration from config.json
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"Configuration loaded successfully from {config_path}")
            
            # Extract lock points from time_ranges end times
            self.config['lock_points'] = [range_item['end'] for range_item in self.config.get('time_ranges', [])]
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            # Fallback to default configuration
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
            # Extract lock points from fallback time_ranges
            self.config['lock_points'] = [range_item['end'] for range_item in self.config['time_ranges']]
        self.processes = {}
        
    def start_schedule_launcher(self):
        """Start schedule launcher"""
        try:
            # 根据平台设置不同的启动参数
            launch_params = [sys.executable, 'schedule_launcher.pyw']
            process_kwargs = {}
            
            # 仅在Windows平台使用CREATE_NO_WINDOW参数
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            self.processes['schedule'] = subprocess.Popen(launch_params, **process_kwargs)
            print("Schedule launcher started")
        except Exception as e:
            print(f"Failed to start schedule launcher: {e}")
    
    def start_range_monitor(self):
        """Start range monitor"""
        try:
            # 根据平台设置不同的启动参数
            launch_params = [sys.executable, 'range_monitor.pyw']
            process_kwargs = {}
            
            # 仅在Windows平台使用CREATE_NO_WINDOW参数
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            self.processes['monitor'] = subprocess.Popen(launch_params, **process_kwargs)
            print("Range monitor started")
        except Exception as e:
            print(f"Failed to start range monitor: {e}")
    
    def stop_process(self, process_name):
        """Stop specified process"""
        if process_name in self.processes:
            self.processes[process_name].terminate()
            del self.processes[process_name]
            print(f"{process_name} stopped")
    
    def cleanup(self):
        """Clean up all subprocesses"""
        for name in list(self.processes.keys()):
            self.stop_process(name)
    
    def is_current_time_in_range(self):
        """Check if current time is within any allowed time range, including overnight ranges"""
        current_time = datetime.now().time()
        time_ranges = self.config.get('time_ranges', [])
        
        # Special case: check if it's after the last range's end and before the first range's start (overnight lock period)
        if time_ranges:
            # Get the last range's end time
            last_range = time_ranges[-1]
            last_end_time = dt_time(*map(int, last_range['end'].split(':')))
            
            # Get the first range's start time
            first_range = time_ranges[0]
            first_start_time = dt_time(*map(int, first_range['start'].split(':')))
            
            # If current time is after last range's end AND before first range's start of next day
            # This handles the overnight lock period
            if current_time > last_end_time:
                # After last range's end, we should be locked
                return False
            elif current_time < first_start_time:
                # Before first range's start, check if it's from previous day's last range end
                # If we're before the first range's start, we should be locked
                return False
        
        # Normal check for current day's ranges
        for time_range in time_ranges:
            start_time = dt_time(*map(int, time_range['start'].split(':')))
            end_time = dt_time(*map(int, time_range['end'].split(':')))
            
            # Standard time range check
            if start_time <= current_time <= end_time:
                return True
        
        return False
    
    def calculate_lock_duration(self):
        """Calculate the duration until the next allowed time range starts or ends, supporting overnight locking"""
        from datetime import timedelta
        current_datetime = datetime.now()
        current_time = current_datetime.time()
        current_date = current_datetime.date()
        time_ranges = self.config.get('time_ranges', [])
        
        if not time_ranges:
            return 30.0  # Default if no time ranges
        
        # Special handling for overnight lock period
        # Get the last range's end time
        last_range = time_ranges[-1]
        last_end_time = dt_time(*map(int, last_range['end'].split(':')))
        
        # Get the first range's start time
        first_range = time_ranges[0]
        first_start_time = dt_time(*map(int, first_range['start'].split(':')))
        
        # Check if we're in the overnight lock period
        if current_time > last_end_time:
            # Calculate time until first range of next day starts
            next_day_start = datetime.combine(current_date + timedelta(days=1), first_start_time)
            minutes_to_next_start = (next_day_start - current_datetime).total_seconds() / 60
            return max(minutes_to_next_start, 0.5)
        elif current_time < first_start_time:
            # Calculate time until first range starts today
            today_start = datetime.combine(current_date, first_start_time)
            minutes_to_start = (today_start - current_datetime).total_seconds() / 60
            return max(minutes_to_start, 0.5)
        
        # Normal case: find the earliest time range that ends after current time
        min_minutes = float('inf')
        
        for time_range in time_ranges:
            # Convert string times to datetime.time objects
            start_time = dt_time(*map(int, time_range['start'].split(':')))
            end_time = dt_time(*map(int, time_range['end'].split(':')))
            
            # For ranges that are currently active or will be active today
            if start_time <= current_time <= end_time:
                # Calculate time until this range ends
                end_datetime = datetime.combine(current_date, end_time)
                minutes_diff = (end_datetime - current_datetime).total_seconds() / 60
                if minutes_diff < min_minutes:
                    min_minutes = minutes_diff
            elif start_time > current_time:
                # Calculate time until this range starts
                start_datetime = datetime.combine(current_date, start_time)
                minutes_diff = (start_datetime - current_datetime).total_seconds() / 60
                if minutes_diff < min_minutes:
                    min_minutes = minutes_diff
        
        # If no suitable range found, default to time until first range of next day
        if min_minutes == float('inf'):
            next_day_start = datetime.combine(current_date + timedelta(days=1), first_start_time)
            min_minutes = (next_day_start - current_datetime).total_seconds() / 60
        
        return max(min_minutes, 0.5)
    
    def start_lock(self):
        """Start lock process immediately"""
        try:
            # 先检查平台，然后根据平台执行相应的锁定命令
            if platform.system() == 'Windows':
                # Windows平台直接调用锁定命令
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], shell=True, check=True)
                print("System locked on Windows platform")
            else:
                # Linux平台：计算锁定时长并调用lock_gnome.py
                try:
                    # 计算锁定时间差值（分钟）
                    lock_duration = self.calculate_lock_duration()
                    print(f"Calculated lock duration: {lock_duration:.2f} minutes")
                    
                    # 直接运行lock_gnome.py并传递倒计时参数
                    subprocess.run([sys.executable, 'lock_gnome.py', str(lock_duration)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print("System locked using lock_gnome.py with countdown")
                except Exception as e:
                    print(f"Failed to run lock_gnome.py: {e}")
                    
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
                            print(f"System locked using command: {' '.join(cmd)}")
                            locked = True
                            break
                        except subprocess.CalledProcessError:
                            continue
        except Exception as e:
            print(f"Failed to lock system immediately: {e}")

def main():
    controller = MainController()
    
    # Register exit handler
    import atexit
    atexit.register(controller.cleanup)
    
    try:
        # Check if current time is outside allowed ranges
        if not controller.is_current_time_in_range():
            print("Current time is outside allowed ranges. Starting lock process immediately...")
            # 立即启动锁定进程
            controller.start_lock()
            
        # Start necessary components
        controller.start_schedule_launcher()
        controller.start_range_monitor()
        
        print("Smart lock system started. Press Ctrl+C to exit.")
        
        # Main loop to keep running
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()