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
# ENSURE USER (SAFE)
# =========================
async def ensure_user(db, user_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )


# =========================
# GET PROFILE (SAFE)
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
                    "wins": 0
                }

            return dict(row)


# =========================
# UPDATE SAFE BALANCE
# =========================
async def update_crypto(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)

        await db.execute(
            """
            UPDATE users 
            SET crypto = MAX(0, crypto + ?) 
            WHERE user_id = ?
            """,
            (amount, user_id)
        )
        await db.commit()


async def update_pln(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)

        await db.execute(
            """
            UPDATE users 
            SET pln = MAX(0, pln + ?) 
            WHERE user_id = ?
            """,
            (amount, user_id)
        )
        await db.commit()


# =========================
# BANK
# =========================
async def update_bank_crypto(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET bank_crypto = MAX(0, bank_crypto + ?) WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


async def update_bank_pln(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET bank_pln = MAX(0, bank_pln + ?) WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# =========================
# WINS
# =========================
async def add_win(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)

        await db.execute(
            "UPDATE users SET wins = wins + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


# =========================
# SAFE TRANSFER CRYPTO
# =========================
async def transfer_crypto(from_id: int, to_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, from_id)
        await ensure_user(db, to_id)

        await db.execute(
            "UPDATE users SET crypto = MAX(0, crypto - ?) WHERE user_id = ?",
            (amount, from_id)
        )

        await db.execute(
            "UPDATE users SET crypto = crypto + ? WHERE user_id = ?",
            (amount, to_id)
        )

        await db.commit()


# =========================
# SAFE TRANSFER PLN
# =========================
async def transfer_pln(from_id: int, to_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, from_id)
        await ensure_user(db, to_id)

        await db.execute(
            "UPDATE users SET pln = MAX(0, pln - ?) WHERE user_id = ?",
            (amount, from_id)
        )

        await db.execute(
            "UPDATE users SET pln = pln + ? WHERE user_id = ?",
            (amount, to_id)
        )

        await db.commit()


# =========================
# BANK INTEREST (SAFE)
# =========================
async def bank_interest(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)

        await db.execute("""
        UPDATE users
        SET 
            crypto = crypto + CAST(bank_crypto * 0.02 AS INTEGER),
            pln = pln + CAST(bank_pln * 0.02 AS INTEGER)
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()


# =========================
# TOP USERS
# =========================
async def get_top_users(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("""
        SELECT *,
        (crypto + bank_crypto + pln + bank_pln) as total
        FROM users
        ORDER BY total DESC
        LIMIT ?
        """, (limit,)) as cur:

            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# =========================
# LOG TRANSACTIONS
# =========================
async def log_transaction(user_id: int, amount: int, type_: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type) VALUES (?, ?, ?)",
            (user_id, amount, type_)
        )
        await db.commit()
