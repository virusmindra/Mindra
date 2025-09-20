# stats.py
# Совмещённая, совместимая версия (Mindra Free / Plus / Pro)
# - напоминания: единая схема с due_utc/run_at/urgent
# - премиум: plus_until / pro_until (integers, epoch), совместимость с "until"
# - триал: 3 дня Mindra+ (один раз)
# - рефералы: пригласившему +7 дней Mindra+, приглашённому +7 дней Mindra+
# - квоты/фичи: безопасные фолбэки, если словари заданы в handlers.py – будут использованы они

from __future__ import annotations

import json
import os
import sqlite3
import logging
import time
try:
    from texts import QUOTAS, FEATURE_MATRIX
except Exception:
    QUOTAS = None
    FEATURE_MATRIX = None
    
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

# ===== опциональные зависимости (не роняем импорт, если их нет) =====
try:
    from storage import get_goals, get_habits, load_goals, load_habits
except Exception:
    def get_goals(_): return []
    def get_habits(_): return []
    def load_goals(): return {}
    def load_habits(): return {}

# ===== конфиг-пути (используем config, если он есть) =====
try:
    from config import DATA_DIR as CFG_DATA_DIR, PREMIUM_DB_PATH as CFG_PREMIUM_DB_PATH, REMIND_DB_PATH as CFG_REMIND_DB_PATH
except Exception:
    CFG_DATA_DIR = CFG_PREMIUM_DB_PATH = CFG_REMIND_DB_PATH = None

DATA_DIR = CFG_DATA_DIR or os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
PREMIUM_DB_PATH = CFG_PREMIUM_DB_PATH or os.path.join(DATA_DIR, "premium.sqlite3")
REMIND_DB_PATH  = CFG_REMIND_DB_PATH  or os.path.join(DATA_DIR, "reminders.sqlite3")

# ===== файлы статы/трекеров =====
STATS_FILE  = os.path.join(DATA_DIR, "stats.json")
GOALS_FILE  = os.path.join(DATA_DIR, "goals.json")
HABITS_FILE = os.path.join(DATA_DIR, "habits.json")

# ===== планы =====
PLAN_FREE = "free"
PLAN_PLUS = "plus"
PLAN_PRO  = "pro"
ALL_PLANS = {PLAN_FREE, PLAN_PLUS, PLAN_PRO}

# ===== админы/владелец (строки) =====
OWNER_ID = os.getenv("OWNER_ID", "7775321566")
ADMIN_USER_IDS = [OWNER_ID]  # можно расширить

def record_payment_session(uid: str, provider: str, tier: str, session_id: str, mode: str = "sub"):
    with premium_db() as db:
        db.execute(
            "INSERT INTO payments (user_id, provider, tier, mode, session_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 'created', strftime('%s','now'), strftime('%s','now'));",
            (str(uid), provider, tier, mode, session_id)
        )
        db.commit()

def mark_payment_active_by_session(session_id: str, subscription_id: str | None = None):
    with premium_db() as db:
        db.execute(
            "UPDATE payments SET status='active', subscription_id=COALESCE(?, subscription_id), updated_at=strftime('%s','now') "
            "WHERE session_id=?;",
            (subscription_id, session_id)
        )
        db.commit()

# ====== УТИЛЫ ВРЕМЕНИ ======
def _now_epoch() -> int:
    return int(time.time())

def _iso_to_epoch_maybe(s: str) -> int:
    """Безопасно: ISO8601/Z → epoch, либо 0."""
    if not s:
        return 0
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return 0

def _parse_any_dt(val: str) -> datetime:
    """ISO/epoch → aware UTC."""
    v = str(val).strip()
    if v.isdigit():
        return datetime.fromtimestamp(int(v), tz=timezone.utc)
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _to_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

