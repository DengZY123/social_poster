# 小红书发布工具 - Windows版本构建指南

## 🎯 概述

本指南将帮助您在Windows环境下构建小红书发布工具的可执行文件。

## 📋 系统要求

### 必需条件
- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 2GB 可用空间

### 推荐条件
- **内存**: 8GB+ RAM (构建过程需要大量内存)
- **磁盘空间**: 5GB+ 可用空间
- **网络**: 稳定的互联网连接 (下载依赖包)

## 🛠️ 环境准备

### 1. 安装Python

从 [Python官网](https://www.python.org/downloads/) 下载并安装Python 3.8+

**重要**: 安装时勾选 "Add Python to PATH"

### 2. 验证安装

打开命令提示符 (cmd) 或 PowerShell，运行：

```bash
python --version
pip --version
```

### 3. 创建虚拟环境 (推荐)

```bash
cd xhs-simple
python -m venv venv
venv\Scripts\activate
```

### 4. 安装依赖包

```bash
pip install -r requirements.txt
```

### 5. 安装Playwright浏览器

```bash
playwright install firefox
```

## 🔨 构建步骤

### 方法一: 使用批处理脚本 (推荐)

1. 打开命令提示符，导航到项目的 `packaging` 目录：
   ```bash
   cd packaging
   ```

2. 运行构建脚本：
   ```bash
   build_windows.bat
   ```

3. 等待构建完成，脚本会自动打开输出目录

### 方法二: 使用Python脚本

1. 打开命令提示符，导航到项目的 `packaging` 目录：
   ```bash
   cd packaging
   ```

2. 运行构建脚本：
   ```bash
   python build_windows.py
   ```

### 方法三: 手动构建

1. 导航到 `packaging` 目录：
   ```bash
   cd packaging
   ```

2. 运行PyInstaller：
   ```bash
   pyinstaller --clean --noconfirm xhs_publisher_windows.spec
   ```

## 📦 构建输出

构建成功后，您将在 `packaging/dist/` 目录中找到：

- `XhsPublisher.exe` - 主可执行文件
- `_internal/` - 依赖文件目录
  - `browsers/firefox/` - 内置Firefox浏览器
  - 其他依赖库和资源文件

## 🚀 运行应用

构建完成后，您可以：

1. **直接运行**: 双击 `XhsPublisher.exe`
2. **命令行运行**: 
   ```bash
   cd dist
   XhsPublisher.exe
   ```

## 📁 文件结构

```
packaging/
├── dist/                          # 构建输出目录
│   ├── XhsPublisher.exe          # 主可执行文件
│   └── _internal/                # 依赖文件
│       ├── browsers/firefox/     # 内置Firefox
│       └── ...                   # 其他依赖
├── build/                        # 构建临时文件
├── xhs_publisher_windows.spec    # Windows构建配置
├── build_windows.py              # Python构建脚本
├── build_windows.bat             # 批处理构建脚本
└── README_WINDOWS.md             # 本文档
```

## 🔧 常见问题

### 1. 构建失败："找不到模块"

**解决方案**:
- 确保已安装所有依赖: `pip install -r requirements.txt`
- 检查虚拟环境是否激活
- 重新安装PyInstaller: `pip install --upgrade PyInstaller`

### 2. 构建失败："内存不足"

**解决方案**:
- 关闭其他程序释放内存
- 增加虚拟内存大小
- 考虑使用更高配置的机器

### 3. 运行时错误："找不到Firefox"

**解决方案**:
- 确保已运行: `playwright install firefox`
- 检查构建日志中是否包含Firefox
- 重新构建应用

### 4. 应用启动缓慢

**原因**: 
- 首次启动需要解压内部文件
- 防病毒软件扫描

**解决方案**:
- 将应用目录添加到防病毒软件白名单
- 等待首次启动完成

### 5. 杀毒软件报毒

**原因**: 
- PyInstaller生成的可执行文件可能被误报
- 内置浏览器可能触发警告

**解决方案**:
- 添加到防病毒软件白名单
- 使用知名杀毒软件的在线扫描验证

## 🎯 优化建议

### 减小文件大小
- 移除不必要的依赖包
- 使用UPX压缩可执行文件 (可选)

### 提高启动速度
- 使用SSD存储
- 添加到防病毒软件白名单

### 分发建议
- 创建安装程序 (使用NSIS等工具)
- 数字签名可执行文件 (避免安全警告)

## 📞 技术支持

如果遇到问题，请：

1. 检查本文档的常见问题部分
2. 查看构建日志中的错误信息
3. 确保环境配置正确
4. 联系技术支持

## 📝 更新日志

- **v1.0.0**: 初始Windows版本
  - 支持Windows 10/11
  - 内置Firefox浏览器
  - 完整的GUI界面
  - 任务调度功能

---

**注意**: 构建过程可能需要10-30分钟，取决于您的硬件配置和网络速度。请耐心等待。 