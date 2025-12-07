#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Prompts 组件基础示例
演示Prompt Templates和Example Selectors的基本使用方法
"""

import os
import sys
from typing import List, Dict, Any
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, FewShotPromptTemplate
from langchain_core.prompts.example_selector import LengthBasedExampleSelector, SemanticSimilarityExampleSelector
from langchain_core.prompts import PipelinePromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 添加utils目录到系统路径，以便导入配置加载器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

def basic_prompt_template_example():
    """基础Prompt Template示例"""
    print("=== 基础Prompt Template示例 ===")
    
    # 创建简单的提示模板
    template = """
请分析以下{subject}的特点：

内容：{content}
背景：{background}

请从以下角度进行分析：
1. 主要特征
2. 优势
3. 改进建议

分析结果：
"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["subject", "content", "background"]
    )
    
    # 格式化提示
    formatted_prompt = prompt.format(
        subject="Python编程语言",
        content="Python是一种高级编程语言，具有简洁的语法和强大的功能",
        background="广泛应用于数据科学、Web开发、人工智能等领域"
    )
    
    print("格式化后的提示：")
    print(formatted_prompt)
    print()
    
    # 使用提示模板调用LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    response = llm.invoke(formatted_prompt)
    print("LLM响应：")
    print(response)
    print()

def chat_prompt_template_example():
    """Chat Prompt Template示例"""
    print("=== Chat Prompt Template示例 ===")
    
    # 创建聊天提示模板
    chat_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的{role}，专门处理{domain}相关的问题。"),
        ("human", "请回答以下问题：{question}"),
    ])
    
    # 格式化聊天提示
    formatted_messages = chat_template.format_messages(
        role="Python编程专家",
        domain="Python编程",
        question="Python中的装饰器是什么？如何使用？"
    )
    
    print("格式化后的消息：")
    for message in formatted_messages:
        print(f"{message.type}: {message.content}")
    print()
    
    # 使用聊天模板调用Chat Model
    chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
    response = chat_model.invoke(formatted_messages)
    print("Chat Model响应：")
    print(response.content)
    print()

def few_shot_prompt_example():
    """Few-shot提示示例"""
    print("=== Few-shot提示示例 ===")
    
    # 创建示例
    examples = [
        {
            "question": "什么是机器学习？",
            "answer": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习，而无需明确编程。"
        },
        {
            "question": "什么是深度学习？",
            "answer": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的学习过程。"
        },
        {
            "question": "什么是神经网络？",
            "answer": "神经网络是受生物神经系统启发的计算模型，由相互连接的节点（神经元）组成。"
        }
    ]
    
    # 创建示例模板
    example_template = """
问题：{question}
答案：{answer}
"""
    
    example_prompt = PromptTemplate(
        template=example_template,
        input_variables=["question", "answer"]
    )
    
    # 创建Few-shot提示模板
    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix="以下是一些问答示例，请按照相同的格式回答问题：",
        suffix="问题：{input}\n答案：",
        input_variables=["input"],
        example_separator="\n"
    )
    
    # 格式化Few-shot提示
    formatted_prompt = few_shot_prompt.format(
        input="什么是自然语言处理？"
    )
    
    print("Few-shot提示：")
    print(formatted_prompt)
    print()
    
    # 调用LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    response = llm.invoke(formatted_prompt)
    print("LLM响应：")
    print(response)
    print()

def length_based_selector_example():
    """基于长度的示例选择器示例"""
    print("=== 基于长度的示例选择器示例 ===")
    
    # 创建示例列表
    examples = [
        {"input": "简短", "output": "这是一个简短的回答。"},
        {"input": "这是一个中等长度的问题，需要详细解释相关概念", "output": "这是一个需要详细解释的中等长度回答，涵盖了相关概念的解释和说明。"},
        {"input": "这是一个很长的问题，需要从多个角度进行全面分析，包括历史背景、现状分析、未来趋势等多个方面", "output": "这是一个全面的回答，从历史背景开始，详细分析了现状，并对未来趋势进行了深入预测，涵盖了所有相关方面。"}
    ]
    
    # 创建基于长度的示例选择器
    example_selector = LengthBasedExampleSelector(
        examples=examples,
        example_prompt=PromptTemplate(
            template="输入：{input}\n输出：{output}",
            input_variables=["input", "output"]
        ),
        max_length=100  # 最大长度限制
    )
    
    # 测试不同长度的输入
    test_inputs = [
        "短问题",
        "这是一个中等长度的问题，需要适当详细的回答",
        "这是一个很长的问题，需要非常全面的回答"
    ]
    
    for test_input in test_inputs:
        selected_examples = example_selector.select_examples({"input": test_input})
        
        print(f"输入长度: {len(test_input)}")
        print(f"选择的示例数量: {len(selected_examples)}")
        print("选择的示例:")
        for i, example in enumerate(selected_examples, 1):
            print(f"  {i}. {example}")
        print()