# --- Premium Challenges ---
def ensure_premium_challenges():
    """Создаёт таблицу weekly-челленджей Mindra+, если её нет."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS premium_challenges (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT    NOT NULL,
                week_start TEXT    NOT NULL,         -- ISO-8601 (YYYY-MM-DD), понедельник
                text       TEXT    NOT NULL,         -- формулировка челленджа
                done       INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL          -- epoch seconds (UTC)
            );
        """)
        db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ch_user_week
            ON premium_challenges(user_id, week_start);
        """)
        db.commit()


# =========================================================
# ================  REMINDERS (SQLite)  ===================
# =========================================================

def ensure_remind_db():
    with sqlite3.connect(REMIND_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT    NOT NULL,
                text       TEXT    NOT NULL,
                run_at     TEXT,                  -- ISO8601 UTC (Z)
                tz         TEXT,
                status     TEXT    NOT NULL DEFAULT 'scheduled',
                created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT,
                due_utc    INTEGER NOT NULL DEFAULT 0,   -- epoch (UTC)
                urgent     INTEGER NOT NULL DEFAULT 0    -- 1 = не переносить в тихие часы
            );
        """)

        cols = {row[1] for row in db.execute("PRAGMA table_info(reminders);")}
        def add(col, ddl):
            if col not in cols:
                db.execute(f"ALTER TABLE reminders ADD COLUMN {ddl};")

        add("tz",         "tz TEXT")
        add("status",     "status TEXT NOT NULL DEFAULT 'scheduled'")
        add("created_at", "created_at TEXT NOT NULL DEFAULT (datetime('now'))")
        add("updated_at", "updated_at TEXT")
        add("due_utc",    "due_utc INTEGER NOT NULL DEFAULT 0")
        add("urgent",     "urgent INTEGER NOT NULL DEFAULT 0")

        db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_due   ON reminders(user_id, due_utc);")
        db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_status_due ON reminders(status,  due_utc);")

        # нормализуем статусы
        db.execute("UPDATE reminders SET status='scheduled' WHERE status IS NULL;")

        # заполнить run_at из due_utc, если пусто
        db.execute("""
            UPDATE reminders
               SET run_at = strftime('%Y-%m-%dT%H:%M:%SZ', due_utc, 'unixepoch')
             WHERE (run_at IS NULL OR run_at = '')
               AND due_utc > 0;
        """)

        # и наоборот: due_utc из run_at
        cur = db.execute("""
            SELECT id, run_at
              FROM reminders
             WHERE (due_utc IS NULL OR due_utc = 0)
               AND run_at IS NOT NULL AND run_at <> '';
        """)
        for _id, iso in cur.fetchall():
            try:
                dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
                db.execute("UPDATE reminders SET due_utc=? WHERE id=?", (int(dt.timestamp()), _id))
            except Exception:
                pass

        db.commit()

