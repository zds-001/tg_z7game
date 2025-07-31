# services/ai_service.py

import logging
import json
from typing import List, Dict, Any
import google.generativeai as genai

from services.db_service import get_chat_history

logger = logging.getLogger(__name__)

gemini_model = None


def initialize_gemini(api_key: str):
    """初始化 Gemini 模型"""
    global gemini_model
    try:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Google Gemini 初始化成功。")
        return gemini_model
    except Exception as e:
        logger.error(f"Google Gemini 初始化失败: {e}")
        return None


async def get_user_intent(user_id: int, user_message: str) -> Dict[str, str]:
    """
    使用 Gemini API 判断用户意图。
    意图分为 'small_talk' (闲聊) 和 'service_request' (服务请求)。
    """
    if not gemini_model:
        return {"intent": "error", "reply": "AI 服务当前不可用。"}

    history_list = await get_chat_history(user_id)
    history_str = "\n".join([f"{item.get('role', 'unknown')}: {item.get('text', '')}" for item in history_list])

    prompt = f"""
    你是一个游戏服务的客服助手。请分析用户最新的消息并判断其意图。
    对话历史:
    {history_str}
    ---
    用户最新消息: "{user_message}"
    ---
    请将用户意图分类为以下两种之一:
    1. "service_request": 用户明确表示需要服务、想玩游戏、询问如何开始或对服务感兴趣。
    2. "small_talk": 用户在闲聊、打招呼、问候或讨论与服务无关的话题。

    如果意图是 "small_talk"，请生成一句自然、简洁、友好的回复。

    请严格按照以下 JSON 格式返回结果，不要添加任何其他解释:
    {{
      "intent": "...",
      "reply": "..."
    }}
    """
    try:
        response = await gemini_model.generate_content_async(prompt)
        # 清理和解析 Gemini 的返回结果
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(cleaned_response)
        logger.info(f"Gemini 意图分析结果: {result}")
        return result
    except Exception as e:
        # 检查是否是配额用尽的错误
        error_str = str(e).lower()
        if "429" in error_str and "quota" in error_str:
            logger.warning(f"Gemini API quota exceeded: {e}")
            return {"intent": "error", "reply": "抱歉，今天的免费调用次数已用完，请明天再试。"}

        logger.error(f"Gemini API 调用失败: {e}")
        return {"intent": "error", "reply": "抱歉，我暂时无法理解。请稍后再试。"}
