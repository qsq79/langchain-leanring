# 项目环境配置指南

本文档详细说明如何配置 AutoGen 0.4+ 学习项目的开发环境。

## 目录

- [系统要求](#系统要求)
- [Python 环境配置](#python-环境配置)
- [虚拟环境创建](#虚拟环境创建)
- [依赖安装](#依赖安装)
- [环境变量配置](#环境变量配置)
- [IDE 配置建议](#ide-配置建议)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 系统要求

### 操作系统
- Linux (推荐 Ubuntu 20.04+)
- macOS 10.15+
- Windows 10/11 (WSL2 推荐)

### Python 版本
- **Python 3.10** 或更高版本
- 推荐使用 Python 3.11 或 3.12

### 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

如果版本低于 3.10，请先安装 Python 3.10+。

---

## Python 环境配置

### 方式 1: 使用 pyenv (推荐用于 macOS/Linux)

```bash
# 安装 pyenv
curl https://pyenv.run | bash

# 添加到 shell 配置 (~/.bashrc 或 ~/.zshrc)
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

# 安装 Python 3.11
pyenv install 3.11.7

# 设置本地 Python 版本
cd /path/to/autogen-learning
pyenv local 3.11.7
```

### 方式 2: 使用 conda

```bash
# 安装 Miniconda 或 Anaconda 后
conda create -n autogen python=3.11
conda activate autogen
```

### 方式 3: 官方安装包

从 [Python 官网](https://www.python.org/downloads/) 下载安装包。

---

## 虚拟环境创建

### 使用 venv (Python 内置)

```bash
# 进入项目目录
cd src/app/autogen-learning

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate

# Windows (CMD):
.venv\Scripts\activate.bat

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 使用 virtualenv

```bash
# 安装 virtualenv
pip install virtualenv

# 创建虚拟环境
virtualenv .venv

# 激活（同 venv）
source .venv/bin/activate
```

### 验证虚拟环境

激活后，命令行提示符前应显示 `(.venv)`：

```bash
(.venv) user@machine:~/autogen-learning$
```

---

## 依赖安装

### 基础安装

仅安装核心依赖：

```bash
# 确保虚拟环境已激活
pip install --upgrade pip

# 安装核心依赖
pip install -r requirements.txt
```

这将安装：
- `autogen-core` - Core API
- `autogen-agentchat` - AgentChat API
- `autogen-ext[openai]` - OpenAI 扩展

### 完整安装

安装所有可选依赖：

```bash
pip install -r requirements-full.txt
```

这将额外安装：
- Azure OpenAI 支持
- Anthropic Claude 支持
- Docker 代码执行
- 向量数据库 (ChromaDB)
- 可观测性工具 (OpenTelemetry)

### 开发环境安装

安装开发工具：

```bash
pip install -e ".[dev]"
```

或使用 pyproject.toml：

```bash
pip install -e ".[dev,all]"
```

---

## 环境变量配置

### 1. 创建环境变量文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

### 2. 配置必需变量

**最低配置**（使用 OpenAI）：

```bash
# 你的 OpenAI API Key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**获取 API Key**:
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 登录或注册账号
3. 创建新的 API Key
4. 复制 key 并粘贴到 `.env` 文件

### 3. 可选配置

**使用 Azure OpenAI**:

```bash
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

**使用 Anthropic Claude**:

```bash
ANTHROPIC_API_KEY=your-anthropic-key
```

**日志配置**:

```bash
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=console    # console, json
```

### 4. 验证环境变量

```bash
# Linux/macOS
echo $OPENAI_API_KEY

# Windows (PowerShell)
echo $Env:OPENAI_API_KEY
```

---

## IDE 配置建议

### VS Code

**推荐扩展**:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    "tamasfe.even-better-toml",
    "editorconfig.editorconfig"
  ]
}
```

**设置** (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### PyCharm

1. **打开项目**: File → Open → 选择项目目录
2. **配置解释器**:
   - File → Settings → Project → Python Interpreter
   - Add → Existing environment
   - 选择 `.venv/bin/python`
3. **启用 pytest**:
   - Settings → Tools → Python Integrated Tools
   - Default test runner: pytest

### Vim/Neovim

**配置示例** (使用 `vim-plug`):

```vim
" Python 支持
Plug 'davidhalter/jedi-vim'
Plug 'psf/black'

" LSP
Plug 'neovim/nvim-lspconfig'
Plug 'nvim-treesitter/nvim-treesitter'

" 调试
Plug 'mfussenegger/nvim-dap'
```

---

## 验证安装

### 1. 验证 Python 和依赖

```bash
# 检查 Python 版本
python --version

# 检查已安装的包
pip list | grep autogen

# 应该看到:
# autogen-agentchat
# autogen-core
# autogen-ext
```

### 2. 运行快速测试

创建测试文件 `test_env.py`:

```python
"""测试环境配置"""
import sys
import os
from dotenv import load_dotenv

def test_python_version():
    """测试 Python 版本"""
    assert sys.version_info >= (3, 10), "Python 3.10+ required"
    print(f"✓ Python version: {sys.version}")

def test_autogen_import():
    """测试 AutoGen 导入"""
    try:
        import autogen_core
        import autogen_agentchat
        print("✓ AutoGen imports successful")
    except ImportError as e:
        print(f"✗ AutoGen import failed: {e}")
        raise

def test_env_vars():
    """测试环境变量"""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✓ OPENAI_API_KEY is set")
    else:
        print("⚠ OPENAI_API_KEY not set (optional for some demos)")

if __name__ == "__main__":
    test_python_version()
    test_autogen_import()
    test_env_vars()
    print("\n✓ Environment check passed!")
```

运行测试：

```bash
python test_env.py
```

### 3. 运行第一个 Demo

```bash
python 01-core/concepts/demo_01_quickstart.py
```

如果看到输出且无错误，说明环境配置成功！

---

## 常见问题

### Q1: pip 安装失败

**问题**: `error: Microsoft Visual C++ 14.0 is required`

**解决** (Windows):
1. 安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 或使用预编译的 wheel 文件

### Q2: ModuleNotFoundError: No module named 'autogen_core'

**原因**: 虚拟环境未激活或安装到错误的位置

**解决**:
```bash
# 确认虚拟环境已激活
which python  # 应该指向 .venv/bin/python

# 重新安装
pip install -r requirements.txt
```

### Q3: OpenAI API Key 无效

**错误**: `AuthenticationError: Incorrect API key provided`

**解决**:
1. 确认 API Key 正确（无多余空格）
2. 检查 `.env` 文件是否在同一目录
3. 确认账户有余额

### Q4: asyncio 错误

**错误**: `RuntimeError: asyncio.run() cannot be called from a running event loop`

**解决**: Jupyter Notebook 中使用：
```python
import nest_asyncio
nest_asyncio.apply()
```

### Q5: Docker 相关错误

**错误**: `Cannot connect to Docker daemon`

**解决**:
```bash
# 启动 Docker 服务
sudo systemctl start docker  # Linux
# 或在 Docker Desktop 中启动 (Windows/macOS)
```

---

## 下一步

环境配置完成后：

1. 阅读 [架构总览](./01-architecture-overview.md)
2. 查看 [学习路径](./02-learning-path.md)
3. 运行第一个示例：`python 01-core/concepts/demo_01_quickstart.py`

祝你学习愉快！🚀
