import os
import sys
import locale
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

# 设置UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

def main():
    try:
        # 获取环境变量
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE")

        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # 清理API key中的特殊字符
        import re
        # 移除所有Unicode引号和其他特殊字符
        api_key = re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb"\'\u0060\u00b4]', '', api_key).strip()
        api_base = re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb"\'\u0060\u00b4]', '', api_base).strip() if api_base else None

        # 初始化模型
        print(f"API Key: {api_key[:10]}...")  # 只显示前10个字符
        print(f"API Base: {api_base}")

        try:
            # 设置环境变量用于init_chat_model
            # 确保环境变量也是干净的
            os.environ["OPENAI_API_KEY"] = api_key
            if api_base:
                os.environ["OPENAI_BASE_URL"] = api_base.strip()
                print(f"使用自定义API base: {api_base}")

            # 使用init_chat_model初始化模型
            # 注意：init_chat_model会自动从环境变量读取API key和base URL
            model = init_chat_model("gpt-4")
            print("模型初始化成功")
        except Exception as init_error:
            print(f"模型初始化失败: {str(init_error)}")
            raise

        # 创建消息
        message = HumanMessage(content="帮我写一段早安，祝福问候的话术。")

        # 调用模型
        print("正在调用模型...")
        response = model.invoke([message])

        # 输出结果
        print("\n" + "="*50)
        print("模型回复:")
        print("="*50)
        # 确保内容正确编码输出
        if hasattr(response.content, 'encode'):
            content = response.content.encode('utf-8', errors='ignore').decode('utf-8')
        else:
            content = str(response.content)
        print(content)
        print("="*50)

    except Exception as e:
        import traceback
        print(f"错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())