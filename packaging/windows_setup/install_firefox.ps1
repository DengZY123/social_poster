# install_firefox.ps1
# 小红书发布工具 - Firefox自动安装配置脚本
# 编码: UTF-8

# 设置控制台输出编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "小红书发布工具 - 浏览器安装助手" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 函数：显示进度
function Show-Progress {
    param($Message)
    Write-Host "► $Message" -ForegroundColor Yellow
}

# 函数：显示成功信息
function Show-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

# 函数：显示错误信息
function Show-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# 函数：显示警告信息
function Show-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

try {
    # 步骤1：检查Python
    Show-Progress "检查 Python 安装..."
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if ($pythonCmd) {
        $pythonVersion = & $pythonCmd.Name --version 2>&1
        Show-Success "Python 已安装: $pythonVersion"
    } else {
        Show-Error "未找到 Python，请先安装 Python"
        Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Blue
        Read-Host "按 Enter 键退出"
        exit 1
    }
    
    # 步骤2：安装 playwright
    Write-Host ""
    Show-Progress "安装 Playwright..."
    & $pythonCmd.Name -m pip install playwright --upgrade
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Playwright 安装失败"
        Read-Host "按 Enter 键退出"
        exit 1
    }
    Show-Success "Playwright 安装成功"
    
    # 步骤3：安装 Firefox
    Write-Host ""
    Show-Progress "安装 Firefox 浏览器（这可能需要几分钟）..."
    & $pythonCmd.Name -m playwright install firefox
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Firefox 安装失败"
        Show-Warning "可能的原因："
        Write-Host "  - 网络连接问题" -ForegroundColor Gray
        Write-Host "  - 防火墙阻止下载" -ForegroundColor Gray
        Write-Host "  - 代理设置问题" -ForegroundColor Gray
        Read-Host "按 Enter 键退出"
        exit 1
    }
    Show-Success "Firefox 安装成功"
    
    # 步骤4：查找 Firefox 路径
    Write-Host ""
    Show-Progress "查找 Firefox 安装路径..."
    
    $playwrightPath = "$env:LOCALAPPDATA\ms-playwright"
    $firefoxPath = ""
    
    # 查找最新的 firefox 目录
    $firefoxDirs = Get-ChildItem -Path $playwrightPath -Directory -Filter "firefox-*" -ErrorAction SilentlyContinue | Sort-Object Name -Descending
    
    if ($firefoxDirs) {
        foreach ($dir in $firefoxDirs) {
            $exePath = Join-Path $dir.FullName "firefox\firefox.exe"
            if (Test-Path $exePath) {
                $firefoxPath = $exePath
                break
            }
        }
    }
    
    if (-not $firefoxPath -or -not (Test-Path $firefoxPath)) {
        Show-Error "未找到 Firefox 可执行文件"
        Write-Host "请手动查找 Firefox 安装路径" -ForegroundColor Yellow
        Read-Host "按 Enter 键退出"
        exit 1
    }
    
    Show-Success "找到 Firefox: $firefoxPath"
    
    # 步骤5：验证 Firefox
    Write-Host ""
    Show-Progress "验证 Firefox..."
    try {
        $versionOutput = & $firefoxPath --version 2>&1
        if ($versionOutput -match "Mozilla Firefox") {
            Show-Success "Firefox 验证成功"
        } else {
            Show-Warning "Firefox 可能无法正常运行，但配置将继续"
        }
    } catch {
        Show-Warning "无法验证 Firefox 版本，但配置将继续"
    }
    
    # 步骤6：创建配置目录
    Write-Host ""
    Show-Progress "创建配置目录..."
    
    $configDir = "$env:LOCALAPPDATA\XhsPublisher"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    Show-Success "配置目录已创建: $configDir"
    
    # 步骤7：保存配置
    Write-Host ""
    Show-Progress "保存配置文件..."
    
    # 创建 JSON 配置
    $config = @{
        firefox_path = $firefoxPath
        install_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        windows_version = [System.Environment]::OSVersion.VersionString
        playwright_path = $playwrightPath
    }
    
    $configJson = $config | ConvertTo-Json -Depth 10
    $configFile = Join-Path $configDir "browser_config.json"
    
    # 使用 UTF-8 编码保存 JSON
    [System.IO.File]::WriteAllText($configFile, $configJson, [System.Text.Encoding]::UTF8)
    
    # 同时保存简单文本格式（兼容性）
    $txtFile = Join-Path $configDir "firefox_path.txt"
    [System.IO.File]::WriteAllText($txtFile, $firefoxPath, [System.Text.Encoding]::UTF8)
    
    Show-Success "配置文件已保存"
    
    # 显示安装摘要
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "安装完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 安装信息：" -ForegroundColor Cyan
    Write-Host "  Firefox 路径: " -NoNewline
    Write-Host $firefoxPath -ForegroundColor White
    Write-Host "  配置文件: " -NoNewline
    Write-Host $configFile -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 您现在可以启动小红书发布工具了！" -ForegroundColor Green
    Write-Host ""
    
    # 成功退出
    exit 0
    
} catch {
    Show-Error "安装过程中发生错误: $_"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "按 Enter 键退出"
    exit 1
}