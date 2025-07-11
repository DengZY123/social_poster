# install_firefox.ps1
# XHS Publisher - Firefox Auto Install Script
# Encoding: UTF-8-BOM

# Set console output encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "XHS Publisher - Browser Install Helper" -ForegroundColor Cyan
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
    Show-Progress "Checking Python installation..."
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if ($pythonCmd) {
        $pythonVersion = & $pythonCmd.Name --version 2>&1
        Show-Success "Python installed: $pythonVersion"
    } else {
        Show-Error "Python not found. Please install Python first"
        Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Blue
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Step 2: Install playwright
    Write-Host ""
    Show-Progress "Installing Playwright..."
    & $pythonCmd.Name -m pip install playwright --upgrade
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Playwright installation failed"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Show-Success "Playwright installed successfully"
    
    # Step 3: Install Firefox
    Write-Host ""
    Show-Progress "Installing Firefox browser (this may take a few minutes)..."
    & $pythonCmd.Name -m playwright install firefox
    if ($LASTEXITCODE -ne 0) {
        Show-Error "Firefox installation failed"
        Show-Warning "Possible reasons:"
        Write-Host "  - Network connection issues" -ForegroundColor Gray
        Write-Host "  - Firewall blocking download" -ForegroundColor Gray
        Write-Host "  - Proxy settings issues" -ForegroundColor Gray
        Read-Host "Press Enter to exit"
        exit 1
    }
    Show-Success "Firefox installed successfully"
    
    # Step 4: Find Firefox path
    Write-Host ""
    Show-Progress "Finding Firefox installation path..."
    
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
        Show-Error "Firefox executable not found"
        Write-Host "Please manually find Firefox installation path" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Show-Success "Found Firefox: $firefoxPath"
    
    # Step 5: Verify Firefox
    Write-Host ""
    Show-Progress "Verifying Firefox..."
    try {
        $versionOutput = & $firefoxPath --version 2>&1
        if ($versionOutput -match "Mozilla Firefox") {
            Show-Success "Firefox verified successfully"
        } else {
            Show-Warning "Firefox may not run properly, but configuration will continue"
        }
    } catch {
        Show-Warning "Cannot verify Firefox version, but configuration will continue"
    }
    
    # Step 6: Create config directory
    Write-Host ""
    Show-Progress "Creating config directory..."
    
    $configDir = "$env:LOCALAPPDATA\XhsPublisher"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    Show-Success "Config directory created: $configDir"
    
    # Step 7: Save configuration
    Write-Host ""
    Show-Progress "Saving configuration files..."
    
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
    
    Show-Success "Configuration files saved"
    
    # Show installation summary
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[Info] Installation Details:" -ForegroundColor Cyan
    Write-Host "  Firefox path: " -NoNewline
    Write-Host $firefoxPath -ForegroundColor White
    Write-Host "  Config file: " -NoNewline
    Write-Host $configFile -ForegroundColor White
    Write-Host ""
    Write-Host "[Success] You can now start XHS Publisher!" -ForegroundColor Green
    Write-Host ""
    
    # Exit successfully
    exit 0
    
} catch {
    Show-Error "An error occurred during installation: $_"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}