@contextmanager
def remind_db():
    ensure_remind_db()
    conn = sqlite3.connect(REMIND_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# =========================================================
# ====================  PREMIUM DB  =======================
# =========================================================


def ensure_premium_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        # На всякий случай включим Foreign Keys (не критично, но полезно на будущее)
        try:
            db.execute("PRAGMA foreign_keys = ON;")
        except Exception:
            pass

        # === premium ==========================================================
        db.execute("""
            CREATE TABLE IF NOT EXISTS premium (
                user_id    TEXT PRIMARY KEY,
                plus_until INTEGER NOT NULL DEFAULT 0,   -- epoch
                pro_until  INTEGER NOT NULL DEFAULT 0    -- epoch
            );
        """)

        cols = {r[1] for r in db.execute("PRAGMA table_info(premium);")}
        # миграция со старой колонки "until" -> в plus_until
        if "until" in cols:
            try:
                rows = db.execute("""
                    SELECT user_id, until
                    FROM premium
                    WHERE until IS NOT NULL AND until <> ''
                """).fetchall()
                for uid, until in rows:
                    ep = _iso_to_epoch_maybe(until)
                    if ep and ep > 0:
                        prev = db.execute("SELECT plus_until FROM premium WHERE user_id=?;", (uid,)).fetchone()
                        prev_ep = int(prev[0]) if prev and prev[0] is not None else 0
                        if ep > prev_ep:
                            db.execute("UPDATE premium SET plus_until=? WHERE user_id=?;", (ep, uid))
            except Exception as e:
                logging.warning("premium.until migration skipped: %s", e)

        # гарантируем наличие новых колонок
        cols = {r[1] for r in db.execute("PRAGMA table_info(premium);")}
        if "plus_until" not in cols:
            db.execute("ALTER TABLE premium ADD COLUMN plus_until INTEGER NOT NULL DEFAULT 0;")
        if "pro_until" not in cols:
            db.execute("ALTER TABLE premium ADD COLUMN pro_until  INTEGER NOT NULL DEFAULT 0;")

        # === user_flags =======================================================
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_flags (
                user_id     TEXT PRIMARY KEY,
                trial_given INTEGER NOT NULL DEFAULT 0,
                created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now'))
            );
        """)

        # === referrals ========================================================
        db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                invitee_id TEXT PRIMARY KEY,
                inviter_id TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
        """)

        # === payments =========================================================
        db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         TEXT    NOT NULL,
                provider        TEXT    NOT NULL,                  -- 'stripe' | 'paypal'
                tier            TEXT    NOT NULL,                  -- 'plus' | 'pro'
                mode            TEXT    NOT NULL DEFAULT 'sub',    -- 'sub' | 'one_time'
                session_id      TEXT,
                subscription_id TEXT,
                status          TEXT    NOT NULL DEFAULT 'created',-- created|paid|active|canceled
                amount_cents    INTEGER,
                currency        TEXT,
                created_at      INTEGER NOT NULL,
                updated_at      INTEGER NOT NULL
            );
        """)

        # миграция столбцов для payments (если схема уже существовала и чего-то не хватает)
        pay_cols = {r[1] for r in db.execute("PRAGMA table_info(payments);")}
        alter_stmts = []
        if "mode" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN mode TEXT NOT NULL DEFAULT 'sub';")
        if "session_id" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN session_id TEXT;")
        if "subscription_id" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN subscription_id TEXT;")
        if "status" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN status TEXT NOT NULL DEFAULT 'created';")
        if "amount_cents" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN amount_cents INTEGER;")
        if "currency" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN currency TEXT;")
        if "created_at" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'));")
        if "updated_at" not in pay_cols:
            alter_stmts.append("ALTER TABLE payments ADD COLUMN updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'));")

        for stmt in alter_stmts:
            db.execute(stmt)

        # индексы для payments
        db.execute("CREATE INDEX IF NOT EXISTS idx_pay_user    ON payments(user_id);")
        db.execute("CREATE INDEX IF NOT EXISTS idx_pay_session ON payments(session_id);")
        db.execute("CREATE INDEX IF NOT EXISTS idx_pay_sub     ON payments(subscription_id);")

        db.commit()
        
@contextmanager
def premium_db():
    ensure_premium_db()
    conn = sqlite3.connect(PREMIUM_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# -------- Триалы --------
def trial_was_given(user_id) -> bool:
    with premium_db() as db:
        row = db.execute("SELECT trial_given FROM user_flags WHERE user_id=?;", (str(user_id),)).fetchone()
        return bool(row and int(row[0]) == 1)

def mark_trial_given(user_id) -> None:
    with premium_db() as db:
        db.execute(
            "INSERT INTO user_flags(user_id, trial_given) VALUES(?,1) "
            "ON CONFLICT(user_id) DO UPDATE SET trial_given=1;",
            (str(user_id),)
        )
        db.commit()


def _premium_has_new_schema(db) -> bool:
    try:
        cols = {r[1] for r in db.execute("PRAGMA table_info(premium);")}
        return "plus_until" in cols and "pro_until" in cols
    except Exception:
        return False

def get_premium_until(user_id: str | int, tier: str | None = None) -> str | None:
    """
    Если tier указан ('plus' | 'pro') — вернуть ISO конца именно этого уровня.
    Если tier=None — вернуть ISO максимального из (plus, pro) (совместимость со старым кодом).
    Поддерживает новую (epoch) и старую ('until' TEXT) схему таблицы.
    """
    uid = str(user_id)
    with premium_db() as db:
        if _premium_has_new_schema(db):
            if tier:
                col = "plus_until" if tier != "pro" else "pro_until"
                row = db.execute(f"SELECT {col} FROM premium WHERE user_id=?;", (uid,)).fetchone()
                if row and int(row[0] or 0) > 0:
                    return datetime.fromtimestamp(int(row[0]), tz=timezone.utc).isoformat()
                return None
            else:
                row = db.execute("SELECT plus_until, pro_until FROM premium WHERE user_id=?;", (uid,)).fetchone()
                if not row:
                    return None
                ep = max(int(row["plus_until"] or 0), int(row["pro_until"] or 0))
                return datetime.fromtimestamp(ep, tz=timezone.utc).isoformat() if ep > 0 else None
        # fallback: старая колонка 'until' (ISO)
        row = db.execute("SELECT until FROM premium WHERE user_id=?;", (uid,)).fetchone()
        return row[0] if row else None

def _set_premium_until_iso(uid: str, until_iso: str) -> None:
    """Back-compat: устанавливаем как Mindra+ (plus_until)."""
    ep = _iso_to_epoch_maybe(until_iso)
    with premium_db() as db:
        prev = db.execute("SELECT plus_until, pro_until FROM premium WHERE user_id=?;", (uid,)).fetchone()
        if prev:
            db.execute("UPDATE premium SET plus_until=? WHERE user_id=?;", (ep, uid))
        else:
            db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, ?, 0);", (uid, ep))
        db.commit()


def set_premium_until(user_id: str | int, until, tier: str | None = None, add_days: bool = False) -> None:
    """
    Устанавливает дату окончания подписки.
    - 'until' может быть datetime или ISO-строка.
    - tier: 'plus' | 'pro' | None(=> 'plus' для совместимости).
    - add_days=True (режим старого API): 'until' трактуется как дата в будущем, и добавляются соответствующие дни.
    Работает и с новой, и со старой схемой.
    """
    uid = str(user_id)
    # нормализуем dt -> aware UTC
    if isinstance(until, datetime):
        dt_utc = until if until.tzinfo else until.replace(tzinfo=timezone.utc)
        dt_utc = dt_utc.astimezone(timezone.utc)
    else:
        try:
            dt_utc = datetime.fromisoformat(str(until).replace("Z", "+00:00"))
        except Exception:
            dt_utc = datetime.now(timezone.utc)
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_utc = dt_utc.astimezone(timezone.utc)

    if add_days:
        days = max(0, int((dt_utc - datetime.now(timezone.utc)).total_seconds() // 86400))
        if days > 0:
            extend_premium_days(uid, days, tier=tier or "plus")
            return

    epoch = int(dt_utc.timestamp())
    with premium_db() as db:
        if _premium_has_new_schema(db):
            col = "plus_until" if (tier or "plus") != "pro" else "pro_until"
            exists = db.execute("SELECT 1 FROM premium WHERE user_id=?;", (uid,)).fetchone()
            if exists:
                db.execute(f"UPDATE premium SET {col}=? WHERE user_id=?;", (epoch, uid))
            else:
                if col == "plus_until":
                    db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, ?, 0);", (uid, epoch))
                else:
                    db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, 0, ?);", (uid, epoch))
        else:
            db.execute(
                "INSERT INTO premium(user_id, until) VALUES(?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET until=excluded.until;",
                (uid, dt_utc.isoformat()),
            )
        db.commit()


def set_premium_until_dt(user_id: str | int, dt_utc: datetime, tier: str | None = None) -> None:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)
    set_premium_until(user_id, dt_utc, tier=tier or "plus")

def extend_premium_days(user_id: str | int, days: int, tier: str | None = None) -> str:
    """
    Продлевает подписку на N дней. Возвращает ISO (UTC).
    Работает и с новой (epoch), и со старой ('until' TEXT) схемой.
    """
    uid = str(user_id)
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    with premium_db() as db:
        if _premium_has_new_schema(db):
            col = "plus_until" if (tier or "plus") != "pro" else "pro_until"
            row = db.execute(f"SELECT {col} FROM premium WHERE user_id=?;", (uid,)).fetchone()
            base = max(now_epoch, int(row[0]) if row and row[0] else 0)
            new_until = base + int(days) * 86400
            if row:
                db.execute(f"UPDATE premium SET {col}=? WHERE user_id=?;", (new_until, uid))
            else:
                if col == "plus_until":
                    db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, ?, 0);", (uid, new_until))
                else:
                    db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, 0, ?);", (uid, new_until))
            db.commit()
            return datetime.fromtimestamp(new_until, tz=timezone.utc).isoformat()

        # старая схема: 'until' (ISO)
        cur_iso = get_premium_until(uid) or datetime.now(timezone.utc).isoformat()
        try:
            base_dt = datetime.fromisoformat(cur_iso.replace("Z", "+00:00"))
            if base_dt.tzinfo is None:
                base_dt = base_dt.replace(tzinfo=timezone.utc)
            if base_dt < datetime.now(timezone.utc):
                base_dt = datetime.now(timezone.utc)
        except Exception:
            base_dt = datetime.now(timezone.utc)

        new_dt = base_dt + timedelta(days=int(days))
        set_premium_until(uid, new_dt)  # по умолчанию — как Mindra+
        return new_dt.isoformat()

def is_premium_db(user_id) -> bool:
    """Совместимость со старым импортом — прокси на новую is_premium()."""
    return is_premium(user_id, tier="any")

def grant_trial_if_eligible(user_id, days: int) -> str | None:
    """
    Даёт триал Mindra+ (если ещё не давали и нет активного премиума).
    Возвращает ISO until или None.
    """
    if trial_was_given(user_id):
        return None

    now = datetime.now(timezone.utc)
    cur = get_premium_until(user_id)
    if cur:
        try:
            dt = _parse_any_dt(cur)
            if dt > now:
                mark_trial_given(user_id)  # отмечаем, чтобы больше не пытаться
                return None
        except Exception:
            pass

    until = now + timedelta(days=int(days))
    set_premium_until(user_id, until)
    mark_trial_given(user_id)
    return until.isoformat()

# -------- Рефералы --------
def _referrals_table_shape(db) -> str:
    """Определяем, какая таблица рефералок есть: 'new' | 'old' | 'none'."""
    tbs = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table';")}
    if "referrals" in tbs:
        cols = {r[1] for r in db.execute("PRAGMA table_info(referrals);")}
        if {"invitee_id", "inviter_id", "created_at"} <= cols:
            return "new"
        if {"invited_user_id", "inviter_user_id", "granted_days"}.issubset(cols):
            return "old"
    return "none"

def grant_plus_days(uid: str, days: int) -> str:
    """Продлевает Mindra+ на N дней. Возвращает ISO (UTC) окончания."""
    uid = str(uid)
    with premium_db() as db:
        row = db.execute("SELECT plus_until FROM premium WHERE user_id=?;", (uid,)).fetchone()
        now = _now_epoch()
        base = max(now, (int(row["plus_until"]) if row else 0))
        new_until = base + int(days) * 86400
        if row:
            db.execute("UPDATE premium SET plus_until=? WHERE user_id=?;", (new_until, uid))
        else:
            db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, ?, 0);", (uid, new_until))
        db.commit()
    return datetime.fromtimestamp(new_until, tz=timezone.utc).isoformat()

def grant_pro_days(uid: str, days: int) -> str:
    uid = str(uid)
    with premium_db() as db:
        row = db.execute("SELECT pro_until FROM premium WHERE user_id=?;", (uid,)).fetchone()
        now = _now_epoch()
        base = max(now, (int(row["pro_until"]) if row else 0))
        new_until = base + int(days) * 86400
        if row:
            db.execute("UPDATE premium SET pro_until=? WHERE user_id=?;", (new_until, uid))
        else:
            db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, 0, ?);", (uid, new_until))
        db.commit()
    return datetime.fromtimestamp(new_until, tz=timezone.utc).isoformat()

def has_plus(uid: str) -> bool:
    with premium_db() as db:
        row = db.execute("SELECT plus_until FROM premium WHERE user_id=?;", (str(uid),)).fetchone()
    return bool(row and int(row["plus_until"]) > _now_epoch())

def has_pro(uid: str) -> bool:
    with premium_db() as db:
        row = db.execute("SELECT pro_until FROM premium WHERE user_id=?;", (str(uid),)).fetchone()
    return bool(row and int(row["pro_until"]) > _now_epoch())

def is_premium(user_id, tier: str = "any") -> bool:
    """tier: 'plus' | 'pro' | 'any'."""
    uid = str(user_id)
    if uid in ADMIN_USER_IDS:
        return True
    if tier == "plus":
        return has_plus(uid)
    if tier == "pro":
        return has_pro(uid)
    return has_plus(uid) or has_pro(uid)

def plan_of(uid: str) -> str:
    if has_pro(uid):
        return PLAN_PRO
    if has_plus(uid):
        return PLAN_PLUS
    return PLAN_FREE

def process_referral(inviter_id: str, invitee_id: str, days: int = 7) -> bool:
    """
    Фиксирует приглашение один раз на invitee и даёт пригласившему +days Mindra+.
    Возвращает True, если начисление выполнено (не было ранее).
    """
    inviter_id = str(inviter_id); invitee_id = str(invitee_id)
    if not inviter_id or not invitee_id or inviter_id == invitee_id:
        return False

    with premium_db() as db:
        shape = _referrals_table_shape(db)
        if shape == "new":
            exists = db.execute("SELECT 1 FROM referrals WHERE invitee_id=?;", (invitee_id,)).fetchone()
            if exists:
                return False
            db.execute("INSERT INTO referrals (invitee_id, inviter_id, created_at) VALUES (?, ?, ?);",
                       (invitee_id, inviter_id, _now_epoch()))
        elif shape == "old":
            exists = db.execute("SELECT 1 FROM referrals WHERE invited_user_id=?;", (invitee_id,)).fetchone()
            if exists:
                return False
            db.execute("INSERT INTO referrals (invited_user_id, inviter_user_id, granted_days) VALUES (?, ?, ?);",
                       (invitee_id, inviter_id, int(days)))
        else:
            db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    invitee_id TEXT PRIMARY KEY,
                    inviter_id TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );
            """)
            db.execute("INSERT INTO referrals (invitee_id, inviter_id, created_at) VALUES (?, ?, ?);",
                       (invitee_id, inviter_id, _now_epoch()))
        db.commit()

    try:
        grant_plus_days(inviter_id, int(days))
    except Exception as e:
        logging.warning("grant_plus_days (referral) failed: %s", e)
    return True

