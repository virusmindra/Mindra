import json
import os, sqlite3, logging
from datetime import datetime, timedelta, timezone
from storage import get_goals, get_habits, load_goals, load_habits
from config import DATA_DIR, PREMIUM_DB_PATH, REMIND_DB_PATH
from contextlib import contextmanager

STATS_FILE = "data/stats.json"
GOALS_FILE = "goals.json"
HABITS_FILE = "habits.json"

ADMIN_USER_IDS = ["7775321566"] 
OWNER_ID = "7775321566"
ADMIN_USER_IDS = [OWNER_ID]  # Можно расширять список

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
REMIND_DB_PATH = os.getenv("REMIND_DB_PATH", os.path.join(DATA_DIR, "reminders.sqlite3"))

def ensure_remind_db():
    with sqlite3.connect(REMIND_DB_PATH) as db:
        # Базовая схема (run_at допускает NULL — удобнее для миграций)
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

        # Миграции недостающих колонок
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

        # Индексы
        db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user_due   ON reminders(user_id, due_utc);")
        db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_status_due ON reminders(status,  due_utc);")

        # Нормализация статусов
        db.execute("UPDATE reminders SET status='scheduled' WHERE status IS NULL;")

        # Заполнить пустой run_at из due_utc
        db.execute("""
            UPDATE reminders
               SET run_at = strftime('%Y-%m-%dT%H:%M:%SZ', due_utc, 'unixepoch')
             WHERE (run_at IS NULL OR run_at = '')
               AND due_utc > 0;
        """)

        # Заполнить пустой/нулевой due_utc из run_at
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
                # игнорируем некорректные строки времени
                pass

        db.commit()


@contextmanager
def remind_db():
    ensure_remind_db()
    conn = sqlite3.connect(REMIND_DB_PATH)
    conn.row_factory = sqlite3.Row  # строки как dict-подобные объекты
    try:
        yield conn
    finally:
        conn.close()



def ensure_premium_db():
    """Создаёт/мигрирует схему premium + referrals под PLUS/PRO."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        # --- основная таблица подписок ---
        db.execute("""
            CREATE TABLE IF NOT EXISTS premium (
                user_id    TEXT PRIMARY KEY,
                plus_until INTEGER NOT NULL DEFAULT 0,  -- Mindra+
                pro_until  INTEGER NOT NULL DEFAULT 0   -- Mindra Pro
            );
        """)
        cols = {r[1] for r in db.execute("PRAGMA table_info(premium);")}
        # миграция со старой схемы: была колонка until (ISO)
        if "until" in cols:
            # добавим новые колонки, если вдруг нет
            if "plus_until" not in cols:
                db.execute("ALTER TABLE premium ADD COLUMN plus_until INTEGER NOT NULL DEFAULT 0;")
            if "pro_until" not in cols:
                db.execute("ALTER TABLE premium ADD COLUMN pro_until  INTEGER NOT NULL DEFAULT 0;")
            # перенесём значения until -> plus_until
            for row in db.execute("SELECT user_id, until FROM premium;").fetchall():
                ep = _iso_to_epoch_maybe(row[1])
                if ep > 0:
                    db.execute("UPDATE premium SET plus_until=? WHERE user_id=?;", (ep, row[0]))
        else:
            # на всякий — гарантируем наличие колонок
            if "plus_until" not in cols:
                db.execute("ALTER TABLE premium ADD COLUMN plus_until INTEGER NOT NULL DEFAULT 0;")
            if "pro_until" not in cols:
                db.execute("ALTER TABLE premium ADD COLUMN pro_until  INTEGER NOT NULL DEFAULT 0;")

        # --- вспомогательная таблица флагов (оставляем твою) ---
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_flags (
                user_id     TEXT PRIMARY KEY,
                trial_given INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT  NOT NULL DEFAULT (datetime('now'))
            );
        """)

        # --- referrals ---
        # Нормальная схема:
        db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                invitee_id TEXT PRIMARY KEY,   -- кто пришёл
                inviter_id TEXT NOT NULL,      -- кто пригласил
                created_at INTEGER NOT NULL    -- epoch
            );
        """)

        # А если у тебя уже есть старая таблица с другими именами колонок — оставим её.
        # Дальше process_referral сам определит, в какую писать.

        db.commit()


# --- Premium Challenges ---
def ensure_premium_challenges():
    """Создаёт таблицу weekly-челленджей, если её нет."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS premium_challenges (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT    NOT NULL,
                week_start TEXT    NOT NULL,         -- ISO-8601 (YYYY-MM-DD) понедельник
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



