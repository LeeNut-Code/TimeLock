import os
import time
import threading
import subprocess
import sys
import json
import platform
from datetime import datetime, time as dt_time

class RangeMonitor:
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
        self.should_monitor = True
        self.is_in_range = False
        self.lock_process = None
        self.last_lock_attempt = None
    
    def parse_time(self, time_str):
        """Parse time string"""
        return datetime.strptime(time_str, "%H:%M").time()
    
    def is_time_in_ranges(self, check_time):
        """Check if time is within allowed ranges, including overnight ranges"""
        time_ranges = self.config.get('time_ranges', [])
        
        # Special case: check if it's after the last range's end and before the first range's start (overnight lock period)
        if time_ranges:
            # Get the last range's end time
            last_range = time_ranges[-1]
            last_end_time = self.parse_time(last_range['end'])
            
            # Get the first range's start time
            first_range = time_ranges[0]
            first_start_time = self.parse_time(first_range['start'])
            
            # If current time is after last range's end
            if check_time > last_end_time:
                # After last range's end, we should be locked
                return False
            elif check_time < first_start_time:
                # Before first range's start, we should be locked
                return False
        
        # Normal check for current day's ranges
        for range_config in time_ranges:
            start_time = self.parse_time(range_config['start'])
            end_time = self.parse_time(range_config['end'])
            if start_time <= check_time <= end_time:
                return True
        
        return False
    
    def is_system_locked(self):
        """Check if system is locked with improved detection"""
        try:
            current_os = platform.system()
            
            if current_os == 'Windows':
                import ctypes
                # Improved Windows lock detection
                # GetForegroundWindow returns 0 when system is locked
                # Also check explorer.exe process status as a backup
                is_locked = ctypes.windll.user32.GetForegroundWindow() == 0
                
                # Additional verification
                if not is_locked:
                    try:
                        # Check if screen saver is running
                        if ctypes.windll.user32.SystemParametersInfoW(0x0072, 0, None, 0):
                            is_locked = True
                    except:
                        pass
                        
                return is_locked
            else:  # Linux
                # Enhanced Linux lock detection with more methods
                try:
                    # Method 1: Check xscreensaver status
                    try:
                        result = subprocess.run(['xscreensaver-command', '-time'], 
                                              capture_output=True, text=True, timeout=1)
                        if 'locked' in result.stdout.lower():
                            print("Linux lock detected via xscreensaver")
                            return True
                    except FileNotFoundError:
                        pass
                    except subprocess.TimeoutExpired:
                        print("Warning: xscreensaver-command timeout")
                    
                    # Method 2: Check GNOME ScreenSaver via dbus (improved with better timeout)
                    try:
                        # First try the standard GNOME ScreenSaver path
                        result = subprocess.run(
                            ['dbus-send', '--session', 
                             '--dest=org.gnome.ScreenSaver', 
                             '--type=method_call', 
                             '--reply-timeout=1000',  # Shorter timeout
                             '/org/gnome/ScreenSaver', 
                             'org.gnome.ScreenSaver.GetActive'],
                            capture_output=True, text=True, timeout=1)
                        if 'boolean true' in result.stdout.lower():
                            print("Linux lock detected via GNOME ScreenSaver")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # Try alternative GNOME path
                        try:
                            result = subprocess.run(
                                ['dbus-send', '--session', 
                                 '--dest=org.gnome.Mutter.ScreenSaver', 
                                 '--type=method_call', 
                                 '--reply-timeout=1000',
                                 '/org/gnome/Mutter/ScreenSaver', 
                                 'org.gnome.ScreenSaver.GetActive'],
                                capture_output=True, text=True, timeout=1)
                            if 'boolean true' in result.stdout.lower():
                                print("Linux lock detected via GNOME Mutter")
                                return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            pass
                    
                    # Method 3: Check KDE ScreenSaver
                    try:
                        result = subprocess.run(
                            ['dbus-send', '--session', 
                             '--dest=org.freedesktop.ScreenSaver', 
                             '--type=method_call', 
                             '--reply-timeout=1000',
                             '/org/freedesktop/ScreenSaver', 
                             'org.freedesktop.ScreenSaver.GetActive'],
                            capture_output=True, text=True, timeout=1)
                        if 'boolean true' in result.stdout.lower():
                            print("Linux lock detected via KDE/FreeDesktop ScreenSaver")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                    
                    # Method 4: Xfce support
                    try:
                        result = subprocess.run(['xfce4-screensaver-command', '-q'], 
                                              capture_output=True, text=True, timeout=1)
                        if 'active' in result.stdout.lower():
                            print("Linux lock detected via Xfce Screensaver")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                    
                    # Method 5: Fall back to xdotool with better handling
                    try:
                        result = subprocess.run(['xdotool', 'getwindowfocus'], 
                                              capture_output=True, text=True, timeout=1)
                        if result.returncode != 0:
                            print("Linux lock detected via xdotool")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # Try wmctrl as alternative
                        try:
                            result = subprocess.run(['wmctrl', '-m'], 
                                                  capture_output=True, text=True, timeout=1)
                            # If wmctrl returns error, desktop might be locked
                            if result.returncode != 0:
                                print("Linux lock detected via wmctrl")
                                return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            pass
                    
                    # If we got here, no lock was detected
                    # Note: This doesn't necessarily mean system is unlocked,
                    # just that we couldn't detect a lock with available methods
                    return False
                    
                except Exception as e:
                    print(f"Linux lock detection error: {e}")
                    # On error, assume unlocked to avoid false negatives
                    return False
                    
        except Exception as e:
            print(f"Error checking lock status: {e}")
            return False
    
    def start_lock(self, force=False):
        """Start lock
        
        Args:
            force: If True, ignore cool-down period for immediate relocking after unlock
        """
        # Only apply cool-down if not forced relock
        current_time = time.time()
        if not force and self.last_lock_attempt and (current_time - self.last_lock_attempt) < 5:
            print(f"Lock attempt skipped due to cool-down period")
            return
            
        self.last_lock_attempt = current_time
        
        if self.lock_process is None or self.lock_process.poll() is not None:
            try:
                current_os = platform.system()
                
                # 根据平台选择锁定程序
                if current_os == 'Windows':
                    lock_script = 'point_locker.pyw'
                else:  # Linux
                    lock_script = 'lock_gnome.py'
                
                print(f"Attempting to lock system at {datetime.now().strftime('%H:%M:%S')}")
                print(f"Using {lock_script} for {current_os} platform")
                
                # 根据平台设置不同的启动参数
                process_kwargs = {}
                if current_os == 'Windows':
                    process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
                self.lock_process = subprocess.Popen(
                    [sys.executable, lock_script],
                    **process_kwargs
                )
                print("Lock process started successfully")
                
                # Check process status after a short delay
                def check_process_status():
                    time.sleep(3)
                    if self.lock_process.poll() is not None:
                        return_code = self.lock_process.poll()
                        print(f"Lock process completed with return code: {return_code}")
                        if return_code != 0:
                            print("Lock process may have failed")
                
                threading.Thread(target=check_process_status, daemon=True).start()
                
            except Exception as e:
                print(f"Failed to start lock process: {e}")
    
    def stop_lock(self):
        """Stop lock process with enhanced unlocking mechanism"""
        current_datetime = datetime.now()
        print(f"[UNLOCK] Attempting to unlock at {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # First, terminate the lock process if it exists
        if self.lock_process:
            try:
                print("[UNLOCK] Terminating lock process")
                self.lock_process.terminate()
                # Wait briefly for process to terminate
                import time
                time.sleep(1)
                # Force kill if still running
                if self.lock_process.poll() is None:
                    print("[UNLOCK] Force killing lock process")
                    self.lock_process.kill()
                self.lock_process = None
                print("[UNLOCK] Lock process stopped successfully")
            except Exception as e:
                print(f"[UNLOCK] Error stopping lock process: {e}")
        
        # Additional platform-specific unlock mechanisms to ensure system is unlocked
        current_os = platform.system()
        if current_os == 'Windows':
            # Windows specific unlock logic could be added here if needed
            print("[UNLOCK] Windows platform detected, system should be unlocked")
        else:  # Linux
            try:
                # Try to ensure screen is unlocked on Linux
                print("[UNLOCK] Linux platform detected, verifying unlock state")
                # This is a safeguard - in practice, terminating the lock process should be sufficient
                # But we can add additional commands if needed
                if hasattr(self, 'is_system_locked') and not self.is_system_locked():
                    print("[UNLOCK] System confirmed unlocked")
                else:
                    print("[UNLOCK] Warning: System might still be locked, additional measures could be added")
            except Exception as e:
                print(f"[UNLOCK] Error verifying unlock state: {e}")
        
        print("[UNLOCK] Unlock process completed")
    
    def monitor_loop(self):
        """Monitor loop with enhanced overnight locking"""
        print(f"Starting monitoring at {datetime.now().strftime('%H:%M:%S')}")
        
        while self.should_monitor:
            current_time = datetime.now().time()
            current_datetime = datetime.now()
            in_range = self.is_time_in_ranges(current_time)
            
            # Special handling for overnight lock period (after last range end until first range start)
            time_ranges = self.config.get('time_ranges', [])
            is_overnight_lock_period = False
            
            if time_ranges:
                # Get the last range's end time
                last_range = time_ranges[-1]
                last_end_time = self.parse_time(last_range['end'])
                
                # Get the first range's start time
                first_range = time_ranges[0]
                first_start_time = self.parse_time(first_range['start'])
                
                # Check if current time is in overnight lock period
                if current_time > last_end_time:
                    is_overnight_lock_period = True
                elif current_time < first_start_time:
                    # For times before first range start, check if it's from previous day
                    is_overnight_lock_period = True
            
            # Handle state transitions
            if in_range != self.is_in_range:
                self.is_in_range = in_range
                if in_range:
                    print("Entering allowed time range, unlocking")
                    self.stop_lock()
                else:
                    print("Entering non-allowed time range, locking")
                    self.start_lock()
            
            # Enhanced lock enforcement
            if not in_range:
                if is_overnight_lock_period:
                    # Stricter enforcement during overnight lock period
                    print(f"[OVERNIGHT LOCK] Checking system lock status at {current_datetime.strftime('%H:%M:%S')}")
                    if not self.is_system_locked():
                        print("[OVERNIGHT LOCK] System unlocked during overnight period, immediately re-locking")
                        # Force lock without cool-down
                        self.start_lock(force=True)
                else:
                    # Regular non-allowed time enforcement
                    if not self.is_system_locked():
                        print("Detected unlock in non-allowed time range, immediately re-locking")
                        # Force the lock without cool-down
                        self.start_lock(force=True)
            
            # Use shorter interval for Linux to improve responsiveness
            # Also use shorter interval during overnight lock period for better enforcement
            if is_overnight_lock_period:
                # More frequent checking during overnight lock period
                time.sleep(1)  # Check every second
            elif platform.system() == 'Windows':
                time.sleep(5)  # Windows: Check every 5 seconds
            else:
                time.sleep(1)  # Linux: Check every 1 second for better responsiveness
    
    def cleanup(self):
        """Clean up resources"""
        self.should_monitor = False
        self.stop_lock()

def main():
    monitor = RangeMonitor()
    
    import atexit
    atexit.register(monitor.cleanup)
    
    try:
        print("Range monitor started")
        monitor.monitor_loop()
    except KeyboardInterrupt:
        print("\nRange monitor exiting")
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    main()