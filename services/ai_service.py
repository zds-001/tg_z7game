# services/ai_service.py

import logging
import json
from typing import Dict
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


async def get_user_intent(user_id: int, user_message: str, language_code: str, service_status: str) -> Dict[str, str]:
    """
    使用 Gemini API 判断用户意图，并根据用户当前状态和语言生成回复。
    """
    if not gemini_model:
        return {"intent": "error", "reply": "AI service is currently unavailable."}

    history_list = await get_chat_history(user_id)
    history_str = "\n".join([f"{item.get('role', 'unknown')}: {item.get('text', '')}" for item in history_list])

    if language_code == 'hi':
        reply_language_instruction = "Hindi"
    else:
        reply_language_instruction = "Hinglish (a casual, friendly mix of Hindi and English commonly spoken in India)"

    prompt = f"""
    You are a customer service assistant for a gaming service. Analyze the user's latest message and determine their intent based on their current status.
    The user's preferred language is {reply_language_instruction}. Your tone should be friendly and casual.

    Conversation History:
    {history_str}
    ---
    User's Latest Message: "{user_message}"
    ---
    **CRITICAL RULE: If the user's service status is already 'confirmed', you MUST classify subsequent simple confirmations like "OK", "thanks", or "got it" as "small_talk", NOT as a new "service_request".**

    Classify the user's intent into one of the following THREE categories:
    1. "service_request": The user is clearly asking for the service for the FIRST time, or is asking again after a long time.
    2. "rejection": The user explicitly states they do not need the service.
    3. "small_talk": The user is engaging in other small talk, greeting, or discussing topics unrelated to the service (this includes simple confirmations after the service has been provided).

    If the intent is "small_talk" or "rejection", please generate a natural, concise, and friendly reply in {reply_language_instruction}. For example, a Hinglish reply could be "OK bhai, no problem!" or "Theek hai, let me know if you need anything else."

    Please return the result strictly in the following JSON format, with no other explanations:
    {{
      "intent": "...",
      "reply": "..."
    }}
    """
    try:
        response = await gemini_model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(cleaned_response)
        # 我们将日志打印移到 message_handler.py 中
        return result
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str and "quota" in error_str:
            logger.warning(f"Gemini API quota exceeded: {e}")
            return {"intent": "error",
                    "reply": "Sorry, the free call quota for today has been used up. Please try again tomorrow."}

        logger.error(f"Gemini API 调用失败: {e}")
        return {"intent": "error", "reply": "Sorry, I couldn't understand that. Please try again later."}
