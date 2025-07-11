# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

小红书定时发布工具 - 简单版，一个用于小红书平台的定时发布工具。

## 核心架构

项目采用分层架构，组件完全隔离：

```
GUI (PyQt6) → QTimer调度 → subprocess → 独立发布脚本 → Firefox
```

- **GUI层**: PyQt6界面，负责用户交互
- **调度层**: 使用QTimer进行定时任务调度，避免复杂异步
- **执行层**: 通过subprocess启动独立发布脚本，完全隔离浏览器操作
- **存储层**: JSON文件存储任务和配置

## 开发命令

### 环境设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装浏览器
playwright install firefox
```

### 运行应用
```bash
# 启动应用（推荐）
./start.sh

# 或直接运行
python main.py

# 调试模式
python main.py --debug
./start.sh debug

# 无头模式
python main.py --headless
./start.sh headless

# 后台运行
./start.sh background
```

### 停止应用
```bash
# 停止后台运行的应用
./stop.sh
```

## 核心模块

### core/models.py
- `PublishTask`: 发布任务数据模型
- `TaskStatus`: 任务状态枚举
- `AppConfig`: 应用配置
- `PublishResult`: 发布结果

### core/scheduler.py
- `SimpleScheduler`: 简单任务调度器
- 使用QTimer进行定时检查
- 通过subprocess执行独立发布脚本

### core/publisher.py
- 独立发布脚本，使用Playwright操作浏览器
- 完全隔离在独立进程中运行

### core/storage.py
- `TaskStorage`: 任务存储管理
- `ConfigStorage`: 配置存储管理
- 基于JSON文件存储

### gui/main_window.py
- 主窗口界面
- 任务创建、管理和监控

## 关键设计原则

1. **零死锁**: 使用QTimer + subprocess，避免GUI线程阻塞
2. **进程隔离**: 浏览器操作完全在独立进程中
3. **简单稳定**: 避免复杂的异步编程
4. **资源管理**: 自动清理旧任务，管理浏览器profiles

## 配置文件

- `tasks.json`: 任务数据存储
- `config.json`: 应用配置
- `firefox_profile/`: Firefox浏览器配置文件夹

## 日志系统

- 控制台日志: INFO级别，彩色输出
- 文件日志: `app.log`，DEBUG级别，自动轮转
- 后台运行日志: `logs/app.log`

## 测试和调试

```bash
# 调试模式启动
python main.py --debug

# 检查进程状态
ps aux | grep python
```

## 注意事项

1. 浏览器操作必须在独立进程中执行
2. 任务状态更新需要通过信号机制
3. 发布间隔限制（默认5分钟）
4. 超时处理（默认5分钟）
5. 重试机制（最大3次）

## 依赖关系

- PyQt6: GUI框架
- playwright: 浏览器自动化
- pandas/openpyxl: Excel处理
- loguru: 日志系统
- pydantic: 数据验证

## 扩展开发

添加新功能时：
1. 保持核心设计原则（进程隔离、简单调度）
2. 使用PyQt6信号机制进行组件通信
3. 新的浏览器操作放在publisher.py中
4. 配置项添加到AppConfig模型中