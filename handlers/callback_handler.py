# handlers/callback_handler.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.db_service import update_user_data


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理内联按钮点击"""
    query = update.callback_query
    await query.answer()  # 必须调用，否则按钮会一直显示加载中

    user_id = query.from_user.id

    if query.data == "confirm_service":
        # 发送链接和文案
        link_text = "发射前30s通知：[点击这里进入游戏](https://www.baidu.com)"  # 请替换为真实链接
        await query.edit_message_text(text=link_text, parse_mode='Markdown')

        # 发送策略表单
        keyboard = [
            [InlineKeyboardButton("策略1", callback_data="strategy_1")],
            [InlineKeyboardButton("策略2", callback_data="strategy_2")],
            [InlineKeyboardButton("策略3 (不可用)", callback_data="disabled_button")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("请选择你的策略：", reply_markup=reply_markup)

        await update_user_data(user_id, {'state': 'service_provided'})

    elif query.data in ["strategy_1", "strategy_2"]:
        await query.edit_message_text(text=f"你已选择 {query.data}。祝你好运！")

    elif query.data == "disabled_button":
        await context.bot.answer_callback_query(query.id, text="此策略当前不可用。", show_alert=True)
