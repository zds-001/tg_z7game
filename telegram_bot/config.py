
# config.py

# --- API 密钥和配置 ---
# !! 重要 !! 请在下方填入你的真实信息

# 从 @BotFather 获取的 Token
# TELEGRAM_BOT_TOKEN = "7754106550:AAHKoHsnJZmrEVEo1QG_wFBJvj45t2htHsI"
# #AIzaSyDzWa_HtlAKeAT5gxTkIxdYr72fb1LxIRk yixiu
# #"AIzaSyBsDxiwMhn9a-3VAtDnMK9Uk_lItUMmmWM"
# # 从 Google AI Studio 获取的 API Key
# GEMINI_API_KEY = "AIzaSyD2IPIYRFOg8ow9k55XklC3_0N4--VrO9Q"
#
# # 本地数据库文件名
# DATABASE_FILE = "bot_database.db"
#
# # --- 机器人行为配置 ---
#
# # 闲聊对话的最大句数，超过后机器人将不再对闲聊进行回复
# MAX_SMALL_TALK_MESSAGES = 30
#
# # 每日定时广播的次数
# DAILY_BROADCAST_COUNT = 30
#
# # 印度时区，用于定时任务
# TIMEZONE = "Asia/Kolkata"



# config.py

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量 (这主要用于本地开发)
# 在服务器上，我们会直接设置环境变量，所以即使 .env 文件不存在也没关系
load_dotenv()

# --- 从环境变量中读取 API 密钥和配置 ---
# os.getenv('VARIABLE_NAME', 'default_value') 会尝试读取环境变量，如果找不到，则使用默认值
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 代理配置 ---
# 如果您设置了 PROXY_URL 环境变量，程序就会使用它
PROXY_URL = os.getenv("PROXY_URL") # 例如 "http://127.0.0.1:7890"

# --- 本地数据库配置 ---
DATABASE_FILE = "bot_database.db"

# --- 机器人行为配置 (这些不是秘密，所以可以直接写在代码里) ---
MAX_SMALL_TALK_MESSAGES = 30
DAILY_BROADCAST_COUNT = 30
TIMEZONE = "Asia/Kolkata"
