"""
items_effects.py
Pomocnicze funkcje efektów przedmiotów sklepu.
Umieść ten plik w tym samym folderze co database.py (NIE w cogs/).
Importuj w games.py: from items_effects import get_luck_bonus, ...
"""
import database as db


async def get_luck_bonus(user_id: int) -> float:
    """Zwraca sumę bonusów szczęścia (lucky_charm +0.05, casino_pass +0.03)."""
    bonus = 0.0
    if await db.has_active_item(user_id, "lucky_charm"):
        bonus += 0.05
    if await db.has_active_item(user_id, "casino_pass"):
        bonus += 0.03
    return bonus


async def get_work_multiplier(user_id: int) -> float:
    """Zwraca mnożnik zarobków z /pracuj (work_boost = x2)."""
    if await db.has_active_item(user_id, "work_boost"):
        return 2.0
    return 1.0


async def get_rob_chance(user_id: int) -> float:
    """Zwraca szansę kradzieży (robber_kit = 70%, domyślnie 45%)."""
    if await db.has_active_item(user_id, "robber_kit"):
        return 0.70
    return 0.45


async def is_shielded(user_id: int) -> bool:
    """Sprawdź czy cel ma aktywną tarczę bankową."""
    return await db.has_active_item(user_id, "shield")


async def get_daily_multiplier(user_id: int) -> float:
    """
    Sprawdź czy daily ma boost x3 (jednorazowy — zużywa przedmiot).
    Zwraca 3.0 jeśli aktywny, 1.0 w przeciwnym razie.
    """
    if await db.has_active_item(user_id, "daily_boost"):
        await db.deactivate_item(user_id, "daily_boost")
        return 3.0
    return 1.0


async def get_vip_daily_bonus(user_id: int) -> int:
    """VIP daje flat +300 do każdego /daily."""
    if await db.has_active_item(user_id, "vip"):
        return 300
    return 0


async def get_max_bet(user_id: int) -> int:
    """casino_pass podnosi max stawkę do 100 000."""
    if await db.has_active_item(user_id, "casino_pass"):
        return 100_000
    return 10_000
