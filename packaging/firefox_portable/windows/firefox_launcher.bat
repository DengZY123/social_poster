@echo off
REM Windows Firefox启动器
REM 使用Playwright的Firefox

set SCRIPT_DIR=%~dp0
set PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\AppData\Local\ms-playwright

python -c "
import asyncio
from playwright.async_api import async_playwright

async def launch_firefox():
    playwright = await async_playwright().start()
    browser = await playwright.firefox.launch(headless=False)
    await asyncio.sleep(86400)
    await browser.close()
    await playwright.stop()

asyncio.run(launch_firefox())
"
