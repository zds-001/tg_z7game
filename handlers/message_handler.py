# handlers/message_handler.py

# 导入 logging 模块，用于记录程序运行信息
import logging
# 从 typing 模块导入 Dict 类型，用于类型提示，让代码更规范
from typing import Dict
# 从 telegram 库导入 Update 类，它包含了所有收到的更新信息（比如消息）
from telegram import Update
# 从 telegram.ext 库导入 ContextTypes，它包含了上下文信息，比如机器人实例
from telegram.ext import ContextTypes

# 导入我们自己写的配置文件
from telegram_bot import config
# 导入我们自己写的语言检测工具
from utils.language_detector import detect_language
# 导入我们自己写的 AI 服务，用来判断用户意图
from services.ai_service import get_user_intent
# 导入我们自己写的数据库服务，用来操作数据库
from services.db_service import get_user_data, update_user_data, save_chat_message
# 从我们创建的公共回复模块中，导入发送链接和注册指南的函数
from handlers.common_replies import send_service_link, send_registration_guide

# 获取一个日志记录器实例，用于在这个文件中打印日志
logger = logging.getLogger(__name__)


# 定义一个异步函数，用于发送注册提醒
async def registration_reminder(context: ContextTypes.DEFAULT_TYPE):
    """提醒用户是否注册完成"""
    # 从上下文中获取 job 对象，它包含了定时任务的信息
    job = context.job
    # 从 job 对象中获取当时设置的用户ID
    user_id = job.user_id
    # 从 job 对象中获取当时设置的聊天ID
    chat_id = job.chat_id

    # 从数据库获取该用户的最新数据
    user_data = await get_user_data(user_id)
    # 检查用户的状态是否仍然是“等待注册确认”
    if user_data.get('state') == 'awaiting_registration_confirmation':
        # 如果是，就发送一条提醒消息
        reminder_message = "Hi! Have you completed the registration? Let me know if you are ready."
        # 使用机器人实例发送消息
        await context.bot.send_message(chat_id=chat_id, text=reminder_message)
        # 将这条提醒消息也保存到数据库的聊天记录中
        await save_chat_message(user_id, "bot", reminder_message)


