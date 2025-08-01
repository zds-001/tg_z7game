# handlers/message_handler.py

import logging
from typing import Dict
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils.language_detector import detect_language
from services.ai_service import get_user_intent
from services.db_service import get_user_data, update_user_data, save_chat_message
from handlers.common_replies import send_service_link, send_registration_guide

logger = logging.getLogger(__name__)


async def registration_reminder(context: ContextTypes.DEFAULT_TYPE):
    """提醒用户是否注册完成"""
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

    user_data = await get_user_data(user_id)
    current_state = user_data.get('state', 'started')
    language_code = user_data.get('language_code', 'en')

    detected_lang = detect_language(user_message)
    if language_code != detected_lang:
        language_code = detected_lang
        await update_user_data(user_id, {'language_code': language_code})

    if current_state == 'awaiting_user_id':
        if user_message.isdigit() and len(user_message) == 9:
            logger.info(f"用户 {user_id} 提供了有效的ID: {user_message}")
            await update.message.reply_text("Thank you! Your registration is successful.")
            await send_service_link(update, context)
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        else:
            logger.warning(f"用户 {user_id} 提供了无效的ID: {user_message}")
            await update.message.reply_text("The ID seems invalid. It must be a 9-digit number. Please try again.")
        return

    intent_data = await get_user_intent(user_id, user_message, language_code, current_state)
    intent = intent_data.get("intent")
    reply = intent_data.get("reply")

    if current_state == 'awaiting_service_confirmation':
        if intent == 'service_request':
            question = "Great! Have you played our game before?"
            await update.message.reply_text(question)
            await update_user_data(user_id, {'state': 'awaiting_experience_confirmation'})
        else:
            await update.message.reply_text(reply)

    elif current_state == 'awaiting_experience_confirmation':
        if intent == 'played_before':
            await send_service_link(update, context)
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        elif intent == 'new_player':
            await send_registration_guide(update, context)
            await update_user_data(user_id, {'state': 'awaiting_registration_confirmation'})
            context.job_queue.run_once(
                registration_reminder, 120, chat_id=update.effective_chat.id,
                user_id=user_id, name=f"reminder_{user_id}"
            )
        else:
            await update.message.reply_text(reply)

    elif current_state == 'awaiting_registration_confirmation':
        if intent == 'registration_complete':
            question = "Awesome! Please send me your 9-digit User ID to complete the process."
            await update.message.reply_text(question)
            await update_user_data(user_id, {'state': 'awaiting_user_id'})
        else:
            await update.message.reply_text(reply)

    # --- 新增：处理对追加引导问题的回复 ---
    elif current_state == 'awaiting_re_engagement':
        if intent == 'service_request':
            await send_service_link(update, context)
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        else:  # 包括拒绝或闲聊
            await update.message.reply_text(reply)
            await update_user_data(user_id, {'state': 'completed'})  # 结束这个流程

    else:  # 其他所有状态，统一当作闲聊处理
        chat_count = user_data.get('chat_message_count', 0)
        if chat_count < config.MAX_SMALL_TALK_MESSAGES:
            await update.message.reply_text(reply)
            await update_user_data(user_id, {'chat_message_count': chat_count + 1})

            # --- 新增：在闲聊后追加引导 ---
            # 只有当用户还未确认服务时，才追加引导
            if user_data.get('service_status') != 'confirmed':
                re_engagement_prompt = "By the way, our game is really fun. Are you sure you don't want to give it a try?"
                await update.message.reply_text(re_engagement_prompt)
                # 更新状态，以便下次能正确处理用户的回复
                await update_user_data(user_id, {'state': 'awaiting_re_engagement'})
        else:
            limit_reply = "Your chat quota has been used up. If you need our service, please use /start again."
            await update.message.reply_text(limit_reply)

    # 统一保存机器人的回复
    await save_chat_message(user_id, "bot", update.message.text)
