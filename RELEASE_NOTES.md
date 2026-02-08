# 发行注记
## 版本: 1.2.1
### 日期: 2026-02-09

### 新增功能
- 改进了Windows锁定监控，现在能够持续检测并重新锁定系统
- 添加了release目录用于存放发布版本文件

### 修改内容
1. **point_locker.pyw**:
   - 重构了`is_system_locked()`方法，使用6种不同的检测方法
   - 添加了`monitor_lock()`方法，持续监控锁定状态
   - 实现了自动重新锁定功能，检测到解锁后立即重新锁定
   - 添加了锁定计数器，便于调试和追踪

2. **range_monitor.pyw**:
   - 修复了`is_time_in_ranges()`方法，正确处理跨午夜的时间范围（如23:53-00:59）
   - 改进了`start_lock()`方法，在启动新锁定进程前先终止旧进程
   - 简化了`monitor_loop()`方法，移除了复杂的跨夜锁定期判断
   - 统一了Windows和Linux平台的锁定监控逻辑

3. **.gitignore**:
   - 添加了`release/`目录，防止跟踪发布文件

### 修复的问题
- 修复了Windows平台无法再次锁定系统的问题
- 修复了跨午夜时间范围判断错误的问题
- 修复了锁定时间结束后继续锁定的问题
- 修复了多个锁定进程同时运行导致的冲突问题

### 技术改进
- 改进了Windows锁定检测的准确性，使用多种方法验证锁定状态
- 优化了进程管理，确保只有一个锁定进程在运行
- 简化了时间范围判断逻辑，提高代码可维护性
- 添加了详细的日志输出，便于调试和问题排查

---

## 版本: 1.2.0
### 日期: 2026-02-08

### 新增功能
- 在Linux平台上，不再锁定系统和屏幕，而是直接使用fullscreen_break.pyw进行全屏休息。
`lock_gnome.py`在运行时，只执行一次，而不是循环运行。

### 修改内容
1. **range_monitor.pyw**:
   - 添加了`linux_lock_executed`标志来跟踪Linux锁定是否已执行
   - 修改了`start_lock()`方法，确保Linux平台只执行一次锁定
   - 在`stop_lock()`方法中重置Linux锁定执行标志
   - 更新了`monitor_loop()`中的锁定逻辑，更好地处理跨夜锁定

2. **lock_gnome.py**:
   - 修改了主函数，现在接受倒计时分钟数作为参数
   - 添加了`run_fullscreen_break()`函数来启动fullscreen_break.pyw
   - 在Linux平台上，现在直接运行fullscreen_break.pyw而不是锁定屏幕

3. **main.pyw**:
   - 更新了`start_lock()`方法，现在传递倒计时参数给lock_gnome.py

### 修复的问题
- 解决了Linux平台上重复执行锁定程序的问题
- 改善了跨夜锁定期间的系统响应性

### 已知问题
- 在某些Linux发行版上，fullscreen_break.pyw可能需要额外的依赖项


