#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Prompts 组件高级示例
演示自定义提示模板、高级示例选择器、输出解析器等高级功能
"""

import os
import sys
import re
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, FewShotPromptTemplate
from langchain_core.prompts.example_selector import BaseExampleSelector
from langchain_core.prompts.base import BasePromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import BaseOutputParser, StrOutputParser, JsonOutputParser, PydanticOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

# 添加项目根目录到系统路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入配置加载器
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class CustomPromptTemplate(BasePromptTemplate, BaseModel):
    """自定义提示模板示例"""
    
    template: str = Field(description="模板字符串")
    input_variables: List[str] = Field(description="输入变量列表")
    output_format: str = Field(default="text", description="输出格式")
    
    @validator("input_variables")
    def validate_input_variables(cls, v):
        if not v:
            raise ValueError("input_variables不能为空")
        return v
    
    def format(self, **kwargs) -> str:
        """格式化提示模板"""
        # 验证必需变量
        for var in self.input_variables:
            if var not in kwargs:
                raise ValueError(f"缺少必需变量: {var}")
        
        # 基础格式化
        formatted = self.template.format(**kwargs)
        
        # 根据输出格式添加额外信息
        if self.output_format == "json":
            formatted += "\n\n请以JSON格式输出答案。"
        elif self.output_format == "markdown":
            formatted += "\n\n请以Markdown格式输出答案。"
        elif self.output_format == "code":
            formatted += "\n\n请以代码格式输出答案，包含适当的注释。"
        
        return formatted
    
    def _prompt_type(self) -> str:
        return "custom_prompt_template"

class ClusteringExampleSelector(BaseExampleSelector):
    """基于聚类的示例选择器"""
    
    def __init__(
        self, 
        examples: List[Dict[str, str]], 
        embeddings_model=None,
        n_clusters: int = 3,
        examples_per_cluster: int = 2
    ):
        self.examples = examples
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.n_clusters = n_clusters
        self.examples_per_cluster = examples_per_cluster
        
        # 预计算嵌入和聚类
        self._precompute_clusters()
    
    def _precompute_clusters(self):
        """预计算示例聚类"""
        # 获取所有示例的文本
        texts = [example["input"] for example in self.examples]
        
        # 计算嵌入
        embeddings = self.embeddings_model.embed_documents(texts)
        
        # 执行聚类
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # 按聚类组织示例
        self.clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in self.clusters:
                self.clusters[label] = []
            self.clusters[label].append(self.examples[i])
    
    def add_example(self, example: Dict[str, str]) -> None:
        """添加新示例并重新聚类"""
        self.examples.append(example)
        self._precompute_clusters()
    
    def select_examples(self, input_variables: Dict[str, str]) -> List[Dict[str, str]]:
        """从每个聚类选择示例"""
        query_text = input_variables.get("input", "")
        query_embedding = self.embeddings_model.embed_query(query_text)
        
        selected_examples = []
        
        # 从每个聚类中选择最相似的示例
        for cluster_examples in self.clusters.values():
            cluster_texts = [ex["input"] for ex in cluster_examples]
            cluster_embeddings = self.embeddings_model.embed_documents(cluster_texts)
            
            # 计算与查询的相似度
            similarities = cosine_similarity([query_embedding], cluster_embeddings)[0]
            
            # 选择最相似的示例
            top_indices = np.argsort(similarities)[-self.examples_per_cluster:]
            selected_examples.extend([cluster_examples[i] for i in top_indices])
        
        return selected_examples

class StructuredOutputParser(BaseOutputParser[Dict[str, Any]]):
    """结构化输出解析器"""
    
    def __init__(self, schema: Dict[str, str]):
        self.schema = schema
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析文本为结构化数据"""
        result = {}
        
        for field_name, field_pattern in self.schema.items():
            pattern = re.compile(field_pattern)
            match = pattern.search(text)
            
            if match:
                result[field_name] = match.group(1).strip()
            else:
                result[field_name] = None
        
        return result
    
    def get_format_instructions(self) -> str:
        """获取格式说明"""
        instructions = "请按照以下格式输出答案：\n"
        for field_name, field_desc in self.schema.items():
            instructions += f"- {field_name}: {field_desc}\n"
        return instructions

