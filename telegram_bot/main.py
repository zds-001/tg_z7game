# main.py

# 导入 dotenv 库中的 load_dotenv 函数，用于从 .env 文件加载环境变量
from dotenv import load_dotenv
# 导入 logging 模块用于记录日志，os 模块用于读取环境变量
import logging, os
# 从 telegram.ext 库导入 Application 和各种处理器类
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# 导入我们自己写的配置文件
from telegram_bot import config
# 导入我们自己写的服务模块
from services import db_service, ai_service
# 导入我们自己写的处理器模块
from handlers import command_handler, message_handler, callback_handler
# 导入我们自己写的定时任务模块
from tasks import scheduled_broadcast

# 执行函数，加载 .env 文件中的环境变量
load_dotenv()
# 从环境变量中读取 GOOGLE_API_KEY
google_key = os.getenv("GOOGLE_API_KEY")
# 从环境变量中读取 TELEGRAM_BOT_TOKEN
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

# --- 日志记录配置 ---
# 配置日志的基本格式、时间和级别
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# 将 httpx 库的日志级别设为 WARNING，避免打印过多不必要的网络请求信息
logging.getLogger("httpx").setLevel(logging.WARNING)
# 获取一个日志记录器实例，用于在这个文件中打印日志
logger = logging.getLogger(__name__)


# 定义一个异步函数，用于在机器人启动前执行初始化任务
async def post_init_setup(application: Application) -> None:
    """
    在机器人启动前，执行所有异步的初始化任务。
    这个函数会被 ApplicationBuilder 的 post_init 参数调用。
    """
    # 打印一条日志，表示设置已开始
    logger.info("正在执行启动前设置...")

    # 1. 初始化数据库
    await db_service.initialize_database()

    # 2. 初始化 Gemini AI 服务
    # 检查 AI 服务是否初始化成功
    if not ai_service.initialize_gemini(google_key):
        # 如果失败，就打印一条严重的错误日志
        logger.critical("Gemini 初始化失败，机器人将无法正常工作。")
        # 在实际应用中可能需要更复杂的处理，但对于调试，这足够了

    # 3. 设置定时任务
    # 从 application 对象中获取任务队列
    job_queue = application.job_queue
    # 检查任务队列是否存在
    if job_queue:
        # 计算每日广播的间隔时间（秒）
        interval_seconds = (24 * 60 * 60) / config.DAILY_BROADCAST_COUNT
        # 添加一个重复执行的任务
        job_queue.run_repeating(scheduled_broadcast.broadcast_task, interval=interval_seconds, first=10)
        # 打印一条成功日志
        logger.info(f"定时任务已添加，每 {interval_seconds:.2f} 秒执行一次。")
    else:
        # 如果任务队列不存在，就打印一条警告日志
        logger.warning("JobQueue 未启用，无法设置定时任务。")


# 定义主函数，这是程序的入口
def main() -> None:
    """
    主函数，用于配置和启动机器人。
    这是一个同步函数，它将事件循环的管理完全交给 python-telegram-bot 库。
    """

    # 打印一条日志，表示正在构建应用
    logger.info("正在构建机器人应用...")

    # 使用 ApplicationBuilder 来链式配置和构建机器人应用
    application = (
        Application.builder()
        # 设置机器人的 Token
        .token(telegram_token)
        # 注册一个在程序启动后、开始轮询前执行的函数
        .post_init(post_init_setup)
        # 注册一个在程序停止时执行的函数，用来优雅地关闭数据库连接
        .post_stop(db_service.close_pool)
        # 完成构建
        .build()
    )

    # --- 注册消息处理器 ---
    # 添加一个命令处理器，将 /start 命令和 start_command 函数关联起来
    application.add_handler(CommandHandler("start", command_handler.start_command))
    # 添加一个消息处理器，处理所有非命令的文本消息
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler.text_message_handler))
    # 添加一个回调查询处理器，处理所有内联按钮的点击
    application.add_handler(CallbackQueryHandler(callback_handler.button_handler))

    # --- 启动机器人 ---
    # run_polling 是一个阻塞调用，它会启动所有东西并保持运行，直到你按 Ctrl-C
    logger.info("机器人已配置完成，开始轮询...")
    # 开始从 Telegram 服务器获取更新（新消息等）
    application.run_polling()
    # 当程序停止时，打印一条日志
    logger.info("机器人已停止。")


# 检查这个脚本是否是作为主程序直接运行的
if __name__ == "__main__":
    # 如果是，就调用 main() 函数，启动整个程序
    main()
