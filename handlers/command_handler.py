# handlers/command_handler.py

from telegram import Update
from telegram.ext import ContextTypes

from services.db_service import update_user_data, save_chat_message


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令"""
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id

    # 将用户信息和 chat_id 保存到 Firestore
    await update_user_data(user_id, {
        'username': user.username,
        'first_name': user.first_name,
        'chat_id': chat_id,
        'state': 'started',
        'chat_message_count': 0,
        'subscribed_to_broadcast': True  # 默认订阅推送
    })

    welcome_message = "你好！我们是一项激动人心的游戏服务。你需要我们的服务吗？"
    await update.message.reply_text(welcome_message)
    await save_chat_message(user_id, "bot", welcome_message)
