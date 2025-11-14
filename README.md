# TimeLock 定时锁机

<div align="center">
  <img src="https://img.shields.io/badge/python-3.6+-brightgreen.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux-orange.svg" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/status-active-brightgreen.svg" alt="Project Status">
  <img src="https://img.shields.io/badge/dependencies-PyQt5-blue.svg" alt="Dependencies">
  <img src="https://img.shields.io/badge/feature-auto%20lock-green.svg" alt="Auto Lock">
  <img src="https://img.shields.io/badge/feature-cross--day%20support-yellow.svg" alt="Cross-day Support">
</div>

## 项目介绍

TimeLock系统是一个智能时间管理工具，旨在帮助用户按照设定的时间计划自动锁定和解锁电脑，实现对工作和休息时间的有效管理。系统支持Windows和Linux（gnome桌面）双平台，具有跨日运行能力，可在特定时间段自动锁定计算机，防止用户在非工作时间使用电脑，同时在工作时间自动解锁。

## 功能特点

### 核心功能
- **智能时间锁定**：根据配置的时间段自动锁定和解锁系统
- **跨日运行支持**：在最后一个时间段结束后持续锁定，直到次日第一个时间段开始
- **双平台兼容**：同时支持Windows和Linux（仅支持gnome桌面）操作系统
- **定时提醒功能**：在锁定或关机前显示友好的提醒弹窗
- **强制锁定机制**：在非允许时间内检测到解锁后立即重新锁定
- **系统关机**：支持在指定时间自动强制关机

### 高级特性
- **精确的时间范围检查**：支持跨日时间范围判断，确保锁定逻辑准确
- **增强的系统锁定检测**：多方法检测系统锁定状态，适应不同桌面环境
- **优雅的锁定流程**：先显示提醒，然后锁定屏幕，可选择关闭显示器
- **灵活的配置选项**：通过JSON配置文件自定义时间范围、提醒时间等
- **详细的日志记录**：记录所有操作和状态变化，便于问题排查

## 使用场景

- **工作时间管理**：企业或个人设置固定工作时段，防止在休息时间使用电脑
- **学习时间规划**：学生设置专注学习时间，提高学习效率
- **儿童上网控制**：限制未成年人在特定时间段使用电脑
- **自律助手**：帮助用户遵守设定的作息时间，避免熬夜
- **公共电脑管理**：在图书馆、实验室等公共场所管理电脑使用时间

## 项目架构

TimeLock系统采用模块化设计，由多个协同工作的组件构成：

- **主控制器**（main.pyw）：系统的核心入口，负责启动其他组件和基础时间判断
- **时间范围监控器**（range_monitor.pyw）：持续监控当前时间是否在允许范围内
- **定时任务调度器**（schedule_launcher.pyw）：按计划执行锁定和关机任务
- **提醒界面**（reminder.pyw）：显示锁定和关机前的倒计时提醒
- **锁定执行器**（point_locker.pyw/lock_gnome.py）：执行实际的屏幕锁定操作
- **配置管理**：通过config.json集中管理系统配置

## 安装与配置

### 系统要求

**Windows 平台**：
- Windows 7/8/10/11
- Python 3.6+
- PyQt5（用于提醒界面）

**Linux 平台**：
- 支持GNOME、KDE、Xfce等主流桌面环境
- Python 3.6+
- PyQt5（用于提醒界面）
- dbus-python（用于媒体控制）

### 安装步骤

1. **安装Python**：确保系统已安装Python 3.6或更高版本
2. **安装依赖**：
   ```
   pip install PyQt5
   # Linux平台额外安装
   pip install dbus-python
   ```
3. **下载项目**：将项目文件下载到本地目录
4. **配置参数**：编辑config.json文件，根据需要修改时间范围和其他设置

## 配置说明

配置文件config.json包含以下主要设置，您可以根据个人需求进行自定义：

```json
{
  "time_ranges": [
    {"start": "08:30", "end": "09:55"},
    {"start": "10:15", "end": "11:45"},
    {"start": "13:10", "end": "15:55"},
    {"start": "16:15", "end": "17:30"},
    {"start": "18:15", "end": "21:10"}
  ],
  "shutdown_time": "21:10",
  "reminder": {"show_before_minutes": 2},
  "break_ui": {
    "wallpaper_path": "/mnt/Datas/Administrator/图片/横屏壁纸/",
    "opacity": 0.65,
    "blur_effect": true,
    "blur_radius": 20
  }
}
```

### 配置参数详解

- **time_ranges**：允许使用电脑的时间段列表，格式为24小时制的"HH:MM"
  - 可以配置多个不连续的时间段
  - 系统会在这些时间段内保持解锁状态
  - 时间段之间的间隔会被视为锁定时间
  - 最后一个时间段结束后到次日第一个时间段开始前为跨日锁定期

- **shutdown_time**：每日自动关机时间，格式为24小时制的"HH:MM"
  - 建议设置为最后一个时间段的结束时间
  - 到达该时间后系统将强制关机

