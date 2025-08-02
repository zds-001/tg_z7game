# services/ai_service.py

# 导入 logging 模块，用于记录程序运行信息
import logging
# 导入 json 模块，用于解析 AI 返回的 JSON 格式字符串
import json
# 从 typing 模块导入 Dict 类型，用于类型提示
from typing import Dict
# 导入 Google Gemini 的官方库
import google.generativeai as genai

# 导入我们自己写的数据库服务，用来获取聊天记录
from services.db_service import get_chat_history

# 获取一个日志记录器实例，用于在这个文件中打印日志
logger = logging.getLogger(__name__)

# 初始化一个全局变量，用来存放 Gemini 模型实例
gemini_model = None


# 定义一个函数，用于初始化 Gemini 模型
def initialize_gemini(api_key: str):
    """初始化 Gemini 模型"""
    # 声明我们将要修改的是全局变量 gemini_model
    global gemini_model
    # 使用 try...except 结构来捕获可能发生的错误
    try:
        # 使用 API Key 配置 Gemini 库
        genai.configure(api_key=api_key)
        # 创建一个 gemini-1.5-flash 模型的实例
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        # 打印一条成功日志
        logger.info("Google Gemini 初始化成功。")
        # 返回创建好的模型实例
        return gemini_model
    # 如果在初始化过程中发生任何异常
    except Exception as e:
        # 打印一条错误日志，并附上错误信息
        logger.error(f"Google Gemini 初始化失败: {e}")
        # 返回 None，表示初始化失败
        return None


# 定义一个异步函数，用于获取用户的意图
async def get_user_intent(user_id: int, user_message: str, language_code: str, current_state: str) -> Dict[str, str]:
    """
    使用 Gemini API 判断用户意图，并根据用户当前状态和语言生成回复。
    """
    # 检查模型是否已成功初始化
    if not gemini_model:
        # 如果没有，就返回一个错误信息
        return {"intent": "error", "reply": "AI service is currently unavailable."}

    # 从数据库获取该用户最近的聊天记录
    history_list = await get_chat_history(user_id)
    # 将聊天记录列表转换成一个多行字符串，方便AI阅读
    history_str = "\n".join([f"{item.get('role', 'unknown')}: {item.get('text', '')}" for item in history_list])

    # 根据传入的语言代码，决定给AI下达的回复语言指令
    if language_code == 'hi':
        # 如果是 'hi'，就要求回复印地语
        reply_language_instruction = "Hindi"
    else:
        # 否则，就要求回复印地语式英语
        reply_language_instruction = "Hinglish (a casual, friendly mix of Hindi and English)"

    # 定义给 Gemini AI 的“说明书”（Prompt）
    prompt = f"""
    You are a customer service assistant for a gaming service. Your goal is to guide the user through a conversation flow.
    The user's preferred language is {reply_language_instruction}.
    The user's current conversation state is: "{current_state}".

    Conversation History:
    {history_str}
    ---
    User's Latest Message: "{user_message}"
    ---
    **Conversation Flow Logic:**
    - If state is 'awaiting_service_confirmation', user is answering "do you need our service?". Intent should be 'service_request' or 'rejection'.
    - If state is 'awaiting_experience_confirmation', user is answering "have you played before?". Intent should be 'played_before' or 'new_player'.
    - If state is 'awaiting_registration_confirmation', user is answering "have you registered?". Intent should be 'registration_complete'.
    - If state is 'awaiting_re_engagement', user is answering "do you want to try the game?". Intent should be 'service_request' or 'rejection'.
    - Any other message should be 'small_talk'.

    **Classify the user's intent into ONE of the following categories based on the logic above:**
    1. "service_request": User wants the service.
    2. "rejection": User does not want the service.
    3. "played_before": User says they have played before.
    4. "new_player": User says they are a new player.
    5. "registration_complete": User confirms they have completed registration.
    6. "registration_not_complete":  user has not confirmed that the registration has been completed
    7. "small_talk": Any other message.

    If the intent is "small_talk" or "rejection", please generate a friendly reply in {reply_language_instruction}.

    Please return the result strictly in the following JSON format:
    {{
      "intent": "...",
      "reply": "..."
    }}
    """
    # 使用 try...except 结构来捕获调用API时可能发生的错误
    try:
        # 异步调用 Gemini 模型，生成内容
        response = await gemini_model.generate_content_async(prompt)
        # 清理AI返回的文本，移除可能存在的代码块标记
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        # 将清理后的字符串解析成 Python 字典
        result = json.loads(cleaned_response)
        # 打印一条成功日志，并附上AI的分析结果
        logger.info(f"Gemini 意图分析结果 (用户状态: {current_state}): {result}")
        # 返回解析后的结果字典
        return result
    # 如果在调用过程中发生任何异常
    except Exception as e:
        # 将错误信息转换为小写字符串，方便检查
        error_str = str(e).lower()
        # 检查错误信息中是否包含 "429" 和 "quota"，这通常表示免费额度用尽
        if "429" in error_str and "quota" in error_str:
            # 如果是，就打印一条警告日志
            logger.warning(f"Gemini API quota exceeded: {e}")
            # 并返回一个专门针对额度用尽的错误信息
            return {"intent": "error",
                    "reply": "Sorry, the free call quota for today has been used up. Please try again tomorrow."}

        # 如果是其他类型的错误
        # 打印一条错误日志
        logger.error(f"Gemini API 调用失败: {e}")
        # 返回一个通用的错误信息
        return {"intent": "error", "reply": "Sorry, I couldn't understand that. Please try again later."}
