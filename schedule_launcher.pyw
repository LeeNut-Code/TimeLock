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
        self.timers = []
        self.current_processes = {}
    
    def parse_time(self, time_str):
        """Parse time string"""
        return datetime.strptime(time_str, "%H:%M").time()
    
    def should_start_reminder(self, lock_time):
        """Check if reminder should be started"""
        reminder_minutes = self.config['reminder']['show_before_minutes']
        reminder_time = (datetime.combine(datetime.today(), lock_time) - 
                        timedelta(minutes=reminder_minutes)).time()
        current_time = datetime.now().time()
        return current_time <= reminder_time
    
    def schedule_lock_point(self, lock_time_str):
        """Schedule lock point task"""
        lock_time = self.parse_time(lock_time_str)
        current_time = datetime.now().time()
        
        # Calculate delay seconds
        now = datetime.now()
        target_datetime = datetime.combine(now.date(), lock_time)
        
        if current_time < lock_time:
            delay_seconds = (target_datetime - now).total_seconds()
            
            # Schedule reminder
            if self.should_start_reminder(lock_time):
                reminder_delay = delay_seconds - (self.config['reminder']['show_before_minutes'] * 60)
                if reminder_delay > 0:
                    timer = threading.Timer(reminder_delay, self.start_reminder, [lock_time_str])
                    timer.start()
                    self.timers.append(timer)
                    print(f"Reminder scheduled: {lock_time_str}, delay: {reminder_delay} seconds")
            
            # Schedule lock
            timer = threading.Timer(delay_seconds, self.start_point_locker)
            timer.start()
            self.timers.append(timer)
            print(f"Lock scheduled: {lock_time_str}, delay: {delay_seconds} seconds")
        else:
            print(f"Lock time {lock_time_str} has passed, skipping")
    
    def schedule_shutdown(self):
        """Schedule shutdown task"""
        shutdown_time = self.parse_time(self.config['shutdown_time'])
        current_time = datetime.now().time()
        
        if current_time < shutdown_time:
            now = datetime.now()
            target_datetime = datetime.combine(now.date(), shutdown_time)
            delay_seconds = (target_datetime - now).total_seconds()
            
            # Schedule shutdown reminder
            reminder_delay = delay_seconds - (self.config['reminder']['show_before_minutes'] * 60)
            if reminder_delay > 0:
                timer = threading.Timer(reminder_delay, self.start_shutdown_reminder)
                timer.start()
                self.timers.append(timer)
                print(f"Shutdown reminder scheduled: {self.config['shutdown_time']}, delay: {reminder_delay} seconds")
            
            # Schedule shutdown
            timer = threading.Timer(delay_seconds, self.start_shutdown)
            timer.start()
            self.timers.append(timer)
            print(f"Shutdown scheduled: {self.config['shutdown_time']}, delay: {delay_seconds} seconds")
        else:
            print(f"Shutdown time {self.config['shutdown_time']} has passed, skipping")
    
    def start_reminder(self, lock_time_str):
        """Start lock reminder window"""
        try:
            process_kwargs = {}
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, 'reminder.pyw', lock_time_str],
                **process_kwargs
            )
            print(f"Lock reminder started: {lock_time_str}")
        except Exception as e:
            print(f"Failed to start lock reminder: {e}")
    
    def start_shutdown_reminder(self):
        """Start shutdown reminder window"""
        try:
            process_kwargs = {}
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, 'reminder.pyw', self.config['shutdown_time'], 'shutdown'],
                **process_kwargs
            )
            print(f"Shutdown reminder started: {self.config['shutdown_time']}")
        except Exception as e:
            print(f"Failed to start shutdown reminder: {e}")
    
    def start_point_locker(self):
        """Start point locker"""
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
                
            print(f"Using {lock_script} for {current_os} platform")
            
            self.current_processes['locker'] = subprocess.Popen(
                [sys.executable, lock_script],
                **process_kwargs
            )
            print("Lock executed")
        except Exception as e:
            print(f"Failed to start lock: {e}")
    
    def start_shutdown(self):
        """Start forced shutdown"""
        try:
            process_kwargs = {}
            if platform.system() == 'Windows':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
            subprocess.Popen(
                [sys.executable, 'shutdown_force.pyw'],
                **process_kwargs
            )
            print("Forced shutdown executed")
        except Exception as e:
            print(f"Failed to start forced shutdown: {e}")
    
    def setup_schedules(self):
        """Set up all scheduled tasks"""
        print("Setting up scheduled tasks...")
        
        # Schedule all lock points
        for lock_time in self.config['lock_points']:
            self.schedule_lock_point(lock_time)
        
        # Schedule shutdown
        self.schedule_shutdown()
        
        # Schedule tomorrow's tasks
        self.schedule_tomorrow()
        
        print("All scheduled tasks set up")
    
    def schedule_tomorrow(self):
        """Schedule tomorrow's tasks"""
        now = datetime.now()
        tomorrow = now.date() + timedelta(days=1)
        first_time = self.parse_time(self.config['lock_points'][0])
        target_datetime = datetime.combine(tomorrow, first_time)
        delay_seconds = (target_datetime - now).total_seconds()
        
        timer = threading.Timer(delay_seconds, self.restart_scheduler)
        timer.start()
        self.timers.append(timer)
        print(f"Scheduler restart scheduled for tomorrow, delay: {delay_seconds} seconds")
    
    def restart_scheduler(self):
        """Restart scheduler"""
        print("Restarting scheduler...")
        self.cleanup()
        self.setup_schedules()
    
    def cleanup(self):
        """Clean up all timers"""
        print("Cleaning up timers...")
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()
        
        # Terminate current processes
        for name, process in self.current_processes.items():
            try:
                process.terminate()
            except:
                pass
        self.current_processes.clear()

def main():
    launcher = ScheduleLauncher()
    
    # Register exit handler
    import atexit
    atexit.register(launcher.cleanup)
    
    try:
        launcher.setup_schedules()
        print("Schedule launcher ready")
        
        # Keep running
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print("\nSchedule launcher exiting")
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    main()