def semantic_similarity_selector_example():
    """基于语义相似度的示例选择器示例"""
    print("=== 基于语义相似度的示例选择器示例 ===")
    
    # 创建示例
    examples = [
        {
            "input": "Python编程语言的特点",
            "output": "Python具有简洁的语法、丰富的库和强大的功能，适合初学者和专业开发者。"
        },
        {
            "input": "JavaScript在Web开发中的应用",
            "output": "JavaScript是前端开发的核心语言，用于创建交互式网页和动态内容。"
        },
        {
            "input": "机器学习算法的分类",
            "output": "机器学习算法分为监督学习、无监督学习和强化学习三大类。"
        },
        {
            "input": "深度学习在图像识别中的应用",
            "output": "深度学习通过卷积神经网络在图像识别、目标检测等领域取得了突破性进展。"
        }
    ]
    
    # 创建基于语义相似度的示例选择器
    try:
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples,
            OpenAIEmbeddings(),
            k=2  # 选择最相似的2个示例
        )
        
        # 测试查询
        test_queries = [
            "Python的优势和劣势",
            "网页开发技术栈",
            "AI技术发展趋势"
        ]
        
        for query in test_queries:
            selected_examples = example_selector.select_examples({"input": query})
            
            print(f"查询: {query}")
            print("选择的相似示例:")
            for i, example in enumerate(selected_examples, 1):
                print(f"  {i}. 输入: {example['input']}")
                print(f"     输出: {example['output']}")
            print()
            
    except Exception as e:
        print(f"语义相似度选择器示例失败: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")
        print()

def pipeline_prompt_example():
    """Pipeline提示模板示例"""
    print("=== Pipeline提示模板示例 ===")
    
    # 定义子模板
    introduction_template = PromptTemplate(
        template="你是一个{role}，具有{experience}的{domain}经验。",
        input_variables=["role", "experience", "domain"]
    )
    
    task_template = PromptTemplate(
        template="当前任务：{task}\n具体要求：{requirements}\n限制条件：{constraints}",
        input_variables=["task", "requirements", "constraints"]
    )
    
    format_template = PromptTemplate(
        template="请按照以下格式输出：\n{format_specification}",
        input_variables=["format_specification"]
    )
    
    # 创建Pipeline模板
    full_prompt = PipelinePromptTemplate(
        pipeline_prompts=[
            ("introduction", introduction_template),
            ("task", task_template),
            ("format", format_template)
        ],
        final_prompt="{introduction}\n\n{task}\n\n{format}\n\n现在请完成上述任务："
    )
    
    # 格式化完整提示
    formatted_prompt = full_prompt.format(
        role="数据科学家",
        experience="5年",
        domain="机器学习",
        task="分析销售数据并预测未来趋势",
        requirements="使用时间序列分析方法，考虑季节性因素",
        constraints="只能使用2020年后的数据",
        format_specification="1. 数据概览\n2. 分析方法\n3. 预测结果\n4. 结论"
    )
    
    print("Pipeline提示模板：")
    print(formatted_prompt)
    print()
    
    # 调用LLM
    try:
        llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
        response = llm.invoke(formatted_prompt)
        print("LLM响应：")
        print(response)
        print()
    except Exception as e:
        print(f"LLM调用失败: {e}")

def dynamic_prompt_example():
    """动态提示示例"""
    print("=== 动态提示示例 ===")
    
    def create_contextual_prompt(user_level, topic):
        """根据用户水平动态创建提示"""
        base_templates = {
            "beginner": """
请用简单易懂的语言向初学者解释{topic}。
要求：
- 使用生活中的例子
- 避免专业术语
- 长度控制在100字以内
""",
            "intermediate": """
请向有一定基础的学员详细解释{topic}。
要求：
- 包含核心概念
- 提供实际应用场景
- 长度控制在200字以内
""",
            "advanced": """
请向专家深入分析{topic}。
要求：
- 包含技术细节
- 讨论优缺点
- 提供最新研究进展
- 长度控制在300字以内
"""
        }
        
        template = base_templates.get(user_level, base_templates["intermediate"])
        return PromptTemplate(
            template=template,
            input_variables=["topic"]
        )
    
    # 测试不同用户水平
    test_cases = [
        ("beginner", "人工智能"),
        ("intermediate", "机器学习"),
        ("advanced", "深度学习")
    ]
    
    for user_level, topic in test_cases:
        prompt_template = create_contextual_prompt(user_level, topic)
        formatted_prompt = prompt_template.format(topic=topic)
        
        print(f"用户水平: {user_level}, 主题: {topic}")
        print("生成的提示:")
        print(formatted_prompt)
        print()
        
        # 调用LLM
        try:
            llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
            response = llm.invoke(formatted_prompt)
            print("LLM响应:")
            print(response)
            print("-" * 50)
        except Exception as e:
            print(f"LLM调用失败: {e}")
        print()

def main():
    """主函数，运行所有示例"""
    print("LangChain Prompts 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # 基础模板示例
        basic_prompt_template_example()
        chat_prompt_template_example()
        
        # Few-shot示例
        few_shot_prompt_example()
        
        # 示例选择器示例
        length_based_selector_example()
        semantic_similarity_selector_example()
        
        # 组合模板示例
        pipeline_prompt_example()
        
        # 动态提示示例
        dynamic_prompt_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()