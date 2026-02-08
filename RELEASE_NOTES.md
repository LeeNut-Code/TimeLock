# 发行注记

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

### 下一步计划
- 添加更多的Linux桌面环境支持
- 实现更精细的媒体播放器控制
- 改进用户界面和体验