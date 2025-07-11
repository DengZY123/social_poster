# Test script to check PowerShell syntax
# Run this first to ensure the main script has no syntax errors

try {
    Write-Host "Testing PowerShell script syntax..." -ForegroundColor Cyan
    
    $scriptPath = Join-Path $PSScriptRoot "install_firefox.ps1"
    
    if (Test-Path $scriptPath) {
        # Parse the script to check for syntax errors
        $errors = $null
        $tokens = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$tokens, [ref]$errors)
        
        if ($errors.Count -eq 0) {
            Write-Host "[OK] Script syntax is valid!" -ForegroundColor Green
            Write-Host "You can safely run install.bat" -ForegroundColor Green
        } else {
            Write-Host "[Error] Script has syntax errors:" -ForegroundColor Red
            foreach ($error in $errors) {
                Write-Host "  Line $($error.Extent.StartLineNumber): $($error.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "[Error] Script not found: $scriptPath" -ForegroundColor Red
    }
} catch {
    Write-Host "[Error] Failed to test script: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"