- **reminder.show_before_minutes**：提前多少分钟显示锁定/关机提醒
  - 默认为2分钟
  - 可以根据需要调整，给用户足够的时间保存工作

- **break_ui**：休息界面的相关配置（主要用于Linux平台）
  - `wallpaper_path`：壁纸文件夹路径
  - `opacity`：背景透明度（0.0-1.0）
  - `blur_effect`：是否启用模糊效果
  - `blur_radius`：模糊半径

## 使用方法

### 基本使用

1. **启动系统**：
   ```
   python main.pyw
   ```
   系统会在后台静默运行，没有主界面，所有操作通过日志记录。

2. **系统启动后会自动**：
   - 从config.json加载配置
   - 检查当前时间是否在允许范围内
   - 启动监控和调度组件作为独立进程
   - 在非允许时间自动锁定系统
   - 在锁定或关机前指定时间显示提醒

3. **自动跨日运行**：系统会在最后一个时间段结束后持续锁定，直到次日第一个时间段开始自动解锁。跨日期间采用更频繁的检查间隔（每秒检查一次）以确保锁定状态。

### 开机自启动设置

**Windows**：
1. 右键点击main.pyw文件，选择「创建快捷方式」
2. 右键点击创建的快捷方式，选择「属性」
3. 在「目标」字段后添加 `start /min` 参数以最小化方式启动
4. 复制快捷方式到启动文件夹（按Win+R，输入`shell:startup`，回车）

**Linux**：
1. 创建启动脚本（timelock_start.sh）：
   ```bash
   #!/bin/bash
   # 切换到TimeLock系统所在目录
   cd /path/to/timelock-system
   # 启动主程序，重定向输出到日志文件
   python3 main.pyw >> timelock.log 2>&1 &
   ```
2. 赋予执行权限：`chmod +x timelock_start.sh`
3. **GNOME桌面**：
   - 打开「设置」→「会话和启动」→「启动应用程序」
   - 点击「添加」，填写名称和命令（指向启动脚本）
5. **通用方法**：
   - 将启动脚本添加到`~/.config/autostart/timelock.desktop`文件中：
   ```
   [Desktop Entry]
   Type=Application
   Exec=/path/to/timelock_start.sh
   Hidden=false
   NoDisplay=false
   X-GNOME-Autostart-enabled=true
   Name=TimeLock
   Comment=智能时间锁定系统
   ```

## 常见问题与故障排除

### 锁定/解锁相关问题

**问题：系统未按预期锁定/解锁**
- 检查config.json中的时间段设置是否正确（格式为"HH:MM"，24小时制）
- 确保系统时间同步准确，时区设置正确
- 查看进程管理器，确认range_monitor.pyw和schedule_launcher.pyw进程是否在运行
- 重启系统后重新启动TimeLock

**问题：跨日期间系统未正确保持锁定状态**
- 确保最后一个时间段的结束时间设置正确
- 检查第一个时间段的开始时间是否设置为次日的有效时间
- 系统会在跨日期间使用更频繁的检查间隔，保持系统锁定

### 配置和兼容性问题

**问题：程序无法启动**
- 确保已安装所有必要的依赖（Python 3.x，PyQt5等）
- 检查Python版本是否兼容（建议使用Python 3.7或更高版本）
- 验证config.json格式是否正确，可使用在线JSON验证工具检查

**问题：在Linux系统上锁定功能不正常**
- 确保已安装GNOME桌面环境或兼容组件
- 检查是否有权限执行锁定命令（可能需要sudo权限）
- 尝试手动运行lock_gnome.py测试锁定功能

**问题：提醒窗口未显示**
- 检查config.json中的reminder配置是否正确
- 确保系统通知权限已授予
- 验证PyQt5是否正确安装

### 其他问题

**问题：如何临时禁用TimeLock系统？**
- 可以通过任务管理器（Windows）或进程管理器（Linux）结束main.pyw进程及其子进程
- 修改config.json，添加当前时间到允许的时间段，然后重启TimeLock
- 注意：这是临时解决方案，系统重启后若有自启动设置，TimeLock会再次运行

**问题：如何修改已配置的时间范围？**
- 直接编辑config.json文件中的time_ranges部分
- 保存修改后，重启TimeLock系统使新配置生效

**问题：系统异常关机后，时间锁定是否会正常工作？**
- 是的，系统重启后，若已设置自启动，TimeLock会重新启动并按照配置工作
- 下次启动时，系统会重新计算锁定和解锁时间

## 注意事项

1. **重要数据保存**：系统在锁定前会显示提醒，请及时保存工作内容
2. **紧急解锁**：在极少数情况下需要紧急使用电脑时，可能需要结束TimeLock相关进程
3. **系统兼容性**：某些定制Linux发行版可能需要额外配置
4. **自启动设置**：确保系统允许Python脚本自启动运行

## 许可证

本项目采用MIT许可证。

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进TimeLock。

## 联系方式

如有任何问题或建议，请通过项目仓库提交反馈。