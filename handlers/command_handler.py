# handlers/command_handler.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.message_handler import text_message_handler
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
        "https://xz.u7777.net/?dl=dkyay3"
        "1. Click the link in our bio.\n"
        "2. Fill in your details.\n"
        "3. Verify your email."
    )
    # --- 已将图片链接替换为更可靠的来源 ---
    registration_photo_url = "https://picsum.photos/seed/register/600/400"
    await context.bot.send_photo(chat_id=chat_id, photo=registration_photo_url, caption=registration_caption,
                                 parse_mode='Markdown')

    # 教程第二步：充值
    recharge_caption = (
        "**Step 2: Recharge**\n\n"
        "1. Go to the 'Wallet' section.\n"
        "2. Choose your payment method.\n"
        "3. Complete the payment to start playing!"
    )
    # --- 已将图片链接替换为更可靠的来源 ---
    recharge_photo_url = "https://picsum.photos/seed/recharge/600/400"
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
    user_data = await get_user_data(user_id)
    # --- 这是修改后的核心逻辑 ---
    # 如果用户已经确认过服务，那么这次的 /start 就当作闲聊处理
    if user_data and user_data.get("service_status") == "confirmed":
        logger.info(f"已确认服务的用户，{user_id}再次输入 /start，将作为闲聊处理")
        await  text_message_handler(update, context)
        return
    # 只有当用户是新用户或者未确认服务时，才开始引导流程
    logger.info(f"新用户{user_id}或未确认用户，开始引导流程")
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
