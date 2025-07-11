# 小红书定时发布工具 - 简单版

一个简单、稳定、易用的小红书定时发布工具。

## 🎯 特点

- **零死锁** - 使用QTimer + subprocess，避免复杂异步
- **易使用** - 直观的GUI界面，一键发布
- **稳定性** - 浏览器操作完全隔离在独立进程
- **定时发布** - 支持精确到分钟的定时发布
- **批量导入** - 支持Excel批量导入发布任务

## 🚀 快速开始

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装浏览器
playwright install firefox

# 4. 运行应用
python main.py
```

## 📋 功能清单

- ✅ 立即发布
- ✅ 定时发布  
- ✅ 任务管理
- ✅ 登录保持
- ✅ Excel导入
- ✅ 日志显示

## 🏗️ 架构

```
GUI (PyQt6) → QTimer调度 → subprocess → 独立发布脚本 → Firefox
```

## 📝 使用说明

1. **登录账号** - 首次使用需要登录小红书账号
2. **创建任务** - 输入标题、内容，选择图片
3. **设置时间** - 选择立即发布或定时发布
4. **监控执行** - 在任务列表中查看执行状态

## 🔧 系统要求

- Python 3.8+
- Firefox浏览器（自动安装）
- Windows/macOS/Linux

## 📄 许可证

MIT License