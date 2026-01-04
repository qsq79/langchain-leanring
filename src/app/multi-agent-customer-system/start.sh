#!/bin/bash

# 多智能体客服系统启动脚本

echo "========================================="
echo "  多智能体客服系统 (Multi-Agent)"
echo "  基于 AutoGen 框架"
echo "========================================="
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $python_version"

# 检查是否满足最低要求 (Python >= 3.8)
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ 错误: 需要 Python 3.8 或更高版本"
    exit 1
fi

echo "✅ Python 版本检查通过"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  警告: 未找到 .env 文件"
    echo "从 .env.example 复制配置文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑并添加你的 API 密钥"
    echo ""
    read -p "按回车键继续，或按 Ctrl+C 取消..."
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "检查并安装依赖..."
pip install -q -r requirements.txt
echo "✅ 依赖安装完成"

# 选择运行模式
echo ""
echo "请选择运行模式:"
echo "  1) CLI 交互模式 (默认)"
echo "  2) 命令行查询模式"
echo "  3) Web API 服务"
echo "  4) 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    2)
        echo ""
        read -p "请输入要查询的问题: " query
        if [ -n "$query" ]; then
            echo ""
            echo "执行查询..."
            echo ""
            python3 run.py -q "$query"
        else
            echo "❌ 错误: 查询问题不能为空"
        fi
        ;;
    3)
        echo ""
        echo "启动 Web API 服务..."
        echo "访问: http://localhost:${API_PORT:-8001}"
        echo "文档: http://localhost:${API_PORT:-8001}/docs"
        echo ""
        python3 src/api/server.py
        ;;
    4)
        echo "退出"
        exit 0
        ;;
    *)
        echo ""
        echo "启动 CLI 交互模式..."
        echo ""
        python3 run.py
        ;;
esac