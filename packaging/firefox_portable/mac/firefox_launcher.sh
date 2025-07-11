#!/bin/bash
# macOS Firefox启动器
# 使用Playwright的Firefox

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright"

# 启动Firefox
exec python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def launch_firefox():
    playwright = await async_playwright().start()
    browser = await playwright.firefox.launch(headless=False)
    # 保持运行
    await asyncio.sleep(86400)  # 24小时
    await browser.close()
    await playwright.stop()

asyncio.run(launch_firefox())
"
