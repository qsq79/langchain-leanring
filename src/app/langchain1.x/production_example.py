import os
import sys
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

def create_model(model_name: str = "gpt-4"):
    """
    创建模型的工厂函数
    推荐在生产环境中使用
    """
    # 加载环境变量
    load_dotenv()

    # 设置默认配置
    os.environ.setdefault('OPENAI_API_KEY', '')
    os.environ.setdefault('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    os.environ.setdefault('OPENAI_TEMPERATURE', '0.7')

    # 使用init_chat_model创建模型
    return init_chat_model(
        model_name,
        temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    )

def main():
    """生产环境示例"""
    try:
        # 创建模型 - 简洁明了
        model = create_model("gpt-4")

        # 使用模型
        message = HumanMessage(content="你好，请介绍一下自己。")
        response = model.invoke([message])

        print(f"模型回复: {response.content}")

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())