# ============ MIGRATION helper (из старого stats.json) ============
def migrate_premium_from_stats(load_stats_func):
    """Миграция старого поля premium_until из stats.json → plus_until (epoch)."""
    try:
        stats = load_stats_func()
    except Exception:
        return
    moved = 0
    with premium_db() as db:
        for uid, user in (stats or {}).items():
            until = user.get("premium_until")
            if not until:
                continue
            ep = _iso_to_epoch_maybe(str(until))
            if ep <= 0:
                continue
            prev = db.execute("SELECT plus_until FROM premium WHERE user_id=?;", (str(uid),)).fetchone()
            prev_ep = int(prev["plus_until"]) if prev else 0
            if ep > prev_ep:
                if prev:
                    db.execute("UPDATE premium SET plus_until=? WHERE user_id=?;", (ep, str(uid)))
                else:
                    db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, ?, 0);", (str(uid), ep))
                moved += 1
        db.commit()
    logging.info("Premium migration completed: %d users", moved)

# =========================================================
# ================== ПРОГРЕСС / ОЧКИ =====================
# =========================================================

def load_stats():
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def add_points(user_id: str, amount: int = 1, reason: str | None = None, **kwargs):
    """Начисляет очки. reason/**kwargs игнорируются (для обратной совместимости)."""
    stats = load_stats()
    uid = str(user_id)
    user = stats.get(uid, {})
    user["points"] = int(user.get("points", 0)) + int(amount)
    if reason:
        logging.info(f"add_points: +{amount} to {uid} (reason={reason})")
    stats[uid] = user
    save_stats(stats)
    return user["points"]

