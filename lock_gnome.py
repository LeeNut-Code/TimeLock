#!/usr/bin/env python3
import platform
import subprocess
import time
import sys
import os
from datetime import datetime, timedelta

# 根据平台导入不同的模块
current_os = platform.system()
if current_os == 'Windows':
    import ctypes
else:
    try:
        import dbus
    except ImportError:
        print("警告: dbus模块未找到，Linux功能可能受限")

def pause_media_playback():
    """
    暂停所有正在播放的媒体
    """
    try:
        # 连接到会话总线
        bus = dbus.SessionBus()
        
        # 获取所有可用的媒体播放器服务
        media_players = [
            'org.mpris.MediaPlayer2.vlc',
            'org.mpris.MediaPlayer2.spotify',
            'org.mpris.MediaPlayer2.rhythmbox',
            'org.mpris.MediaPlayer2.chromium',
            'org.mpris.MediaPlayer2.firefox',
            'org.mpris.MediaPlayer2.browser',
            'org.mpris.MediaPlayer2.amarok'
        ]
        
        paused_players = []
        
        for player_name in media_players:
            try:
                # 尝试连接到媒体播放器
                player = bus.get_object(player_name, '/org/mpris/MediaPlayer2')
                
                # 获取播放控制接口
                player_interface = dbus.Interface(
                    player, 
                    'org.mpris.MediaPlayer2.Player'
                )
                
                # 检查播放状态
                properties = dbus.Interface(
                    player,
                    'org.freedesktop.DBus.Properties'
                )
                status = properties.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                
                # 如果正在播放，则暂停
                if status == 'Playing':
                    player_interface.Pause()
                    paused_players.append(player_name)
                    print(f"已暂停: {player_name}")
                    
            except dbus.exceptions.DBusException:
                # 播放器不存在，继续尝试下一个
                continue
        
        return paused_players
        
    except Exception as e:
        print(f"暂停媒体时出错: {e}")
        return []

def lock_screen():
    """
    锁定屏幕 - 根据不同平台使用不同的实现
    """
    if current_os == 'Windows':
        return lock_windows_screen()
    else:
        return lock_linux_screen()

def lock_windows_screen():
    """
    锁定 Windows 屏幕
    """
    try:
        # 使用Windows API锁定屏幕
        ctypes.windll.user32.LockWorkStation()
        print("Windows屏幕已成功锁定")
        return True
    except Exception as e:
        print(f"Windows锁定屏幕失败: {e}")
        return False

def lock_linux_screen():
    """
    锁定 Linux 桌面（主要针对GNOME）
    """
    try:
        # 如果没有dbus模块，直接使用备用方法
        if 'dbus' not in globals():
            return lock_gnome_fallback()
            
        # 连接到会话总线
        bus = dbus.SessionBus()
        
        # 获取屏幕保护器接口
        screensaver = bus.get_object(
            'org.gnome.ScreenSaver',
            '/org/gnome/ScreenSaver'
        )
        
        # 调用锁定方法
        lock = screensaver.get_dbus_method('Lock', 'org.gnome.ScreenSaver')
        lock()
        
        print("Linux屏幕已成功锁定")
        return True
        
    except Exception as e:
        print(f"Linux锁定屏幕错误: {e}")
        # 尝试使用备用方法
        return lock_gnome_fallback()

def lock_gnome_fallback():
    """
    备用锁定方法
    """
    try:
        commands = [
            ['gnome-screensaver-command', '--lock'],
            ['dbus-send', '--type=method_call', '--dest=org.gnome.ScreenSaver',
             '/org/gnome/ScreenSaver', 'org.gnome.ScreenSaver.Lock'],
            ['xdg-screensaver', 'lock']
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=5)
                print("屏幕已成功锁定（使用备用方法）")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        print("无法锁定屏幕")
        return False
        
    except Exception as e:
        print(f"备用锁定方法错误: {e}")
        return False

def mute_system_audio():
    """
    可选：静音系统音频
    """
    try:
        subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', '1'], 
                      check=True, capture_output=True)
        print("系统音频已静音")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['amixer', '-D', 'pulse', 'set', 'Master', 'mute'], 
                          check=True, capture_output=True)
            print("系统音频已静音（使用amixer）")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("无法静音系统音频")
            return False

def run_fullscreen_break(countdown_minutes):
    """
    在Linux平台上运行fullscreen_break.pyw程序并传递倒计时值
    """
    if current_os != 'Windows':
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fullscreen_break_path = os.path.join(script_dir, 'fullscreen_break.pyw')
        
        # 检查文件是否存在
        if os.path.exists(fullscreen_break_path):
            try:
                # 以非阻塞方式启动fullscreen_break.pyw，并传递倒计时参数
                print(f"正在启动fullscreen_break.pyw，倒计时: {countdown_minutes}分钟")
                subprocess.Popen([sys.executable, fullscreen_break_path, str(countdown_minutes)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
                return True
            except Exception as e:
                print(f"启动fullscreen_break.pyw失败: {e}")
                return False
        else:
            print(f"fullscreen_break.pyw文件未找到: {fullscreen_break_path}")
            return False
    else:
        print("Windows平台，跳过运行fullscreen_break.pyw")
        return False

def main(countdown_minutes=None):
    """
    主函数：先暂停媒体，然后锁定屏幕，在Linux平台上同时运行fullscreen_break
    
    参数:
        countdown_minutes: 倒计时分钟数，如果为None则需要从配置中获取或使用默认值
    """
    print("正在准备锁定屏幕...")
    
    # 只在Linux平台上执行媒体控制功能
    if current_os != 'Windows':
        # 暂停媒体播放
        print("正在暂停媒体播放...")
        paused_players = pause_media_playback()
        
        # 可选：静音系统音频
        print("正在静音系统音频...")
        mute_system_audio()
        
        # 运行fullscreen_break.pyw（只在Linux平台）
        if countdown_minutes is not None:
            run_fullscreen_break(countdown_minutes)
    else:
        print("Windows平台，跳过媒体控制")
    
    # 短暂延迟确保操作完成
    time.sleep(0.5)
    
    # 锁定屏幕
    print("正在锁定屏幕...")
    lock_success = lock_screen()
    
    if lock_success:
        print("屏幕锁定流程完成")
    else:
        print("屏幕锁定失败")
    
    return lock_success

if __name__ == "__main__":
    # 从命令行参数获取倒计时分钟数（如果有）
    countdown = None
    if len(sys.argv) > 1:
        try:
            countdown = float(sys.argv[1])
        except ValueError:
            print("无法解析倒计时参数，将使用默认值")
    
    main(countdown)
