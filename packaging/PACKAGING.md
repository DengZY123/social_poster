# 小红书发布工具打包指南

## 概述

本文档详细说明了如何将小红书发布工具打包成独立的可执行应用，包括内嵌 Firefox 浏览器的完整解决方案。

## 打包方案对比

### 1. PyInstaller（推荐）
- **优点**：成熟稳定，支持跨平台，可以生成单文件或目录形式
- **缺点**：打包体积较大
- **适用场景**：生产环境发布

### 2. Nuitka
- **优点**：性能更好，可以编译成真正的二进制代码
- **缺点**：配置复杂，跨平台支持有限
- **适用场景**：需要高性能的场景

## 快速开始

### 1. 准备环境

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装打包依赖
pip install -r requirements.txt
pip install PyInstaller>=6.0.0

# 确保 Firefox 已安装
playwright install firefox
```

### 2. 执行打包

```bash
# 使用自动化脚本
cd packaging
./build.sh

# 或者手动执行
python build.py
```

### 3. 测试打包结果

```bash
# macOS
open dist/XhsPublisher.app

# Windows
dist\XhsPublisher.exe

# Linux
./dist/XhsPublisher
```

## 内嵌浏览器方案

### 工作原理

1. **动态检测**：使用 `firefox_finder.py` 自动查找系统中的 Playwright Firefox
2. **智能打包**：将整个 Firefox 应用打包到 `browsers/firefox` 目录
3. **运行时加载**：应用启动时优先使用内置浏览器，失败时回退到系统浏览器

### 关键文件

- `firefox_finder.py`：动态查找 Firefox 路径
- `path_detector.py`：运行时路径检测和管理
- `xhs_publisher.spec`：PyInstaller 配置文件
- `app_config.py`：打包环境配置适配

### 浏览器路径映射

```
开发环境：
~/Library/Caches/ms-playwright/firefox-1488/firefox/
    ↓
打包后：
XhsPublisher.app/Contents/MacOS/browsers/firefox/
```

## 常见问题

### 1. 浏览器找不到

**问题**：打包后提示 "Executable doesn't exist"

**解决方案**：
1. 确保打包前已安装 Firefox：`playwright install firefox`
2. 检查打包日志是否包含 Firefox
3. 验证打包后的目录结构

### 2. 打包体积过大

**问题**：打包后的应用超过 200MB

**原因**：
- Firefox 浏览器本身约 120MB
- PyQt6 和其他依赖约 80MB

**优化方案**：
1. 使用 UPX 压缩（已在配置中启用）
2. 排除不必要的模块（见 `excludes` 配置）
3. 考虑使用在线下载浏览器的方案

### 3. 权限问题

**问题**：macOS 提示应用来自未识别的开发者

**解决方案**：
```bash
# 移除隔离属性
xattr -cr /Applications/XhsPublisher.app

# 或者在系统偏好设置中允许
```

### 4. 路径问题

**问题**：找不到配置文件或日志文件

**解决方案**：
打包后的应用使用用户目录存储数据：
- macOS: `~/Library/Application Support/XhsPublisher/`
- Windows: `%APPDATA%\XhsPublisher\`
- Linux: `~/.config/XhsPublisher/`

## 高级配置

### 自定义打包选项

编辑 `xhs_publisher.spec` 文件：

```python
# 添加图标
icon='path/to/icon.icns',  # macOS
icon='path/to/icon.ico',   # Windows

# 修改应用信息
info_plist={
    'CFBundleIdentifier': 'com.yourcompany.xhspublisher',
    'CFBundleVersion': '1.0.1',
}
```

### 多平台打包

```bash
# 为 Windows 打包（需要在 Windows 或使用 Wine）
python build_nuitka.py

# 为不同架构打包
--target-arch=x86_64  # Intel
--target-arch=arm64   # Apple Silicon
```

### 签名和公证（macOS）

```bash
# 签名应用
codesign --deep --force --verify --sign "Developer ID Application: Your Name" XhsPublisher.app

# 公证应用
xcrun altool --notarize-app --file XhsPublisher.zip
```

## 调试技巧

### 1. 查看打包日志

```bash
# 使用 --debug 选项
python build.py --debug

# 查看 PyInstaller 详细输出
pyinstaller --debug all xhs_publisher.spec
```

### 2. 测试路径检测

```bash
# 在打包前测试路径检测
python packaging/scripts/path_detector.py

# 测试 Firefox 查找
python packaging/firefox_finder.py
```

### 3. 验证打包内容

```bash
# 查看打包后的文件结构
tree dist/XhsPublisher.app/Contents/

# 检查是否包含 Firefox
ls -la dist/XhsPublisher.app/Contents/MacOS/browsers/firefox/
```

## 发布清单

打包发布前的检查清单：

- [ ] 更新版本号（`PROJECT_VERSION`）
- [ ] 清理测试数据和日志
- [ ] 运行完整测试
- [ ] 检查所有依赖版本
- [ ] 构建不同平台版本
- [ ] 测试打包后的应用
- [ ] 准备发布说明
- [ ] 创建安装包（可选）

## 持续改进

### 计划中的优化

1. **减小体积**：研究按需下载浏览器的方案
2. **自动更新**：集成自动更新机制
3. **安装程序**：创建专业的安装向导
4. **代码签名**：自动化签名流程

### 贡献指南

欢迎提交改进建议和问题报告。打包相关的代码主要在 `packaging/` 目录下。

## 参考资源

- [PyInstaller 文档](https://pyinstaller.org/)
- [Playwright 浏览器管理](https://playwright.dev/docs/browsers)
- [macOS 代码签名](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows 代码签名](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)