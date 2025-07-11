# install_firefox.ps1
# XHS Publisher - Firefox Auto Install Script
# Encoding: UTF-8-BOM

# Set console output encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "XHS Publisher - Browser Install Helper" -ForegroundColor Cyan
Write-Host "小红书发布工具 - 浏览器安装助手" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function: Show Progress
function Show-Progress {
    param($Message)
    Write-Host "[Progress] $Message" -ForegroundColor Yellow
}

# Function: Show Success
function Show-Success {
    param($Message)
    Write-Host "[Success] $Message" -ForegroundColor Green
}

# Function: Show Error
function Show-Error {
    param($Message)
    Write-Host "[Error] $Message" -ForegroundColor Red
}

# Function: Show Warning
function Show-Warning {
    param($Message)
    Write-Host "[Warning] $Message" -ForegroundColor Yellow
}

try {
    # Step 1: Check Python
    Show-Progress "Checking Python installation... / 检查 Python 安装..."
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if ($pythonCmd) {
        $pythonVersion = & $pythonCmd.Name --version 2>&1
        Show-Success "Python installed: $pythonVersion / Python 已安装: $pythonVersion"
    } else {
        Show-Error "Python not found. Please install Python first / 未找到 Python，请先安装 Python"
        Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Blue
        Read-Host "Press Enter to exit / 按 Enter 键退出"
        exit 1
    }
    
    # Step 2: Install playwright
    Write-Host ""
    Show-Progress "Installing Playwright... / 安装 Playwright..."
    & $pythonCmd.Name -m pip install playwright --upgrade
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Playwright installation failed / Playwright 安装失败"
        Read-Host "Press Enter to exit / 按 Enter 键退出"
        exit 1
    }
    Show-Success "Playwright installed successfully / Playwright 安装成功"
    
    # Step 3: Install Firefox
    Write-Host ""
    Show-Progress "Installing Firefox browser (this may take a few minutes)... / 安装 Firefox 浏览器（这可能需要几分钟）..."
    & $pythonCmd.Name -m playwright install firefox
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Firefox installation failed / Firefox 安装失败"
        Show-Warning "Possible reasons / 可能的原因："
        Write-Host "  - Network connection issues / 网络连接问题" -ForegroundColor Gray
        Write-Host "  - Firewall blocking download / 防火墙阻止下载" -ForegroundColor Gray
        Write-Host "  - Proxy settings issues / 代理设置问题" -ForegroundColor Gray
        Read-Host "Press Enter to exit / 按 Enter 键退出"
        exit 1
    }
    Show-Success "Firefox installed successfully / Firefox 安装成功"
    
    # Step 4: Find Firefox path
    Write-Host ""
    Show-Progress "Finding Firefox installation path... / 查找 Firefox 安装路径..."
    
    $playwrightPath = "$env:LOCALAPPDATA\ms-playwright"
    $firefoxPath = ""
    
    # Find the latest firefox directory
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
        Show-Error "Firefox executable not found / 未找到 Firefox 可执行文件"
        Write-Host "Please manually find Firefox installation path / 请手动查找 Firefox 安装路径" -ForegroundColor Yellow
        Read-Host "Press Enter to exit / 按 Enter 键退出"
        exit 1
    }
    
    Show-Success "Found Firefox: $firefoxPath / 找到 Firefox: $firefoxPath"
    
    # Step 5: Verify Firefox
    Write-Host ""
    Show-Progress "Verifying Firefox... / 验证 Firefox..."
    try {
        $versionOutput = & $firefoxPath --version 2>&1
        if ($versionOutput -match "Mozilla Firefox") {
            Show-Success "Firefox verified successfully / Firefox 验证成功"
        } else {
            Show-Warning "Firefox may not run properly, but configuration will continue / Firefox 可能无法正常运行，但配置将继续"
        }
    } catch {
        Show-Warning "Cannot verify Firefox version, but configuration will continue / 无法验证 Firefox 版本，但配置将继续"
    }
    
    # Step 6: Create config directory
    Write-Host ""
    Show-Progress "Creating config directory... / 创建配置目录..."
    
    $configDir = "$env:LOCALAPPDATA\XhsPublisher"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    Show-Success "Config directory created: $configDir / 配置目录已创建: $configDir"
    
    # Step 7: Save configuration
    Write-Host ""
    Show-Progress "Saving configuration files... / 保存配置文件..."
    
    # Create JSON configuration
    $config = @{
        firefox_path = $firefoxPath
        install_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        windows_version = [System.Environment]::OSVersion.VersionString
        playwright_path = $playwrightPath
    }
    
    $configJson = $config | ConvertTo-Json -Depth 10
    $configFile = Join-Path $configDir "browser_config.json"
    
    # Save JSON with UTF-8 encoding
    [System.IO.File]::WriteAllText($configFile, $configJson, [System.Text.Encoding]::UTF8)
    
    # Also save in simple text format (for compatibility)
    $txtFile = Join-Path $configDir "firefox_path.txt"
    [System.IO.File]::WriteAllText($txtFile, $firefoxPath, [System.Text.Encoding]::UTF8)
    
    Show-Success "Configuration files saved / 配置文件已保存"
    
    # Show installation summary
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installation Complete! / 安装完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[Info] Installation Details / 安装信息：" -ForegroundColor Cyan
    Write-Host "  Firefox path / Firefox 路径: " -NoNewline
    Write-Host $firefoxPath -ForegroundColor White
    Write-Host "  Config file / 配置文件: " -NoNewline
    Write-Host $configFile -ForegroundColor White
    Write-Host ""
    Write-Host "[Success] You can now start XHS Publisher! / 您现在可以启动小红书发布工具了！" -ForegroundColor Green
    Write-Host ""
    
    # Exit successfully
    exit 0
    
} catch {
    Show-Error "An error occurred during installation / 安装过程中发生错误: $_"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit / 按 Enter 键退出"
    exit 1
}