class MultiTurnConversationTemplate(ChatPromptTemplate):
    """多轮对话模板"""
    
    def __init__(self, system_prompt: str, max_turns: int = 5):
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.conversation_history = []
        
        # 初始化模板
        super().__init__(
            input_variables=["input"],
            messages=[
                ("system", system_prompt),
                *self._build_history_messages()
            ]
        )
    
    def _build_history_messages(self):
        """构建历史消息"""
        messages = []
        for turn in self.conversation_history:
            if turn["role"] == "human":
                messages.append(("human", turn["content"]))
            elif turn["role"] == "ai":
                messages.append(("ai", turn["content"]))
        return messages
    
    def add_turn(self, role: str, content: str):
        """添加对话轮次"""
        self.conversation_history.append({"role": role, "content": content})
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_turns * 2:
            self.conversation_history = self.conversation_history[-self.max_turns * 2:]
    
    def format_with_history(self, user_input: str) -> List[BaseMessage]:
        """格式化包含历史的消息"""
        self.add_turn("human", user_input)
        
        messages = [SystemMessage(content=self.system_prompt)]
        
        for turn in self.conversation_history:
            if turn["role"] == "human":
                messages.append(HumanMessage(content=turn["content"]))
            elif turn["role"] == "ai":
                messages.append(AIMessage(content=turn["content"]))
        
        return messages

class AdaptivePromptTemplate(BasePromptTemplate):
    """自适应提示模板"""
    
    def __init__(
        self, 
        base_template: str,
        complexity_templates: Dict[str, str],
        input_variables: List[str]
    ):
        self.base_template = base_template
        self.complexity_templates = complexity_templates
        super().__init__(
            template=base_template,
            input_variables=input_variables
        )
    
    def format(self, **kwargs) -> str:
        """根据输入复杂度选择模板"""
        complexity = self._assess_complexity(kwargs)
        
        if complexity in self.complexity_templates:
            template = self.complexity_templates[complexity]
        else:
            template = self.base_template
        
        return template.format(**kwargs)
    
    def _assess_complexity(self, inputs: Dict[str, Any]) -> str:
        """评估输入复杂度"""
        # 简单的复杂度评估逻辑
        text_length = sum(len(str(v)) for v in inputs.values())
        
        if text_length < 100:
            return "simple"
        elif text_length < 500:
            return "medium"
        else:
            return "complex"
    
    def _prompt_type(self) -> str:
        return "adaptive_prompt_template"

def custom_template_example():
    """自定义模板示例"""
    print("=== 自定义模板示例 ===")
    
    # 创建自定义模板
    custom_template = CustomPromptTemplate(
        template="""
请分析以下{subject}：

{description}

分析要求：
- 识别主要特点
- 评估优缺点
- 提供改进建议
""",
        input_variables=["subject", "description"],
        output_format="markdown"
    )
    
    # 格式化模板
    formatted_prompt = custom_template.format(
        subject="React框架",
        description="React是Facebook开发的用于构建用户界面的JavaScript库"
    )
    
    print("自定义模板格式化结果：")
    print(formatted_prompt)
    print()
    
    # 使用模板
    try:
        llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
        response = llm.invoke(formatted_prompt)
        print("LLM响应：")
        print(response)
        print()
    except Exception as e:
        print(f"LLM调用失败: {e}")