TITLES = {
    "ru": [(0,"🌱 Новичок"),(100,"✨ Мотиватор"),(250,"🔥 Уверенный"),
           (500,"💎 Наставник"),(float('inf'),"🌟 Легенда")],
    "uk": [(0,"🌱 Новачок"),(100,"✨ Мотиватор"),(250,"🔥 Впевнений"),
           (500,"💎 Наставник"),(float('inf'),"🌟 Легенда")],
    "be": [(0,"🌱 Пачатковец"),(100,"✨ Матыватар"),(250,"🔥 Упэўнены"),
           (500,"💎 Настаўнік"),(float('inf'),"🌟 Легенда")],
    "kk": [(0,"🌱 Бастаушы"),(100,"✨ Мотивация беруші"),(250,"🔥 Сенімді"),
           (500,"💎 Ұстаз"),(float('inf'),"🌟 Аңыз")],
    "kg": [(0,"🌱 Жаңы келген"),(100,"✨ Мотивациячы"),(250,"🔥 Ишенимдүү"),
           (500,"💎 Наcатчы"),(float('inf'),"🌟 Легенда")],
    "hy": [(0,"🌱 Նորեկ"),(100,"✨ Մոտիվատոր"),(250,"🔥 Վստահ"),
           (500,"💎 Խորհրդատու"),(float('inf'),"🌟 Լեգենդ")],
    "ce": [(0,"🌱 Дика хьалхар"),(100,"✨ Мотивация кхетар"),(250,"🔥 Дукха ву"),
           (500,"💎 Къастийна"),(float('inf'),"🌟 Легенда")],
    "md": [(0,"🌱 Începător"),(100,"✨ Motivator"),(250,"🔥 Încrezător"),
           (500,"💎 Mentor"),(float('inf'),"🌟 Legenda")],
    "ka": [(0,"🌱 დამწყები"),(100,"✨ მოტივატორი"),(250,"🔥 დარწმუნებული"),
           (500,"💎 მენტორი"),(float('inf'),"🌟 ლეგენდა")],
    "en": [(0,"🌱 Newbie"),(100,"✨ Motivator"),(250,"🔥 Confident"),
           (500,"💎 Mentor"),(float('inf'),"🌟 Legend")],
     "es": [
        (0, "🌱 Principiante"),
        (100, "✨ Motivador"),
        (250, "🔥 Seguro"),
        (500, "💎 Mentor"),
        (float('inf'), "🌟 Leyenda"),
    ],
    "de": [
        (0, "🌱 Anfänger"),
        (100, "✨ Motivator"),
        (250, "🔥 Selbstsicher"),
        (500, "💎 Mentor"),
        (float('inf'), "🌟 Legende"),
    ],
    "pl": [
        (0, "🌱 Nowicjusz"),
        (100, "✨ Motywator"),
        (250, "🔥 Pewny siebie"),
        (500, "💎 Mentor"),
        (float('inf'), "🌟 Legenda"),
    ],
    "fr": [
        (0, "🌱 Débutant"),
        (100, "✨ Motivateur"),
        (250, "🔥 Confiant"),
        (500, "💎 Mentor"),
        (float('inf'), "🌟 Légende"),
    ],
}

