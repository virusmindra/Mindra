import json
import os
from stats import add_points  # добавь в начало goals.py

GOALS_FILE = "goals.json"
GOALS_FILE = Path("user_goals.json")

def mark_goal_done(user_id, index):
    goals = load_goals()
    if user_id in goals and 0 <= index < len(goals[user_id]):
        goals[user_id][index]["done"] = True
        save_goals(goals)
        add_points(user_id, 10)  # начисляем 10 баллов
        return True
    return False

# Загружаем цели
def load_goals():
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохраняем цели
def save_goals(data):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Добавляем новую цель (с дедлайном и напоминанием)
def add_goal(user_id, goal_text, deadline=None, remind=False):
    goals = load_goals()
    if user_id not in goals:
        goals[user_id] = []
    goals[user_id].append({
        "text": goal_text,
        "done": False,
        "deadline": deadline,
        "remind": remind
    })
    save_goals(goals)

# Получаем цели
def get_goals(user_id):
    goals = load_goals()
    return goals.get(user_id, [])

# Отметить цель как выполненную
def mark_goal_done(user_id, index):
    goals = load_goals()
    if user_id in goals and 0 <= index < len(goals[user_id]):
        goals[user_id][index]["done"] = True
        save_goals(goals)
        return True
    return False

# Удалить цель
def delete_goal(user_id, index):
    goals = load_goals()
    if user_id in goals and 0 <= index < len(goals[user_id]):
        goals[user_id].pop(index)
        save_goals(goals)