def clustering_selector_example():
    """聚类示例选择器示例"""
    print("=== 聚类示例选择器示例 ===")
    
    # 创建示例数据
    examples = [
        {"input": "Python基础语法", "output": "Python具有简洁的语法结构，易于学习。"},
        {"input": "Python高级特性", "output": "Python支持装饰器、生成器等高级特性。"},
        {"input": "JavaScript基础", "output": "JavaScript是网页开发的基础语言。"},
        {"input": "JavaScript框架", "output": "React、Vue是流行的JavaScript框架。"},
        {"input": "机器学习概念", "output": "机器学习让计算机从数据中学习规律。"},
        {"input": "深度学习应用", "output": "深度学习在图像识别、NLP等领域应用广泛。"}
    ]
    
    try:
        # 创建聚类选择器
        selector = ClusteringExampleSelector(
            examples=examples,
            n_clusters=3,
            examples_per_cluster=1
        )
        
        # 测试查询
        test_queries = [
            "Python编程特点",
            "Web开发技术",
            "AI技术趋势"
        ]
        
        for query in test_queries:
            selected_examples = selector.select_examples({"input": query})
            
            print(f"查询: {query}")
            print("选择的示例:")
            for i, example in enumerate(selected_examples, 1):
                print(f"  {i}. {example}")
            print()
            
    except Exception as e:
        print(f"聚类选择器示例失败: {e}")

def structured_output_parser_example():
    """结构化输出解析器示例"""
    print("=== 结构化输出解析器示例 ===")
    
    # 定义输出模式
    output_schema = {
        "main_point": r"主要观点[：:]\s*(.+?)(?:\n|$)",
        "supporting_evidence": r"支持论据[：:]\s*(.+?)(?:\n|$)",
        "conclusion": r"结论[：:]\s*(.+?)(?:\n|$)"
    }
    
    # 创建解析器
    parser = StructuredOutputParser(output_schema)
    
    # 创建提示模板
    template = PromptTemplate(
        template=f"""
请分析以下主题并提供结构化答案：

主题：{{topic}}

{parser.get_format_instructions()}

请详细分析：{{question}}
""",
        input_variables=["topic", "question"]
    )
    
    # 格式化提示
    formatted_prompt = template.format(
        topic="人工智能",
        question="人工智能对社会的影响有哪些？"
    )
    
    print("格式化提示：")
    print(formatted_prompt)
    print()
    
    # 使用LLM生成响应
    try:
        llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
        response = llm.invoke(formatted_prompt)
        
        print("LLM原始响应：")
        print(response)
        print()
        
        # 解析结构化输出
        parsed_result = parser.parse(response)
        
        print("解析后的结构化结果：")
        for field, value in parsed_result.items():
            print(f"{field}: {value}")
        print()
        
    except Exception as e:
        print(f"结构化输出解析失败: {e}")

def multi_turn_conversation_example():
    """多轮对话模板示例"""
    print("=== 多轮对话模板示例 ===")
    
    # 创建多轮对话模板
    conversation_template = MultiTurnConversationTemplate(
        system_prompt="你是一个专业的Python编程助手，善于解答Python相关问题。"
    )
    
    try:
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        
        # 模拟多轮对话
        user_inputs = [
            "什么是Python的装饰器？",
            "能给我一个具体的例子吗？",
            "装饰器在实际项目中有什么用途？"
        ]
        
        for user_input in user_inputs:
            print(f"用户: {user_input}")
            
            # 格式化消息
            messages = conversation_template.format_with_history(user_input)
            
            # 生成响应
            response = chat_model.invoke(messages)
            ai_response = response.content
            
            print(f"助手: {ai_response}")
            print("-" * 50)
            
            # 添加到对话历史
            conversation_template.add_turn("human", user_input)
            conversation_template.add_turn("ai", ai_response)
        
        print()
        
    except Exception as e:
        print(f"多轮对话示例失败: {e}")

