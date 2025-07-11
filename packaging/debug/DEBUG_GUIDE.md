# 小红书发布工具 - 调试版使用指南

## 🔍 调试版本说明

当您的打包程序运行时立即退出，无法看到错误信息时，调试版本可以帮助您找到问题所在。

调试版本的所有文件都在 `packaging/debug/` 目录中，与其他打包文件分开管理。

## 🚀 快速开始

### 1. 构建调试版本

在 `packaging/debug` 目录下运行：

```bash
# 进入调试目录
cd packaging/debug

# 运行构建脚本
# Windows
python build_debug.py

# macOS/Linux  
python3 build_debug.py
```

### 2. 运行调试版本

构建完成后，有两种运行方式：

**方式一：直接运行可执行文件**
```bash
# Windows（在 packaging/debug 目录中）
dist\XhsPublisherDebug.exe

# macOS
./dist/XhsPublisherDebug

# Linux
./dist/XhsPublisherDebug
```

**方式二：使用运行脚本（推荐）**
```bash
# Windows（在 packaging/debug 目录中）
run_debug.bat

# macOS/Linux
./run_debug.sh
```

## 📋 调试版本特性

### ✅ 详细的启动过程显示
- 逐步显示每个启动阶段
- 实时输出当前正在执行的操作
- 清晰的时间戳和日志级别

### ✅ 完整的环境检查
- **Python环境检查**：版本、路径、平台信息
- **系统路径检查**：Python路径、环境变量
- **依赖模块检查**：逐个验证每个必需的Python包
- **项目结构检查**：验证关键文件和目录是否存在
- **环境设置**：自动配置打包环境路径

### ✅ 详细的错误信息
- 完整的异常堆栈跟踪
- 明确的错误发生位置
- 具体的失败原因说明

### ✅ 控制台保持打开
- Windows上会暂停等待用户输入
- 确保您能看到所有错误信息
- 不会立即关闭控制台窗口

## 🔧 常见问题排查

### 问题1：依赖模块导入失败
**症状**：显示 "❌ 模块导入失败"
**解决方案**：
1. 检查是否安装了所有依赖：`pip install -r requirements.txt`
2. 确认Python版本 >= 3.8
3. 重新安装有问题的模块

### 问题2：项目结构文件缺失
**症状**：显示 "❌ 项目结构检查失败"
**解决方案**：
1. 确保在正确的项目目录下构建
2. 检查是否有必要的文件被意外删除
3. 重新下载完整的项目代码

### 问题3：Firefox浏览器问题
**症状**：显示 "❌ Firefox浏览器检查失败"
**解决方案**：
```bash
# 重新安装Playwright Firefox
playwright install firefox
```

### 问题4：路径问题
**症状**：显示路径相关错误
**解决方案**：
1. 检查文件路径是否包含中文或特殊字符
2. 尝试将项目移动到简单路径下（如 C:\projects\）
3. 确保有足够的磁盘空间

## 📊 调试输出示例

正常启动的调试输出应该类似：

```
============================================================
  小红书发布工具 - 调试启动
============================================================
[10:30:15] [INFO] 开始启动过程...
[10:30:15] [INFO] Windows平台，控制台将保持打开状态
[10:30:15] [INFO] 执行步骤: Python环境检查

============================================================
  Python环境检查
============================================================
[10:30:15] [INFO] Python版本: 3.11.0
[10:30:15] [INFO] Python可执行文件: C:\Python311\python.exe
[10:30:15] [INFO] 平台: win32
[10:30:15] [INFO] 当前工作目录: C:\project\packaging\debug
[10:30:15] [INFO] ✅ 运行在打包环境中
...
```

## 🐛 提交问题报告

如果调试版本仍然无法解决问题，请提供以下信息：

1. **完整的控制台输出**（从开始到结束）
2. **系统信息**：
   - 操作系统版本
   - Python版本
   - 安装的包版本
3. **错误重现步骤**
4. **项目文件结构**（如果可能的话）

## 📁 文件说明

调试版本的所有文件都在 `packaging/debug/` 目录中：

- `main_debug.py` - 调试版主程序
- `xhs_publisher_debug.spec` - 调试版PyInstaller配置
- `build_debug.py` - 调试版构建脚本
- `run_debug.bat/sh` - 运行脚本（构建后生成）
- `DEBUG_GUIDE.md` - 本使用指南

## 💡 小贴士

1. **保存输出**：您可以将控制台输出重定向到文件：
   ```bash
   # Windows（在 packaging/debug 目录中）
   dist\XhsPublisherDebug.exe > debug_output.txt 2>&1
   
   # macOS/Linux
   ./dist/XhsPublisherDebug > debug_output.txt 2>&1
   ```

2. **多次测试**：如果第一次运行失败，可以多试几次，有时是临时的环境问题。

3. **清理重建**：如果修改了代码，记得重新运行 `build_debug.py` 构建。

4. **环境隔离**：建议在虚拟环境中构建，避免系统环境的干扰。

## 🔄 从调试版本到正式版本

一旦通过调试版本找到并解决了问题，您可以：

1. 回到 `packaging` 目录，使用正常的构建脚本重新构建：
   ```bash
   cd ../  # 回到 packaging 目录
   python build_windows.py  # 或其他构建脚本
   ```

2. 或者修改现有的spec文件，添加必要的修复。

3. 确保在正式版本中也应用了相同的修复。

## 📂 目录结构

```
packaging/
├── debug/                          # 调试版本专用目录
│   ├── main_debug.py              # 调试版主程序
│   ├── xhs_publisher_debug.spec   # 调试版配置
│   ├── build_debug.py             # 调试版构建脚本
│   ├── DEBUG_GUIDE.md             # 使用指南
│   ├── dist/                      # 构建输出目录
│   └── run_debug.bat/sh           # 运行脚本（构建后生成）
├── 其他正常的打包文件...
└── ...
``` 