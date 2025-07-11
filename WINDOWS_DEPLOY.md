# Windows部署指南

## 必需文件清单

在Windows上拉取代码时，packaging目录中只需要以下文件：

### 核心文件
```
packaging/
├── xhs_publisher_windows.spec    # Windows PyInstaller配置
├── build_windows.bat             # 打包批处理脚本
├── build_windows.py              # 打包Python脚本
├── requirements_windows.txt      # Windows依赖
├── main_packaged.py             # 打包入口文件
├── app_config.py                # 应用配置适配器
├── __init__.py                  # Python包标识
├── windows_setup/               # Windows安装脚本目录（完整保留）
│   ├── install.bat
│   ├── install_firefox.ps1
│   ├── test_config.py
│   └── 使用说明.txt
├── resources/                   # 资源文件目录（完整保留）
│   ├── icons/
│   └── images/
└── scripts/                     # 必需的脚本
    ├── __init__.py
    └── path_detector.py
```

## 快速部署步骤

1. **拉取代码时排除不需要的文件**
   ```bash
   # 使用稀疏检出
   git clone --no-checkout https://github.com/your-repo/xhs-simple.git
   cd xhs-simple
   git sparse-checkout init --cone
   git sparse-checkout set --no-cone '/*' '!/packaging/*.md' '!/packaging/build.sh' '!/packaging/firefox_portable/mac'
   git checkout
   ```

2. **或者拉取后手动清理**
   ```bash
   # 删除不需要的文件
   del packaging\*.md
   del packaging\build.sh
   del packaging\build_console.sh
   rmdir /s /q packaging\firefox_portable\mac
   del packaging\xhs_publisher.spec
   del packaging\xhs_publisher_console.spec
   ```

3. **安装依赖并打包**
   ```bash
   cd packaging
   build_windows.bat
   ```

## 最小化部署

如果想要最精简的部署，可以只保留这些关键文件：
- `xhs_publisher_windows.spec`
- `build_windows.bat`
- `main_packaged.py`
- `app_config.py`
- `windows_setup/` (整个目录)
- `scripts/path_detector.py`

其他文件都可以在需要时再添加。