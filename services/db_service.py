# services/db_service.py

import logging
import aiomysql
from typing import List, Dict, Any

from telegram_bot import config
logger = logging.getLogger(__name__)

pool = None


async def get_pool():
    """获取或创建数据库连接池"""
    global pool
    if pool is None:
        logger.info("Creating database connection pool...")
        pool = await aiomysql.create_pool(
            host=config.DB_HOST,
            port=3306,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            db=config.DB_NAME,
            autocommit=True  # 自动提交事务
        )
    return pool


async def initialize_database():
    """初始化数据库，创建必要的表。"""
    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 创建 users 表 (MySQL 语法)
            await cur.execute("""
                              CREATE TABLE IF NOT EXISTS users
                              (
                                  user_id
                                  BIGINT
                                  PRIMARY
                                  KEY,
                                  username
                                  VARCHAR
                              (
                                  255
                              ),
                                  first_name VARCHAR
                              (
                                  255
                              ),
                                  chat_id BIGINT UNIQUE,
                                  state VARCHAR
                              (
                                  50
                              ),
                                  chat_message_count INT DEFAULT 0,
                                  subscribed_to_broadcast BOOLEAN DEFAULT 1,
                                  service_status VARCHAR
                              (
                                  20
                              ) DEFAULT 'pending',
                                  push_message_count INT DEFAULT 0,
                                  language_code VARCHAR
                              (
                                  10
                              ) DEFAULT 'en'
                                  )
                              """)
            # 创建 chat_history 表
            await cur.execute("""
                              CREATE TABLE IF NOT EXISTS chat_history
                              (
                                  message_id
                                  INT
                                  AUTO_INCREMENT
                                  PRIMARY
                                  KEY,
                                  user_id
                                  BIGINT,
                                  role
                                  VARCHAR
                              (
                                  20
                              ),
                                  text TEXT,
                                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                  FOREIGN KEY
                              (
                                  user_id
                              ) REFERENCES users
                              (
                                  user_id
                              )
                                  )
                              """)
    logger.info(f"数据库 '{config.DB_NAME}' 初始化成功。")


async def get_user_data(user_id: int) -> Dict[str, Any]:
    """根据用户ID获取用户数据"""
    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            return row if row else {}


async def update_user_data(user_id: int, data: Dict[str, Any]):
    """使用 INSERT ... ON DUPLICATE KEY UPDATE 更新或创建用户数据"""
    data['user_id'] = user_id

    columns = ', '.join(f"`{k}`" for k in data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    updates = ', '.join(f"`{k}` = VALUES(`{k}`)" for k in data.keys())

    sql = f"INSERT INTO users ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"

    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, tuple(data.values()))


async def get_chat_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """获取用户的对话历史"""
    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            sql = "SELECT role, text FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s"
            await cur.execute(sql, (user_id, limit))
            rows = await cur.fetchall()
            return list(reversed(rows))


async def save_chat_message(user_id: int, role: str, text: str):
    """保存单条对话消息到数据库"""
    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = "INSERT INTO chat_history (user_id, role, text) VALUES (%s, %s, %s)"
            await cur.execute(sql, (user_id, role, text))


async def get_subscribed_users() -> List[Dict[str, Any]]:
    """获取所有符合条件的订阅用户信息"""
    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            sql = """
                  SELECT user_id, chat_id, language_code \
                  FROM users
                  WHERE service_status = 'confirmed'
                    AND subscribed_to_broadcast = 1
                    AND chat_id IS NOT NULL
                    AND push_message_count < %s \
                  """
            await cur.execute(sql, (config.MAX_PUSH_MESSAGES,))
            return await cur.fetchall()


async def increment_push_count(user_id: int):
    """为指定用户增加一次推送计数"""
    db_pool = await get_pool()
    async with db_pool.acquire() as conn:
        async with conn.cursor() as cur:
            sql = "UPDATE users SET push_message_count = push_message_count + 1 WHERE user_id = %s"
            await cur.execute(sql, (user_id,))