# 定义处理所有文本消息的主函数
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理所有文本消息，作为一个状态机"""
    # 如果收到的更新里没有消息，或者消息里没有文本，就直接返回，不做任何处理
    if not update.message or not update.message.text:
        return

    # 从 update 对象中获取用户ID
    user_id = update.effective_user.id
    # 从 update 对象中获取用户发送的文本消息
    user_message = update.message.text
    # 将用户发送的这条消息保存到数据库
    await save_chat_message(user_id, "user", user_message)

    # 从数据库获取该用户的完整数据
    user_data = await get_user_data(user_id)
    # 获取用户当前所处的对话状态，如果没记录，则默认为 'started'
    current_state = user_data.get('state', 'started')
    # 获取用户偏好的语言，如果没记录，则默认为 'en' (英语)
    language_code = user_data.get('language_code', 'en')

    # 调用语言检测工具，判断用户最新消息的语言
    detected_lang = detect_language(user_message)
    # 如果检测到的语言和数据库里存的不一样
    if language_code != detected_lang:
        # 就更新数据库里该用户的偏好语言
        language_code = detected_lang
        await update_user_data(user_id, {'language_code': language_code})

    # 检查用户当前是否处于“等待输入用户ID”的状态
    if current_state == 'awaiting_user_id':
        # 如果是，就判断用户发来的消息是不是9位纯数字
        if user_message.isdigit() and len(user_message) == 9:
            # 如果是，就打印一条成功日志
            logger.info(f"用户 {user_id} 提供了有效的ID: {user_message}")
            # 在数据库里记录一下
            await save_chat_message(user_id, "bot", "User ID validation successful.")
            # 回复用户注册成功
            await update.message.reply_text("Thank you! Your registration is successful.")
            # 发送游戏链接和策略按钮
            await send_service_link(update, context)
            # 更新用户的状态为“已完成”，并将会员状态设为“已确认”
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        else:
            # 如果不是9位纯数字，就打印一条警告日志
            logger.warning(f"用户 {user_id} 提供了无效的ID: {user_message}")
            # 回复用户ID无效，让他重试
            await update.message.reply_text("The ID seems invalid. It must be a 9-digit number. Please try again.")
            # 在数据库里记录一下
            await save_chat_message(user_id, "bot", "Invalid ID provided.")
        # 无论ID是否有效，处理完就直接返回，不再执行下面的AI判断
        return

    # 对于其他所有状态，调用AI服务来判断用户的意图
    intent_data = await get_user_intent(user_id, user_message, language_code, current_state)
    # 从AI返回的结果中获取意图标签
    intent = intent_data.get("intent")
    # 从AI返回的结果中获取建议的回复内容
    reply = intent_data.get("reply")

    # 检查用户当前是否处于“等待确认服务”的状态
    if current_state == 'awaiting_service_confirmation':
        # 如果用户的意图是“需要服务”
        if intent == 'service_request':
            # 就向用户提问“您以前玩过我们的游戏吗？”
            question = "Great! Have you played our game before?"
            await update.message.reply_text(question)
            await save_chat_message(user_id, "bot", question)
            # 并将用户的状态更新为“等待确认游戏经验”
            await update_user_data(user_id, {'state': 'awaiting_experience_confirmation'})
        # 如果用户的意图是“拒绝”
        elif intent == 'rejection':
            # 就回复AI生成的礼貌拒绝语
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)
        # 如果是其他意图（比如闲聊）
        else:
            # 就回复AI生成的闲聊内容
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)

    # 检查用户当前是否处于“等待确认游戏经验”的状态
    elif current_state == 'awaiting_experience_confirmation':
        # 如果用户的意图是“玩过”
        if intent == 'played_before':
            # 就直接发送游戏链接和策略按钮
            await send_service_link(update, context)
            await save_chat_message(user_id, "bot", "Service link sent.")
            # 并将用户的状态更新为“已完成”，会员状态设为“已确认”
            await update_user_data(user_id, {'state': 'completed', 'service_status': 'confirmed'})
        # 如果用户的意图是“没玩过”（新玩家）
        elif intent == 'new_player':
            # 就发送注册和充值教程
            await send_registration_guide(update, context)
            await save_chat_message(user_id, "bot", "Registration guide sent.")
            # 并将用户的状态更新为“等待注册确认”
            await update_user_data(user_id, {'state': 'awaiting_registration_confirmation'})
            # 同时，设置一个2分钟后触发的一次性定时任务，用来提醒用户
            context.job_queue.run_once(
                registration_reminder,  # 要执行的函数
                120,  # 延迟时间（秒）
                chat_id=update.effective_chat.id,  # 将聊天ID传给任务
                user_id=user_id,  # 将用户ID传给任务
                name=f"reminder_{user_id}"  # 给任务起个唯一的名字
            )
        # 如果是其他意图（比如闲聊）
        else:
            # 就回复AI生成的闲聊内容
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)

    # 检查用户当前是否处于“等待注册确认”的状态
    elif current_state == 'awaiting_registration_confirmation':
        # 如果用户的意图是“注册完成”
        if intent == 'registration_complete':
            # 就向用户提问，索要他的用户ID
            question = "Awesome! Please send me your 9-digit User ID to complete the process."
            await update.message.reply_text(question)
            await save_chat_message(user_id, "bot", question)
            # 并将用户的状态更新为“等待输入用户ID”
            await update_user_data(user_id, {'state': 'awaiting_user_id'})
        # 如果是其他意图（比如闲聊或说“还没好”）
        else:
            # 就回复AI生成的闲聊内容
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)

    # 如果用户不处于以上任何一个引导流程中
    else:
        # 就当作普通闲聊处理
        # 获取用户已经闲聊的次数
        chat_count = user_data.get('chat_message_count', 0)
        # 检查是否小于设定的上限（30次）
        if chat_count < config.MAX_SMALL_TALK_MESSAGES:
            # 如果没到上限，就正常回复闲聊
            await update.message.reply_text(reply)
            await save_chat_message(user_id, "bot", reply)
            # 并将闲聊次数加一
            await update_user_data(user_id, {'chat_message_count': chat_count + 1})
        else:
            # 如果已达到上限，就发送固定的额度用尽提示
            limit_reply = "Your chat quota has been used up. If you need our service, please use /start again."
            await update.message.reply_text(limit_reply)
            await save_chat_message(user_id, "bot", limit_reply)