async def goal_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = user_languages.get(user_id, "ru")
    await query.answer()

    # Мультиязычные тексты
    btn_texts = {
        "ru": {
            "write_goal": "✍️ Напиши свою цель:\n`/goal Прочитать 10 страниц`",
            "no_goals": "❌ У тебя пока нет целей. Добавь первую с помощью /goal",
            "your_goals": "📋 Твои цели:",
            "write_habit": "🌱 Напиши свою привычку:\n`/habit Делать зарядку утром`",
            "no_habits": "❌ У тебя пока нет привычек. Добавь первую через /habit",
            "your_habits": "📊 Твои привычки:"
        },
        "uk": {
            "write_goal": "✍️ Напиши свою ціль:\n`/goal Прочитати 10 сторінок`",
            "no_goals": "❌ У тебе поки немає цілей. Додай першу за допомогою /goal",
            "your_goals": "📋 Твої цілі:",
            "write_habit": "🌱 Напиши свою звичку:\n`/habit Робити зарядку вранці`",
            "no_habits": "❌ У тебе поки немає звичок. Додай першу через /habit",
            "your_habits": "📊 Твої звички:"
        },
        "be": {
            "write_goal": "✍️ Напішы сваю мэту:\n`/goal Прачытай 10 старонак`",
            "no_goals": "❌ У цябе пакуль няма мэтаў. Дадай першую з дапамогай /goal",
            "your_goals": "📋 Твае мэты:",
            "write_habit": "🌱 Напішы сваю звычку:\n`/habit Рабіць зарадку раніцай`",
            "no_habits": "❌ У цябе пакуль няма звычак. Дадай першую праз /habit",
            "your_habits": "📊 Твае звычкі:"
        },
        "kk": {
            "write_goal": "✍️ Мақсатыңды жаз:\n`/goal 10 бет оқу`",
            "no_goals": "❌ Әзірге мақсатың жоқ. Алғашқыны /goal арқылы қоса аласың",
            "your_goals": "📋 Сенің мақсаттарың:",
            "write_habit": "🌱 Әдетіңді жаз:\n`/habit Таңертең жаттығу жасау`",
            "no_habits": "❌ Әзірге әдетің жоқ. Алғашқыны /habit арқылы қос",
            "your_habits": "📊 Сенің әдеттерің:"
        },
        "kg": {
            "write_goal": "✍️ Максатыңды жаз:\n`/goal 10 бет оку`",
            "no_goals": "❌ Азырынча максатың жок. Биринчисин /goal аркылуу кош!",
            "your_goals": "📋 Сенин максаттарың:",
            "write_habit": "🌱 Адатынды жаз:\n`/habit Таңкы көнүгүү жасоо`",
            "no_habits": "❌ Азырынча адатың жок. Биринчисин /habit аркылуу кош",
            "your_habits": "📊 Сенин адаттарың:"
        },
        "hy": {
            "write_goal": "✍️ Գրիր քո նպատակը:\n`/goal Կարդալ 10 էջ`",
            "no_goals": "❌ Դեռ նպատակ չունես։ Ավելացրու առաջինը /goal հրամանով",
            "your_goals": "📋 Քո նպատակները:",
            "write_habit": "🌱 Գրիր քո սովորությունը:\n`/habit Անել լիցքավորում առավոտյան`",
            "no_habits": "❌ Դեռ սովորություն չունես։ Ավելացրու առաջինը /habit հրամանով",
            "your_habits": "📊 Քո սովորությունները:"
        },
        "ce": {
            "write_goal": "✍️ Хьоьшу мацахь лаца:\n`/goal Къобалле 10 агӀо`",
            "no_goals": "❌ Хьоьш цуьнан мацахь цуьнан. /goal кхолларш ду!",
            "your_goals": "📋 Са мацахь:",
            "write_habit": "🌱 Хьоьшу привычка лаца:\n`/habit Бахьар хьалхара йолуш`",
            "no_habits": "❌ Хьоьш цуьнан привычка цуьнан. /habit лаца ду",
            "your_habits": "📊 Са привычка:"
        },
        "md": {
            "write_goal": "✍️ Scrie obiectivul tău:\n`/goal Citește 10 pagini`",
            "no_goals": "❌ Încă nu ai obiective. Adaugă primul cu /goal",
            "your_goals": "📋 Obiectivele tale:",
            "write_habit": "🌱 Scrie obiceiul tău:\n`/habit Fă exerciții dimineața`",
            "no_habits": "❌ Încă nu ai obiceiuri. Adaugă primul cu /habit",
            "your_habits": "📊 Obiceiurile tale:"
        },
        "ka": {
            "write_goal": "✍️ დაწერე შენი მიზანი:\n`/goal წავიკითხო 10 გვერდი`",
            "no_goals": "❌ ჯერჯერობით არ გაქვს მიზანი. დაამატე პირველი /goal-ით",
            "your_goals": "📋 შენი მიზნები:",
            "write_habit": "🌱 დაწერე შენი ჩვევა:\n`/habit დილის ვარჯიში`",
            "no_habits": "❌ ჯერჯერობით არ გაქვს ჩვევა. დაამატე პირველი /habit-ით",
            "your_habits": "📊 შენი ჩვევები:"
        },
        "en": {
            "write_goal": "✍️ Write your goal:\n`/goal Read 10 pages`",
            "no_goals": "❌ You don’t have any goals yet. Add your first with /goal",
            "your_goals": "📋 Your goals:",
            "write_habit": "🌱 Write your habit:\n`/habit Morning exercise`",
            "no_habits": "❌ You don’t have any habits yet. Add your first with /habit",
            "your_habits": "📊 Your habits:"
        }
    }

    t = btn_texts.get(lang, btn_texts["ru"])

    if query.data == "create_goal":
        await query.edit_message_text(t["write_goal"], parse_mode="Markdown")

    elif query.data == "show_goals":
        goals = get_goals(user_id)
        if not goals:
            await query.edit_message_text(t["no_goals"])
        else:
            goals_list = "\n".join([f"• {g['text']} {'✅' if g.get('done') else '❌'}" for g in goals])
            await query.edit_message_text(f"{t['your_goals']}\n{goals_list}")

    elif query.data == "create_habit":
        await query.edit_message_text(t["write_habit"], parse_mode="Markdown")

    elif query.data == "show_habits":
        habits = get_habits(user_id)
        if not habits:
            await query.edit_message_text(t["no_habits"])
        else:
            habits_list = "\n".join([f"• {h['text']} {'✅' if h.get('done') else '❌'}" for h in habits])
            await query.edit_message_text(f"{t['your_habits']}\n{habits_list}")
                    return True
    return False
    
def load_goals():
    if GOALS_FILE.exists():
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_goals(data):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_goal_for_user(user_id, goal_text):
    user_id = str(user_id)
    data = load_goals()
    if user_id not in data:
        data[user_id] = []
    if goal_text not in data[user_id]:
        data[user_id].append(goal_text)
    save_goals(data)

def get_goals_for_user(user_id):
    user_id = str(user_id)
    data = load_goals()
    return data.get(user_id, [])