def get_user_points(user_id: str) -> int:
    stats = load_stats()
    return int(stats.get(str(user_id), {}).get("points", 0))

def get_user_title(points: int, lang: str = "ru") -> str:
    lang_titles = TITLES.get(lang, TITLES["ru"])
    for threshold, title in lang_titles:
        if points < threshold:
            return title
    return lang_titles[-1][1]

def get_next_title_info(points: int, lang: str = "ru"):
    lang_titles = TITLES.get(lang, TITLES["ru"])
    for threshold, title in lang_titles:
        if points < threshold:
            return title, int(threshold - points)
    return lang_titles[-1][1], 0

def build_titles_ladder(lang: str = "ru") -> str:
    lang_titles = TITLES.get(lang, TITLES["ru"])
    lines = []
    for threshold, title in lang_titles:
        if threshold == float("inf"):
            lines.append(f"{title} — ∞")
        else:
            lines.append(f"{title} — {int(threshold)}+")
    return "\n".join(lines)

# =============== Агрегированная статистика пользователя ===============
def get_stats(user_id: str):
    user_id = str(user_id)
    goals_data = load_goals() or {}
    user_goals = goals_data.get(user_id, [])
    completed_goals = sum(1 for goal in user_goals if isinstance(goal, dict) and goal.get("done"))

    habits_data = load_habits() or {}
    user_habits = habits_data.get(user_id, [])
    completed_habits = sum(1 for habit in user_habits if isinstance(habit, dict) and habit.get("done"))

    days_active = len({(g.get("created_at") or "")[:10] for g in user_goals if isinstance(g, dict) and g.get("created_at")}) if user_goals else 0
    mood_entries = 0

    return {
        "completed_goals": completed_goals,
        "completed_habits": completed_habits,
        "days_active": days_active,
        "mood_entries": mood_entries,
    }

