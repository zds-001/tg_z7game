# services/db_service.py

import logging
import aiosqlite
from typing import List, Dict, Any

import config

logger = logging.getLogger(__name__)

DB_FILE = config.DATABASE_FILE


async def initialize_database():
    """初始化数据库，创建必要的表。"""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                             user_id
                             INTEGER
                             PRIMARY
                             KEY,
                             username
                             TEXT,
                             first_name
                             TEXT,
                             chat_id
                             INTEGER
                             UNIQUE,
                             state
                             TEXT,
                             chat_message_count
                             INTEGER
                             DEFAULT
                             0,
                             subscribed_to_broadcast
                             BOOLEAN
                             DEFAULT
                             1
                         )
                         """)
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS chat_history
                         (
                             message_id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             user_id
                             INTEGER,
                             role
                             TEXT,
                             text
                             TEXT,
                             timestamp
                             DATETIME
                             DEFAULT
                             CURRENT_TIMESTAMP,
                             FOREIGN
                             KEY
                         (
                             user_id
                         ) REFERENCES users
                         (
                             user_id
                         )
                             )
                         """)
        await db.commit()
    logger.info(f"数据库 '{DB_FILE}' 初始化成功。")


async def get_user_data(user_id: int) -> Dict[str, Any]:
    """根据用户ID获取用户数据"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}


async def update_user_data(user_id: int, data: Dict[str, Any]):
    """使用 INSERT OR REPLACE 更新或创建用户数据"""
    data['user_id'] = user_id

    current_data = await get_user_data(user_id)
    final_data = {**current_data, **data}

    columns = ', '.join(final_data.keys())
    placeholders = ', '.join('?' for _ in final_data)
    sql = f"INSERT OR REPLACE INTO users ({columns}) VALUES ({placeholders})"

    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(sql, tuple(final_data.values()))
        await db.commit()


async def get_chat_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """获取用户的对话历史"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        sql = "SELECT role, text FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?"
        async with db.execute(sql, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in reversed(rows)]


async def save_chat_message(user_id: int, role: str, text: str):
    """保存单条对话消息到数据库"""
    async with aiosqlite.connect(DB_FILE) as db:
        sql = "INSERT INTO chat_history (user_id, role, text) VALUES (?, ?, ?)"
        await db.execute(sql, (user_id, role, text))
        await db.commit()


async def get_subscribed_users() -> List[Dict[str, Any]]:
    """获取所有订阅了广播的用户信息 (user_id 和 chat_id)"""
    async with aiosqlite.connect(DB_FILE) as db:
        db.row_factory = aiosqlite.Row
        # 确保这里查询了 user_id 和 chat_id 两列
        sql = "SELECT user_id, chat_id FROM users WHERE subscribed_to_broadcast = 1 AND chat_id IS NOT NULL"
        async with db.execute(sql) as cursor:
            rows = await cursor.fetchall()
            # 返回字典列表
            return [dict(row) for row in rows]
