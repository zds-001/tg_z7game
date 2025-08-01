# main.py
from dotenv import load_dotenv
import logging,os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
#备注查一下
# 导入配置和各个模块
from telegram_bot import config
from services import db_service, ai_service
from handlers import command_handler, message_handler, callback_handler
from tasks import scheduled_broadcast
load_dotenv()
google_key = os.getenv("GOOGLE_API_KEY")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
# --- 日志记录配置 ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def post_init_setup(application: Application) -> None:
    """
    在机器人启动前，执行所有异步的初始化任务。
    这个函数会被 ApplicationBuilder 的 post_init 参数调用。
    """
    logger.info("正在执行启动前设置...")

    # 1. 初始化本地 SQLite 数据库
    await db_service.initialize_database()

    # 2. 初始化 Gemini 服务 (这是一个同步函数，直接调用即可)
    if not ai_service.initialize_gemini(google_key):
        logger.critical("Gemini 初始化失败，机器人将无法正常工作。")
        # 在实际应用中可能需要更复杂的处理，但对于调试，这足够了

    # 3. 设置定时任务
    job_queue = application.job_queue
    if job_queue:
        interval_seconds = (24 * 60 * 60) / config.DAILY_BROADCAST_COUNT
        job_queue.run_repeating(scheduled_broadcast.broadcast_task, interval=interval_seconds, first=10)
        logger.info(f"定时任务已添加，每 {interval_seconds:.2f} 秒执行一次。")
    else:
        logger.warning("JobQueue 未启用，无法设置定时任务。")


def main() -> None:
    """
    主函数，用于配置和启动机器人。
    这是一个同步函数，它将事件循环的管理完全交给 python-telegram-bot 库。
    """

    logger.info("正在构建机器人应用...")

    # 使用 post_init hook 来执行异步的设置任务
    application = (
        Application.builder()
        .token(telegram_token)
        .post_init(post_init_setup)
        .post_stop(db_service.close_pool)
        .build()
    )

    # --- 注册消息处理器 ---
    application.add_handler(CommandHandler("start", command_handler.start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.text_message_handler))
    application.add_handler(CallbackQueryHandler(callback_handler.button_handler))

    # --- 启动机器人 ---
    # run_polling 是一个阻塞调用，它会启动所有东西并保持运行，直到你按 Ctrl-C
    logger.info("机器人已配置完成，开始轮询...")
    application.run_polling()
    logger.info("机器人已停止。")


if __name__ == "__main__":
    main()