def _collect_activity_dates(user_goals, user_habits):
    dates = set()
    for g in user_goals:
        if isinstance(g, dict) and g.get("done_at"):
            dates.add(g["done_at"])
    for h in user_habits:
        if isinstance(h, dict) and h.get("done_at"):
            dates.add(h["done_at"])
    return dates

def get_user_stats(user_id: str):
    user_id = str(user_id)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    goals = get_goals(user_id) or []
    habits = get_habits(user_id) or []

    total_goals = len(goals)
    completed_goals = sum(1 for g in goals if isinstance(g, dict) and g.get("done"))
    completed_goals_today = sum(1 for g in goals if isinstance(g, dict) and g.get("done_at") == today)

    total_habits = len(habits)
    completed_habits = sum(1 for h in habits if isinstance(h, dict) and h.get("done"))
    completed_habits_today = sum(1 for h in habits if isinstance(h, dict) and h.get("done_at") == today)

    # очки — из stats.json
    points = get_user_points(user_id)

    return {
        "points": points,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "completed_goals_today": completed_goals_today,
        "total_habits": total_habits,
        "completed_habits": completed_habits,
        "completed_habits_today": completed_habits_today,
    }

# =========================================================
# ====== Фичи/Квоты (безопасные фолбэки, если нет в handlers) ======
# =========================================================

