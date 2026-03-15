import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta

class TestLock:
    def __init__(self):
        # 配置文件路径
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        # 保存原始配置
        self.original_config = None
        # 读取当前配置
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"配置已成功从 {self.config_path} 加载")
            # 保存原始配置
            self.original_config = config.copy()
            return config
        except Exception as e:
            print(f"加载配置失败: {e}")
            return None
    
    def save_config(self, config):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"配置已成功保存到 {self.config_path}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def modify_lock_time(self):
        """修改锁定时间为当前时间的 show_before_minutes +1分钟后"""
        if not self.config:
            print("配置加载失败，无法修改锁定时间")
            return False
        
        # 获取当前时间
        current_time = datetime.now()
        print(f"当前时间: {current_time.strftime('%H:%M:%S')}")
        
        # 获取 show_before_minutes
        show_before_minutes = self.config.get('reminder', {}).get('show_before_minutes', 2)
        print(f"show_before_minutes: {show_before_minutes}")
        
        # 按照用户要求设置时间范围
        # 第一个时间范围：当前时间-1分钟 到 当前时间+3分钟
        range1_start = (current_time - timedelta(minutes=1)).strftime('%H:%M')
        range1_end = (current_time + timedelta(minutes=3)).strftime('%H:%M')
        
        # 第二个时间范围：当前时间+4分钟 到 23:59
        range2_start = (current_time + timedelta(minutes=4)).strftime('%H:%M')
        range2_end = "23:59"
        
        print(f"第一个时间范围: 开始 {range1_start}, 结束 {range1_end}")
        print(f"第二个时间范围: 开始 {range2_start}, 结束 {range2_end}")
        print(f"锁定时间范围: 开始 {range1_end}, 结束 {range2_start}")
        print(f"提醒时间: {range1_end}")
        
        # 修改配置文件中的时间范围
        self.config['time_ranges'] = [
            {
                "start": range1_start,
                "end": range1_end
            },
            {
                "start": range2_start,
                "end": range2_end
            }
        ]
        
        # 保存修改后的配置
        if self.save_config(self.config):
            print("配置已修改，设置了两个时间范围")
            return True
        else:
            return False
    
    def run_main(self):
        """运行 main.pyw 进行测试"""
        try:
            print("正在启动 main.pyw 进行测试...")
            # 根据平台设置不同的启动参数
            process_kwargs = {}
            if sys.platform == 'win32':
                process_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            
            # 启动 main.pyw
            main_process = subprocess.Popen(
                [sys.executable, 'main.pyw'],
                **process_kwargs
            )
            print(f"main.pyw 已启动，PID: {main_process.pid}")
            return main_process
        except Exception as e:
            print(f"启动 main.pyw 失败: {e}")
            return None
    
    def restore_config(self):
        """恢复原始配置"""
        if self.original_config:
            if self.save_config(self.original_config):
                print("原始配置已恢复")
                return True
            else:
                return False
        else:
            print("没有原始配置可恢复")
            return False
    
    def run_test(self):
        """运行测试"""
        print("开始测试锁定和解锁功能...")
        
        # 1. 读取配置到缓存（在__init__中已完成）
        print("配置已读取到缓存")
        
        # 2. 修改为测试配置
        if not self.modify_lock_time():
            print("修改锁定时间失败，测试终止")
            return
        
        # 3. 运行 main.pyw
        main_process = self.run_main()
        if not main_process:
            print("启动 main.pyw 失败，测试终止")
            self.restore_config()
            return
        
        # 等待锁定和解锁过程完成
        # 计算等待时间：确保覆盖整个锁定和解锁过程
        # 等待时间 = 4分钟锁定结束时间 + 2分钟缓冲 = 6分钟
        wait_time = 4 * 60  # 6分钟等待时间
        print(f"等待 {wait_time} 秒，让锁定和解锁过程完成...")
        
        # 分阶段等待，提供更多反馈
        for i in range(wait_time // 10):
            time.sleep(10)
            remaining = wait_time - (i + 1) * 10
            if remaining % 30 == 0:
                print(f"剩余等待时间: {remaining} 秒...")
        
        # 终止 main.pyw 进程
        try:
            main_process.terminate()
            print("main.pyw 进程已终止")
        except Exception as e:
            print(f"终止 main.pyw 进程失败: {e}")
        
        # 4. main.pyw结束后还原配置
        self.restore_config()
        
        print("测试完成！")
        print("\n测试结果说明：")
        print("1. 系统应该在计算的锁定时间自动锁定")
        print("2. 系统应该在计算的解锁时间后自动解锁")
        print("3. 解锁后系统不应该重新锁定")
        print("4. 测试完成后配置文件已恢复为原始状态")

if __name__ == "__main__":
    test = TestLock()
    test.run_test()
