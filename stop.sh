#!/bin/bash

# 停止应用脚本

echo "🛑 停止小红书定时发布工具..."

# 检查PID文件
if [ -f "app.pid" ]; then
    PID=$(cat app.pid)
    
    # 检查进程是否存在
    if ps -p $PID > /dev/null 2>&1; then
        echo "📋 找到进程 ID: $PID"
        echo "🔄 正在停止进程..."
        
        # 温柔地停止进程
        kill $PID
        
        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ 应用已停止"
                rm -f app.pid
                exit 0
            fi
            echo "⏳ 等待进程结束... ($i/10)"
            sleep 1
        done
        
        # 强制停止
        echo "💀 强制停止进程..."
        kill -9 $PID
        rm -f app.pid
        echo "✅ 应用已强制停止"
    else
        echo "⚠️ 进程不存在，清理PID文件"
        rm -f app.pid
    fi
else
    echo "📄 未找到PID文件，尝试查找Python进程..."
    
    # 查找相关Python进程
    PIDS=$(pgrep -f "python.*main.py")
    
    if [ -n "$PIDS" ]; then
        echo "📋 找到相关进程: $PIDS"
        echo "🔄 正在停止..."
        kill $PIDS
        sleep 2
        
        # 检查是否还有进程运行
        REMAINING=$(pgrep -f "python.*main.py")
        if [ -n "$REMAINING" ]; then
            echo "💀 强制停止残留进程..."
            kill -9 $REMAINING
        fi
        echo "✅ 相关进程已停止"
    else
        echo "⚠️ 未找到相关进程"
    fi
fi

echo "🏁 停止操作完成"