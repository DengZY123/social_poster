XHS Publisher - Firefox Browser Installation Guide
==================================================

1. INSTALLATION STEPS

   1.1. Double-click "install.bat" to run
        - If prompted for administrator privileges, right-click and select "Run as administrator"

   1.2. Wait for installation to complete
        - The script will automatically install necessary components
        - The process takes about 3-5 minutes

   1.3. After successful installation
        - You will see "Installation Complete!" message
        - Firefox path will be saved to configuration file automatically


2. PREREQUISITES

   2.1. Python must be installed
        - If not installed, visit https://www.python.org/downloads/
        - During installation, check "Add Python to PATH"

   2.2. Internet connection required
        - The installer needs to download Firefox browser
        - If behind a corporate proxy, configure proxy settings first


3. FILE LOCATIONS

   - Firefox browser: %LOCALAPPDATA%\ms-playwright\firefox-*\firefox\firefox.exe
   - Configuration file: %LOCALAPPDATA%\XhsPublisher\browser_config.json
   - Firefox path (text): %LOCALAPPDATA%\XhsPublisher\firefox_path.txt


4. TROUBLESHOOTING

   Q: "Python not found" error?
   A: Install Python first, then run the installer again

   Q: Installation interrupted?
   A: Simply run install.bat again, it will handle the situation

   Q: How to view configuration files?
   A: Press Win+R, type %LOCALAPPDATA%\XhsPublisher and press Enter

   Q: Need to manually edit Firefox path?
   A: Edit the file %LOCALAPPDATA%\XhsPublisher\firefox_path.txt


5. TECHNICAL SUPPORT

   If you encounter issues, please provide:
   - Error screenshots
   - Windows version
   - Python version