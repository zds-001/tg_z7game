# handlers/common_replies.py

# 从 telegram 库导入 Update, InlineKeyboardButton, InlineKeyboardMarkup 类
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# 从 telegram.ext 库导入 ContextTypes，它包含了上下文信息
from telegram.ext import ContextTypes
# 导入我们自己写的数据库服务，用来保存聊天记录
from services.db_service import save_chat_message


# 定义一个异步函数，用于发送服务链接和策略按钮
async def send_service_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一个独立的函数，用于发送服务链接和策略按钮"""
    # 从 update 对象中获取用户ID
    user_id = update.effective_user.id
    # 从 update 对象中获取聊天ID
    chat_id = update.effective_chat.id

    # 定义包含可点击链接的文本
    link_text = "发射前30s通知：[点击这里进入游戏](https://www.example.com)"
    # 使用机器人实例发送这条消息
    await context.bot.send_message(chat_id=chat_id, text=link_text, parse_mode='Markdown')
    # 将这条消息保存到数据库的聊天记录中
    await save_chat_message(user_id, "bot", link_text)

    # 定义附带策略按钮的消息文本
    strategy_text = "请选择你的策略："
    # 定义一个包含三个按钮的键盘布局
    keyboard = [
        # 第一个按钮
        [InlineKeyboardButton("策略1", callback_data="strategy_1")],
        # 第二个按钮
        [InlineKeyboardButton("策略2", callback_data="strategy_2")],
        # 第三个按钮
        [InlineKeyboardButton("策略3 (不可用)", callback_data="disabled_button")],
    ]
    # 将键盘布局包装成一个回复标记对象
    reply_markup = InlineKeyboardMarkup(keyboard)
    # 发送这条消息，并附带我们创建的策略按钮
    await context.bot.send_message(chat_id=chat_id, text=strategy_text, reply_markup=reply_markup)
    # 将这条消息也保存到数据库的聊天记录中
    await save_chat_message(user_id, "bot", strategy_text)


# 定义一个异步函数，用于发送图文并茂的注册教程
async def send_registration_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """发送图文并茂的注册和充值教程"""
    # 从 update 对象中获取用户ID
    user_id = update.effective_user.id
    # 从 update 对象中获取聊天ID
    chat_id = update.effective_chat.id

    # --- 教程第一步：注册 ---
    # 定义注册教程的文字说明
    registration_caption = (
        "**Step 1: Registration**\n\n"
        "1. Click the link in our bio.\n"
        "2. Fill in your details.\n"
        "3. Verify your email."
    )
    # 定义一张占位图片
    registration_photo_url = "https://picsum.photos/seed/register/600/400"
    # 发送图片，并将文字说明作为图片的标题
    await context.bot.send_photo(chat_id=chat_id, photo=registration_photo_url, caption=registration_caption,
                                 parse_mode='Markdown')
    # 将这次发送的图片和标题内容，作为一个记录保存到数据库
    await save_chat_message(user_id, "bot", f"[Photo] {registration_caption}")

    # --- 教程第二步：充值 ---
    # 定义充值教程的文字说明
    recharge_caption = (
        "**Step 2: Recharge**\n\n"
        "1. Go to the 'Wallet' section.\n"
        "2. Choose your payment method.\n"
        "3. Complete the payment to start playing!"
    )
    # 定义另一张占位图片
    recharge_photo_url = "https://picsum.photos/seed/recharge/600/400"
    # 发送第二张图片和对应的说明
    await context.bot.send_photo(chat_id=chat_id, photo=recharge_photo_url, caption=recharge_caption,
                                 parse_mode='Markdown')
    # 将这次发送的图片和标题内容，也保存到数据库
    await save_chat_message(user_id, "bot", f"[Photo] {recharge_caption}")

    # --- 引导用户下一步操作 ---
    # 定义一条纯文本消息，告诉用户下一步该做什么
    follow_up_text = "Please follow the guide to register. Let me know when you are done!"
    # 发送这条消息
    await context.bot.send_message(chat_id=chat_id, text=follow_up_text)
    # 将这条消息也保存到数据库
    await save_chat_message(user_id, "bot", follow_up_text)
