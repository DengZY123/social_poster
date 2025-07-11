# Windows 打包和安装完整指南

## 一、开发环境打包流程

### 1. 环境准备

```bash
# 1.1 安装Python 3.8+
# 下载地址: https://www.python.org/downloads/
# 安装时勾选 "Add Python to PATH"

# 1.2 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 1.3 安装依赖
cd packaging
pip install -r requirements_windows.txt

# 1.4 安装Playwright Firefox（可选，用户可以后续安装）
playwright install firefox
```

### 2. 执行打包

```bash
# 2.1 进入packaging目录
cd packaging

# 2.2 运行打包脚本
build_windows.bat

# 或者直接运行Python脚本
python build_windows.py
```

### 3. 打包结果

打包完成后，会在 `packaging/dist/` 目录生成：
```
dist/
├── XhsPublisher.exe         # 主程序
└── _internal/              # 依赖文件（PyInstaller 6.0+）
    ├── *.dll               # 系统库
    ├── *.pyd               # Python扩展
    └── ...                 # 其他依赖
```

## 二、用户安装流程

### 方案A：单文件分发（推荐）

1. **准备分发包**
   ```
   XhsPublisher/
   ├── XhsPublisher.exe     # 从dist目录复制
   ├── _internal/           # 从dist目录复制（整个文件夹）
   └── windows_setup/       # Firefox安装脚本
       ├── install.bat
       ├── install_firefox.ps1
       └── 使用说明.txt
   ```

2. **用户安装步骤**
   - 步骤1：解压分发包到任意目录（如 `C:\Program Files\XhsPublisher\`）
   - 步骤2：运行 `windows_setup\install.bat` 安装Firefox
   - 步骤3：双击 `XhsPublisher.exe` 启动程序

### 方案B：创建安装程序

使用 NSIS (Nullsoft Scriptable Install System) 创建安装程序：

1. **安装NSIS**
   - 下载地址: https://nsis.sourceforge.io/Download

2. **创建安装脚本** `installer.nsi`：
   ```nsis
   ; 小红书发布工具安装程序
   !define PRODUCT_NAME "小红书发布工具"
   !define PRODUCT_VERSION "1.0.0"
   !define PRODUCT_PUBLISHER "Your Company"
   
   ; 安装程序基本设置
   Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
   OutFile "XhsPublisher_Setup.exe"
   InstallDir "$PROGRAMFILES\XhsPublisher"
   RequestExecutionLevel admin
   
   ; 安装页面
   !include "MUI2.nsh"
   !insertmacro MUI_PAGE_WELCOME
   !insertmacro MUI_PAGE_DIRECTORY
   !insertmacro MUI_PAGE_INSTFILES
   !insertmacro MUI_PAGE_FINISH
   !insertmacro MUI_LANGUAGE "SimpChinese"
   
   ; 安装内容
   Section "MainSection" SEC01
     SetOutPath "$INSTDIR"
     
     ; 复制程序文件
     File /r "dist\*.*"
     File /r "windows_setup"
     
     ; 创建开始菜单快捷方式
     CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
     CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\XhsPublisher.exe"
     CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\安装Firefox浏览器.lnk" "$INSTDIR\windows_setup\install.bat"
     CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\uninstall.exe"
     
     ; 创建桌面快捷方式
     CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\XhsPublisher.exe"
     
     ; 写入卸载信息
     WriteUninstaller "$INSTDIR\uninstall.exe"
     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
   SectionEnd
   
   ; 卸载程序
   Section "Uninstall"
     Delete "$INSTDIR\*.*"
     RMDir /r "$INSTDIR"
     Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
     RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
     DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
   SectionEnd
   ```

3. **生成安装程序**
   ```bash
   makensis installer.nsi
   ```

## 三、首次运行配置

### 1. Firefox浏览器安装

用户首次运行时，如果没有安装Firefox：
1. 程序会提示"浏览器未安装"
2. 用户运行 `windows_setup\install.bat`
3. 脚本自动安装Firefox并保存路径到配置文件
4. 重新启动程序即可使用

### 2. 配置文件位置

- Firefox路径配置：`%LOCALAPPDATA%\XhsPublisher\browser_config.json`
- 任务数据：`%LOCALAPPDATA%\XhsPublisher\tasks.json`
- 日志文件：`%LOCALAPPDATA%\XhsPublisher\logs\app.log`

## 四、故障排除

### 常见问题

1. **"缺少VCRUNTIME140.dll"错误**
   - 安装 Visual C++ Redistributable
   - 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe

2. **"Windows已保护你的电脑"提示**
   - 点击"更多信息"
   - 选择"仍要运行"

3. **Firefox安装失败**
   - 检查网络连接
   - 检查代理设置
   - 手动安装playwright：`pip install playwright && playwright install firefox`

4. **程序启动后立即退出**
   - 查看日志文件：`%LOCALAPPDATA%\XhsPublisher\logs\app.log`
   - 确保Firefox已正确安装

## 五、批量部署

对于企业批量部署：

1. **预安装Firefox**
   ```batch
   :: 静默安装脚本
   @echo off
   python -m pip install playwright
   python -m playwright install firefox
   ```

2. **预配置路径**
   创建配置文件 `%LOCALAPPDATA%\XhsPublisher\browser_config.json`：
   ```json
   {
     "firefox_path": "C:\\Users\\%USERNAME%\\AppData\\Local\\ms-playwright\\firefox-1488\\firefox\\firefox.exe",
     "install_date": "2024-01-01 00:00:00"
   }
   ```

3. **静默安装**
   ```batch
   XhsPublisher_Setup.exe /S
   ```

## 六、更新升级

1. **手动更新**
   - 下载新版本
   - 替换exe和_internal文件夹
   - 保留配置文件

2. **自动更新**（需要额外开发）
   - 可以集成自动更新功能
   - 检查版本并下载更新包

## 七、完整打包检查清单

- [ ] Python 3.8+ 已安装
- [ ] 所有依赖包已安装
- [ ] PyInstaller 正确配置
- [ ] 打包生成exe文件
- [ ] Firefox安装脚本正常工作
- [ ] 程序可以正常启动
- [ ] 配置文件正确保存和读取
- [ ] 日志文件正常生成
- [ ] 快捷方式创建成功（如果使用安装程序）