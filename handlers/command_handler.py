# handlers/command_handler.py

import logging
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

    await context.bot.send_message(chat_id=update.effective_chat.id, text=link_text, parse_mode='Markdown')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="请选择你的策略：", reply_markup=reply_markup)


async def send_registration_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """发送图文并茂的注册和充值教程"""
    chat_id = update.effective_chat.id

    # 教程第一步：注册
    registration_caption = (
        "**Step 1: Registration**\n\n"
        "1. Click the link in our bio.\n"
        "2. Fill in your details.\n"
        "3. Verify your email."
    )
    # 您需要提供一张真实图片的URL
    registration_photo_url = "https://placehold.co/600x400/EEE/31343C?text=Registration+Guide"
    await context.bot.send_photo(chat_id=chat_id, photo=registration_photo_url, caption=registration_caption,
                                 parse_mode='Markdown')

    # 教程第二步：充值
    recharge_caption = (
        "**Step 2: Recharge**\n\n"
        "1. Go to the 'Wallet' section.\n"
        "2. Choose your payment method.\n"
        "3. Complete the payment to start playing!"
    )
    recharge_photo_url = "https://placehold.co/600x400/31343C/EEE?text=Recharge+Guide"
    await context.bot.send_photo(chat_id=chat_id, photo=recharge_photo_url, caption=recharge_caption,
                                 parse_mode='Markdown')

    # 新增：引导用户下一步操作
    await context.bot.send_message(
        chat_id=chat_id,
        text="Please follow the guide to register. Let me know when you are done!"
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令，开始对话流"""
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id

    # 每次 /start 都重置对话状态
    await update_user_data(user_id, {
        'username': user.username,
        'first_name': user.first_name,
        'chat_id': chat_id,
        'state': 'awaiting_service_confirmation',  # 设置初始状态
        'subscribed_to_broadcast': True,
    })

    welcome_message = "Hi there! We offer an exciting gaming service. Are you interested?"
    await update.message.reply_text(welcome_message)
    await save_chat_message(user_id, "bot", welcome_message)
