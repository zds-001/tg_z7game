# handlers/common_replies.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# 导入数据库保存函数
from services.db_service import save_chat_message


async def send_service_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一个独立的函数，用于发送服务链接和策略按钮"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    link_text = "发射前30s通知：[点击这里进入游戏](https://www.example.com)"
    await context.bot.send_message(chat_id=chat_id, text=link_text, parse_mode='Markdown')
    await save_chat_message(user_id, "bot", link_text)

    strategy_text = "请选择你的策略："
    keyboard = [
        [InlineKeyboardButton("策略1", callback_data="strategy_1")],
        [InlineKeyboardButton("策略2", callback_data="strategy_2")],
        [InlineKeyboardButton("策略3 (不可用)", callback_data="disabled_button")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=strategy_text, reply_markup=reply_markup)
    await save_chat_message(user_id, "bot", strategy_text)


async def send_registration_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """发送图文并茂的注册和充值教程"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    registration_caption = (
        "**Step 1: Registration**\n\n"
        "1. Click the link in our bio.\n"
        "2. Fill in your details.\n"
        "3. Verify your email."
    )
    registration_photo_url = "https://picsum.photos/seed/register/600/400"
    await context.bot.send_photo(chat_id=chat_id, photo=registration_photo_url, caption=registration_caption,
                                 parse_mode='Markdown')
    await save_chat_message(user_id, "bot", f"[Photo] {registration_caption}")

    recharge_caption = (
        "**Step 2: Recharge**\n\n"
        "1. Go to the 'Wallet' section.\n"
        "2. Choose your payment method.\n"
        "3. Complete the payment to start playing!"
    )
    recharge_photo_url = "https://picsum.photos/seed/recharge/600/400"
    await context.bot.send_photo(chat_id=chat_id, photo=recharge_photo_url, caption=recharge_caption,
                                 parse_mode='Markdown')
    await save_chat_message(user_id, "bot", f"[Photo] {recharge_caption}")

    follow_up_text = "Please follow the guide to register. Let me know when you are done!"
    await context.bot.send_message(chat_id=chat_id, text=follow_up_text)
    await save_chat_message(user_id, "bot", follow_up_text)
