import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "economy.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                total_lost INTEGER DEFAULT 0,
                last_daily TEXT DEFAULT NULL,
                last_work TEXT DEFAULT NULL,
                last_beg TEXT DEFAULT NULL,
                last_crime TEXT DEFAULT NULL,
                last_rob TEXT DEFAULT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                expires_at TEXT DEFAULT NULL,
                purchased_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER PRIMARY KEY,
                spin_wins INTEGER DEFAULT 0,
                spin_losses INTEGER DEFAULT 0,
                spin_earned INTEGER DEFAULT 0,
                spin_lost INTEGER DEFAULT 0,
                blackjack_wins INTEGER DEFAULT 0,
                blackjack_losses INTEGER DEFAULT 0,
                blackjack_earned INTEGER DEFAULT 0,
                blackjack_lost INTEGER DEFAULT 0,
                slots_wins INTEGER DEFAULT 0,
                slots_losses INTEGER DEFAULT 0,
                slots_earned INTEGER DEFAULT 0,
                slots_lost INTEGER DEFAULT 0,
                coinflip_wins INTEGER DEFAULT 0,
                coinflip_losses INTEGER DEFAULT 0,
                roulette_wins INTEGER DEFAULT 0,
                roulette_losses INTEGER DEFAULT 0,
                mines_wins INTEGER DEFAULT 0,
                mines_losses INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                biggest_win INTEGER DEFAULT 0,
                biggest_loss INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            await db.execute(
                "INSERT INTO users (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as c2:
                row2 = await c2.fetchone()
                return dict(row2)


async def get_game_stats(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM game_stats WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            await db.execute(
                "INSERT INTO game_stats (user_id) VALUES (?)", (user_id,)
            )
            await db.commit()
            async with db.execute(
                "SELECT * FROM game_stats WHERE user_id = ?", (user_id,)
            ) as c2:
                row2 = await c2.fetchone()
                return dict(row2)


async def record_game(user_id: int, game: str, won: bool, net_amount: int):
    await get_game_stats(user_id)
    won_int = 1 if won else 0
    lost_int = 0 if won else 1
    earned = max(0, net_amount)
    lost = max(0, -net_amount)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            UPDATE game_stats SET
                {game}_wins = {game}_wins + ?,
                {game}_losses = {game}_losses + ?,
                {game}_earned = {game}_earned + ?,
                {game}_lost = {game}_lost + ?,
                total_games = total_games + 1,
                total_wins = total_wins + ?,
                total_losses = total_losses + ?,
                biggest_win = CASE WHEN ? > biggest_win THEN ? ELSE biggest_win END,
                biggest_loss = CASE WHEN ? > biggest_loss THEN ? ELSE biggest_loss END
            WHERE user_id = ?
        """, (
            won_int, lost_int, earned, lost,
            won_int, lost_int,
            earned, earned,
            lost, lost,
            user_id,
        ))
        await db.commit()


async def record_game_no_stats(user_id: int, game: str, won: bool, net_amount: int):
    await get_game_stats(user_id)
    won_int = 1 if won else 0
    lost_int = 0 if won else 1
    earned = max(0, net_amount)
    lost = max(0, -net_amount)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE game_stats SET
                total_games = total_games + 1,
                total_wins = total_wins + ?,
                total_losses = total_losses + ?,
                biggest_win = CASE WHEN ? > biggest_win THEN ? ELSE biggest_win END,
                biggest_loss = CASE WHEN ? > biggest_loss THEN ? ELSE biggest_loss END
            WHERE user_id = ?
        """, (
            won_int, lost_int,
            earned, earned,
            lost, lost,
            user_id,
        ))
        await db.commit()


async def update_balance(user_id: int, amount: int):
    await get_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def set_balance(user_id: int, amount: int):
    await get_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def update_bank(user_id: int, amount: int):
    await get_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET bank = bank + ? WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def set_bank(user_id: int, amount: int):
    await get_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET bank = ? WHERE user_id = ?",
            (amount, user_id),
        )
        await db.commit()


async def update_cooldown(user_id: int, field: str):
    await get_user(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {field} = datetime('now') WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()


async def get_top_users(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT u.user_id, u.balance, u.bank, (u.balance + u.bank) as total,
                      COALESCE(g.total_wins, 0) as total_wins,
                      COALESCE(g.total_games, 0) as total_games
               FROM users u
               LEFT JOIN game_stats g ON u.user_id = g.user_id
               ORDER BY total DESC LIMIT ?""",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_top_winners(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT g.user_id, g.total_wins, g.total_games, g.biggest_win,
                      (g.spin_earned + g.blackjack_earned + g.slots_earned) as total_earned
               FROM game_stats g
               WHERE g.total_games > 0
               ORDER BY g.total_wins DESC LIMIT ?""",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def log_transaction(user_id: int, amount: int, type_: str, description: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
            (user_id, amount, type_, description),
        )
        await db.commit()


async def get_inventory(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE inventory SET active = 0
            WHERE user_id = ? AND expires_at IS NOT NULL AND expires_at < datetime('now')
        """, (user_id,))
        await db.commit()
        async with db.execute(
            "SELECT * FROM inventory WHERE user_id = ? ORDER BY purchased_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def add_to_inventory(user_id: int, item_id: str, duration: str = None):
    expires_sql = None
    if duration == "24h":
        expires_sql = "datetime('now', '+24 hours')"
    elif duration == "12h":
        expires_sql = "datetime('now', '+12 hours')"
    elif duration == "6h":
        expires_sql = "datetime('now', '+6 hours')"
    elif duration == "8h":
        expires_sql = "datetime('now', '+8 hours')"

    async with aiosqlite.connect(DB_PATH) as db:
        if expires_sql:
            await db.execute(
                f"INSERT INTO inventory (user_id, item_id, active, expires_at) VALUES (?, ?, 1, {expires_sql})",
                (user_id, item_id),
            )
        else:
            await db.execute(
                "INSERT INTO inventory (user_id, item_id, active, expires_at) VALUES (?, ?, 1, NULL)",
                (user_id, item_id),
            )
        await db.commit()


async def has_active_item(user_id: int, item_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE inventory SET active = 0
            WHERE user_id = ? AND item_id = ? AND expires_at IS NOT NULL AND expires_at < datetime('now')
        """, (user_id, item_id))
        await db.commit()
        async with db.execute(
            "SELECT id FROM inventory WHERE user_id = ? AND item_id = ? AND active = 1 LIMIT 1",
            (user_id, item_id),
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
