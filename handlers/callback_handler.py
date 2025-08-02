# handlers/callback_handler.py

# 从 telegram 库导入 Update 类，它包含了所有收到的更新信息
from telegram import Update
# 从 telegram.ext 库导入 ContextTypes，它包含了上下文信息，比如机器人实例
from telegram.ext import ContextTypes

# 导入我们自己写的数据库服务，用来更新用户数据
from services.db_service import update_user_data
# 导入我们公共回复模块中的发送链接函数
from handlers.common_replies import send_service_link


# 定义一个异步函数，专门用来处理用户点击内联按钮的操作
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理内联按钮点击"""
    # 从 update 对象中获取回调查询对象，它包含了按钮的所有信息
    query = update.callback_query
    # 必须调用 answer()，以通知 Telegram 我们已经收到了这次点击，否则用户的按钮会一直显示加载中
    await query.answer()

    # 从 query 对象中获取点击按钮的那个用户的ID
    user_id = query.from_user.id

    # 检查被点击按钮的 callback_data (我们设置的隐藏“身份证”) 是否是 "confirm_service"
    if query.data == "confirm_service":
        # 1. 如果是，就在数据库里将这个用户的服务状态更新为 "confirmed"
        await update_user_data(user_id, {'service_status': 'confirmed'})

        # 2. 从聊天记录中删除那个带有“愿意接收链接?”按钮的原始消息，让界面更整洁
        await query.delete_message()

        # 3. 调用我们独立的函数，来给用户发送游戏链接和策略按钮
        await send_service_link(update, context)

    # 检查被点击按钮的 callback_data 是否是 "strategy_1" 或 "strategy_2"
    elif query.data in ["strategy_1", "strategy_2"]:
        # 如果是，就编辑当前消息的文本，告诉用户他的选择
        await query.edit_message_text(text=f"你已选择 {query.data}。祝你好运！")

    # 检查被点击按钮的 callback_data 是否是 "disabled_button"
    elif query.data == "disabled_button":
        # 如果是，就给用户弹出一个提示框，告诉他这个按钮不可用
        await context.bot.answer_callback_query(query.id, text="此策略当前不可用。", show_alert=True)
