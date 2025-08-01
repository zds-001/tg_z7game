# handlers/callback_handler.py

from telegram import Update
from telegram.ext import ContextTypes

from services.db_service import update_user_data
from handlers.command_handler import send_service_link  # 导入发送链接的函数


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理内联按钮点击"""
    query = update.callback_query
    await query.answer()  # 必须调用，否则按钮会一直显示加载中

    user_id = query.from_user.id

    if query.data == "confirm_service":
        # 1. 将用户的服务状态更新为 "confirmed"
        await update_user_data(user_id, {'service_status': 'confirmed'})

        # 2. 从 query 中删除原始的 "愿意接收链接?" 消息
        await query.delete_message()

        # 3. 调用独立的函数来发送链接和策略
        await send_service_link(update, context)

    elif query.data in ["strategy_1", "strategy_2"]:
        await query.edit_message_text(text=f"你已选择 {query.data}。祝你好运！")

    elif query.data == "disabled_button":
        await context.bot.answer_callback_query(query.id, text="此策略当前不可用。", show_alert=True)
