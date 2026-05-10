import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "economy.db")


# =========================
# INIT DB
# =========================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,

            crypto INTEGER DEFAULT 0,
            pln INTEGER DEFAULT 0,

            bank_crypto INTEGER DEFAULT 0,
            bank_pln INTEGER DEFAULT 0,

            wins INTEGER DEFAULT 0,

            total_earned INTEGER DEFAULT 0,
            total_lost INTEGER DEFAULT 0,

            last_daily TEXT DEFAULT NULL,
            last_work TEXT DEFAULT NULL,

            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)

        await db.commit()


# =========================
# ENSURE USER
# =========================
async def ensure_user(db, user_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )


# =========================
# GET PROFILE
# =========================
async def get_profile(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        await ensure_user(db, user_id)

        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()

            if not row:
                return {
                    "crypto": 0,
                    "pln": 0,
                    "bank_crypto": 0,
                    "bank_pln": 0,
                    "wins": 0,
                    "last_daily": None,
                    "last_work": None
                }

            return dict(row)


# =========================
# CRYPTO
# =========================
async def update_crypto(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)

        await db.execute("""
        UPDATE users
        SET crypto = crypto + ?
        WHERE user_id = ?
        """, (amount,
