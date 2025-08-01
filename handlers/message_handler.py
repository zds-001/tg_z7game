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

    # 1. 检测语言并获取用户数据
    language_code = detect_language(user_message)
    user_data = await get_user_data(user_id)
    if user_data.get('language_code') != language_code:
        await update_user_data(user_id, {'language_code': language_code})
        logger.info(f"用户 {user_id} 的偏好语言已更新为 '{language_code}'。")

    chat_count = user_data.get('chat_message_count', 0)
    service_status = user_data.get('service_status', 'pending')  # 获取用户服务状态

    # 2. 调用AI进行意图识别（传入语言和状态）
    logger.info(f"准备为用户 {user_id} 的消息调用 Gemini API...")
    intent_data = await get_user_intent(user_id, user_message, language_code, service_status)
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
            limit_reply_en = "Hello, your chat quota has been used up. If you need our service, you can tell me directly."
            limit_reply_hi = "नमस्ते, आपका चैट कोटा समाप्त हो गया है। यदि आपको हमारी सेवा की आवश्यकता है, तो आप मुझे सीधे बता सकते हैं।"
            limit_reply = limit_reply_hi if language_code == 'hi' else limit_reply_en
            await update.message.reply_text(limit_reply)
            await save_chat_message(user_id, "bot", limit_reply)
            logger.info(f"用户 {user_id} 已达到终生闲聊上限。")

    elif intent == "service_request":
        # --- 这是最终的、更健壮的逻辑 ---
        logger.info(f"用户 {user_id} 的服务状态是: {service_status}")
        # 如果用户已经是 'confirmed' 状态，我们就忽略这个服务请求，当作闲聊处理。
        if service_status == 'confirmed':
            logger.warning(f"用户 {user_id} 已确认服务，但再次触发了 service_request 意图。已忽略。")

            # 根据用户语言，回复一句固定的、表示“收到”的消息
            response_text_en = "OK, got it! Feel free to ask if you have any other questions."
            response_text_hi = "ठीक है, समझ गया! यदि आपके कोई अन्य प्रश्न हैं तो बेझिझक पूछें।"
            response_text = response_text_hi if language_code == 'hi' else response_text_en

            await update.message.reply_text(response_text)
            await save_chat_message(user_id, "bot", response_text)
            return  # 终止执行，防止重复发送链接

        # 只有当用户是第一次请求服务时，才执行下面的代码
        logger.info(f"用户 {user_id} 首次请求服务，发送链接。")
        await update_user_data(user_id, {'service_status': 'confirmed'})
        await send_service_link(update, context)
        await save_chat_message(user_id, "bot", "Service link sent.")

    elif intent == "rejection":
        logger.info(f"用户 {user_id} 拒绝了服务。")
        await update.message.reply_text(reply)
        await save_chat_message(user_id, "bot", reply)

    else:  # 处理 error 或其他未知情况
        await update.message.reply_text(reply)
        await save_chat_message(user_id, "bot", reply)
