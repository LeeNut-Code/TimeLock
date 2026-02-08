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
        self.should_monitor = True
        self.is_in_range = False
        self.lock_process = None
        self.last_lock_attempt = None
        self.linux_lock_executed = False  # 新增：跟踪Linux锁定是否已执行

    def parse_time(self, time_str):
        """解析时间字符串"""
        return datetime.strptime(time_str, "%H:%M").time()
    
    def is_time_in_ranges(self, check_time):
        """检查时间是否在允许范围内，包括跨夜范围"""
        time_ranges = self.config.get('time_ranges', [])
        
        # 特殊情况：检查是否在最后一个范围结束后且在第一个范围开始前（跨夜锁定期）
        if time_ranges:
            # 获取最后一个范围的结束时间
            last_range = time_ranges[-1]
            last_end_time = self.parse_time(last_range['end'])
            
            # 获取第一个范围的开始时间
            first_range = time_ranges[0]
            first_start_time = self.parse_time(first_range['start'])
            
            # 如果当前时间在最后一个范围结束后
            if check_time > last_end_time:
                # 在最后一个范围结束后，我们应该被锁定
                return False
            elif check_time < first_start_time:
                # 在第一个范围开始前，我们应该被锁定
                return False
        
        # 正常检查当天的范围
        for range_config in time_ranges:
            start_time = self.parse_time(range_config['start'])
            end_time = self.parse_time(range_config['end'])
            if start_time <= check_time <= end_time:
                return True
        
        return False
    
    def is_system_locked(self):       # 检查系统是否被锁定，使用改进x检测方法"""
        try:
            current_os = platform.system()
            
            if current_os == 'Windows':
                import ctypes
                # 改进的Windows锁定检测
                # GetForegroundWindow在系统锁定时返回0
                # 同时检查explorer.exe进程状态作为备份
                is_locked = ctypes.windll.user32.GetForegroundWindow() == 0
                
                # 额外验证
                if not is_locked:
                    try:
                        # 检查屏幕保护程序是否正在运行
                        if ctypes.windll.user32.SystemParametersInfoW(0x0072, 0, None, 0):
                            is_locked = True
                    except:
                        pass
                        
                return is_locked
            else:  # Linux
                # 增强的Linux锁定检测，使用更多方法
                try:
                    # 方法1：检查xscreensaver状态
                    try:
                        result = subprocess.run(['xscreensaver-command', '-time'], 
                                              capture_output=True, text=True, timeout=1)
                        if 'locked' in result.stdout.lower():
                            print("通过xscreensaver检测到Linux锁定")
                            return True
                    except FileNotFoundError:
                        pass
                    except subprocess.TimeoutExpired:
                        print("警告：xscreensaver-command超时")
                    
                    # 方法2：通过dbus检查GNOME屏幕保护程序（改进超时处理）
                    try:
                        # 首先尝试标准的GNOME屏幕保护程序路径
                        result = subprocess.run(
                            ['dbus-send', '--session', 
                             '--dest=org.gnome.ScreenSaver', 
                             '--type=method_call', 
                             '--reply-timeout=1000',  # 更短的超时
                             '/org/gnome/ScreenSaver', 
                             'org.gnome.ScreenSaver.GetActive'],
                            capture_output=True, text=True, timeout=1)
                        if 'boolean true' in result.stdout.lower():
                            print("通过GNOME屏幕保护程序检测到Linux锁定")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # 尝试替代的GNOME路径
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
                                print("通过GNOME Mutter检测到Linux锁定")
                                return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            pass
                    
                    # 方法3：检查KDE屏幕保护程序
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
                            print("通过KDE/FreeDesktop屏幕保护程序检测到Linux锁定")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                    
                    # 方法4：Xfce支持
                    try:
                        result = subprocess.run(['xfce4-screensaver-command', '-q'], 
                                              capture_output=True, text=True, timeout=1)
                        if 'active' in result.stdout.lower():
                            print("通过Xfce屏幕保护程序检测到Linux锁定")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                    
                    # 方法5：使用更好的处理回退到xdotool
                    try:
                        result = subprocess.run(['xdotool', 'getwindowfocus'], 
                                              capture_output=True, text=True, timeout=1)
                        if result.returncode != 0:
                            print("通过xdotool检测到Linux锁定")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # 尝试wmctrl作为替代
                        try:
                            result = subprocess.run(['wmctrl', '-m'], 
                                                  capture_output=True, text=True, timeout=1)
                            # 如果wmctrl返回错误，桌面可能被锁定
                            if result.returncode != 0:
                                print("通过wmctrl检测到Linux锁定")
                                return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            pass
                    
                    # 如果到这里，没有检测到锁定
                    # 注意：这不一定意味着系统未锁定，
                    # 只是我们无法用可用的方法检测到锁定
                    return False
                    
                except Exception as e:
                    print(f"Linux锁定检测错误: {e}")
                    # 出错时，假设未锁定以避免假阴性
                    return False
                    
        except Exception as e:
            print(f"检查锁定状态时出错: {e}")
            return False
    
    def start_lock(self, force=False):
        """启动锁定
        
        参数:
            force: 如果为True，忽略冷却期以在解锁后立即重新锁定
        """
        # 仅在非强制重新锁定时应用冷却期
        current_time = time.time()
        if not force and self.last_lock_attempt and (current_time - self.last_lock_attempt) < 5:
            print(f"由于冷却期，锁定尝试被跳过")
            return
            
        self.last_lock_attempt = current_time
        
        current_os = platform.system()
        
        # Linux平台特殊处理：只运行一次lock_gnome.py
        if current_os != 'Windows':
            if self.linux_lock_executed:
                print("Linux锁定已执行过，跳过重复执行")
                return
            else:
                self.linux_lock_executed = True
                print("首次执行Linux锁定")
        
        if self.lock_process is None or self.lock_process.poll() is not None:
            try:
                # 根据平台选择锁定程序
                if current_os == 'Windows':
                    lock_script = 'point_locker.pyw'
                else:  # Linux
                    lock_script = 'lock_gnome.py'
                
                print(f"尝试在 {datetime.now().strftime('%H:%M:%S')} 锁定系统")
                print(f"为 {current_os} 平台使用 {lock_script}")
                
                # 准备启动参数
                launch_args = [sys.executable, lock_script]
                
                # 如果是Linux平台，计算并传递倒计时参数
                if current_os != 'Windows':
                    # 计算锁定持续时间（分钟）
                    lock_duration = self.calculate_lock_duration()
                    launch_args.append(str(lock_duration))
                    print(f"传递倒计时参数: {lock_duration} 分钟")
                
                # 根据平台设置不同的启动参数
                process_kwargs = {}
                if current_os == 'Windows':
                    process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                
                self.lock_process = subprocess.Popen(
                    launch_args,
                    **process_kwargs
                )
                print("锁定进程启动成功")
                
                # 短暂延迟后检查进程状态
                def check_process_status():
                    time.sleep(3)
                    if self.lock_process.poll() is not None:
                        return_code = self.lock_process.poll()
                        print(f"锁定进程完成，返回码: {return_code}")
                        if return_code != 0:
                            print("锁定进程可能已失败")
                            # 如果Linux锁定失败，重置标志以便重试
                            if current_os != 'Windows':
                                self.linux_lock_executed = False
                
                threading.Thread(target=check_process_status, daemon=True).start()
                
            except Exception as e:
                print(f"启动锁定进程失败: {e}")
                # 如果启动失败，重置Linux锁定标志
                if current_os != 'Windows':
                    self.linux_lock_executed = False

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

    def stop_lock(self):
        """停止锁定进程，使用增强的解锁机制"""
        current_datetime = datetime.now()
        print(f"[解锁] 尝试在 {current_datetime.strftime('%Y-%m-%d %H:%M:%S')} 解锁")
        
        # 首先，如果存在锁定进程则终止它
        if self.lock_process:
            try:
                print("[解锁] 终止锁定进程")
                self.lock_process.terminate()
                # 等待进程终止
                import time
                time.sleep(1)
                # 如果仍在运行则强制杀死
                if self.lock_process.poll() is None:
                    print("[解锁] 强制杀死锁定进程")
                    self.lock_process.kill()
                self.lock_process = None
                print("[解锁] 锁定进程停止成功")
            except Exception as e:
                print(f"[解锁] 停止锁定进程时出错: {e}")
        
        # 重置Linux锁定执行标志
        if platform.system() != 'Windows':
            self.linux_lock_executed = False
            print("[解锁] 重置Linux锁定执行标志")
        
        # 额外的平台特定解锁机制以确保系统已解锁
        current_os = platform.system()
        if current_os == 'Windows':
            # Windows特定解锁逻辑可在此处添加（如需要）
            print("[解锁] 检测到Windows平台，系统应该已解锁")
        else:  # Linux
            try:
                # 尝试确保Linux上的屏幕已解锁
                print("[解锁] 检测到Linux平台，验证解锁状态")
                # 这是一个安全措施 - 实际上，终止锁定进程应该就足够了
                # 但如果需要可以添加额外命令
                if hasattr(self, 'is_system_locked') and not self.is_system_locked():
                    print("[解锁] 系统确认已解锁")
                else:
                    print("[解锁] 警告：系统可能仍被锁定，可以添加额外措施")
            except Exception as e:
                print(f"[解锁] 验证解锁状态时出错: {e}")
        
        print("[解锁] 解锁过程完成")
    
    def monitor_loop(self):
        """监控循环，带有增强的跨夜锁定"""
        print(f"在 {datetime.now().strftime('%H:%M:%S')} 开始监控")
        
        while self.should_monitor:
            current_time = datetime.now().time()
            current_datetime = datetime.now()
            in_range = self.is_time_in_ranges(current_time)
            
            # 跨夜锁定期的特殊处理（在最后一个范围结束后直到第一个范围开始）
            time_ranges = self.config.get('time_ranges', [])
            is_overnight_lock_period = False
            
            if time_ranges:
                # 获取最后一个范围的结束时间
                last_range = time_ranges[-1]
                last_end_time = self.parse_time(last_range['end'])
                
                # 获取第一个范围的开始时间
                first_range = time_ranges[0]
                first_start_time = self.parse_time(first_range['start'])
                
                # 检查当前时间是否在跨夜锁定期
                if current_time > last_end_time:
                    is_overnight_lock_period = True
                elif current_time < first_start_time:
                    # 对于第一个范围开始前的时间，检查是否来自前一天
                    is_overnight_lock_period = True
            
            # 处理状态转换
            if in_range != self.is_in_range:
                self.is_in_range = in_range
                if in_range:
                    print("进入允许时间范围，解锁")
                    self.stop_lock()
                else:
                    print("进入不允许时间范围，锁定")
                    self.start_lock()
            
            # 增强的锁定执行
            if not in_range:
                if is_overnight_lock_period:
                    # 跨夜锁定期更严格的执行
                    print(f"[跨夜锁定] 在 {current_datetime.strftime('%H:%M:%S')} 检查系统锁定状态")
                    if not self.is_system_locked():
                        print("[跨夜锁定] 跨夜期间系统未锁定，立即重新锁定")
                        # 强制锁定而不使用冷却期
                        self.start_lock(force=True)
                else:
                    # 常规不允许时间执行
                    if not self.is_system_locked():
                        print("在不允许时间范围内检测到解锁，立即重新锁定")
                        # 强制锁定而不使用冷却期
                        self.start_lock(force=True)
            
            # Linux使用更短间隔以提高响应性
            # 跨夜锁定期也使用更短间隔以获得更好的执行效果
            if is_overnight_lock_period:
                # 跨夜锁定期更频繁检查
                time.sleep(1)  # 每秒检查一次
            elif platform.system() == 'Windows':
                time.sleep(5)  # Windows：每5秒检查一次
            else:
                time.sleep(1)  # Linux：每1秒检查一次以获得更好的响应性
    
    def cleanup(self):
        """清理资源"""
        self.should_monitor = False
        self.stop_lock()

def main():
    monitor = RangeMonitor()
    
    import atexit
    atexit.register(monitor.cleanup)
    
    try:
        print("范围监控器已启动")
        monitor.monitor_loop()
    except KeyboardInterrupt:
        print("\n范围监控器退出")
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    main()