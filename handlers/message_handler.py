# handlers/message_handler.py

import logging
from typing import Dict
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot import config
from utils.language_detector import detect_language
from services.ai_service import get_user_intent
from services.db_service import get_user_data, update_user_data, save_chat_message
from handlers.command_handler import send_service_link, send_registration_guide

logger = logging.getLogger(__name__)


async def registration_reminder(context: ContextTypes.DEFAULT_TYPE):
    """1分钟后提醒用户是否注册完成"""
    job = context.job
    user_id = job.user_id
    chat_id = job.chat_id

    user_data = await get_user_data(user_id)
    if user_data.get('state') == 'awaiting_registration_confirmation':
        reminder_message = "Hi! Have you completed the registration? Let me know if you are ready."
        await context.bot.send_message(chat_id=chat_id, text=reminder_message)
        await save_chat_message(user_id, "bot", reminder_message)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理所有文本消息，作为一个状态机"""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_message = update.message.text
    await save_chat_message(user_id, "user", user_message)

    # 1. 获取用户当前状态
    user_data = await get_user_data(user_id)
    current_state = user_data.get('state', 'started')
    language_code = user_data.get('language_code', 'en')

    detected_lang = detect_language(user_message)
    if language_code != detected_lang:
        language_code = detected_lang
        await update_user_data(user_id, {'language_code': language_code})

    # --- 新增：如果当前状态是等待用户ID，则跳过AI，直接进行验证 ---
    if current_state == 'awaiting_user_id':
        if user_message.isdigit() and len(user_message) == 9:
            logger.info(f"用户 {user_id} 提供了有效的ID: {user_message}")
            await save_chat_message(user_id, "bot", "User ID validation successful.")
            await update.message.reply_text("Thank you! Your registration is successful.")
            await send_service_link(update, context)
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        else:
            logger.warning(f"用户 {user_id} 提供了无效的ID: {user_message}")
            await update.message.reply_text("The ID seems invalid. It must be a 9-digit number. Please try again.")
            await save_chat_message(user_id, "bot", "Invalid ID provided.")
        return  # 在这里结束处理

    # 2. 调用AI进行意图识别 (for all other states)
    intent_data = await get_user_intent(user_id, user_message, language_code, current_state)
    intent = intent_data.get("intent")
    reply = intent_data.get("reply")

    # 3. 根据当前状态和用户意图，执行不同操作
    if current_state == 'awaiting_service_confirmation':
        if intent == 'service_request':
            question = "Great! Have you played our game before?"
            await update.message.reply_text(question)
            await save_chat_message(user_id, "bot", question)
            await update_user_data(user_id, {'state': 'awaiting_experience_confirmation'})
        elif intent == 'rejection':
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)
        else:
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)

    elif current_state == 'awaiting_experience_confirmation':
        if intent == 'played_before':
            await send_service_link(update, context)
            await save_chat_message(user_id, "bot", "Service link sent.")
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        elif intent == 'new_player':
            await send_registration_guide(update, context)
            await save_chat_message(user_id, "bot", "Registration guide sent.")
            await update_user_data(user_id, {'state': 'awaiting_registration_confirmation'})
            context.job_queue.run_once(
                registration_reminder, 60, chat_id=update.effective_chat.id,
                user_id=user_id, name=f"reminder_{user_id}"
            )
        else:
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)

    elif current_state == 'awaiting_registration_confirmation':
        if intent == 'registration_complete':
            question = "Awesome! Please send me your 9-digit User ID to complete the process."
            await update.message.reply_text(question)
            await save_chat_message(user_id, "bot", question)
            await update_user_data(user_id, {'state': 'awaiting_user_id'})
        else:
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)

    else:
        chat_count = user_data.get('chat_message_count', 0)
        if chat_count < config.MAX_SMALL_TALK_MESSAGES:
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)
            await update_user_data(user_id, {'chat_message_count': chat_count + 1})
        else:
            limit_reply = "Your chat quota has been used up. If you need our service, please use /start again."
            await update.message.reply_text(limit_reply)
            await save_chat_message(user_id, "bot", limit_reply)
