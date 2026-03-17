"""SQLite database operations."""

import aiosqlite
from pathlib import Path

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    subscription TEXT DEFAULT 'free',
    subscription_until TEXT,
    stores_limit INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT DEFAULT '',
    api_key TEXT NOT NULL,
    added_at TEXT DEFAULT (datetime('now')),
    last_check TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS penalties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER NOT NULL,
    rrd_id INTEGER,
    srid TEXT,
    penalty_date TEXT,
    amount REAL NOT NULL,
    reason TEXT DEFAULT '',
    supply_id INTEGER,
    nm_id INTEGER,
    brand_name TEXT DEFAULT '',
    sa_name TEXT DEFAULT '',
    subject_name TEXT DEFAULT '',
    appeal_deadline TEXT,
    notified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (store_id) REFERENCES stores(id)
);

CREATE INDEX IF NOT EXISTS idx_penalties_store ON penalties(store_id);
CREATE INDEX IF NOT EXISTS idx_penalties_srid ON penalties(srid);
CREATE INDEX IF NOT EXISTS idx_stores_user ON stores(user_id);
"""


async def init_db():
    """Initialize database and create tables."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.execute("PRAGMA journal_mode=WAL")
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Get database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


# --- Users ---

async def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        await db.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(await cursor.fetchone())


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_subscription(user_id: int, plan: str, until: str | None, limit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET subscription=?, subscription_until=?, stores_limit=?, updated_at=datetime('now') WHERE user_id=?",
            (plan, until, limit, user_id),
        )
        await db.commit()


# --- Stores ---

async def add_store(user_id: int, api_key: str, name: str = "") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO stores (user_id, api_key, name) VALUES (?, ?, ?)",
            (user_id, api_key, name),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_stores(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM stores WHERE user_id = ? AND is_active = 1 ORDER BY added_at",
            (user_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_store(store_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_store(store_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE stores SET is_active = 0 WHERE id = ?", (store_id,))
        await db.commit()


async def get_user_store_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM stores WHERE user_id = ? AND is_active = 1",
            (user_id,),
        )
        row = await cursor.fetchone()
        return row[0]


async def update_store_last_check(store_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE stores SET last_check = datetime('now') WHERE id = ?",
            (store_id,),
        )
        await db.commit()


async def get_all_active_stores() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT s.*, u.user_id as owner_id FROM stores s "
            "JOIN users u ON s.user_id = u.user_id "
            "WHERE s.is_active = 1"
        )
        return [dict(r) for r in await cursor.fetchall()]


# --- Penalties ---

async def penalty_exists(store_id: int, srid: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM penalties WHERE store_id = ? AND srid = ?",
            (store_id, srid),
        )
        return await cursor.fetchone() is not None


async def save_penalty(store_id: int, data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO penalties
            (store_id, rrd_id, srid, penalty_date, amount, reason, supply_id,
             nm_id, brand_name, sa_name, subject_name, appeal_deadline, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                store_id,
                data.get("rrd_id"),
                data.get("srid", ""),
                data.get("penalty_date", ""),
                data.get("amount", 0),
                data.get("reason", ""),
                data.get("supply_id"),
                data.get("nm_id"),
                data.get("brand_name", ""),
                data.get("sa_name", ""),
                data.get("subject_name", ""),
                data.get("appeal_deadline", ""),
                0,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_penalties(user_id: int, limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT p.*, s.name as store_name
            FROM penalties p
            JOIN stores s ON p.store_id = s.id
            WHERE s.user_id = ? AND s.is_active = 1
            ORDER BY p.created_at DESC LIMIT ?""",
            (user_id, limit),
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_user_penalty_stats(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT
                COUNT(*) as total_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(CASE WHEN penalty_date >= date('now', '-30 days') THEN amount ELSE 0 END), 0) as month_amount,
                COALESCE(SUM(CASE WHEN penalty_date >= date('now', '-7 days') THEN amount ELSE 0 END), 0) as week_amount
            FROM penalties p
            JOIN stores s ON p.store_id = s.id
            WHERE s.user_id = ? AND s.is_active = 1""",
            (user_id,),
        )
        row = await cursor.fetchone()
        return {
            "total_count": row[0],
            "total_amount": row[1],
            "month_amount": row[2],
            "week_amount": row[3],
        }


async def mark_penalty_notified(penalty_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE penalties SET notified = 1 WHERE id = ?", (penalty_id,)
        )
        await db.commit()


# --- Admin stats ---

async def get_bot_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        users = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM stores WHERE is_active = 1")
        stores = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM penalties")
        penalties = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE subscription = 'pro'")
        pro_users = (await cursor.fetchone())[0]
        return {
            "users": users,
            "stores": stores,
            "penalties": penalties,
            "pro_users": pro_users,
        }