# Фолбэки, если FEATURE_MATRIX/QUOTAS не определены в handlers.py
_FEATURE_MATRIX_FALLBACK = {
    PLAN_FREE: {"reminders_unlimited": False},
    PLAN_PLUS: {"reminders_unlimited": False},
    PLAN_PRO:  {"reminders_unlimited": True},
}
_QUOTAS_FALLBACK = {
    PLAN_FREE: {"reminders_active": 1, "eleven_daily_seconds": 0},
    PLAN_PLUS: {"reminders_active": 5, "eleven_daily_seconds": 8 * 60},
    PLAN_PRO:  {"reminders_active": 200, "eleven_daily_seconds": 0},
}

def has_feature(uid: str, feature_key: str) -> bool:
    plan = plan_of(uid)
    fm = (
        globals().get("FEATURE_MATRIX")
        or FEATURE_MATRIX
        or _FEATURE_MATRIX_FALLBACK
    )
    return bool(fm.get(plan, {}).get(feature_key, False))

def quota(uid: str, key: str) -> int:
    plan = plan_of(uid)
    q = (
        globals().get("QUOTAS")
        or QUOTAS
        or _QUOTAS_FALLBACK
    )
    return int(q.get(plan, {}).get(key, 0))

def reminders_active_limit(uid: str) -> int:
    # если в QUOTAS есть явная квота — используем её
    try:
        lim = int(quota(uid, "reminders_active"))
        if lim > 0:
            return lim
    except Exception:
        pass
    # доп. правило: Pro с флагом reminders_unlimited
    if has_feature(uid, "reminders_unlimited"):
        return 10**9
    return 5 if is_premium(uid) else 1