async def show_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    goals = get_goals_for_user(user_id)  # Новая функция хранения

    # Мультиязычные подписи
    goals_texts = {
        "ru": {
            "no_goals": "🎯 У тебя пока нет целей. Добавь первую с помощью /goal",
            "your_goals": "📋 *Твои цели:*",
            "done": "✅", "not_done": "🔸"
        },
        "uk": {
            "no_goals": "🎯 У тебе поки немає цілей. Додай першу за допомогою /goal",
            "your_goals": "📋 *Твої цілі:*",
            "done": "✅", "not_done": "🔸"
        },
        "be": {
            "no_goals": "🎯 У цябе пакуль няма мэтаў. Дадай першую з дапамогай /goal",
            "your_goals": "📋 *Твае мэты:*",
            "done": "✅", "not_done": "🔸"
        },
        "kk": {
            "no_goals": "🎯 Әзірге мақсатың жоқ. Алғашқыны /goal арқылы қоса аласың",
            "your_goals": "📋 *Сенің мақсаттарың:*",
            "done": "✅", "not_done": "🔸"
        },
        "kg": {
            "no_goals": "🎯 Азырынча максатың жок. Биринчисин /goal аркылуу кош!",
            "your_goals": "📋 *Сенин максаттарың:*",
            "done": "✅", "not_done": "🔸"
        },
        "hy": {
            "no_goals": "🎯 Դեռ նպատակ չունես։ Ավելացրու առաջինը /goal հրամանով",
            "your_goals": "📋 *Քո նպատակները:*",
            "done": "✅", "not_done": "🔸"
        },
        "ce": {
            "no_goals": "🎯 Хьоьш цуьнан мацахь цуьнан. /goal кхолларш ду!",
            "your_goals": "📋 *Са мацахь:*",
            "done": "✅", "not_done": "🔸"
        },
        "md": {
            "no_goals": "🎯 Încă nu ai obiective. Adaugă primul cu /goal",
            "your_goals": "📋 *Obiectivele tale:*",
            "done": "✅", "not_done": "🔸"
        },
        "ka": {
            "no_goals": "🎯 ჯერჯერობით არ გაქვს მიზანი. დაამატე პირველი /goal-ით",
            "your_goals": "📋 *შენი მიზნები:*",
            "done": "✅", "not_done": "🔸"
        },
        "en": {
            "no_goals": "🎯 You don’t have any goals yet. Add your first with /goal",
            "your_goals": "📋 *Your goals:*",
            "done": "✅", "not_done": "🔸"
        },
    }

    t = goals_texts.get(lang, goals_texts["ru"])

    if not goals:
        await update.message.reply_text(t["no_goals"])
        return

    reply = f"{t['your_goals']}\n\n"
    for idx, goal in enumerate(goals, 1):
        status = t["done"] if goal.get("done") else t["not_done"]
        reply += f"{idx}. {status} {goal.get('text', '')}\n"

    await update.message.reply_markdown(reply)

