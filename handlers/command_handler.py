# handlers/command_handler.py
import logging

from telegram_bot import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.db_service import get_user_data, update_user_data, save_chat_message

logger = logging.getLogger(__name__)


async def send_service_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一个独立的函数，用于发送服务链接和策略按钮"""
    link_text = "发射前30s通知：[点击这里进入游戏](https://www.example.com)"
    keyboard = [
        [InlineKeyboardButton("策略1", callback_data="strategy_1")],
        [InlineKeyboardButton("策略2", callback_data="strategy_2")],
        [InlineKeyboardButton("策略3 (不可用)", callback_data="disabled_button")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.reply_text(link_text, parse_mode='Markdown')
        await update.callback_query.message.reply_text("请选择你的策略：", reply_markup=reply_markup)
    else:
        await update.message.reply_text(link_text, parse_mode='Markdown')
        await update.message.reply_text("请选择你的策略：", reply_markup=reply_markup)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令"""
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id

    user_data = await get_user_data(user_id)

    if user_data and user_data.get('service_status') == 'confirmed':
        logger.info(f"老用户 {user_id} 已确认服务，直接发送链接。")
        await send_service_link(update, context)
        await save_chat_message(user_id, "bot", "您好，这是您需要的服务链接。")
    else:
        logger.info(f"新用户 {user_id} 或未确认用户，发送欢迎消息。")
        await update_user_data(user_id, {
            'username': user.username,
            'first_name': user.first_name,
            'chat_id': chat_id,
            'state': 'started',
            'subscribed_to_broadcast': True,
            'service_status': 'pending',
            'push_message_count': 0  # 初始化推送计数
        })

        welcome_message = "你好！我们是一项激动人心的游戏服务。你需要我们的服务吗？"
        await update.message.reply_text(welcome_message)
        await save_chat_message(user_id, "bot", welcome_message)
