# 🔍 调试功能说明

## 问题：打包程序运行后立即退出？

如果您的打包程序运行时立即退出，无法看到错误信息，请使用我们的**调试版本**来排查问题。

## 🚀 快速使用调试版本

### 1. 进入调试目录
```bash
cd packaging/debug
```

### 2. 构建调试版本
```bash
# Windows
python build_debug.py

# macOS/Linux
python3 build_debug.py
```

### 3. 运行调试版本
```bash
# Windows
run_debug.bat

# macOS/Linux
./run_debug.sh
```

## ✨ 调试版本特性

- ✅ **详细启动日志** - 逐步显示启动过程
- ✅ **依赖检查** - 验证所有Python模块
- ✅ **路径验证** - 检查文件和目录
- ✅ **错误详情** - 完整的错误堆栈信息
- ✅ **控制台保持打开** - 不会闪退

## 📋 详细说明

请查看 `debug/DEBUG_GUIDE.md` 获取完整的使用指南。

## 📂 文件组织

```
packaging/
├── debug/                    # 🔍 调试版本（专用目录）
│   ├── build_debug.py       # 构建脚本
│   ├── main_debug.py        # 调试主程序
│   └── DEBUG_GUIDE.md       # 详细指南
├── build_windows.py         # 正常构建脚本
├── xhs_publisher.spec       # 正常配置文件
└── ...                      # 其他打包文件
```

调试版本的所有文件都在 `debug/` 目录中，与正常的打包文件分开管理，避免混淆。 