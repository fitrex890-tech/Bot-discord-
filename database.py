import aiosqlite
import os
from datetime import datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "economy.db")


# =========================
# INIT DB
# =========================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            crypto      INTEGER DEFAULT 0,
            pln         INTEGER DEFAULT 0,
            bank_crypto INTEGER DEFAULT 0,
            bank_pln    INTEGER DEFAULT 0,
            wins        INTEGER DEFAULT 0,
            last_daily  TEXT    DEFAULT NULL,
            last_work   TEXT    DEFAULT NULL,
            last_rob    TEXT    DEFAULT NULL,
            last_beg    TEXT    DEFAULT NULL,
            last_crime  TEXT    DEFAULT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            amount     INTEGER,
            type       TEXT,
            note       TEXT    DEFAULT NULL,
            created_at TEXT    DEFAULT (datetime('now'))
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            item_id    TEXT    NOT NULL,
            active     INTEGER DEFAULT 1,
            expires_at TEXT    DEFAULT NULL,
            bought_at  TEXT    DEFAULT (datetime('now'))
        )
        """)

        # Migracje — bezpieczne, ignoruje błędy gdy kolumna już istnieje
        for col in [
            "ALTER TABLE users ADD COLUMN last_rob   TEXT DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN last_beg   TEXT DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN last_crime TEXT DEFAULT NULL",
            "ALTER TABLE transactions ADD COLUMN note TEXT DEFAULT NULL",
        ]:
            try:
                await db.execute(col)
            except Exception:
                pass

        await db.commit()


# =========================
# ENSURE USER
# =========================
async def ensure_user(db, user_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
    )
    await db.commit()


# =========================
# GET PROFILE (pełne dane)
# =========================
async def get_profile(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await ensure_user(db, user_id)
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}


# =========================
# GET USER — alias używany przez shop/giveaway
# Zwraca dict z kluczem "balance" = crypto (portfel)
# =========================
async def get_user(user_id: int) -> dict:
    data = await get_profile(user_id)
    data["balance"] = data.get("crypto", 0)
    return data


# =========================
# UPDATE BALANCE — alias używany przez giveaway/shop
# Aktualizuje pole crypto (portfel)
# =========================
async def update_balance(user_id: int, amount: int):
    await update_crypto(user_id, amount)


# =========================
# CRYPTO
# =========================
async def update_crypto(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET crypto = MAX(0, crypto + ?) WHERE user_id = ?",
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
            "UPDATE users SET pln = MAX(0, pln + ?) WHERE user_id = ?",
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
            "UPDATE users SET bank_crypto = MAX(0, bank_crypto + ?) WHERE user_id = ?",
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
            "UPDATE users SET bank_pln = MAX(0, bank_pln + ?) WHERE user_id = ?",
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
            "UPDATE users SET wins = wins + 1 WHERE user_id = ?", (user_id,)
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
            f"UPDATE users SET {field} = ? WHERE user_id = ?", (now, user_id)
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
               FROM users ORDER BY total DESC LIMIT ?""",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# =========================
# LOG TRANSACTION
# =========================
async def log_transaction(user_id: int, amount: int, type_: str, note: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type, note) VALUES (?, ?, ?, ?)",
            (user_id, amount, type_, note)
        )
        await db.commit()


# =========================
# TRANSACTION HISTORY
# =========================
async def get_transactions(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT amount, type, note, created_at FROM transactions
               WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# =========================
# INVENTORY — pobierz przedmioty
# Automatycznie deaktywuje wygasłe
# =========================
async def get_inventory(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await ensure_user(db, user_id)

        # Deaktywuj wygasłe
        now = datetime.utcnow().isoformat()
        await db.execute(
            """UPDATE inventory SET active = 0
               WHERE user_id = ? AND active = 1
               AND expires_at IS NOT NULL AND expires_at <= ?""",
            (user_id, now)
        )
        await db.commit()

        async with db.execute(
            """SELECT * FROM inventory WHERE user_id = ?
               ORDER BY bought_at DESC""",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# =========================
# INVENTORY — sprawdź czy przedmiot jest aktywny
# =========================
async def has_active_item(user_id: int, item_id: str) -> bool:
    items = await get_inventory(user_id)
    return any(i["item_id"] == item_id and i["active"] for i in items)


# =========================
# INVENTORY — dodaj przedmiot
# czas_trwania: "24h", "12h", "6h", "jednorazowe", None
# =========================
async def add_to_inventory(user_id: int, item_id: str, czas_trwania: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user_id)

        expires_at = None
        if czas_trwania and czas_trwania != "jednorazowe":
            hours = _parse_duration_hours(czas_trwania)
            if hours:
                expires_at = (datetime.utcnow() + timedelta(hours=hours)).isoformat()

        await db.execute(
            """INSERT INTO inventory (user_id, item_id, active, expires_at)
               VALUES (?, ?, 1, ?)""",
            (user_id, item_id, expires_at)
        )
        await db.commit()


# =========================
# INVENTORY — dezaktywuj przedmiot (po użyciu jednorazowego)
# =========================
async def deactivate_item(user_id: int, item_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE inventory SET active = 0
               WHERE user_id = ? AND item_id = ? AND active = 1""",
            (user_id, item_id)
        )
        await db.commit()


def _parse_duration_hours(czas: str) -> float | None:
    """Parsuje '24h', '12h', '6h', '8h' → liczbę godzin."""
    czas = czas.strip().lower()
    if czas.endswith("h"):
        try:
            return float(czas[:-1])
        except ValueError:
            return None
    return None

