# handlers/message_handler.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram_bot import config
from utils.language_detector import is_indian_language
from services.ai_service import get_user_intent
from services.db_service import get_user_data, update_user_data, save_chat_message

logger = logging.getLogger(__name__)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理所有文本消息"""
    if not update.message or not update.message.text:
        return  # 忽略非文本消息

    user_message = update.message.text
    user_id = update.effective_user.id
    await save_chat_message(user_id, "user", user_message)

    # 1. 语言检测
    if not is_indian_language(user_message):
        reply_text = "不好意思我们只在印度实行"
        await update.message.reply_text(reply_text)
        await save_chat_message(user_id, "bot", reply_text)
        return

    # 2. 意图识别
    logger.info(f"准备为用户 {user_id} 的消息调用 Gemini API...")
    intent_data = await get_user_intent(user_id, user_message)
    logger.info(f"Gemini API 调用完成，返回意图: {intent_data.get('intent')}")

    intent = intent_data.get("intent")
    reply = intent_data.get("reply")

    user_data = await get_user_data(user_id)
    chat_count = user_data.get('chat_message_count', 0)

    # 3. 根据意图处理
    if intent == "small_talk":
        if chat_count < config.MAX_SMALL_TALK_MESSAGES:
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)
            # 手动增加计数器
            await update_user_data(user_id, {'chat_message_count': chat_count + 1})
        else:
            logger.info(f"用户 {user_id} 已达到 {config.MAX_SMALL_TALK_MESSAGES} 句闲聊上限。")

    elif intent == "service_request":
        keyboard = [
            [InlineKeyboardButton("愿意接收链接", callback_data="confirm_service")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        reply_text = "太好了！你愿意接收我们的服务链接吗？"
        await update.message.reply_text(reply_text, reply_markup=reply_markup)
        await save_chat_message(user_id, "bot", reply_text)
        await update_user_data(user_id, {'state': 'awaiting_confirmation'})

    else:  # Gemini 返回错误或其他情况
        await update.message.reply_text(reply)
        await save_chat_message(user_id, "bot", reply)
