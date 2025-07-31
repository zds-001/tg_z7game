# tasks/scheduled_broadcast.py

import logging
import asyncio
import random
from datetime import datetime
from telegram.ext import ContextTypes, Application
from telegram.error import Forbidden  # 导入 Forbidden 错误类型

from services.db_service import get_subscribed_users, update_user_data

logger = logging.getLogger(__name__)


async def broadcast_task(context: ContextTypes.DEFAULT_TYPE):
    """
    定时广播任务。
    这个函数由 python-telegram-bot 的 JobQueue 调用。
    """
    logger.info("开始执行每日广播任务...")

    app: Application = context.application

    subscribed_users = await get_subscribed_users()
    if not subscribed_users:
        logger.info("没有订阅用户，广播任务结束。")
        return

    # --- 您的随机倍率逻辑 ---
    def get_random_multiplier():
        ranges = [
            (2.34, 5.67),
            (5.67, 6.78),
            (6.78, 12.34),
            (12.34, 99.99)
        ]
        weights = [80, 15, 4, 1]  # 对应概率总和为100%
        chosen_range = random.choices(ranges, weights=weights, k=1)[0]
        return str(round(random.uniform(*chosen_range), 2))

    multiplier = get_random_multiplier()
    broadcast_message = f"30s后{multiplier}x 即将发射，快去下注"

    # --- 发送广播，并处理已拉黑的用户 ---
    for user in subscribed_users:
        user_id = user.get("user_id")
        chat_id = user.get("chat_id")

        if not chat_id:
            continue

        try:
            await app.bot.send_message(chat_id=chat_id, text=broadcast_message)
        except Forbidden:
            # 如果用户拉黑了机器人，则自动取消订阅，下次不再发送
            logger.warning(f"用户 {user_id} ({chat_id}) 已拉黑机器人。正在将其取消订阅...")
            await update_user_data(user_id, {'subscribed_to_broadcast': 0})
        except Exception as e:
            # 处理其他错误，比如网络连接问题
            logger.error(f"向 {chat_id} 发送广播失败: {e}")

    # --- 您的随机延迟逻辑 ---
    delay = random.randint(60, 120)
    logger.info(f"将等待 {delay} 秒后发送排行榜...")
    await asyncio.sleep(delay)

    # --- 您的动态排行榜逻辑 ---
    # 重新获取一次订阅列表，因为在上面的循环中可能有人被取消订阅了
    active_subscribers = await get_subscribed_users()
    if not active_subscribers:
        logger.info("没有活跃的订阅用户，不再发送排行榜。")
        return

    GIDnumber = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    results = []
    for _ in range(10):
        random_number = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        number = random.choice(range(500, 1001, 5))
        results.append((random_number, number))

    results.sort(key=lambda x: x[1], reverse=True)

    leaderboard = (
        "🎉 शर्त लाभ रैंकिंग 🎉\n"
        f"本轮游戏编号：{GIDnumber}，爆点倍率：{multiplier}x\n\n"
    )
    for random_number, number in results:
        leaderboard += f"👤user:{random_number}  payout  💰{number}\n"

    # --- 发送排行榜 ---
    for user in active_subscribers:
        chat_id = user.get("chat_id")
        if not chat_id:
            continue
        try:
            await app.bot.send_message(chat_id=chat_id, text=leaderboard)
        except Exception as e:
            logger.error(f"向 {chat_id} 发送排行榜失败: {e}")

    logger.info("广播及排行榜发送完毕。")

