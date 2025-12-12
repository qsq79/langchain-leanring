#!/bin/bash
# 一键安装项目依赖脚本

echo "=== 安装LangChain项目依赖 ==="
echo

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "当前Python版本: $python_version"

# 检查pip版本
pip_version=$(pip3 --version | awk '{print $2}')
echo "当前pip版本: $pip_version"

# 检查requirements.txt文件是否存在
requirements_file="src/app/langchain1.x/requirements.txt"
if [ ! -f "$requirements_file" ]; then
    echo "错误: 找不到文件 $requirements_file"
    exit 1
fi

echo
echo "即将安装 $requirements_file 中的所有依赖..."
echo

# 询问用户是否继续
read -p "是否继续安装? (y/n): " choice
if [ "$choice" != "y" ]; then
    echo "安装已取消"
    exit 0
fi

# 安装依赖
echo "正在安装依赖..."
pip3 install -r "$requirements_file"

# 检查安装结果
if [ $? -eq 0 ]; then
    echo
    echo "✅ 依赖安装成功!"
    echo
    echo "建议运行验证脚本检查安装结果:"
    echo "python3 validate_requirements.py"
else
    echo
    echo "❌ 依赖安装失败!"
    echo "请检查错误信息并尝试手动安装"
    exit 1
fi