def adaptive_template_example():
    """自适应模板示例"""
    print("=== 自适应模板示例 ===")
    
    # 定义不同复杂度的模板
    complexity_templates = {
        "simple": """
简单分析{subject}：
{content}

请用一句话总结要点。
""",
        "medium": """
详细分析{subject}：
{content}

要求：
1. 识别主要特点（2-3点）
2. 简要评价优缺点
3. 给出总体结论
""",
        "complex": """
全面分析{subject}：
{content}

分析框架：
1. 背景介绍
2. 核心特点分析
3. 优势与劣势对比
4. 适用场景评估
5. 发展趋势预测
6. 总结与建议

请按照上述框架进行全面分析。
"""
    }
    
    # 创建自适应模板
    adaptive_template = AdaptivePromptTemplate(
        base_template=complexity_templates["medium"],
        complexity_templates=complexity_templates,
        input_variables=["subject", "content"]
    )
    
    # 测试不同复杂度的输入
    test_cases = [
        {
            "subject": "Python语言",
            "content": "Python是一种编程语言"
        },
        {
            "subject": "React框架", 
            "content": "React是Facebook开发的JavaScript库，用于构建用户界面，具有组件化、虚拟DOM等特点，被广泛应用于Web开发。"
        },
        {
            "subject": "机器学习技术",
            "content": "机器学习是人工智能的一个重要分支，它使计算机能够从数据中学习，而无需明确编程。机器学习包括监督学习、无监督学习和强化学习等多种方法，在图像识别、自然语言处理、推荐系统等领域有着广泛的应用。随着大数据和计算能力的提升，机器学习技术正在快速发展，深度学习作为其中的重要分支，在近年来取得了突破性进展，特别是在计算机视觉和自然语言处理方面。"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        
        # 评估复杂度
        complexity = adaptive_template._assess_complexity(test_case)
        print(f"评估复杂度: {complexity}")
        
        # 格式化提示
        formatted_prompt = adaptive_template.format(**test_case)
        
        print("生成的提示:")
        print(formatted_prompt)
        print()
        
        # 调用LLM（可选）
        try:
            llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
            response = llm.invoke(formatted_prompt)
            print("LLM响应:")
            print(response)
            print("-" * 50)
            print()
        except Exception as e:
            print(f"LLM调用失败: {e}")

async def parallel_prompt_processing_example():
    """并行提示处理示例"""
    print("=== 并行提示处理示例 ===")
    
    # 创建不同的提示模板
    templates = {
        "summary": PromptTemplate(
            template="请总结以下内容：{content}",
            input_variables=["content"]
        ),
        "analysis": PromptTemplate(
            template="请分析以下内容的关键点：{content}",
            input_variables=["content"]
        ),
        "translation": PromptTemplate(
            template="请将以下内容翻译成英文：{content}",
            input_variables=["content"]
        )
    }
    
    # 创建LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 测试内容
    test_content = "人工智能正在改变我们的生活方式，从智能家居到自动驾驶，AI技术无处不在。"
    
    print(f"原始内容: {test_content}")
    print()
    
    try:
        # 创建并行处理链
        parallel_chain = RunnableParallel({
            "summary": templates["summary"] | llm,
            "analysis": templates["analysis"] | llm,
            "translation": templates["translation"] | llm
        })
        
        # 并行执行
        results = await parallel_chain.ainvoke({"content": test_content})
        
        print("并行处理结果:")
        for task, result in results.items():
            print(f"{task.capitalize()}:")
            print(result.strip())
            print()
        
    except Exception as e:
        print(f"并行处理失败: {e}")

def main():
    """主函数，运行所有高级示例"""
    print("LangChain Prompts 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 自定义模板示例
        custom_template_example()
        
        # 高级选择器示例
        clustering_selector_example()
        
        # 输出解析器示例
        structured_output_parser_example()
        
        # 多轮对话示例
        multi_turn_conversation_example()
        
        # 自适应模板示例
        adaptive_template_example()
        
        # 并行处理示例
        asyncio.run(parallel_prompt_processing_example())
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()