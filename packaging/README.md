# 小红书发布工具 - 打包环境

这个目录包含了将小红书发布工具打包为可执行文件的所有配置和资源。

## 📁 目录结构

```
packaging/
├── README.md                   # 本文件
├── build_requirements.txt      # 打包专用依赖
├── xhs_publisher.spec          # PyInstaller配置文件
├── build.py                   # 自动化打包脚本
├── app_config.py              # 应用配置适配器
├── firefox_portable/          # 便携版Firefox浏览器
│   ├── mac/                   # macOS版本
│   └── windows/               # Windows版本
├── resources/                 # 静态资源文件
│   ├── icons/                 # 应用图标
│   ├── images/                # 示例图片
│   └── configs/               # 默认配置
├── scripts/                   # 辅助脚本
│   ├── download_firefox.py    # Firefox下载脚本
│   └── path_detector.py       # 路径检测器
├── dist/                      # 构建输出目录
└── temp/                      # 临时文件目录
```

## 🚀 使用方法

### 1. 准备环境
```bash
cd packaging
python -m pip install -r build_requirements.txt
```

### 2. 下载Firefox
```bash
python scripts/download_firefox.py
```

### 3. 构建应用
```bash
# 构建macOS版本
python build.py --platform mac

# 构建Windows版本（在Windows环境下）
python build.py --platform windows

# 构建所有平台
python build.py --all
```

## 📦 输出文件

- **macOS**: `dist/XhsPublisher.app`
- **Windows**: `dist/XhsPublisher.exe`

## ⚠️ 注意事项

1. 此目录完全独立于开发环境，不会影响源代码
2. Firefox浏览器会被完整打包，文件较大（~250MB）
3. 首次构建需要下载Firefox，请确保网络连接
4. Windows版本需要在Windows环境下构建

## 🔧 技术细节

- 使用PyInstaller进行打包
- 集成便携版Firefox浏览器
- 支持跨平台打包（Mac/Windows）
- 自动处理依赖和资源文件
- 智能路径检测，适配打包后环境