# 🔑 Ключевые слова для определения "похоже на цель" на разных языках
goal_keywords_by_lang = {
    "ru": [
        "хочу", "планирую", "мечтаю", "цель", "начну", "запишусь", "начать",
        "буду делать", "постараюсь", "нужно", "пора", "начинаю", "собираюсь",
        "решил", "решила", "буду", "привычка", "добавить"
    ],
    "uk": [
        "хочу", "планую", "мрію", "ціль", "почну", "запишусь", "почати",
        "буду робити", "постараюся", "треба", "пора", "починаю", "збираюся",
        "вирішив", "вирішила", "буду", "звичка", "додати"
    ],
    "be": [
        "хачу", "планую", "мараю", "мэта", "пачну", "запішуся", "пачаць",
        "буду рабіць", "пастараюся", "трэба", "пара", "пачынаю", "збіраюся",
        "вырашыў", "вырашыла", "буду", "звычка", "дадаць"
    ],
    "kk": [
        "қалаймын", "жоспарлап отырмын", "арманым", "мақсат", "бастаймын", "жазыламын", "бастау",
        "істеймін", "тырысамын", "керек", "уақыты келді", "бастаймын", "жоспарлаймын",
        "шештім", "әдет", "қосу"
    ],
    "kg": [
        "каалайм", "пландоо", "күйүм", "максат", "баштайм", "жазылам", "баштоо",
        "кылам", "аракет кылам", "керек", "убагы келди", "баштайм", "чечтим",
        "адат", "кошуу"
    ],
    "hy": [
        "ուզում եմ", "նախատեսում եմ", "երազում եմ", "նպատակ", "սկսեմ", "գրանցվեմ", "սկսել",
        "պիտի անեմ", "կփորձեմ", "պետք է", "ժամանակն է", "սկսում եմ", "հավաքվում եմ",
        "որոշեցի", "սովորություն", "ավելացնել"
    ],
    "ce": [
        "декъаш", "план", "хьоьшам", "мацахь", "дахьа", "дӀалийтта", "кхеташ",
        "хийцам", "йаьлла", "керла", "хьажар", "йаьлча", "дӀаязде", "привычка"
    ],
    "md": [
        "vreau", "planific", "visez", "obiectiv", "încep", "mă înscriu", "să încep",
        "voi face", "mă voi strădui", "trebuie", "e timpul", "mă apuc", "mă pregătesc",
        "am decis", "obicei", "adaugă"
    ],
    "ka": [
        "მინდა", "ვგეგმავ", "ვოცნებობ", "მიზანი", "დავიწყებ", "ჩავეწერო", "დაწყება",
        "ვაპირებ", "ვეცდები", "საჭიროა", "დროა", "ვიწყებ", "ვსწყვეტ", "ჩვევის", "დამატება"
    ],
    "en": [
        "want", "plan", "dream", "goal", "start", "sign up", "begin",
        "will do", "try to", "need", "time to", "starting", "going to",
        "decided", "habit", "add"
    ],
}

# 🔍 Функция определения
def is_goal_like(text: str, lang: str = "ru") -> bool:
    keywords = goal_keywords_by_lang.get(lang, goal_keywords_by_lang["ru"])
    lower_text = text.lower()
    return any(kw in lower_text for kw in keywords)

async def handle_goal_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # 🌐 Тексты для всех языков
    texts = {
        "ru": {
            "no_index": "⚠️ Укажи номер цели, которую ты выполнил(а).",
            "done": "🎉 Отлично! Цель отмечена как выполненная!",
            "bonus": "\n🏅 Ты получил(а) +10 очков! Всего: {points}",
            "not_found": "⚠️ Цель не найдена."
        },
        "uk": {
            "no_index": "⚠️ Вкажи номер цілі, яку ти виконав(ла).",
            "done": "🎉 Чудово! Ціль відзначена як виконана!",
            "bonus": "\n🏅 Ти отримав(ла) +10 балів! Разом: {points}",
            "not_found": "⚠️ Ціль не знайдена."
        },
        "be": {
            "no_index": "⚠️ Пакажы нумар мэты, якую ты выканаў(ла).",
            "done": "🎉 Выдатна! Мэта адзначана як выкананая!",
            "bonus": "\n🏅 Ты атрымаў(ла) +10 ачкоў! Усяго: {points}",
            "not_found": "⚠️ Мэта не знойдзена."
        },
        "kk": {
            "no_index": "⚠️ Орындаған мақсатыңның нөмірін көрсет.",
            "done": "🎉 Тамаша! Мақсат орындалды деп белгіленді!",
            "bonus": "\n🏅 Сен +10 ұпай алдың! Барлығы: {points}",
            "not_found": "⚠️ Мақсат табылмады."
        },
        "kg": {
            "no_index": "⚠️ Аткарган максатыңдын номерин көрсөт.",
            "done": "🎉 Сонун! Максат аткарылды деп белгиленди!",
            "bonus": "\n🏅 Сен +10 упай алдың! Баары: {points}",
            "not_found": "⚠️ Максат табылган жок."
        },
        "hy": {
            "no_index": "⚠️ Նշիր նպատակի համարը, որը կատարել ես։",
            "done": "🎉 Հիանալի է! Նպատակը նշված է որպես կատարված։",
            "bonus": "\n🏅 Դու ստացել ես +10 միավոր։ Ընդամենը՝ {points}",
            "not_found": "⚠️ Նպատակը չի գտնվել։"
        },
        "ce": {
            "no_index": "⚠️ Цахьана мацахь номер язде.",
            "done": "🎉 Баркалла! Мацахь тӀетоха цаьнан!",
            "bonus": "\n🏅 Хьо +10 балл дӀабула! Юкъ: {points}",
            "not_found": "⚠️ Мацахь йац."
        },
        "md": {
            "no_index": "⚠️ Indică numărul obiectivului pe care l-ai îndeplinit.",
            "done": "🎉 Minunat! Obiectivul a fost marcat ca îndeplinit!",
            "bonus": "\n🏅 Ai primit +10 puncte! Total: {points}",
            "not_found": "⚠️ Obiectivul nu a fost găsit."
        },
        "ka": {
            "no_index": "⚠️ მიუთითე მიზნის ნომერი, რომელიც შეასრულე.",
            "done": "🎉 შესანიშნავია! მიზანი შესრულებულად მონიშნულია!",
            "bonus": "\n🏅 შენ მიიღე +10 ქულა! სულ: {points}",
            "not_found": "⚠️ მიზანი ვერ მოიძებნა."
        },
        "en": {
            "no_index": "⚠️ Specify the number of the goal you completed.",
            "done": "🎉 Great! The goal has been marked as completed!",
            "bonus": "\n🏅 You got +10 points! Total: {points}",
            "not_found": "⚠️ Goal not found."
        }
    }

    t = texts.get(lang, texts["ru"])

    # если не передан номер
    index = int(context.args[0]) if context.args else None
    if index is None:
        await update.message.reply_text(t["no_index"])
        return

    if mark_goal_done(user_id, index):
        add_points(user_id, 5)
        response = t["done"]
        # Премиум бонус
        if user_id in PREMIUM_USERS:  # ✅ замени на свою проверку
            user_points[user_id] = user_points.get(user_id, 0) + 10
            response += t["bonus"].format(points=user_points[user_id])
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(t["not_found"])

