import aiosqlite
import os
from datetime import datetime

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

            last_daily TEXT DEFAULT NULL,
            last_work TEXT DEFAULT NULL,
            last_rob TEXT DEFAULT NULL,

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

        # Migracja - dodaj kolumny jeśli nie istnieją
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_rob TEXT DEFAULT NULL")
        except Exception:
            pass

        await db.commit()


# =========================
# ENSURE USER
# =========================
async def ensure_user(db, user_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    await db.commit()


# =========================
# PROFILE
# =========================
async def get_profile(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await ensure_user(db, user_id)
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}


# =========================
# CRYPTO
# =========================
async def update_crypto(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET crypto = crypto + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# =========================
# PLN
# =========================
async def update_pln(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET pln = pln + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# =========================
# BANK CRYPTO
# =========================
async def update_bank_crypto(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET bank_crypto = bank_crypto + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# =========================
# BANK PLN
# =========================
async def update_bank_pln(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET bank_pln = bank_pln + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# =========================
# WINS
# =========================
async def increment_wins(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET wins = wins + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


# =========================
# COOLDOWNS
# =========================
async def get_cooldown(user_id: int, field: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await ensure_user(db, user_id)
        async with db.execute(
            f"SELECT {field} FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[field] if row else None


async def set_cooldown(user_id: int, field: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        now = datetime.utcnow().isoformat()
        await db.execute(
            f"UPDATE users SET {field} = ? WHERE user_id = ?",
            (now, user_id)
        )
        await db.commit()


# =========================
# LEADERBOARD
# =========================
async def get_leaderboard(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT user_id, crypto, pln, bank_crypto, bank_pln,
                      (crypto + pln + bank_crypto + bank_pln) AS total
               FROM users
               ORDER BY total DESC
               LIMIT ?""",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# =========================
# LOG TRANSACTION
# =========================
async def log_transaction(user_id: int, amount: int, type_: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type) VALUES (?, ?, ?)",
            (user_id, amount, type_)
        )
        await db.commit()


# =========================
# TRANSACTION HISTORY
# =========================
async def get_transactions(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT amount, type, created_at FROM transactions
               WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
