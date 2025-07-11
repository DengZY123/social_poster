#!/bin/bash
# -*- coding: utf-8 -*-
"""
小红书发布工具打包脚本
支持自动检测和包含 Firefox 浏览器
"""

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印彩色信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查虚拟环境
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_error "未检测到虚拟环境，请先激活虚拟环境"
        print_info "运行: source venv/bin/activate"
        exit 1
    else
        print_info "虚拟环境: $VIRTUAL_ENV"
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 PyInstaller
    if ! python -m PyInstaller --version &> /dev/null; then
        print_warning "PyInstaller 未安装，正在安装..."
        pip install PyInstaller>=6.0.0
    fi
    
    # 检查 Playwright
    if ! python -c "import playwright" &> /dev/null; then
        print_error "Playwright 未安装"
        exit 1
    fi
    
    print_info "依赖检查完成"
}

# 清理旧的构建
clean_build() {
    print_info "清理旧的构建目录..."
    rm -rf dist build *.spec
    print_info "清理完成"
}

# 执行打包
run_build() {
    print_info "开始打包..."
    
    # 切换到 packaging 目录
    cd "$(dirname "$0")"
    
    # 运行打包脚本
    python build.py
    
    if [ $? -eq 0 ]; then
        print_info "打包成功！"
        
        # 显示输出文件
        if [ -d "dist" ]; then
            print_info "输出文件："
            ls -la dist/
        fi
    else
        print_error "打包失败！"
        exit 1
    fi
}

# 主流程
main() {
    echo "🚀 小红书发布工具打包脚本"
    echo "================================"
    
    # 检查虚拟环境
    check_venv
    
    # 检查依赖
    check_dependencies
    
    # 清理旧构建
    if [[ "$1" == "--clean" ]]; then
        clean_build
    fi
    
    # 执行打包
    run_build
    
    echo "================================"
    echo "✅ 打包流程完成"
}

# 运行主流程
main "$@"