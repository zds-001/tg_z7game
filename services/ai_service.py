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


async def get_user_intent(user_id: int, user_message: str, language_code: str, current_state: str) -> Dict[str, str]:
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
        reply_language_instruction = "Hinglish (a casual, friendly mix of Hindi and English)"

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
    - If state is 'awaiting_service_confirmation', user is answering "do you need our service?". Intent should be 'service_request' (yes) or 'rejection' (no).
    - If state is 'awaiting_experience_confirmation', user is answering "have you played before?". Intent should be 'played_before' (yes) or 'new_player' (no).
    - If state is 'awaiting_registration_confirmation', user is answering "have you registered?". Intent should be 'registration_complete' (e.g., "yes", "I'm done", "finished").
    - If state is 'awaiting_re_engagement', user is answering "do you want to try the game?". Intent should be 'service_request' or 'rejection'.

    - Any other message should be 'small_talk'.

    **Classify the user's intent into ONE of the following categories based on the logic above:**
    1. "service_request": User wants the service.
    2. "rejection": User does not want the service.
    3. "played_before": User says they have played before.
    4. "new_player": User says they are a new player.
    5. "registration_complete": User confirms they have completed registration.
    6. "small_talk": Any other message that doesn't fit the current state's expected answer.

    If the intent is "small_talk" or "rejection", please generate a friendly reply in {reply_language_instruction}.

    Please return the result strictly in the following JSON format:
    {{
      "intent": "...",
      "reply": "..."
    }}
    """
    try:
        response = await gemini_model.generate_content_async(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(cleaned_response)
        logger.info(f"Gemini 意图分析结果 (用户状态: {current_state}): {result}")
        return result
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str and "quota" in error_str:
            logger.warning(f"Gemini API quota exceeded: {e}")
            return {"intent": "error",
                    "reply": "Sorry, the free call quota for today has been used up. Please try again tomorrow."}

        logger.error(f"Gemini API 调用失败: {e}")
        return {"intent": "error", "reply": "Sorry, I couldn't understand that. Please try again later."}