def _now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _iso_to_epoch_maybe(s: str) -> int:
    """Преобразуем ISO8601/Z в epoch, безопасно."""
    if not s:
        return 0
    try:
        # поддержим '...Z' и '+00:00'
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return 0

@contextmanager
def premium_db():
    """Единая точка подключения к premium.sqlite3."""
    ensure_premium_db()
    conn = sqlite3.connect(PREMIUM_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

    
def _to_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def trial_was_given(user_id) -> bool:
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        row = db.execute("SELECT trial_given FROM user_flags WHERE user_id=?;", (str(user_id),)).fetchone()
        return bool(row and int(row[0]) == 1)

def mark_trial_given(user_id) -> None:
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        db.execute(
            "INSERT INTO user_flags(user_id, trial_given) VALUES(?,1) "
            "ON CONFLICT(user_id) DO UPDATE SET trial_given=1;",
            (str(user_id),)
        )
        db.commit()

def grant_trial_if_eligible(user_id, days: int) -> str | None:
    """Выдаёт триал (N дней), если ещё не выдавали и сейчас нет активного премиума.
       Возвращает iso-дату until или None, если не выдано."""
    if trial_was_given(user_id):
        return None

    now = datetime.now(timezone.utc)
    cur = get_premium_until(user_id)
    if cur:
        try:
            dt = datetime.fromisoformat(cur)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt > now:
                # уже премиум — просто пометим, чтобы не пытаться ещё раз
                mark_trial_given(user_id)
                return None
        except Exception:
            pass

    until = now + timedelta(days=int(days))
    set_premium_until(user_id, _to_utc(until).isoformat())
    mark_trial_given(user_id)
    return _to_utc(until).isoformat()

def referral_already_claimed(invited_id) -> bool:
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        row = db.execute("SELECT 1 FROM referrals WHERE invited_user_id=?;", (str(invited_id),)).fetchone()
        return row is not None


def _parse_any_dt(val: str) -> datetime:
    v = str(val).strip()
    if v.isdigit():
        return datetime.fromtimestamp(int(v), tz=timezone.utc)
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def get_premium_until(user_id: str | int) -> str | None:
    uid = str(user_id)
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        row = db.execute("SELECT until FROM premium WHERE user_id=?;", (uid,)).fetchone()
        return row[0] if row else None


def _set_premium_until_iso(uid: str, until_iso: str) -> None:
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        db.execute(
            "INSERT INTO premium(user_id, until) VALUES(?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET until=excluded.until;",
            (uid, until_iso),
        )
        db.commit()

def set_premium_until(user_id, until, add_days: bool = False) -> None:
    """
    Back-compat:
      - until может быть datetime ИЛИ ISO-строкой.
      - add_days=True — старое поведение «добавить N дней» (если until — datetime в будущем).
    Новым кодом лучше пользоваться set_premium_until_dt() или extend_premium_days().
    """
    uid = str(user_id)

    # Если просили именно "добавить дни"
    if add_days and isinstance(until, datetime):
        now = datetime.now(timezone.utc)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        else:
            until = until.astimezone(timezone.utc)
        delta_days = max(0, int((until - now).total_seconds() // 86400))
        if delta_days > 0:
            extend_premium_days(uid, delta_days)
        else:
            # если delta_days == 0, просто выставим указанную дату
            _set_premium_until_iso(uid, until.isoformat())
        return

    # Обычная установка срока
    if isinstance(until, datetime):
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        else:
            until = until.astimezone(timezone.utc)
        _set_premium_until_iso(uid, until.isoformat())
    else:
        _set_premium_until_iso(uid, str(until))

def set_premium_until_dt(user_id: str | int, dt_utc: datetime) -> None:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)
    _set_premium_until_iso(str(user_id), dt_utc.isoformat())
    
def extend_premium_days(user_id: str | int, days: int) -> str:
    now = datetime.now(timezone.utc)
    cur = get_premium_until(user_id)
    base = now
    if cur:
        try:
            dt = _parse_any_dt(cur)
            if dt > now:
                base = dt
        except Exception:
            pass
    new_until = base + timedelta(days=int(days))
    set_premium_until_dt(user_id, new_until)
    return new_until.isoformat()
    
def is_premium_db(user_id) -> bool:
    """Чистая проверка по БД, без знания про админов (чтобы не тянуть handlers)."""
    until = get_premium_until(user_id)
    if not until:
        return False
    try:
        return _parse_any_dt(until) > datetime.now(timezone.utc)
    except Exception:
        logging.warning("Bad premium_until for %s: %r", user_id, until)
        return False

def migrate_premium_from_stats(load_stats):
    """Одноразовая миграция из старого stats.json (передай сюда функцию load_stats)."""
    try:
        stats = load_stats()
    except Exception:
        return
    moved = 0
    with sqlite3.connect(PREMIUM_DB_PATH) as db:
        for uid, user in (stats or {}).items():
            until = user.get("premium_until")
            if not until:
                continue
            try:
                iso = _parse_any_dt(until).isoformat()
                db.execute(
                    "INSERT INTO premium(user_id, until) VALUES(?, ?) "
                    "ON CONFLICT(user_id) DO UPDATE SET until=excluded.until;",
                    (str(uid), iso),
                )
                moved += 1
            except Exception as e:
                logging.warning("Skip premium migrate for %s: %r (%s)", uid, until, e)
        db.commit()
    logging.info("Premium migration completed: %d users", moved)
    
def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(stats):
    # 🟣 Создаём директорию, если её нет
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def got_trial(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    return user.get("got_trial", False)
    
def set_trial(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    user["got_trial"] = True
    stats[str(user_id)] = user
    save_stats(stats)

def got_referral(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    return user.get("got_referral", False)

def set_referral(user_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    user["got_referral"] = True
    stats[str(user_id)] = user
    save_stats(stats)
    
def add_referral(user_id, referrer_id):
    stats = load_stats()
    user = stats.get(str(user_id), {})
    referrals = user.get("referrals", [])
    if referrer_id not in referrals:
        referrals.append(referrer_id)
    user["referrals"] = referrals
    stats[str(user_id)] = user
    save_stats(stats)

# ==== USER PROGRESS ====

def add_points(user_id: str, amount: int = 1, reason: str | None = None, **kwargs):
    """Начисляет очки. Параметр reason и любые лишние kwargs игнорируются (для совместимости)."""
    stats = load_stats()
    uid = str(user_id)

    user = stats.get(uid, {})
    user["points"] = int(user.get("points", 0)) + int(amount)

    # (опционально) короткий лог — можно убрать
    if reason:
        logging.info(f"add_points: +{amount} to {uid} (reason={reason})")

    stats[uid] = user
    save_stats(stats)
    return user["points"]


# Если у тебя уже есть такой словарь в stats.py — оставь свой и не дублируй.
TITLES = {
    "ru": [(50,"🌱 Новичок"),(100,"✨ Мотиватор"),(250,"🔥 Уверенный"),
           (500,"💎 Наставник"),(float('inf'),"🌟 Легенда")],
    "uk": [(50,"🌱 Новачок"),(100,"✨ Мотиватор"),(250,"🔥 Впевнений"),
           (500,"💎 Наставник"),(float('inf'),"🌟 Легенда")],
    "be": [(50,"🌱 Пачатковец"),(100,"✨ Матыватар"),(250,"🔥 Упэўнены"),
           (500,"💎 Настаўнік"),(float('inf'),"🌟 Легенда")],
    "kk": [(50,"🌱 Бастаушы"),(100,"✨ Мотивация беруші"),(250,"🔥 Сенімді"),
           (500,"💎 Ұстаз"),(float('inf'),"🌟 Аңыз")],
    "kg": [(50,"🌱 Жаңы келген"),(100,"✨ Мотивациячы"),(250,"🔥 Ишенимдүү"),
           (500,"💎 Наcатчы"),(float('inf'),"🌟 Легенда")],
    "hy": [(50,"🌱 Նորեկ"),(100,"✨ Մոտիվատոր"),(250,"🔥 Վստահ"),
           (500,"💎 Խորհրդատու"),(float('inf'),"🌟 Լեգենդ")],
    "ce": [(50,"🌱 Дика хьалхар"),(100,"✨ Мотивация кхетар"),(250,"🔥 Дукха ву"),
           (500,"💎 Къастийна"),(float('inf'),"🌟 Легенда")],
    "md": [(50,"🌱 Începător"),(100,"✨ Motivator"),(250,"🔥 Încrezător"),
           (500,"💎 Mentor"),(float('inf'),"🌟 Legenda")],
    "ka": [(50,"🌱 დამწყები"),(100,"✨ მოტივატორი"),(250,"🔥 დარწმუნებული"),
           (500,"💎 მენტორი"),(float('inf'),"🌟 ლეგენდა")],
    "en": [(50,"🌱 Newbie"),(100,"✨ Motivator"),(250,"🔥 Confident"),
           (500,"💎 Mentor"),(float('inf'),"🌟 Legend")],
}

def get_user_points(user_id: str) -> int:
    stats = load_stats()
    return stats.get(str(user_id), {}).get("points", 0)

def get_user_title(points: int, lang: str = "ru") -> str:
    lang_titles = TITLES.get(lang, TITLES["ru"])
    for threshold, title in lang_titles:
        if points < threshold:
            return title
    return lang_titles[-1][1]

def get_next_title_info(points: int, lang: str = "ru"):
    """
    Возвращает (next_title, to_next).
    next_title — название следующего звания (или текущее максимальное),
    to_next — сколько очков осталось (0, если уже максимум).
    """
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
    

def get_stats(user_id: str):
    user_id = str(user_id)

    goals_data = load_goals() or {}
    user_goals = goals_data.get(user_id, [])
    completed_goals = sum(1 for goal in user_goals if goal.get("done"))

    habits_data = load_habits() or {}
    user_habits = habits_data.get(user_id, [])
    completed_habits = sum(1 for habit in user_habits if habit.get("done"))

    # Если в целях хранится дата (например, created_at), можно считать активные дни
    days_active = len({g.get("created_at")[:10] for g in user_goals if g.get("created_at")}) if user_goals else 0

    mood_entries = 0  # если добавишь учет настроений — посчитаем тут

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

    goals = get_goals(user_id)
    habits = get_habits(user_id)

    total_goals = len(goals)
    completed_goals = sum(1 for g in goals if isinstance(g, dict) and g.get("done"))
    completed_goals_today = sum(1 for g in goals if isinstance(g, dict) and g.get("done_at") == today)

    total_habits = len(habits)
    completed_habits = sum(1 for h in habits if isinstance(h, dict) and h.get("done"))
    completed_habits_today = sum(1 for h in habits if isinstance(h, dict) and h.get("done_at") == today)

    # Поинты: берём откуда есть, мягко
    points = 0
    try:
        from handlers import user_points  # если живёт там
        points = user_points.get(user_id, 0)
    except Exception:
        try:
            from stats import user_points  # если живёт тут
            points = user_points.get(user_id, 0)
        except Exception:
            points = 0

    return {
        "points": points,
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "completed_goals_today": completed_goals_today,
        "total_habits": total_habits,
        "completed_habits": completed_habits,
        "completed_habits_today": completed_habits_today,
    }


def grant_plus_days(uid: str, days: int) -> str:
    """Продлевает Mindra+ на N дней. Возвращает ISO (UTC) окончания."""
    uid = str(uid)
    with premium_db() as db:
        row = db.execute("SELECT plus_until FROM premium WHERE user_id=?;", (uid,)).fetchone()
        now = _now_epoch()
        base = max(now, (row["plus_until"] if row else 0))
        new_until = base + days * 86400
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
        base = max(now, (row["pro_until"] if row else 0))
        new_until = base + days * 86400
        if row:
            db.execute("UPDATE premium SET pro_until=? WHERE user_id=?;", (new_until, uid))
        else:
            db.execute("INSERT INTO premium (user_id, plus_until, pro_until) VALUES (?, 0, ?);", (uid, new_until))
        db.commit()
    return datetime.fromtimestamp(new_until, tz=timezone.utc).isoformat()

def has_plus(uid: str) -> bool:
    with premium_db() as db:
        row = db.execute("SELECT plus_until FROM premium WHERE user_id=?;", (str(uid),)).fetchone()
    return bool(row and row["plus_until"] > _now_epoch())

def has_pro(uid: str) -> bool:
    with premium_db() as db:
        row = db.execute("SELECT pro_until FROM premium WHERE user_id=?;", (str(uid),)).fetchone()
    return bool(row and row["pro_until"] > _now_epoch())

def is_premium(user_id, tier: str = "any") -> bool:
    """tier: 'plus' | 'pro' | 'any'."""
    uid = str(user_id)
    # админы — всегда премиум
    if uid in ADMIN_USER_IDS:
        return True
    if tier == "plus":
        return has_plus(uid)
    if tier == "pro":
        return has_pro(uid)
    return has_plus(uid) or has_pro(uid)


def plan_of(uid: str) -> str:
    """Возвращает PLAN_FREE / PLAN_PLUS / PLAN_PRO."""
    if has_pro(uid):
        return PLAN_PRO
    if has_plus(uid):
        return PLAN_PLUS
    return PLAN_FREE

# Хелперы для твоих ограничений
def has_feature(uid: str, feature_key: str) -> bool:
    plan = plan_of(uid)
    return bool(FEATURE_MATRIX.get(plan, {}).get(feature_key, False))

def quota(uid: str, key: str) -> int:
    plan = plan_of(uid)
    return int(QUOTAS.get(plan, {}).get(key, 0))

# (если используешь в разных местах удобные геттеры)
def reminders_active_limit(uid: str) -> int:
    return quota(uid, "reminders_max") or 0

def _referrals_table_shape(db) -> str:
    """Определяем, какая таблица рефералок есть: 'new' | 'old' | 'none'."""
    tbs = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table';")}
    if "referrals" in tbs:
        cols = {r[1] for r in db.execute("PRAGMA table_info(referrals);")}
        if {"invitee_id", "inviter_id", "created_at"} <= cols:
            return "new"
    if "referrals" in tbs:
        cols = {r[1] for r in db.execute("PRAGMA table_info(referrals);")}
        if {"invited_user_id", "inviter_user_id", "granted_days"}.issubset(cols):
            return "old"
    return "none"

def process_referral(inviter_id: str, invitee_id: str, days: int = 7) -> bool:
    """
    Фиксирует факт приглашения один раз на invitee и даёт пригласившему +days Mindra+.
    Возвращает True, если зачисление выполнено (не было ранее).
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
                       (invitee_id, inviter_id, days))
        else:
            # если таблицы не оказалось (маловероятно) — создадим новую и продолжим
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

    # Бонус — именно Mindra+ (не Pro)
    try:
        grant_plus_days(inviter_id, days)
    except Exception as e:
        logging.warning("grant_plus_days (referral) failed: %s", e)
    return True
