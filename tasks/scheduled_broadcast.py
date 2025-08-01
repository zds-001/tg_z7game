# tasks/scheduled_broadcast.py

import logging
import asyncio
import random
from datetime import datetime
from telegram.ext import ContextTypes, Application
from telegram.error import Forbidden

from services.db_service import get_subscribed_users, update_user_data, increment_push_count

logger = logging.getLogger(__name__)


async def broadcast_task(context: ContextTypes.DEFAULT_TYPE):
    """定时广播任务，根据用户语言发送不同内容。"""
    logger.info("开始执行每日广播任务...")
    app: Application = context.application

    subscribed_users = await get_subscribed_users()
    if not subscribed_users:
        logger.info("没有符合条件的订阅用户，广播任务结束。")
        return

    # --- 您的随机倍率逻辑 ---
    def get_random_multiplier():
        ranges = [(2.34, 5.67), (5.67, 6.78), (6.78, 12.34), (12.34, 99.99)]
        weights = [80, 15, 4, 1]
        chosen_range = random.choices(ranges, weights=weights, k=1)[0]
        return str(round(random.uniform(*chosen_range), 2))

    multiplier = get_random_multiplier()

    # --- 创建不同语言版本的消息 ---
    broadcast_message_en = f"30s later, {multiplier}x is about to launch, hurry up and place your bets"
    broadcast_message_hi = f"30 सेकंड में {multiplier}x लॉन्च होने वाला है, जल्दी करें और अपना दांव लगाएं"

    successfully_sent_user_ids = []
    for user in subscribed_users:
        user_id = user.get("user_id")
        chat_id = user.get("chat_id")
        language_code = user.get("language_code", "en")  # 默认为英文
        if not chat_id: continue

        # 根据用户语言选择消息
        message_to_send = broadcast_message_hi if language_code == 'hi' else broadcast_message_en

        try:
            await app.bot.send_message(chat_id=chat_id, text=message_to_send)
            successfully_sent_user_ids.append(user_id)
        except Forbidden:
            logger.warning(f"用户 {user_id} ({chat_id}) 已拉黑机器人。正在将其取消订阅...")
            await update_user_data(user_id, {'subscribed_to_broadcast': 0})
        except Exception as e:
            logger.error(f"向 {chat_id} 发送广播失败: {e}")

    for user_id in successfully_sent_user_ids:
        await increment_push_count(user_id)
    logger.info(f"已为 {len(successfully_sent_user_ids)} 名用户增加推送计数。")

    delay = random.randint(60, 120)
    logger.info(f"将等待 {delay} 秒后发送排行榜...")
    await asyncio.sleep(delay)

    if not successfully_sent_user_ids:
        logger.info("没有成功接收消息的用户，不再发送排行榜。")
        return

    GIDnumber = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    results = []
    for _ in range(10):
        random_number = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        number = random.choice(range(500, 1001, 5))
        results.append((random_number, number))
    results.sort(key=lambda x: x[1], reverse=True)

    # --- 创建不同语言版本的排行榜 ---
    leaderboard_en = (
        "🎉 Bet Profit Ranking 🎉\n"
        f"Round ID: {GIDnumber}, Multiplier: {multiplier}x\n\n"
    )
    leaderboard_hi = (
        "🎉 शर्त लाभ रैंकिंग 🎉\n"
        f"इस दौर का खेल नंबर: {GIDnumber}, विस्फोट बिंदु गुणक: {multiplier}x\n\n"
    )
    for random_number, number in results:
        leaderboard_en += f"👤user:{random_number}  payout  💰{number}\n"
        leaderboard_hi += f"👤user:{random_number}  payout  💰{number}\n"

    for user in subscribed_users:
        if user.get("user_id") in successfully_sent_user_ids:
            chat_id = user.get("chat_id")
            language_code = user.get("language_code", "en")
            if not chat_id: continue

            leaderboard_to_send = leaderboard_hi if language_code == 'hi' else leaderboard_en

            try:
                await app.bot.send_message(chat_id=chat_id, text=leaderboard_to_send)
            except Exception as e:
                logger.error(f"向 {chat_id} 发送排行榜失败: {e}")

    logger.info("广播及排行榜发送完毕。")
