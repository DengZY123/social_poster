#!/bin/bash

# 小红书定时发布工具 - 简单版启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 小红书定时发布工具 - 简单版"
echo "================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi
echo "✅ Python 版本: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先复制或创建虚拟环境"
    echo "提示: 可以从xhs-scheduler项目复制虚拟环境"
    echo "命令: cp -r ../xhs-scheduler/venv ./venv"
    exit 1
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 检查并安装依赖
echo "📚 检查依赖包..."
# 检查是否存在PyQt6
if ! python -c "import PyQt6" 2>/dev/null; then
    echo "❌ PyQt6 未安装，请检查虚拟环境"
    exit 1
fi

# 检查是否存在ujson（xhs-simple特有依赖）
if ! python -c "import ujson" 2>/dev/null; then
    echo "📦 安装ujson依赖..."
    pip install ujson==5.10.0
    if [[ $? -ne 0 ]]; then
        echo "❌ 安装ujson失败"
        exit 1
    fi
    echo "✅ ujson安装完成"
fi

echo "✅ 依赖包检查完成"

# 检查并安装Playwright浏览器
echo "🌐 检查浏览器..."
if ! python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().firefox.launch(headless=True).close()" 2>/dev/null; then
    echo "📦 安装Firefox浏览器..."
    playwright install firefox
    if [[ $? -ne 0 ]]; then
        echo "❌ 安装Firefox浏览器失败"
        exit 1
    fi
    echo "✅ Firefox浏览器安装完成"
fi

# 创建必要目录
mkdir -p firefox_profile
mkdir -p logs

echo "🎯 启动应用..."
echo "================================="

# 根据参数决定启动方式
case "${1:-gui}" in
    "debug"|"d")
        echo "🔧 调试模式启动..."
        python main.py --debug
        ;;
    "headless"|"h")
        echo "👻 无头模式启动..."
        python main.py --headless
        ;;
    "background"|"bg")
        echo "🔄 后台模式启动..."
        nohup python main.py > logs/app.log 2>&1 &
        echo $! > app.pid
        echo "✅ 应用已在后台启动"
        echo "📋 进程ID: $(cat app.pid)"
        echo "📄 日志文件: logs/app.log"
        echo "🛑 停止应用: ./stop.sh"
        ;;
    "gui"|*)
        echo "🖥️ GUI模式启动..."
        python main.py
        ;;
esac

echo "👋 应用已退出"