
import os
from dotenv import load_dotenv

load_dotenv()

# --- 代理配置 ---
PROXY_URL = os.getenv("PROXY_URL")
# 本地数据库文件名
# --- MySQL 数据库配置 (从环境变量读取) ---
DB_HOST = os.getenv("DB_HOST") # 您的 Cloud SQL 实例的 IP 地址
DB_USER = os.getenv("DB_USER") # 您创建的数据库用户名 (例如 'bot_user')
DB_PASSWORD = os.getenv("DB_PASSWORD") # 对应的密码
DB_NAME = os.getenv("DB_NAME") # 您创建的数据库名 (例如 'bot_data')






# --- 机器人行为配置 ---
# 闲聊对话的最大句数，超过后机器人将不再对闲聊进行回复
MAX_SMALL_TALK_MESSAGES = 30

# 每日定时广播的次数
DAILY_BROADCAST_COUNT = 1000

# 印度时区，用于定时任务
TIMEZONE = "Asia/Kolkata"

MAX_PUSH_MESSAGES = 90

# config.py