async def handle_add_goal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")

    # 🌐 Тексты для всех языков
    texts = {
        "ru": "✨ Готово! Я записала это как твою цель 💪\n\n👉 {goal}",
        "uk": "✨ Готово! Я записала це як твою ціль 💪\n\n👉 {goal}",
        "be": "✨ Гатова! Я запісала гэта як тваю мэту 💪\n\n👉 {goal}",
        "kk": "✨ Дайын! Мен мұны сенің мақсатың ретінде жазып қойдым 💪\n\n👉 {goal}",
        "kg": "✨ Даяр! Муну сенин максатың катары жазып койдум 💪\n\n👉 {goal}",
        "hy": "✨ Պատրաստ է! Ես սա գրեցի որպես քո նպատակ 💪\n\n👉 {goal}",
        "ce": "✨ Лелош! Са хаьа я хьайн мацахьара дӀасер 💪\n\n👉 {goal}",
        "md": "✨ Gata! Am salvat asta ca obiectivul tău 💪\n\n👉 {goal}",
        "ka": "✨ მზადაა! ეს შენს მიზნად ჩავწერე 💪\n\n👉 {goal}",
        "en": "✨ Done! I’ve saved this as your goal 💪\n\n👉 {goal}",
    }

    # 📌 Получаем текст цели
    if "|" in query.data:
        _, goal_text = query.data.split("|", 1)
    else:
        # запасной вариант, если почему-то нет данных
        goal_text = context.chat_data.get("goal_candidate", {
            "ru": "Моя цель",
            "uk": "Моя ціль",
            "be": "Мая мэта",
            "kk": "Менің мақсатым",
            "kg": "Менин максатым",
            "hy": "Իմ նպատակս",
            "ce": "Са мацахь",
            "md": "Obiectivul meu",
            "ka": "ჩემი მიზანი",
            "en": "My goal",
        }.get(lang, "Моя цель"))

    # 💾 Сохраняем цель
    add_goal_for_user(user_id, goal_text)

    # 📤 Отправляем сообщение
    await query.message.reply_text(texts.get(lang, texts["ru"]).format(goal=goal_text))

async def delete_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = user_languages.get(user_id, "ru")
    msgs = DELETE_MESSAGES.get(lang, DELETE_MESSAGES["ru"])

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(msgs["usage"], parse_mode="Markdown")
        return

    index = int(context.args[0]) - 1
    success = delete_goal(user_id, index)

    if success:
        await update.message.reply_text(msgs["deleted"])
    else:
        await update.message.reply_text(msgs["not_found"])
