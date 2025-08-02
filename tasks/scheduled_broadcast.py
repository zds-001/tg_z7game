# tasks/scheduled_broadcast.py

# 导入 logging 模块，用于记录程序运行信息
import logging
# 导入 asyncio 模块，用于处理异步操作，比如 sleep
import asyncio
# 导入 random 模块，用于生成随机数
import random
# 从 datetime 模块导入 datetime 类，用于获取当前时间
from datetime import datetime
# 从 telegram.ext 库导入 ContextTypes 和 Application 类
from telegram.ext import ContextTypes, Application
# 从 telegram.error 库导入 Forbidden 错误类型，专门用来处理用户拉黑机器人的情况
from telegram.error import Forbidden

# 导入我们自己写的数据库服务中的函数
from services.db_service import get_subscribed_users, update_user_data, increment_push_count

# 获取一个日志记录器实例，用于在这个文件中打印日志
logger = logging.getLogger(__name__)


# 定义一个异步函数，作为我们的定时广播任务
async def broadcast_task(context: ContextTypes.DEFAULT_TYPE):
    """定时广播任务，根据用户语言发送不同内容。"""
    # 打印一条日志，表示任务已开始
    logger.info("开始执行每日广播任务...")
    # 从上下文中获取 application 对象，它包含了机器人实例
    app: Application = context.application

    # 从数据库获取所有符合条件的订阅用户信息
    subscribed_users = await get_subscribed_users()
    # 如果没有找到任何用户
    if not subscribed_users:
        # 打印一条日志，然后直接返回，结束本次任务
        logger.info("没有符合条件的订阅用户，广播任务结束。")
        return

    # --- 您的随机倍率逻辑 ---
    # 定义一个内部函数，用于生成随机倍率
    def get_random_multiplier():
        # 定义几个倍率范围
        ranges = [(2.34, 5.67), (5.67, 6.78), (6.78, 12.34), (12.34, 99.99)]
        # 定义每个范围对应的权重（概率）
        weights = [80, 15, 4, 1]
        # 根据权重随机选择一个范围
        chosen_range = random.choices(ranges, weights=weights, k=1)[0]
        # 在选定的范围内生成一个随机浮点数，并保留两位小数
        return str(round(random.uniform(*chosen_range), 2))

    # 调用函数，生成本次广播的倍率
    multiplier = get_random_multiplier()

    # --- 创建不同语言版本的消息 ---
    # 创建英文版的广播消息
    broadcast_message_en = f"30s later, {multiplier}x is about to launch, hurry up and place your bets"
    # 创建印地语版的广播消息
    broadcast_message_hi = f"30 सेकंड में {multiplier}x लॉन्च होने वाला है, जल्दी करें और अपना दांव लगाएं"

    # 创建一个空列表，用来记录成功发送了消息的用户ID
    successfully_sent_user_ids = []
    # 遍历所有订阅用户
    for user in subscribed_users:
        # 获取用户ID
        user_id = user.get("user_id")
        # 获取聊天ID
        chat_id = user.get("chat_id")
        # 获取用户的偏好语言，如果没记录，则默认为 'en' (英语)
        language_code = user.get("language_code", "en")
        # 如果聊天ID不存在，就跳过这个用户
        if not chat_id: continue

        # 根据用户的偏好语言，选择要发送的消息版本
        message_to_send = broadcast_message_hi if language_code == 'hi' else broadcast_message_en

        # 使用 try...except 结构来捕获发送过程中可能发生的错误
        try:
            # 尝试发送消息
            await app.bot.send_message(chat_id=chat_id, text=message_to_send)
            # 如果发送成功，就将该用户的ID添加到成功列表中
            successfully_sent_user_ids.append(user_id)
        # 如果捕获到的是 Forbidden 错误（用户拉黑了机器人）
        except Forbidden:
            # 打印一条警告日志
            logger.warning(f"用户 {user_id} ({chat_id}) 已拉黑机器人。正在将其取消订阅...")
            # 在数据库中将该用户的订阅状态更新为 0 (False)
            await update_user_data(user_id, {'subscribed_to_broadcast': 0})
        # 如果捕获到的是其他类型的错误（比如网络问题）
        except Exception as e:
            # 打印一条错误日志
            logger.error(f"向 {chat_id} 发送广播失败: {e}")

    # 遍历所有成功接收到消息的用户
    for user_id in successfully_sent_user_ids:
        # 为他们每个人在数据库里的推送次数加一
        await increment_push_count(user_id)
    # 打印一条日志，记录本次操作
    logger.info(f"已为 {len(successfully_sent_user_ids)} 名用户增加推送计数。")

    # 生成一个60到120秒之间的随机延迟时间
    delay = random.randint(60, 120)
    # 打印日志，告知将要等待
    logger.info(f"将等待 {delay} 秒后发送排行榜...")
    # 异步等待指定的秒数
    await asyncio.sleep(delay)

    # 如果没有任何用户成功收到第一条消息
    if not successfully_sent_user_ids:
        # 打印日志，然后直接返回，不再发送排行榜
        logger.info("没有成功接收消息的用户，不再发送排行榜。")
        return

    # 生成一个16位的随机游戏ID
    GIDnumber = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    # 创建一个空列表，用来存放排行榜结果
    results = []
    # 循环10次，生成10条排行榜记录
    for _ in range(10):
        # 生成一个9位的随机用户ID
        random_number = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        # 生成一个500到1000之间的、步长为5的随机数字
        number = random.choice(range(500, 1001, 5))
        # 将生成的记录添加到结果列表中
        results.append((random_number, number))
    # 按照 payout 数字从高到低对结果进行排序
    results.sort(key=lambda x: x[1], reverse=True)

    # --- 创建不同语言版本的排行榜 ---
    # 创建英文版的排行榜标题
    leaderboard_en = (
        "🎉 Bet Profit Ranking 🎉\n"
        f"Round ID: {GIDnumber}, Multiplier: {multiplier}x\n\n"
    )
    # 创建印地语版的排行榜标题
    leaderboard_hi = (
        "🎉 शर्त लाभ रैंकिंग 🎉\n"
        f"इस दौर का खेल नंबर: {GIDnumber}, विस्फोट बिंदु गुणक: {multiplier}x\n\n"
    )
    # 遍历排序后的结果
    for random_number, number in results:
        # 将每一条记录追加到两个语言版本的排行榜字符串中
        leaderboard_en += f"👤user:{random_number}  payout  💰{number}\n"
        leaderboard_hi += f"👤user:{random_number}  payout  💰{number}\n"

    # 再次遍历所有订阅用户
    for user in subscribed_users:
        # 检查这个用户是否在成功收到第一条消息的列表中
        if user.get("user_id") in successfully_sent_user_ids:
            # 获取聊天ID
            chat_id = user.get("chat_id")
            # 获取用户的偏好语言
            language_code = user.get("language_code", "en")
            # 如果聊天ID不存在，就跳过
            if not chat_id: continue

            # 根据用户的偏好语言，选择要发送的排行榜版本
            leaderboard_to_send = leaderboard_hi if language_code == 'hi' else leaderboard_en

            # 尝试发送排行榜
            try:
                await app.bot.send_message(chat_id=chat_id, text=leaderboard_to_send)
            # 如果发送失败，就打印一条错误日志
            except Exception as e:
                logger.error(f"向 {chat_id} 发送排行榜失败: {e}")

    # 打印一条日志，表示所有任务已完成
    logger.info("广播及排行榜发送完毕。")
