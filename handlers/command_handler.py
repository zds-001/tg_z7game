# handlers/command_handler.py
import asyncio
# 导入 logging 模块，用于记录程序运行信息
import logging
import time

# 从 telegram 库导入 Update, InlineKeyboardButton, InlineKeyboardMarkup 类
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
# 从 telegram.ext 库导入 ContextTypes，它包含了上下文信息
from telegram.ext import ContextTypes
# 导入我们自己写的 AI 服务，用来判断用户意图
from services.ai_service import get_user_intent
# 导入我们自己写的消息处理器，用来处理闲聊
from handlers.message_handler import text_message_handler
# 导入我们自己写的数据库服务，用来操作数据库
from services.db_service import get_user_data, update_user_data, save_chat_message

# 获取一个日志记录器实例，用于在这个文件中打印日志
logger = logging.getLogger(__name__)


# 定义一个异步函数，用于发送服务链接和策略按钮
async def send_service_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """一个独立的函数，用于发送服务链接和策略按钮"""
    # 定义包含可点击链接的文本
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    link_text = "发射前30s通知：[点击这里进入游戏](https://www.example.com)"
    # 定义一个包含三个按钮的键盘布局
    keyboard = [
        # 第一个按钮，显示文字为“策略1”，隐藏数据为 "strategy_1"
        [InlineKeyboardButton("策略1", callback_data="strategy_1")],
        # 第二个按钮
        [InlineKeyboardButton("策略2", callback_data="strategy_2")],
        # 第三个按钮
        [InlineKeyboardButton("策略3 (不可用)", callback_data="disabled_button")],
    ]
    # 将键盘布局包装成一个回复标记对象
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 发送包含链接的消息，并设置解析模式为 Markdown 以便链接生效
    await context.bot.send_message(chat_id=update.effective_chat.id, text=link_text, parse_mode='Markdown')
    # 发送另一条消息，附带我们创建的策略按钮
    await context.bot.send_message(chat_id=update.effective_chat.id, text="请选择你的策略：", reply_markup=reply_markup)


# 定义一个异步函数，用于发送图文并茂的注册教程
async def send_registration_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """发送图文并茂的注册和充值教程"""
    # 获取当前聊天的ID
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # --- 教程第一步：注册 ---
    #先发送一条带链接的文案
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(5)
    registration_link_messgae = (
        "**Step 1: Registration**\n\n"
        "Please use this link to register:\n"
        "https://xz.u7777.net/?dl=dkyay3"
    )
    await context.bot.send_message(chat_id=chat_id, text=registration_link_messgae,parse_mode='Markdown')
    await save_chat_message(user_id, "bot", registration_link_messgae)
    # 定义注册教程的文字说明
    registration_caption = (
        "**Step 1: Registration**\n\n"
        "1. Click the link in our bio.\n"
        "2. Fill in your details.\n"
        "3. Verify your email."
    )
    # 定义一张占位图片
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO) #正在上传照片
    await asyncio.sleep(5)
    registration_photo_url = "https://picsum.photos/seed/register/600/400"
    # 发送图片，并将文字说明作为图片的标题
    await context.bot.send_photo(chat_id=chat_id, photo=registration_photo_url, caption=registration_caption,
                                 parse_mode='Markdown')

    # --- 教程第二步：充值 ---
    # 定义充值教程的文字说明
    recharge_caption = (
        "**Step 2: Recharge**\n\n"
        "1. Go to the 'Wallet' section.\n"
        "2. Choose your payment method.\n"
        "3. Complete the payment to start playing!"
    )
    # 定义另一张占位图片
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
    await asyncio.sleep(5)
    recharge_photo_url = "https://picsum.photos/seed/recharge/600/400"
    # 发送第二张图片和对应的说明
    await context.bot.send_photo(chat_id=chat_id, photo=recharge_photo_url, caption=recharge_caption,
                                 parse_mode='Markdown')

    # --- 新增：引导用户下一步操作 ---
    # 发送一条纯文本消息，告诉用户下一步该做什么
    await context.bot.send_message(
        chat_id=chat_id,
        text="Please follow the guide to register. Let me know when you are done!"
    )


# 定义处理 /start 命令的主函数
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理 /start 命令。
    - 如果用户是已订阅状态，则作为闲聊处理。
    - 如果用户是未订阅状态（或新用户），则重置并开始引导流程。
    """
    # 从 update 对象中获取用户信息
    user = update.effective_user
    # 获取用户ID
    user_id = user.id
    # 获取聊天ID
    chat_id = update.effective_chat.id

    # 从数据库获取该用户的历史数据
    user_data = await get_user_data(user_id)


    # 检查用户数据是否存在，并且 subscribed_to_broadcast 字段的值是否为 1 (True)
    if user_data and user_data.get('subscribed_to_broadcast') == 1:
        # 如果是，就打印一条日志
        logger.info(f"已订阅用户 {user_id} 发送 /start，将作为闲聊处理。")

        # 将这次的 /start 当作一条普通得闲聊消息来处理
        # 获取用户偏好的语言，默认为英语
        language_code = user_data.get('language_code', 'en')
        # 对于已订阅用户，我们可以假设他们处于一个非引导状态，比如 'completed'
        current_state = user_data.get('state', 'completed')

        # 直接调用 AI 服务，获取一句针对 "/start" 的闲聊回复
        intent_data = await get_user_intent(user_id, "/start", language_code, current_state)
        # 从 AI 结果中获取回复内容，如果 AI 没给，就使用一个默认的问候语
        reply = intent_data.get("reply", "Hello again! How can I help you today?")

        # 将这句闲聊回复发送给用户
        await update.message.reply_text(reply)

        # 将这次交互（用户发 /start，机器人回闲聊）保存到数据库
        await save_chat_message(user_id, "user", "/start")
        await save_chat_message(user_id, "bot", reply)

        # 在这里结束函数，不再执行下面的新用户引导流程
        return

    # --- 对于新用户或已取消订阅的用户 ---
    # 只有当用户是新用户或未订阅时，才会执行这里的代码
    logger.info(f"新用户 {user_id} 或未订阅用户，开始引导流程。")

    # 重置所有相关状态，确保一次全新的开始
    await update_user_data(user_id, {
        'username': user.username,
        'first_name': user.first_name,
        'chat_id': chat_id,
        'state': 'awaiting_service_confirmation',  # 将状态设置为“等待确认服务”
        'service_status': 'pending',  # 将服务状态重置为“待定”
        'subscribed_to_broadcast': True,  # 重新将用户标记为“已订阅”
        'push_message_count': 0,  # 重置推送计数
        'chat_message_count': 0,  # 重置闲聊计数
    })
    welcome_message = "Hi there! We offer an exciting gaming service. Are you interested?"
    await update.message.reply_text(welcome_message)
    await save_chat_message(user_id, "bot", welcome_message)
