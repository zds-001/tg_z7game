# handlers/message_handler.py

import logging
from typing import Dict
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot import config
from utils.language_detector import detect_language
from services.ai_service import get_user_intent
from services.db_service import get_user_data, update_user_data, save_chat_message
from handlers.command_handler import send_service_link

logger = logging.getLogger(__name__)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理所有文本消息"""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_message = update.message.text
    await save_chat_message(user_id, "user", user_message)

    # 1. 检测语言并更新用户偏好
    language_code = detect_language(user_message)
    user_data = await get_user_data(user_id)
    # 如果数据库中记录的语言与本次不同，则更新
    if user_data.get('language_code') != language_code:
        await update_user_data(user_id, {'language_code': language_code})
        logger.info(f"用户 {user_id} 的偏好语言已更新为 '{language_code}'。")

    chat_count = user_data.get('chat_message_count', 0)

    # 2. 调用AI进行意图识别（传入语言代码）
    logger.info(f"准备为用户 {user_id} 的消息调用 Gemini API...")
    intent_data = await get_user_intent(user_id, user_message, language_code)
    logger.info(f"Gemini API 调用完成，返回意图: {intent_data.get('intent')}")

    intent = intent_data.get("intent")
    reply = intent_data.get("reply")

    # 3. 根据意图处理
    if intent == "small_talk":
        if chat_count < config.MAX_SMALL_TALK_MESSAGES:
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)
            await update_user_data(user_id, {'chat_message_count': chat_count + 1})
        else:
            limit_reply_en = "Hello, your chat quota for today has been used up. Please come back tomorrow! If you need our service, you can tell me directly."
            limit_reply_hi = "नमस्ते, आज के लिए आपका चैट कोटा समाप्त हो गया है। कृपया कल फिर आएं! यदि आपको हमारी सेवा की आवश्यकता है, तो आप मुझे सीधे बता सकते हैं।"
            limit_reply = limit_reply_hi if language_code == 'hi' else limit_reply_en
            await update.message.reply_text(limit_reply)
            await save_chat_message(user_id, "bot", limit_reply)
            logger.info(f"用户 {user_id} 已达到终生闲聊上限。")

    elif intent == "service_request":
        logger.info(f"用户 {user_id} 请求服务，直接发送链接。")
        await update_user_data(user_id, {'service_status': 'confirmed'})
        await send_service_link(update, context)
        await save_chat_message(user_id, "bot", "Service link sent.")

    else:
        await update.message.reply_text(reply)
        await save_chat_message(user_id, "bot", reply)
