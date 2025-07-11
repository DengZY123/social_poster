#!/bin/bash
# 构建带控制台输出的调试版本

echo "🖥️  构建控制台调试版本"
echo "此版本会显示终端窗口，方便查看所有调试信息"
echo "================================"

# 激活虚拟环境
source ../venv/bin/activate

# 运行构建
python build.py --console --no-clean

echo "================================"
echo "✅ 控制台版本构建完成"
echo "运行方式："
echo "  cd dist"
echo "  ./XhsPublisher.app/Contents/MacOS/XhsPublisher"
echo ""
echo "所有日志都会在终端中显示"