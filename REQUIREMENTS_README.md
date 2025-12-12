# 项目依赖管理说明

本项目已将所有子目录的依赖整合到 [`src/app/langchain1.x/requirements.txt`](src/app/langchain1.x/requirements.txt) 文件中，便于统一管理。

## 依赖结构

`src/app/langchain1.x/requirements.txt` 文件按功能分类组织依赖：

1. **LangChain核心依赖** - 所有模块共用
2. **数值计算和科学计算** - 包括numpy和scikit-learn
3. **HTTP请求和异步支持** - 包括requests和aiohttp
4. **数据处理** - 包括pandas和pydantic
5. **向量数据库和搜索** - 包括faiss-cpu和chromadb
6. **数据存储** - 包括pymongo和redis
7. **网页解析** - beautifulsoup4
8. **缓存支持** - gptcache
9. **开发测试工具** - pytest和pytest-asyncio

## 使用方法

### 安装所有依赖

#### 方法一：使用一键安装脚本（推荐）

```bash
./install_dependencies.sh
```

#### 方法二：直接使用pip

```bash
pip install -r src/app/langchain1.x/requirements.txt
```

### 安装特定模块依赖

如果只需要安装特定模块的依赖，可以使用：

```bash
# 安装基础LangChain依赖
pip install langchain>=0.1.0 langchain-openai>=0.1.0 langchain-community>=0.1.0

# 安装向量数据库相关依赖
pip install faiss-cpu>=1.7.0 chromadb>=0.4.0
```

## 添加新依赖

当需要为项目添加新依赖时，请按照以下步骤：

1. **编辑 `src/app/langchain1.x/requirements.txt` 文件**
2. **在文件末尾添加新依赖**
3. **按照已有格式添加注释说明依赖用途**

例如，添加一个新的依赖：

```txt
# 09-rag - 新增的向量数据库支持
pinecone-client>=2.2.0
```

## 验证依赖

可以使用提供的验证脚本检查根目录的requirements.txt是否包含所有子目录的依赖：

```bash
python3 validate_requirements.py
```

### 更新依赖

可以使用提供的更新脚本添加新依赖：

```bash
# 命令行方式
python3 update_requirements.py <依赖名称> [版本要求] [类别] [描述]

# 示例
python3 update_requirements.py pinecone-client ">=2.2.0" "向量数据库和搜索" "Pinecone向量数据库支持"

# 交互式方式
python3 update_requirements.py
```

## 保留子目录requirements.txt的原因

虽然已经将所有依赖整合到根目录，但仍然保留了各子目录的requirements.txt文件，原因如下：

1. **模块独立性** - 便于单独运行各个模块的示例代码
2. **文档参考** - 清楚展示每个模块需要的特定依赖
3. **向后兼容** - 保证现有代码和文档的引用不会失效

## 版本管理

- 所有依赖都指定了最低版本要求，确保兼容性
- 核心依赖(LangChain系列)保持版本一致
- 特定功能依赖可能在不同模块中有不同版本要求，已统一为较高版本

## 故障排除

如果遇到依赖冲突或安装问题：

1. 建议使用虚拟环境
2. 确保Python版本兼容
3. 检查pip版本是否最新：`pip install --upgrade pip`
4. 某些依赖可能需要系统级支持，如faiss-cpu在某些环境下可能需要额外配置