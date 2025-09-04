import os

# 🔤 Сообщения для ответа пользователю при распознавании голоса
VOICE_TEXTS_BY_LANG = {
    "ru": {"you_said": "📝 Ты сказал(а):", "error": "❌ Ошибка при распознавании голоса, попробуй позже."},
    "uk": {"you_said": "📝 Ти сказав(ла):", "error": "❌ Помилка розпізнавання голосу, спробуй пізніше."},
    "be": {"you_said": "📝 Ты сказаў(ла):", "error": "❌ Памылка пры распазнаванні голасу, паспрабуй пазней."},
    "kk": {"you_said": "📝 Сен айттың:", "error": "❌ Дыбысты тануда қате, кейінірек көр."},
    "kg": {"you_said": "📝 Сен мындай дедиң:", "error": "❌ Үндү таанууда ката, кийинчерээк аракет кыл."},
    "hy": {"you_said": "📝 Դու ասեցիր․", "error": "❌ Սխալ ձայնի ճանաչման ժամանակ, փորձիր ուշացնել."},
    "ce": {"you_said": "📝 Хьо йаьлла:", "error": "❌ ГӀалат хьо дохку, дагӀийна кхеташ."},
    "md": {"you_said": "📝 Ai spus:", "error": "❌ Eroare la recunoașterea vocii, încearcă mai târziu."},
    "ka": {"you_said": "📝 შენ თქვი:", "error": "❌ ხმის ამოცნობის შეცდომა, სცადე მოგვიანებით."},
    "en": {"you_said": "📝 You said:", "error": "❌ Error recognizing voice, please try again later."},
}

LANG_TO_TTS = {
    "ru":"ru", "uk":"uk", "md":"ro", "be":"be", "kk":"kk",
    "kg":"ky", "hy":"hy", "ka":"ka", "ce":"ru", "en":"en"
}

# ==== PLANS ===========================
PLAN_FREE = "free"
PLAN_PLUS = "plus"        # Mindra+
PLAN_PRO  = "pro"         # Mindra Pro

ALL_PLANS = (PLAN_FREE, PLAN_PLUS, PLAN_PRO)
PLAN_LABEL = {"plus": "Mindra+", "pro": "Mindra Pro"}


# Сообщения об ограничении (10 языков)
TRACKER_LIMIT_TEXTS = {
    "ru": {
        "free_goal":  "⚠️ В бесплатном тарифе доступна только *{limit}* цель.\nСейчас: *{current}/{limit}*.\nОбнови до *Mindra+*, чтобы иметь до *5 целей*.",
        "free_habit": "⚠️ В бесплатном тарифе доступна только *{limit}* привычка.\nСейчас: *{current}/{limit}*.\nОбнови до *Mindra+*, чтобы иметь до *5 привычек*.",
        "plus_goal":  "⚠️ В Mindra+ лимит — *{limit}* целей.\nСейчас: *{current}/{limit}*.\nПерейди на *Mindra Pro*, чтобы снять лимиты.",
        "plus_habit": "⚠️ В Mindra+ лимит — *{limit}* привычек.\nСейчас: *{current}/{limit}*.\nПерейди на *Mindra Pro*, чтобы снять лимиты.",
    },
    "uk": {
        "free_goal":  "⚠️ У безкоштовному тарифі доступна лише *{limit}* ціль.\nЗараз: *{current}/{limit}*.\nОформи *Mindra+*, щоб мати до *5 цілей*.",
        "free_habit": "⚠️ У безкоштовному тарифі доступна лише *{limit}* звичка.\nЗараз: *{current}/{limit}*.\nОформи *Mindra+*, щоб мати до *5 звичок*.",
        "plus_goal":  "⚠️ У Mindra+ ліміт — *{limit}* цілей.\nЗараз: *{current}/{limit}*.\nПерейдіть на *Mindra Pro*, щоб зняти ліміти.",
        "plus_habit": "⚠️ У Mindra+ ліміт — *{limit}* звичок.\nЗараз: *{current}/{limit}*.\nПерейдіть на *Mindra Pro*, щоб зняти ліміти.",
    },
    "en": {
        "free_goal":  "⚠️ Free plan allows only *{limit}* goal.\nNow: *{current}/{limit}*.\nUpgrade to *Mindra+* for up to *5 goals*.",
        "free_habit": "⚠️ Free plan allows only *{limit}* habit.\nNow: *{current}/{limit}*.\nUpgrade to *Mindra+* for up to *5 habits*.",
        "plus_goal":  "⚠️ Mindra+ limit is *{limit}* goals.\nNow: *{current}/{limit}*.\nGo *Mindra Pro* for unlimited.",
        "plus_habit": "⚠️ Mindra+ limit is *{limit}* habits.\nNow: *{current}/{limit}*.\nGo *Mindra Pro* for unlimited.",
    },
    "md": {
        "free_goal":  "⚠️ În planul gratuit este permis doar *{limit}* obiectiv.\nAcum: *{current}/{limit}*.\nTreci la *Mindra+* pentru până la *5 obiective*.",
        "free_habit": "⚠️ În planul gratuit este permis doar *{limit}* obicei.\nAcum: *{current}/{limit}*.\nTreci la *Mindra+* pentru până la *5 obiceiuri*.",
        "plus_goal":  "⚠️ În Mindra+ limita este *{limit}* obiective.\nAcum: *{current}/{limit}*.\nAlege *Mindra Pro* pentru nelimitat.",
        "plus_habit": "⚠️ În Mindra+ limita este *{limit}* obiceiuri.\nAcum: *{current}/{limit}*.\nAlege *Mindra Pro* pentru nelimitat.",
    },
    "be": {
        "free_goal":  "⚠️ У бясплатным тарыфе дазволена толькі *{limit}* мэта.\nЗараз: *{current}/{limit}*.\nАформі *Mindra+*, каб мець да *5 мэт*.",
        "free_habit": "⚠️ У бясплатным тарыфе дазволена толькі *{limit}* звычка.\nЗараз: *{current}/{limit}*.\nАформі *Mindra+*, каб мець да *5 звычак*.",
        "plus_goal":  "⚠️ У Mindra+ ліміт — *{limit}* мэт.\nЗараз: *{current}/{limit}*.\nПераходзь на *Mindra Pro*, каб зняць ліміты.",
        "plus_habit": "⚠️ У Mindra+ ліміт — *{limit}* звычак.\nЗараз: *{current}/{limit}*.\nПераходзь на *Mindra Pro*, каб зняць ліміты.",
    },
    "kk": {
        "free_goal":  "⚠️ Тегін жоспар тек *{limit}* мақсатқа рұқсат етеді.\nҚазір: *{current}/{limit}*.\n*Mindra+* — *5 мақсатқа дейін*.",
        "free_habit": "⚠️ Тегін жоспар тек *{limit}* әдетке рұқсат етеді.\nҚазір: *{current}/{limit}*.\n*Mindra+* — *5 әдетке дейін*.",
        "plus_goal":  "⚠️ Mindra+ лимиті — *{limit}* мақсат.\nҚазір: *{current}/{limit}*.\n*Mindra Pro* — шектеусіз.",
        "plus_habit": "⚠️ Mindra+ лимиті — *{limit}* әдет.\nҚазір: *{current}/{limit}*.\n*Mindra Pro* — шектеусіз.",
    },
    "kg": {
        "free_goal":  "⚠️ Тегин планда болгону *{limit}* максатка уруксат.\nАзыр: *{current}/{limit}*.\n*Mindra+* — *5 максатка чейин*.",
        "free_habit": "⚠️ Тегин планда болгону *{limit}* адатка уруксат.\nАзыр: *{current}/{limit}*.\n*Mindra+* — *5 адатка чейин*.",
        "plus_goal":  "⚠️ Mindra+ лимити — *{limit}* максат.\nАзыр: *{current}/{limit}*.\n*Mindra Pro* — чек жок.",
        "plus_habit": "⚠️ Mindra+ лимити — *{limit}* адат.\nАзыр: *{current}/{limit}*.\n*Mindra Pro* — чек жок.",
    },
    "hy": {
        "free_goal":  "⚠️ Անվճար փաթեթում թույլատրվում է միայն *{limit}* նպատակ։\nՀիմա՝ *{current}/{limit}*։\nՆվազեցրու սահմանափակումները *Mindra+*-ով՝ մինչև *5 նպատակ*։",
        "free_habit": "⚠️ Անվճար փաթեթում թույլատրվում է միայն *{limit}* սովորություն։\nՀիմա՝ *{current}/{limit}*։\n*Mindra+*՝ մինչև *5 սովորություն*։",
        "plus_goal":  "⚠️ Mindra+-ում սահմանը *{limit}* նպատակ է։\nՀիմա՝ *{current}/{limit}*։\n*Mindra Pro* — առանց սահմանների։",
        "plus_habit": "⚠️ Mindra+-ում սահմանը *{limit}* սովորություն է։\nՀիմա՝ *{current}/{limit}*։\n*Mindra Pro* — առանց սահմանների։",
    },
    "ka": {
        "free_goal":  "⚠️ უფასო პაკეტში მხოლოდ *{limit}* მიზანია დაშვებული.\nახლა: *{current}/{limit}*.\n*Mindra+* — *მდე 5 მიზანი*.",
        "free_habit": "⚠️ უფასო პაკეტში მხოლოდ *{limit}* ჩვევაა დაშვებული.\nახლა: *{current}/{limit}*.\n*Mindra+* — *მდე 5 ჩვევა*.",
        "plus_goal":  "⚠️ Mindra+ ლიმიტი — *{limit}* მიზანი.\nახლა: *{current}/{limit}*.\n*Mindra Pro* — შეუზღუდავად.",
        "plus_habit": "⚠️ Mindra+ ლიმიტი — *{limit}* ჩვევა.\nახლა: *{current}/{limit}*.\n*Mindra Pro* — შეუზღუდავად.",
    },
    "ce": {
        "free_goal":  "⚠️ Беплатна хан *{limit}* максат йу.\nХӀинца: *{current}/{limit}*.\n*Mindra+* — до *5* максата.",
        "free_habit": "⚠️ Беплатна хан *{limit}* гӀирс йу.\nХӀинца: *{current}/{limit}*.\n*Mindra+* — до *5* гӀирса.",
        "plus_goal":  "⚠️ Mindra+ да лахар — *{limit}* максата.\nХӀинца: *{current}/{limit}*.\n*Mindra Pro* — дац лахар.",
        "plus_habit": "⚠️ Mindra+ да лахар — *{limit}* гӀирса.\nХӀинца: *{current}/{limit}*.\n*Mindra Pro* — дац лахар.",
    },
}
MENU_TEXTS = {
    "ru": {
        "title": "🏠 Главное меню",
        "premium_until": "💎 Премиум до: *{until}*",
        "premium_none": "💎 Премиум: *нет*",
        "features": "🧰 Функции",
        "plus_features": "💠 Премиум-функции",
        "premium": "💎 Премиум",
        "settings": "⚙️ Настройки",
        "back": "⬅️ Назад",
        "close": "✖️ Закрыть",

        # Функции (обычные)
        "feat_title": "🧰 Функции",
        "feat_body": "Выбери раздел:",
        "feat_tracker": "🎯 Трекер (цели и привычки)",
        "feat_reminders": "⏰ Напоминания",
        "feat_points": "⭐️ Очки/Титул",
        "feat_mood": "🧪 Тест настроения",
        "features_mode": "🎛 Режим общения (/mode)",

        # Премиум-функции
        "plus_title": "💠 Премиум-функции",
        "plus_body": "Доступно в Mindra+:",
        "plus_voice": "🎙 Озвучка",
        "plus_sleep": "😴 Звуки для сна",
        "plus_story": "📖 Сказка",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        # Премиум
        "prem_title": "💎 Премиум",
        "premium_days": "Сколько осталось?",
        "invite": "Пригласить друга (+7 дней)",
        "premium_buy": "Купить Mindra+",

        # Настройки
        "set_title": "⚙️ Настройки",
        "set_body": "Что настроить?",
        "set_lang": "🌐 Язык",
        "set_tz": "🕒 Часовой пояс",
        "set_feedback": "💌 Оставить отзыв",
        "feedback_ask": "Напиши сюда отзыв, идею или баг — я передам его разработчику 💜",
        "feedback_thx": "Спасибо за отзыв! ✨",
    },

    "uk": {
        "title": "🏠 Головне меню",
        "premium_until": "💎 Преміум до: *{until}*",
        "premium_none": "💎 Преміум: *немає*",
        "features": "🧰 Функції",
        "plus_features": "💠 Преміум-функції",
        "premium": "💎 Преміум",
        "settings": "⚙️ Налаштування",
        "back": "⬅️ Назад",
        "close": "✖️ Закрити",

        "feat_title": "🧰 Функції",
        "feat_body": "Оберіть розділ:",
        "feat_tracker": "🎯 Трекер (цілі та звички)",
        "feat_reminders": "⏰ Нагадування",
        "feat_points": "⭐️ Бали/Титул",
        "feat_mood": "🧪 Тест настрою",
        "features_mode": "🎛 Режим спілкування (/mode)",

        "plus_title": "💠 Преміум-функції",
        "plus_body": "Доступно в Mindra+:",
        "plus_voice": "🎙 Озвучення",
        "plus_sleep": "😴 Звуки для сну",
        "plus_story": "📖 Казка",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Преміум",
        "premium_days": "Скільки залишилось?",
        "invite": "Запросити друга (+7 днів)",
        "premium_buy": "Купити Mindra+",

        "set_title": "⚙️ Налаштування",
        "set_body": "Що налаштувати?",
        "set_lang": "🌐 Мова",
        "set_tz": "🕒 Часовий пояс",
        "set_feedback": "💌 Залишити відгук",
        "feedback_ask": "Напишіть ваш відгук або ідею — я передам розробнику 💜",
        "feedback_thx": "Дякуємо за відгук! ✨",
    },

    "en": {
        "title": "🏠 Main menu",
        "premium_until": "💎 Premium until: *{until}*",
        "premium_none": "💎 Premium: *none*",
        "features": "🧰 Features",
        "plus_features": "💠 Premium features",
        "premium": "💎 Premium",
        "settings": "⚙️ Settings",
        "back": "⬅️ Back",
        "close": "✖️ Close",

        "feat_title": "🧰 Features",
        "feat_body": "Pick a section:",
        "feat_tracker": "🎯 Tracker (goals & habits)",
        "feat_reminders": "⏰ Reminders",
        "feat_points": "⭐️ Points/Title",
        "feat_mood": "🧪 Mood test",
        "features_mode": "🎛 Chat mode (/mode)",

        "plus_title": "💠 Premium features",
        "plus_body": "Included in Mindra+:",
        "plus_voice": "🎙 Voice",
        "plus_sleep": "😴 Sleep sounds",
        "plus_story": "📖 Story",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Premium",
        "premium_days": "How many days left?",
        "invite": "Invite a friend (+7 days)",
        "premium_buy": "Buy Mindra+",

        "set_title": "⚙️ Settings",
        "set_body": "What to configure?",
        "set_lang": "🌐 Language",
        "set_tz": "🕒 Time zone",
        "set_feedback": "💌 Leave feedback",
        "feedback_ask": "Type your feedback or idea — I’ll pass it to the developer 💜",
        "feedback_thx": "Thanks for your feedback! ✨",
    },

    "md": {  # Romanian / Moldovenească
        "title": "🏠 Meniu principal",
        "premium_until": "💎 Premium până la: *{until}*",
        "premium_none": "💎 Premium: *nu*",
        "features": "🧰 Funcții",
        "plus_features": "💠 Funcții Premium",
        "premium": "💎 Premium",
        "settings": "⚙️ Setări",
        "back": "⬅️ Înapoi",
        "close": "✖️ Închide",

        "feat_title": "🧰 Funcții",
        "feat_body": "Alege o secțiune:",
        "feat_tracker": "🎯 Tracker (obiective & obiceiuri)",
        "feat_reminders": "⏰ Mementouri",
        "feat_points": "⭐️ Puncte/Titlu",
        "feat_mood": "🧪 Test stare de spirit",
        "features_mode": "🎛 Modul chat (/mode)",

        "plus_title": "💠 Funcții Premium",
        "plus_body": "Incluse în Mindra+:",
        "plus_voice": "🎙 Voce",
        "plus_sleep": "😴 Sunete pentru somn",
        "plus_story": "📖 Poveste",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Premium",
        "premium_days": "Câte zile au rămas?",
        "invite": "Invită un prieten (+7 zile)",
        "premium_buy": "Cumpără Mindra+",

        "set_title": "⚙️ Setări",
        "set_body": "Ce dorești să configurezi?",
        "set_lang": "🌐 Limba",
        "set_tz": "🕒 Fus orar",
        "set_feedback": "💌 Trimite feedback",
        "feedback_ask": "Scrie feedbackul sau ideea ta — o transmit dezvoltatorului 💜",
        "feedback_thx": "Mulțumim pentru feedback! ✨",
    },

    "be": {
        "title": "🏠 Галоўнае меню",
        "premium_until": "💎 Прэміум да: *{until}*",
        "premium_none": "💎 Прэміум: *няма*",
        "features": "🧰 Функцыі",
        "plus_features": "💠 Прэміум-функцыі",
        "premium": "💎 Прэміум",
        "settings": "⚙️ Налады",
        "back": "⬅️ Назад",
        "close": "✖️ Закрыць",

        "feat_title": "🧰 Функцыі",
        "feat_body": "Абярыце раздзел:",
        "feat_tracker": "🎯 Трэкер (мэты і звычкі)",
        "feat_reminders": "⏰ Напамінкі",
        "feat_points": "⭐️ Балы/Тытул",
        "feat_mood": "🧪 Тэст настрою",
        "features_mode": "🎛 Рэжым зносін (/mode)",

        "plus_title": "💠 Прэміум-функцыі",
        "plus_body": "Даступна ў Mindra+:",
        "plus_voice": "🎙 Голас",
        "plus_sleep": "😴 Гукі для сну",
        "plus_story": "📖 Казка",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Прэміум",
        "premium_days": "Колькі засталося?",
        "invite": "Запрасіць сябра (+7 дзён)",
        "premium_buy": "Набыць Mindra+",

        "set_title": "⚙️ Налады",
        "set_body": "Што наладзіць?",
        "set_lang": "🌐 Мова",
        "set_tz": "🕒 Часавы пояс",
        "set_feedback": "💌 Пакінуць водгук",
        "feedback_ask": "Напішыце водгук або ідэю — перадам распрацоўшчыку 💜",
        "feedback_thx": "Дзякуй за водгук! ✨",
    },

    "kk": {
        "title": "🏠 Негізгі мәзір",
        "premium_until": "💎 Премиум аяқталуы: *{until}*",
        "premium_none": "💎 Премиум: *жоқ*",
        "features": "🧰 Функциялар",
        "plus_features": "💠 Премиум-функциялар",
        "premium": "💎 Премиум",
        "settings": "⚙️ Баптаулар",
        "back": "⬅️ Артқа",
        "close": "✖️ Жабу",

        "feat_title": "🧰 Функциялар",
        "feat_body": "Бөлімді таңдаңыз:",
        "feat_tracker": "🎯 Трекер (мақсаттар мен әдеттер)",
        "feat_reminders": "⏰ Еске салғыштар",
        "feat_points": "⭐️ Ұпай/Титул",
        "feat_mood": "🧪 Көңіл-күй тесті",
        "features_mode": "🎛 Чат режимі (/mode)",

        "plus_title": "💠 Премиум-функциялар",
        "plus_body": "Mindra+ құрамында:",
        "plus_voice": "🎙 Дауыс",
        "plus_sleep": "😴 Ұйқы дыбыстары",
        "plus_story": "📖 Ертегі",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Премиум",
        "premium_days": "Қанша күн қалды?",
        "invite": "Досты шақыру (+7 күн)",
        "premium_buy": "Mindra+ сатып алу",

        "set_title": "⚙️ Баптаулар",
        "set_body": "Нені баптаймыз?",
        "set_lang": "🌐 Тіл",
        "set_tz": "🕒 Уақыт белдеуі",
        "set_feedback": "💌 Пікір қалдыру",
        "feedback_ask": "Пікіріңізді/идеяңызды жазыңыз — әзірлеушіге жеткіземін 💜",
        "feedback_thx": "Пікір үшін рақмет! ✨",
    },

    "kg": {
        "title": "🏠 Башкы меню",
        "premium_until": "💎 Премиум бүткөнгө чейин: *{until}*",
        "premium_none": "💎 Премиум: *жок*",
        "features": "🧰 Функциялар",
        "plus_features": "💠 Премиум-функциялар",
        "premium": "💎 Премиум",
        "settings": "⚙️ Жөндөөлөр",
        "back": "⬅️ Артка",
        "close": "✖️ Жабуу",

        "feat_title": "🧰 Функциялар",
        "feat_body": "Бөлүмдү тандаңыз:",
        "feat_tracker": "🎯 Трекер (максаттар жана адаттар)",
        "feat_reminders": "⏰ Эскертмелер",
        "feat_points": "⭐️ Упай/Наам",
        "feat_mood": "🧪 Көңүл-күй тести",
        "features_mode": "🎛 Байланыш режими (/mode)",

        "plus_title": "💠 Премиум-функциялар",
        "plus_body": "Mindra+ курамында:",
        "plus_voice": "🎙 Үн менен окуу",
        "plus_sleep": "😴 Уктоо үндөрү",
        "plus_story": "📖 Жомок",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Премиум",
        "premium_days": "Канча күн калды?",
        "invite": "Досуңду чакыр (+7 күн)",
        "premium_buy": "Mindra+ сатып алуу",

        "set_title": "⚙️ Жөндөөлөр",
        "set_body": "Эмне жөндөйбүз?",
        "set_lang": "🌐 Тил",
        "set_tz": "🕒 Саат алкагы",
        "set_feedback": "💌 Пикир калтыруу",
        "feedback_ask": "Пикириңизди/идеяңызды жазыңыз — иштеп чыгуучуга өткөрөм 💜",
        "feedback_thx": "Пикириңиз үчүн рахмат! ✨",
    },

    "hy": {
        "title": "🏠 Գլխավոր մենյու",
        "premium_until": "💎 Պրեմիումը մինչև՝ *{until}*",
        "premium_none": "💎 Պրեմիում՝ *չկա*",
        "features": "🧰 Ֆունկցիաներ",
        "plus_features": "💠 Պրեմիում ֆունկցիաներ",
        "premium": "💎 Պրեմիում",
        "settings": "⚙️ Կարգավորումներ",
        "back": "⬅️ Վերադառնալ",
        "close": "✖️ Փակել",

        "feat_title": "🧰 Ֆունկցիաներ",
        "feat_body": "Ընտրեք բաժինը․",
        "feat_tracker": "🎯 Թրեքեր (նպատակներ և սովորություններ)",
        "feat_reminders": "⏰ Հիշեցումներ",
        "feat_points": "⭐️ Միավորներ/Կոչում",
        "feat_mood": "🧪 Տրամադրության թեստ",
        "features_mode": "🎛 Շփման ռեժիմ (/mode)",

        "plus_title": "💠 Պրեմիում ֆունկցիաներ",
        "plus_body": "Mindra+ փաթեթում՝",
        "plus_voice": "🎙 Ձայնային ընթերցում",
        "plus_sleep": "😴 Քնի ձայներ",
        "plus_story": "📖 Հեքիաթ",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Պրեմիում",
        "premium_days": "Քանի՞ օր է մնացել",
        "invite": "Հրավիրել ընկերոջ (+7 օր)",
        "premium_buy": "Գնել Mindra+",

        "set_title": "⚙️ Կարգավորումներ",
        "set_body": "Ի՞նչ կարգավորել։",
        "set_lang": "🌐 Լեզու",
        "set_tz": "🕒 Ժամային գոտի",
        "set_feedback": "💌 Թողնել կարծիք",
        "feedback_ask": "Գրեք ձեր կարծիքը կամ գաղափարը — կփոխանցեմ մշակողին 💜",
        "feedback_thx": "Շնորհակալություն կարծիքի համար! ✨",
    },

    "ka": {
        "title": "🏠 მთავარი მენიუ",
        "premium_until": "💎 პრემიუმი მოქმედებსამდე: *{until}*",
        "premium_none": "💎 პრემიუმი: *არა*",
        "features": "🧰 ფუნქციები",
        "plus_features": "💠 პრემიუმ-ფუნქციები",
        "premium": "💎 პრემიუმი",
        "settings": "⚙️ პარამეტრები",
        "back": "⬅️ უკან",
        "close": "✖️ დახურვა",

        "feat_title": "🧰 ფუნქციები",
        "feat_body": "აირჩიე განყოფილება:",
        "feat_tracker": "🎯 ტრეკერი (მიზნები და ჩვევები)",
        "feat_reminders": "⏰ შეხსენებები",
        "feat_points": "⭐️ ქულები/ტიტული",
        "feat_mood": "🧪 განწყობის ტესტი",
        "features_mode": "🎛 ჩატის რეჟიმი (/mode)",

        "plus_title": "💠 პრემიუმ-ფუნქციები",
        "plus_body": "Mindra+-ში შედის:",
        "plus_voice": "🎙 ხმოვანი პასუხი",
        "plus_sleep": "😴 ძილის ხმები",
        "plus_story": "📖 ზღაპარი",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 პრემიუმი",
        "premium_days": "რამდენი დღე დარჩა?",
        "invite": "მოიწვიე მეგობარი (+7 დღე)",
        "premium_buy": "შეიძინე Mindra+",

        "set_title": "⚙️ პარამეტრები",
        "set_body": "რას ვანstellოთ?",
        "set_lang": "🌐 ენა",
        "set_tz": "🕒 დროის სარტყელი",
        "set_feedback": "💌 დატოვე უკუკავშირი",
        "feedback_ask": "დაწერე იდეა/უკუკავშირი — გადავცემ დეველოპერს 💜",
        "feedback_thx": "მადლობა გამოხმაურებისთვის! ✨",
    },

    "ce": {
        "title": "🏠 Кхоьламан мәзхьа",
        "premium_until": "💎 Премиум хьалха: *{until}*",
        "premium_none": "💎 Премиум: *дийцар дац*",
        "features": "🧰 Функци",
        "plus_features": "💠 Премиум-функци",
        "premium": "💎 Премиум",
        "settings": "⚙️ Настройка",
        "back": "⬅️ Йуьккха",
        "close": "✖️ ДӀахӀоттар",

        "feat_title": "🧰 Функци",
        "feat_body": "Дакъахо а са цӀера:",
        "feat_tracker": "🎯 Трекер (максаташ та гӀирсаш)",
        "feat_reminders": "⏰ ДӀасалаш",
        "feat_points": "⭐️ Балаш/Титул",
        "feat_mood": "🧪 ХӀам тӀест",
        "features_mode": "🎛 Режим чулацаман (/mode)",

        "plus_title": "💠 Премиум-функци",
        "plus_body": "Mindra+ да:",
        "plus_voice": "🎙 Дохьургам",
        "plus_sleep": "😴 Дерриг ухуш хур",
        "plus_story": "📖 ХӀикхар",
        "plus_pmode": "🟣 Premium-mode",
        "plus_pstats": "📊 Premium-stats",
        "plus_preport": "📝 Premium-report",
        "plus_pchallenge": "🏆 Premium-challenge",

        "prem_title": "💎 Премиум",
        "premium_days": "Кхин деранца?",
        "invite": "Ду тӀео доттагӀа (+7 де)",
        "premium_buy": "Mindra+ юкъара",

        "set_title": "⚙️ Настройка",
        "set_body": "Ма туйлина?",
        "set_lang": "🌐 Мотт",
        "set_tz": "🕒 Ваха бериг",
        "set_feedback": "💌 ДӀаяздар дӀаязде",
        "feedback_ask": "ДӀаязде хьо кхин — дIадакхяр чурахь ду разработчику 💜",
        "feedback_thx": "Баркалла дӀаязда! ✨",
    },
}


UPSELL_TEXTS = {
    "ru": {
        "title": "Нужна подписка",
        "feature_story_voice": "Озвучка сказок доступна в {plus} и {pro}. Откройте волшебные истории с голосом и фоном 🌙",
        "feature_eleven":     "Премиальные голоса ElevenLabs доступны в {plus} и {pro}.",
        "feature_bgm":        "Фоновые звуки поверх речи доступны в {plus}/{pro}.",
        "feature_sleep_long": "Длительность сна больше {min} мин — в {plus}/{pro}.",
        "feature_story_long": "Средние и длинные сказки — в {plus}/{pro}.",
        "feature_quota_msg":  "Достигнут дневной лимит сообщений ({n}). Больше — в {plus}/{pro}.",
        "feature_goals":      "Больше целей — в {plus}/{pro}.",
        "feature_habits":     "Больше привычек — в {plus}/{pro}.",
        "feature_reminders":  "Больше напоминаний — в {plus}/{pro}.",
        "cta": "Оформить → /premium",
    },
    "uk": {
        "title": "Потрібна підписка",
        "feature_story_voice": "Озвучення казок доступне в {plus} та {pro}.",
        "feature_eleven":      "Голоси ElevenLabs — в {plus} та {pro}.",
        "feature_bgm":         "Фонові звуки поверх мови — в {plus}/{pro}.",
        "feature_sleep_long":  "Тривалість сну понад {min} хв — в {plus}/{pro}.",
        "feature_story_long":  "Середні та довгі казки — в {plus}/{pro}.",
        "feature_quota_msg":   "Денний ліміт повідомлень ({n}) досягнуто. Більше — в {plus}/{pro}.",
        "feature_goals":       "Більше цілей — в {plus}/{pro}.",
        "feature_habits":      "Більше звичок — в {plus}/{pro}.",
        "feature_reminders":   "Більше нагадувань — в {plus}/{pro}.",
        "cta": "Оформити → /premium",
    },
    "en": {
        "title": "Subscription required",
        "feature_story_voice": "Story voice playback is available on {plus} and {pro}.",
        "feature_eleven":      "Premium ElevenLabs voices are on {plus} and {pro}.",
        "feature_bgm":         "Background ambience over speech is on {plus}/{pro}.",
        "feature_sleep_long":  "Sleep longer than {min} min is on {plus}/{pro}.",
        "feature_story_long":  "Medium/long stories are on {plus}/{pro}.",
        "feature_quota_msg":   "Daily message cap ({n}) reached. Get more with {plus}/{pro}.",
        "feature_goals":       "More goals with {plus}/{pro}.",
        "feature_habits":      "More habits with {plus}/{pro}.",
        "feature_reminders":   "More reminders with {plus}/{pro}.",
        "cta": "Upgrade → /premium",
    },

    # ——— MD (ro) ———
    "md": {
        "title": "Necesită abonament",
        "feature_story_voice": "Redarea cu voce a poveștilor este disponibilă în {plus} și {pro}.",
        "feature_eleven":      "Vocile premium ElevenLabs sunt disponibile în {plus} și {pro}.",
        "feature_bgm":         "Sunete de fundal peste vorbire sunt disponibile în {plus}/{pro}.",
        "feature_sleep_long":  "Durată pentru somn peste {min} min — în {plus}/{pro}.",
        "feature_story_long":  "Povești medii și lungi — în {plus}/{pro}.",
        "feature_quota_msg":   "Limita zilnică de mesaje ({n}) a fost atinsă. Mai mult în {plus}/{pro}.",
        "feature_goals":       "Mai multe obiective — în {plus}/{pro}.",
        "feature_habits":      "Mai multe obiceiuri — în {plus}/{pro}.",
        "feature_reminders":   "Mai multe mementouri — în {plus}/{pro}.",
        "cta": "Upgrade → /premium",
    },

    # ——— BE (be) ———
    "be": {
        "title": "Патрабуецца падпіска",
        "feature_story_voice": "Агучванне казак даступна ў {plus} і {pro}.",
        "feature_eleven":      "Галасы ElevenLabs даступныя ў {plus} і {pro}.",
        "feature_bgm":         "Фонавыя гукі паверх маўлення — у {plus}/{pro}.",
        "feature_sleep_long":  "Працягласць сну больш за {min} хв — у {plus}/{pro}.",
        "feature_story_long":  "Сярэднія і доўгія казкі — у {plus}/{pro}.",
        "feature_quota_msg":   "Дзённы ліміт паведамленняў ({n}) дасягнуты. Больш — у {plus}/{pro}.",
        "feature_goals":       "Больш мэтаў — у {plus}/{pro}.",
        "feature_habits":      "Больш звычак — у {plus}/{pro}.",
        "feature_reminders":   "Больш напамінкаў — у {plus}/{pro}.",
        "cta": "Абнавіць → /premium",
    },

    # ——— KK (kk) ———
    "kk": {
        "title": "Жазылым қажет",
        "feature_story_voice": "Ертегіні дауыспен тыңдау {plus} және {pro} жоспарларында қолжетімді.",
        "feature_eleven":      "ElevenLabs дауыстары {plus} және {pro} жоспарларында.",
        "feature_bgm":         "Сөйлеудің үстіне фондық дыбыстар — {plus}/{pro}.",
        "feature_sleep_long":  "{min} минуттан ұзақ ұйқы дыбыстары — {plus}/{pro}.",
        "feature_story_long":  "Орта және ұзын ертегілер — {plus}/{pro}.",
        "feature_quota_msg":   "Күндік хабарлама шегі ({n}) орындалды. Көбірек — {plus}/{pro}.",
        "feature_goals":       "Көбірек мақсат — {plus}/{pro}.",
        "feature_habits":      "Көбірек әдет — {plus}/{pro}.",
        "feature_reminders":   "Көбірек еске салғыш — {plus}/{pro}.",
        "cta": "Жаңарту → /premium",
    },

    # ——— KG (ky) ———
    "kg": {
        "title": "Жазылуу керек",
        "feature_story_voice": "Жомокту үн менен угуу {plus} жана {pro} пландарында жеткиликтүү.",
        "feature_eleven":      "ElevenLabs үндөрү {plus} жана {pro} пландарында.",
        "feature_bgm":         "Сүйлөөнүн үстүнө фон кошуу — {plus}/{pro}.",
        "feature_sleep_long":  "{min} мүнөттөн узун уктоо — {plus}/{pro}.",
        "feature_story_long":  "Орто жана узун жомоктор — {plus}/{pro}.",
        "feature_quota_msg":   "Күндүк билдирүү лимити ({n}) бүттү. Көбүрөөк — {plus}/{pro}.",
        "feature_goals":       "Көбүрөөк максат — {plus}/{pro}.",
        "feature_habits":      "Көбүрөөк адат — {plus}/{pro}.",
        "feature_reminders":   "Көбүрөөк эскертме — {plus}/{pro}.",
        "cta": "Жаңыртуу → /premium",
    },

    # ——— HY (hy) ———
    "hy": {
        "title": "Պահանջվում է բաժանորդագրություն",
        "feature_story_voice": "Հեքիաթների ձայնային ընթերցումը հասանելի է {plus} և {pro} փաթեթներում։",
        "feature_eleven":      "ElevenLabs-ի պրեմիում ձայները՝ {plus} և {pro}։",
        "feature_bgm":         "Ֆոնային ձայներ խոսքի վրա՝ {plus}/{pro}։",
        "feature_sleep_long":  "{min} րոպեից երկար քնի ձայներ՝ {plus}/{pro}։",
        "feature_story_long":  "Միջին/երկար հեքիաթներ՝ {plus}/{pro}։",
        "feature_quota_msg":   "Օրվա սահմանաչափը ({n}) սպառվել է։ Ավելի շատ՝ {plus}/{pro}։",
        "feature_goals":       "Ավելի շատ նպատակներ՝ {plus}/{pro}։",
        "feature_habits":      "Ավելի շատ սովորություններ՝ {plus}/{pro}։",
        "feature_reminders":   "Ավելի շատ հիշեցումներ՝ {plus}/{pro}։",
        "cta": "Թարմացնել → /premium",
    },

    # ——— KA (ka) ———
    "ka": {
        "title": "საჭიროა გამოწერა",
        "feature_story_voice": "ზღაპრების ხმოვანი გაშვება ხელმისაწვდომია {plus}-სა და {pro}-ზე.",
        "feature_eleven":      "ElevenLabs-ის ხმები — {plus}/{pro}.",
        "feature_bgm":         "საუბარზე ფონური ხმები — {plus}/{pro}.",
        "feature_sleep_long":  "{min} წთ-ზე მეტი ძილის ხმა — {plus}/{pro}.",
        "feature_story_long":  "საშუალო/გრძელი ზღაპრები — {plus}/{pro}.",
        "feature_quota_msg":   "დღიური ლიმიტი ({n}) ამოიწურა. მეტი — {plus}/{pro}.",
        "feature_goals":       "მეტი მიზანი — {plus}/{pro}.",
        "feature_habits":      "მეტი ჩვევა — {plus}/{pro}.",
        "feature_reminders":   "მეტი შეხსენება — {plus}/{pro}.",
        "cta": "განახლება → /premium",
    },

    # ——— CE (ce) ———
    "ce": {
        "title": "ДӀаяздар хир",
        "feature_story_voice": "Йоза агӀо (сказка) хьалха {plus}/{pro} чохь.",
        "feature_eleven":      "ElevenLabs хьалха {plus}/{pro}.",
        "feature_bgm":         "Фонов хьалха хӀокху хьалхарш дийна — {plus}/{pro}.",
        "feature_sleep_long":  "{min} дакъ йоцу тӀеххьара хьалха — {plus}/{pro}.",
        "feature_story_long":  "Юккха/дуккха агӀонаш — {plus}/{pro}.",
        "feature_quota_msg":   "Дийн лимит ({n}) дӀайо. ТӀехь кхечу — {plus}/{pro}.",
        "feature_goals":       "Кхечуьна максаташ — {plus}/{pro}.",
        "feature_habits":      "Кхечуьна гӀацаш — {plus}/{pro}.",
        "feature_reminders":   "Кхечуьна хьажоргаш — {plus}/{pro}.",
        "cta": "Upgrade → /premium",
    },
}

PLAN_LABELS = {
    "ru": {PLAN_FREE:"Бесплатно", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "uk": {PLAN_FREE:"Безкоштовно", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "md": {PLAN_FREE:"Gratuit", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "be": {PLAN_FREE:"Бясплатна", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "kk": {PLAN_FREE:"Тегін", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "kg": {PLAN_FREE:"Акысыз", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "hy": {PLAN_FREE:"Անվճար", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "ka": {PLAN_FREE:"უფასო", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "ce": {PLAN_FREE:"Биллийнан", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "en": {PLAN_FREE:"Free", PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
}
# ==== FEATURE MATRIX (булевы фичи) ====
# True / False: доступность фичи на плане
FEATURE_MATRIX = {
    PLAN_FREE: {
        "chat": True,
        "voice_tts": True,          # базовый gTTS
        "eleven_tts": False,        # ElevenLabs
        "voice_bgm_mix": False,     # фон поверх речи
        "story_cmd": True,          # /story доступна, но короткие и без авто-озвучки
        "story_voice": False,       # озвучка сказок
        "story_medium_long": False, # средние/длинные сказки
        "sleep_sounds": True,       # /sleep доступна
        "sleep_all_sounds": False,  # не все пресеты
        "voice_settings_advanced": False, # вкладки «движок», «фон» ограничены
    },
    PLAN_PLUS: {
        "chat": True,
        "voice_tts": True,
        "eleven_tts": True,
        "voice_bgm_mix": True,
        "story_cmd": True,
        "story_voice": True,
        "story_medium_long": True,   # средние разрешим
        "sleep_sounds": True,
        "sleep_all_sounds": True,    # все пресеты
        "voice_settings_advanced": True,
    },
    PLAN_PRO: {
        "chat": True,
        "voice_tts": True,
        "eleven_tts": True,
        "voice_bgm_mix": True,
        "story_cmd": True,
        "story_voice": True,
        "story_medium_long": True,   # и длинные тоже (ниже квотой)
        "sleep_sounds": True,
        "sleep_all_sounds": True,
        "voice_settings_advanced": True,
    },
}

# ==== QUOTAS (числовые лимиты по планам) ====
QUOTAS = {
    PLAN_FREE: {
        "daily_messages": 10,
        "goals_max": 3,
        "habits_max": 3,
        "reminders_max": 3,
        "sleep_max_minutes": 15,    # максимум длительность /sleep
        "story_max_paras": 5,       # «short»
    },
    PLAN_PLUS: {
        "daily_messages": 100,
        "goals_max": 20,
        "habits_max": 20,
        "reminders_max": 50,
        "sleep_max_minutes": 90,
        "story_max_paras": 8,       # medium
    },
    PLAN_PRO: {
        "daily_messages": 1000,
        "goals_max": 100,
        "habits_max": 100,
        "reminders_max": 200,
        "sleep_max_minutes": 240,
        "story_max_paras": 12,      # long
    },
}

SLEEP_UI_TEXTS = {
    "ru": {
        "title": "😴 Звуки для сна",
        "sound": "Звук: *{sound}*",
        "duration": "Длительность: *{min} мин*",
        "gain": "Громкость: *{db} dB*",
        "pick_sound": "Выберите звук:",
        "pick_duration": "Выберите длительность:",
        "pick_gain": "Выберите громкость:",
        "start": "▶️ Запустить",
        "stop": "⏹ Стоп",
        "started": "Запускаю звук *{sound}* на *{min} мин*… Приятного отдыха 🌙",
        "stopped": "Окей, остановил.",
        "err_ffmpeg": "Не найден ffmpeg — не могу подготовить аудио.",
        "err_missing": "Файл звука не найден. Проверь путь в BGM_PRESETS.",
    },
    "uk": {
        "title": "😴 Звуки для сну",
        "sound": "Звук: *{sound}*",
        "duration": "Тривалість: *{min} хв*",
        "gain": "Гучність: *{db} dB*",
        "pick_sound": "Оберіть звук:",
        "pick_duration": "Оберіть тривалість:",
        "pick_gain": "Оберіть гучність:",
        "start": "▶️ Запустити",
        "stop": "⏹ Стоп",
        "started": "Запускаю звук *{sound}* на *{min} хв*… Гарного відпочинку 🌙",
        "stopped": "Гаразд, зупинив.",
        "err_ffmpeg": "Не знайдено ffmpeg — не можу підготувати аудіо.",
        "err_missing": "Файл звуку не знайдено. Перевірте шлях у BGM_PRESETS.",
    },
    "md": {  # Romanian / Moldovan
        "title": "😴 Sunete pentru somn",
        "sound": "Sunet: *{sound}*",
        "duration": "Durată: *{min} min*",
        "gain": "Volum: *{db} dB*",
        "pick_sound": "Alege sunetul:",
        "pick_duration": "Alege durata:",
        "pick_gain": "Alege volumul:",
        "start": "▶️ Pornește",
        "stop": "⏹ Oprește",
        "started": "Pornesc *{sound}* pentru *{min} min*… Somn ușor 🌙",
        "stopped": "Oprit.",
        "err_ffmpeg": "ffmpeg nu a fost găsit — nu pot genera audio.",
        "err_missing": "Fișierul audio nu a fost găsit. Verifică calea în BGM_PRESETS.",
    },
    "be": {
        "title": "😴 Гукі для сну",
        "sound": "Гук: *{sound}*",
        "duration": "Працягласць: *{min} хв*",
        "gain": "Гучнасць: *{db} dB*",
        "pick_sound": "Абяры гук:",
        "pick_duration": "Абяры працягласць:",
        "pick_gain": "Абяры гучнасць:",
        "start": "▶️ Пуск",
        "stop": "⏹ Стоп",
        "started": "Уключаю *{sound}* на *{min} хв*… Прыемнага адпачынку 🌙",
        "stopped": "Спыніў.",
        "err_ffmpeg": "ffmpeg не знойдзены — не магу падрыхтаваць аўдыя.",
        "err_missing": "Файл гуку не знойдзены. Правер шлях у BGM_PRESETS.",
    },
    "kk": {  # Kazakh (Cyrillic)
        "title": "😴 Ұйқыға арналған дыбыстар",
        "sound": "Дыбыс: *{sound}*",
        "duration": "Ұзақтығы: *{min} мин*",
        "gain": "Дыбыс күші: *{db} dB*",
        "pick_sound": "Дыбысты таңдаңыз:",
        "pick_duration": "Ұзақтығын таңдаңыз:",
        "pick_gain": "Дыбыс күшін таңдаңыз:",
        "start": "▶️ Іске қосу",
        "stop": "⏹ Тоқтату",
        "started": "*{sound}* дыбысын *{min} мин* іске қосамын… Жақсы тынығыңыз 🌙",
        "stopped": "Тоқтатылды.",
        "err_ffmpeg": "ffmpeg табылмады — аудио дайындай алмаймын.",
        "err_missing": "Дыбыс файлы табылмады. BGM_PRESETS ішіндегі жолды тексеріңіз.",
    },
    "kg": {  # Kyrgyz
        "title": "😴 Уктоо үчүн үндөр",
        "sound": "Үн: *{sound}*",
        "duration": "Узактыгы: *{min} мин*",
        "gain": "Үндүн деңгээли: *{db} dB*",
        "pick_sound": "Үндү танда:",
        "pick_duration": "Узактыкты танда:",
        "pick_gain": "Деңгээлди танда:",
        "start": "▶️ Баштоо",
        "stop": "⏹ Токтотуу",
        "started": "*{sound}* үнүн *{min} мин* коём… Жакшы эс алыңыз 🌙",
        "stopped": "Токтоттум.",
        "err_ffmpeg": "ffmpeg табылган жок — аудио даярдай албайм.",
        "err_missing": "Үн файлы табылган жок. BGM_PRESETS жолун текшер.",
    },
    "hy": {  # Armenian
        "title": "😴 Քնի ձայներ",
        "sound": "Ձայն՝ *{sound}*",
        "duration": "Տևողություն՝ *{min} րոպե*",
        "gain": "Ձայնի մակարդակ՝ *{db} dB*",
        "pick_sound": "Ընտրեք ձայնը․",
        "pick_duration": "Ընտրեք տևողությունը․",
        "pick_gain": "Ընտրեք ձայնի մակարդակը․",
        "start": "▶️ Սկսել",
        "stop": "⏹ Կանգնեցնել",
        "started": "Միացնում եմ *{sound}*՝ *{min} րոպե*… Քաղցր երազներ 🌙",
        "stopped": "Կանգնեցվեց։",
        "err_ffmpeg": "ffmpeg չի գտնվել — չեմ կարող պատրաստել աուդիոն։",
        "err_missing": "Ձայնային ֆայլը չի գտնվել։ Ստուգեք ուղին BGM_PRESETS-ում։",
    },
    "ka": {  # Georgian
        "title": "😴 ძილის ხმები",
        "sound": "ხმა: *{sound}*",
        "duration": "ხანგრძლივობა: *{min} წთ*",
        "gain": "მოცულობა: *{db} dB*",
        "pick_sound": "აირჩიეთ ხმა:",
        "pick_duration": "აირჩიეთ ხანგრძლივობა:",
        "pick_gain": "აირჩიეთ მოცულობა:",
        "start": "▶️ დაწყება",
        "stop": "⏹ გაჩერება",
        "started": "ვრთავ *{sound}*-ს *{min} წუთით*… სასიამოვნო მოსვენებას 🌙",
        "stopped": "გაჩერებულია.",
        "err_ffmpeg": "ffmpeg ვერ მოიძებნა — აუდიოს მომზადება შეუძლებელია.",
        "err_missing": "ხმის ფაილი ვერ მოიძებნა. გადაამოწმეთ ბილიკი BGM_PRESETS-ში.",
    },
    "ce": {  # Chechen
        "title": "😴 Дийна хетам беарам",
        "sound": "Хьалха: *{sound}*",
        "duration": "Хатта: *{min} мин*",
        "gain": "Лела: *{db} dB*",
        "pick_sound": "Хьалха дахар:",
        "pick_duration": "Хатта дахар:",
        "pick_gain": "Лела дахар:",
        "start": "▶️ Даша",
        "stop": "⏹ Кхолла",
        "started": "*{sound}* *{min} мин* деш ву… Бетта хьоьлла 🌙",
        "stopped": "Кхоллаа.",
        "err_ffmpeg": "ffmpeg йоц — аудио тайар даккха дац.",
        "err_missing": "Хьалхан файлах йоц. BGM_PRESETS чу йол хьажа.",
    },
    "en": {
        "title": "😴 Sleep sounds",
        "sound": "Sound: *{sound}*",
        "duration": "Duration: *{min} min*",
        "gain": "Volume: *{db} dB*",
        "pick_sound": "Pick a sound:",
        "pick_duration": "Pick duration:",
        "pick_gain": "Pick volume:",
        "start": "▶️ Start",
        "stop": "⏹ Stop",
        "started": "Starting *{sound}* for *{min} min*… Sweet dreams 🌙",
        "stopped": "Stopped.",
        "err_ffmpeg": "ffmpeg not found — can't render audio.",
        "err_missing": "Sound file not found. Check BGM_PRESETS path.",
    },
}

# === VOICE SETTINGS UI: i18n (10 языков) ===
VOICE_UI_TEXTS = {
    "ru": {
        "title": "🎙 Настройки голоса",
        "engine": "Движок: *{engine}*",
        "voice": "Голос: *{voice}*",
        "speed": "Скорость: *{speed}x*",
        "voice_only": "Только голос: *{v}*",
        "auto_story": "Авто-озвучка сказок: *{v}*",
        "on": "вкл", "off": "выкл",
        "btn_engine": "⚙️ Движок",
        "btn_voice": "🗣 Голос",
        "btn_speed": "⏱ Скорость",
        "btn_beh": "🎛 Поведение",
        "btn_bg": "🎧 Фон",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Выбери голос:",
        "no_eleven_key": "⚠️ ElevenLabs ключ не найден — доступен только gTTS.",
        "bgm": "Фон: *{bg}* ({db} dB)",
    },
    "uk": {
        "title": "🎙 Налаштування голосу",
        "engine": "Движок: *{engine}*",
        "voice": "Голос: *{voice}*",
        "speed": "Швидкість: *{speed}x*",
        "voice_only": "Лише голос: *{v}*",
        "auto_story": "Авто-озвучення казок: *{v}*",
        "on": "увімк", "off": "вимк",
        "btn_engine": "⚙️ Движок",
        "btn_voice": "🗣 Голос",
        "btn_speed": "⏱ Швидкість",
        "btn_beh": "🎛 Поведінка",
        "btn_bg": "🎧 Фон",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Вибери голос:",
        "no_eleven_key": "⚠️ Ключ ElevenLabs не знайдено — доступний лише gTTS.",
        "bgm": "Фон: *{bg}* ({db} dB)",
    },
    "md": {  # Romanian/Moldovenească
        "title": "🎙 Setări voce",
        "engine": "Motor: *{engine}*",
        "voice": "Voce: *{voice}*",
        "speed": "Viteză: *{speed}x*",
        "voice_only": "Doar voce: *{v}*",
        "auto_story": "Voce automată pentru povești: *{v}*",
        "on": "pornit", "off": "oprit",
        "btn_engine": "⚙️ Motor",
        "btn_voice": "🗣 Voce",
        "btn_speed": "⏱ Viteză",
        "btn_beh": "🎛 Comportament",
        "btn_bg": "🎧 Ambianță",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Alege o voce:",
        "no_eleven_key": "⚠️ Cheia ElevenLabs nu este setată — disponibil doar gTTS.",
        "bgm": "Ambianță: *{bg}* ({db} dB)",
    },
    "be": {
        "title": "🎙 Налады голасу",
        "engine": "Рухавік: *{engine}*",
        "voice": "Голас: *{voice}*",
        "speed": "Хуткасць: *{speed}x*",
        "voice_only": "Толькі голас: *{v}*",
        "auto_story": "Аўта-агучванне казак: *{v}*",
        "on": "укл", "off": "выкл",
        "btn_engine": "⚙️ Рухавік",
        "btn_voice": "🗣 Голас",
        "btn_speed": "⏱ Хуткасць",
        "btn_beh": "🎛 Паводзіны",
        "btn_bg": "🎧 Фон",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Абяры голас:",
        "no_eleven_key": "⚠️ Ключ ElevenLabs не знойдзены — даступны толькі gTTS.",
        "bgm": "Фон: *{bg}* ({db} dB)",
    },
    "kk": {
        "title": "🎙 Дауыс баптаулары",
        "engine": "Қозғалтқыш: *{engine}*",
        "voice": "Дауыс: *{voice}*",
        "speed": "Жылдамдық: *{speed}x*",
        "voice_only": "Тек дауыс: *{v}*",
        "auto_story": "Ертегілерді авто-дауыстау: *{v}*",
        "on": "қосулы", "off": "өшірулі",
        "btn_engine": "⚙️ Қозғалтқыш",
        "btn_voice": "🗣 Дауыс",
        "btn_speed": "⏱ Жылдамдық",
        "btn_beh": "🎛 Мінез-құлық",
        "btn_bg": "🎧 Фон",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Дауысты таңда:",
        "no_eleven_key": "⚠️ ElevenLabs кілті орнатылмаған — тек gTTS қолжетімді.",
        "bgm": "Фон: *{bg}* ({db} dB)",
    },
    "kg": {
        "title": "🎙 Үн жөндөөлөрү",
        "engine": "Двигатель: *{engine}*",
        "voice": "Үн: *{voice}*",
        "speed": "Ылдамдык: *{speed}x*",
        "voice_only": "Жалаң үн: *{v}*",
        "auto_story": "Жомокторду авто-үн: *{v}*",
        "on": "күйүк", "off": "өчүк",
        "btn_engine": "⚙️ Двигатель",
        "btn_voice": "🗣 Үн",
        "btn_speed": "⏱ Ылдамдык",
        "btn_beh": "🎛 Жүрүм-турум",
        "btn_bg": "🎧 Фон",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Үн танда:",
        "no_eleven_key": "⚠️ ElevenLabs ачкычы коюлган эмес — gTTS гана жеткиликтүү.",
        "bgm": "Фон: *{bg}* ({db} dB)",
    },
    "hy": {
        "title": "🎙 Ձայնային կարգավորումներ",
        "engine": "Շարժիչ՝ *{engine}*",
        "voice": "Ձայն՝ *{voice}*",
        "speed": "Արագություն՝ *{speed}x*",
        "voice_only": "Միայն ձայն՝ *{v}*",
        "auto_story": "Ավտո-ձայն հեքիաթների համար՝ *{v}*",
        "on": "միացված", "off": "անջատված",
        "btn_engine": "⚙️ Շարժիչ",
        "btn_voice": "🗣 Ձայն",
        "btn_speed": "⏱ Արագություն",
        "btn_beh": "🎛 Վարքագիծ",
        "btn_bg": "🎧 Ֆոն",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Ընտրիր ձայնը․",
        "no_eleven_key": "⚠️ ElevenLabs բանալին կարգավորված չէ — հասանելի է միայն gTTS-ը.",
        "bgm": "Ֆոն՝ *{bg}* ({db} dB)",
    },
    "ka": {
        "title": "🎙 ხმის პარამეტრები",
        "engine": "ძრავი: *{engine}*",
        "voice": "ხმა: *{voice}*",
        "speed": "სიჩქარე: *{speed}x*",
        "voice_only": "მხოლოდ ხმა: *{v}*",
        "auto_story": "ზღაპრების ავტო-ხმოვანი: *{v}*",
        "on": " ჩართული", "off": " გამორთული",
        "btn_engine": "⚙️ ძრავი",
        "btn_voice": "🗣 ხმა",
        "btn_speed": "⏱ სიჩქარე",
        "btn_beh": "🎛 ქცევა",
        "btn_bg": "🎧 ფონური ხმა",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "აირჩიე ხმა:",
        "no_eleven_key": "⚠️ ElevenLabs გასაღები დაყენებული არაა — მხოლოდ gTTS ხელმისაწვდომია.",
        "bgm": "ფონი: *{bg}* ({db} dB)",
    },
    "ce": {
        "title": "🎙 Хьалха настройках",
        "engine": "Движок: *{engine}*",
        "voice": "Хьалха: *{voice}*",
        "speed": "Хийцам: *{speed}x*",
        "voice_only": "Только хьалха: *{v}*",
        "auto_story": "Къассаш авто-агӏоца: *{v}*",
        "on": "йух/вкл", "off": "йуъ/выкл",
        "btn_engine": "⚙️ Движок",
        "btn_voice": "🗣 Хьалха",
        "btn_speed": "⏱ Хийцам",
        "btn_beh": "🎛 Поведение",
        "btn_bg": "🎧 Фон",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Хьалха хӀоттор:",
        "no_eleven_key": "⚠️ ElevenLabs ключа ца йо — до гӀир gTTS.",
        "bgm": "Фон: *{bg}* ({db} dB)",
    },
    "en": {
        "title": "🎙 Voice settings",
        "engine": "Engine: *{engine}*",
        "voice": "Voice: *{voice}*",
        "speed": "Speed: *{speed}x*",
        "voice_only": "Voice only: *{v}*",
        "auto_story": "Auto voice for stories: *{v}*",
        "on": "on", "off": "off",
        "btn_engine": "⚙️ Engine",
        "btn_voice": "🗣 Voice",
        "btn_speed": "⏱ Speed",
        "btn_beh": "🎛 Behavior",
        "btn_bg": "🎧 Ambience",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Pick a voice:",
        "no_eleven_key": "⚠️ ElevenLabs key not set — only gTTS available.",
        "bgm": "Ambience: *{bg}* ({db} dB)",
    },
}

DEFAULT_ELEVEN_FEMALE = "21m00Tcm4TlvDq8ikWAM"
DEFAULT_ELEVEN_MALE = "JBFqnCBsd6RMkjVDRZzb" 
# === Пресеты голосов (10 языков; подставь voice_id где нужно) ===
VOICE_PRESETS = {
    "ru": [
        ("👩 Женский (Eleven)", "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Мужской (Eleven)", "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Женский (gTTS)",   "gTTS",   ""),
    ],
    "uk": [
        ("👩 Жіночий (Eleven)", "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Чоловічий (Eleven)","eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Жіночий (gTTS)",    "gTTS",   ""),
    ],
    "md": [
        ("👩 Feminin (Eleven)",  "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Masculin (Eleven)", "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Feminin (gTTS)",    "gTTS",   ""),
    ],
    "be": [
        ("👩 Жаночы (Eleven)",   "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Мужчынскі (Eleven)", "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Жаночы (gTTS)",      "gTTS",   ""),
    ],
    "kk": [
        ("👩 Әйел дауысы (Eleven)", "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Ер дауысы (Eleven)",   "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Әйел (gTTS)",          "gTTS",   ""),
    ],
    "kg": [
        ("👩 Аял үнү (Eleven)",   "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Эркек үнү (Eleven)", "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Аял (gTTS)",         "gTTS",   ""),
    ],
    "hy": [
        ("👩 Կանացի (Eleven)",   "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Տղամարդկ. (Eleven)","eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Կանացի (gTTS)",     "gTTS",   ""),
    ],
    "ka": [
        ("👩 ქალი (Eleven)",      "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 კაცი (Eleven)",       "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 ქალი (gTTS)",         "gTTS",   ""),
    ],
    "ce": [
        ("👩 Йоьцуш (Eleven)",     "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Дика (Eleven)",       "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Йоьцуш (gTTS)",        "gTTS",   ""),
    ],
    "en": [
        ("👩 Female (Eleven)",     "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Male (Eleven)",       "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Female (gTTS)",       "gTTS",   ""),
    ],
}

# --- Фоновые лупы (опционально) ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# какие варианты громкости показывать в меню фона, в децибелах
BGM_GAIN_CHOICES = [-25, -20, -15, -10, -5, 0, 5]

BGM_PRESETS = {
    "off":   {"label": "🚫 Off",        "path": None},
    "rain":  {"label": "🌧 Rain",       "path": os.path.join(BASE_DIR, "assets", "bgm", "rain_loop.mp3")},
    "fire":  {"label": "🔥 Fireplace",  "path": os.path.join(BASE_DIR, "assets", "bgm", "fireplace_loop.mp3")},
    "ocean": {"label": "🌊 Ocean",      "path": os.path.join(BASE_DIR, "assets", "bgm", "ocean_loop.mp3")},
    "lofi":  {"label": "🎵 Lo-fi",      "path": os.path.join(BASE_DIR, "assets", "bgm", "lofi_loop.mp3")},
}

STORY_INTENT = {
    "ru": ["сказку","сказка","рассказ","байку","историю на ночь","колыбельную",
           "расскажи сказку","сочини сказку","придумай сказку",
           "курочка ряба","колобок","красная шапочка"],
    "uk": ["казку","казка","оповідання","історію на ніч","колискову",
           "розкажи казку","склади казку"],
    "md": ["poveste","povești","basm","poveste de seară","de culcare","spune o poveste"],
    "be": ["казку","казка","апавяданне","на ноч","калыханка"],
    "kk": ["ертегі","әңгіме","ұйқы алдында","ертегі айт"],
    "kg": ["жомок","аңгеме","уктоочу окуя","жомок айтып бер"],
    "hy": ["հեքիաթ","պատմություն","քնելուց առաջ","ասա հեքիաթ"],
    "ka": ["ზღაპარი","ისტორია","დაძინებამდე","მითხარი ზღაპარი"],
    "ce": ["хьикьа","истори","хьалхар кхета","хьикьа йоцу"],
    "en": ["story","bedtime story","bedtime","fairy tale","tale","tell me a story",
           "a bedtime tale"],
}
# ——— Stories i18n (10 языков) ———
STORY_TEXTS = {
    "ru": {"title":"📖 Сказка от Миндры",
           "usage":"Использование: `/story тема | имя=Мила | длина=короткая|средняя|длинная | голос=on`\nНапр.: `/story космос имя=Мила голос=on`",
           "making":"✨ Придумываю историю…",
           "ready":"Готово! Хочешь ещё одну?",
           "btn_more":"🎲 Ещё одну", "btn_voice":"🔊 Голосом", "btn_close":"✖️ Закрыть",
           "suggest":"Хочешь, придумаю сказку на эту тему и расскажу?",
           "btn_ok": "✅ Да",
           "btn_no": "❌ Нет",
          },
    "uk": {"title":"📖 Казка від Міндри",
           "usage":"Використання: `/story тема | ім'я=Міла | довжина=коротка|середня|довга | голос=on`",
           "making":"✨ Придумую історію…","ready":"Готово! Ще одну?",
           "btn_more":"🎲 Ще одну","btn_voice":"🔊 Голосом","btn_close":"✖️ Закрити",
           "suggest":"Хочеш, я складу казку на цю тему і розповім?",
           "btn_ok": "✅ Так",
           "btn_no": "❌ Ні",
          },
    "md": {"title":"📖 Poveste de la Mindra",
           "usage":"Folosește: `/story tema | nume=Mila | lungime=scurtă|medie|lungă | voce=on`",
           "making":"✨ Creez povestea…","ready":"Gata! Încă una?",
           "btn_more":"🎲 Încă una","btn_voice":"🔊 Voce","btn_close":"✖️ Închide",
           "suggest":"Vrei să creez o poveste pe această temă și să ți-o citesc?",
           "btn_ok": "✅ OK",
           "btn_no": "❌ Nu",
          },
    "be": {"title":"📖 Казка ад Міндры",
           "usage":"Выкарыстанне: `/story тэма | імя=Міла | даўжыня=кароткая|сярэдняя|доўгая | голас=on`",
           "making":"✨ Прыдумваю гісторыю…","ready":"Гатова! Яшчэ?",
           "btn_more":"🎲 Яшчэ","btn_voice":"🔊 Голасам","btn_close":"✖️ Закрыць",
           "suggest":"Хочаш, прыдумаю казку на гэтую тэму і прачитаю?",
           "btn_ok": "✅ Так",
           "btn_no": "❌ Не",
          },
    "kk": {"title":"📖 Mindra ертегісі",
           "usage":"Қолдану: `/story тақырып | есім=Мила | ұзындық=қысқа|орта|ұзын | дауыс=on`",
           "making":"✨ Ертегі құрастырып жатырмын…","ready":"Дайын! Тағы керек пе?",
           "btn_more":"🎲 Тағы","btn_voice":"🔊 Дауыспен","btn_close":"✖️ Жабу",
           "suggest":"Осы тақырыпта ертегі құрастырып, дауыспен айтып берейін бе?",
           "btn_ok": "✅ Иә",
           "btn_no": "❌ Жоқ",
          },
    "kg": {"title":"📖 Миндранын жомогу",
           "usage":"Колдонуу: `/story тема | ысым=Мила | узундук=кыска|орто|узун | үн=on`",
           "making":"✨ Жомок ойлоп табам…","ready":"Даяр! Дагыбы?",
           "btn_more":"🎲 Дагы","btn_voice":"🔊 Үн менен","btn_close":"✖️ Жабуу",
           "suggest":"Ушул тема боюнча жомок түзүп, окуп берейинби?",
           "btn_ok": "✅ Ооба",
           "btn_no": "❌ Жок",
          },
    "hy": {"title":"📖 Մինդրայի հեքիաթ",
           "usage":"Օգտ․՝ `/story թեմա | անուն=Միլա | երկար=կարճ|միջին|երկար | ձայն=on`",
           "making":"✨ Ստեղծում եմ պատմություն…","ready":"Պատրաստ է․ ևս մեկ՞",
           "btn_more":"🎲 Եվս մեկը","btn_voice":"🔊 Ձայնով","btn_close":"✖️ Փակել",
           "suggest":"Ցանկանու՞մ ես՝ այս թեմայով հեքիաթ հորինեմ ու կարդամ։",
           "btn_ok": "✅ Այո",
           "btn_no": "❌ Ոչ",
          },
    "ka": {"title":"📖 მინდრას ზღაპარი",
           "usage":"გამოყენება: `/story თემა | სახელი=მილა | სიგრძე=მოკლე|საშუალო|გრძელი | ხმა=on`",
           "making":"✨ ისტორიას ვქმნი…","ready":"მზადაა! კიდევ ერთი?",
           "btn_more":"🎲 კიდევ","btn_voice":"🔊 ხმოვანი","btn_close":"✖️ დახურვა",
           "suggest":"გინდა ამ თემაზე ზღაპარი მოვიფიქრო და გითხრა?",
           "btn_ok": "✅ დიახ",
           "btn_no": "❌ არა",
          },
    "ce": {"title":"📖 Миндра легенда",
           "usage":"Лело: `/story тема | цӀе=Мила | кӀехк=кхир|орта|дулг | хӀалха=on`",
           "making":"✨ Историй кхета…","ready":"Доза! Керла я?",
           "btn_more":"🎲 Керла","btn_voice":"🔊 ХӀалха","btn_close":"✖️ ДӀайхьа",
           "suggest":"Хьона тема юкъ йиш йолу легенда хийца?",
           "btn_ok": "✅ ХӀа",
           "btn_no": "❌ Йоъ",
          },
    "en": {"title":"📖 Mindra’s bedtime story",
           "usage":"Usage: `/story topic | name=Mila | length=short|medium|long | voice=on`",
           "making":"✨ Spinning the tale…","ready":"Done! Another one?",
           "btn_more":"🎲 Another","btn_voice":"🔊 Voice","btn_close":"✖️ Close",
           "suggest":"Want me to craft a story about this and read it to you?",
           "btn_ok": "✅ OK",
           "btn_no": "❌ No",
          },
}

VOICE_MODE_TEXTS = {
    "ru":{"on":"🔊 Голосовой режим включён. Я буду присылать ответы голосом.",
          "off":"🔇 Голосовой режим выключен.",
          "help":"Использование: /voice_mode on|off",
          "err":"⚠️ Укажи on|off. Пример: /voice_mode on"},
    "uk":{"on":"🔊 Голосовий режим увімкнено. Відповідатиму голосом.",
          "off":"🔇 Голосовий режим вимкнено.",
          "help":"Використання: /voice_mode on|off",
          "err":"⚠️ Вкажи on|off. Приклад: /voice_mode on"},
    "md":{"on":"🔊 Modul vocal activat. Voi răspunde cu voce.",
          "off":"🔇 Modul vocal dezactivat.",
          "help":"Utilizare: /voice_mode on|off",
          "err":"⚠️ Specifică on|off. Exemplu: /voice_mode on"},
    "be":{"on":"🔊 Галасавы рэжым уключаны. Буду адказваць голасам.",
          "off":"🔇 Галасавы рэжым выключаны.",
          "help":"Выкарыстанне: /voice_mode on|off",
          "err":"⚠️ Пакажы on|off. Прыклад: /voice_mode on"},
    "kk":{"on":"🔊 Дыбыстық режим қосылды. Дыбыспен жауап беремін.",
          "off":"🔇 Дыбыстық режим өшірілді.",
          "help":"Қолдану: /voice_mode on|off",
          "err":"⚠️ on|off көрсет. Мысал: /voice_mode on"},
    "kg":{"on":"🔊 Үн режими күйдү. Үн менен жооп берем.",
          "off":"🔇 Үн режими өчтү.",
          "help":"Колдонуу: /voice_mode on|off",
          "err":"⚠️ on|off деп жаз. Мисал: /voice_mode on"},
    "hy":{"on":"🔊 Ձայնային ռեժիմը միացված է։ Կպատասխանեմ ձայնայինով։",
          "off":"🔇 Ձայնային ռեժիմը անջատված է։",
          "help":"Օգտագործում՝ /voice_mode on|off",
          "err":"⚠️ Նշիր on|off. Օր․ /voice_mode on"},
    "ka":{"on":"🔊 ხმის რეჟიმი ჩართულია. ვუპასუხებ ხმოვანით.",
          "off":"🔇 ხმის რეჟიმი გამორთულია.",
          "help":"გამოყენება: /voice_mode on|off",
          "err":"⚠️ მიუთითე on|off. მაგალითი: /voice_mode on"},
    "ce":{"on":"🔊 Хьалха режим хьалба. Со хӀинца дIаяздарна.",
          "off":"🔇 Хьалха режим йуъ хьалха.",
          "help":"Лело: /voice_mode on|off",
          "err":"⚠️ on|off хаза. Масал: /voice_mode on"},
    "en":{"on":"🔊 Voice mode is ON. I’ll reply with voice.",
          "off":"🔇 Voice mode is OFF.",
          "help":"Usage: /voice_mode on|off",
          "err":"⚠️ Specify on|off. Example: /voice_mode on"},
}

CHALLENGE_BANK = {
    "ru": [
        "Сделай зарядку 5 дней из 7",
        "Ложись спать до 23:00 три раза на неделе",
        "30 минут чтения 4 раза за неделю",
        "Без сахара 3 дня подряд",
        "Прогулка 7 000 шагов 5 раз",
    ],
    "uk": ["Тренування 5 днів з 7","Сон до 23:00 тричі","Читання 30 хв ×4","Без цукру 3 дні","7000 кроків ×5"],
    "md": ["Exerciții 5/7","Somn până la 23:00 ×3","Citit 30 min ×4","Fără zahăr 3 zile","7000 pași ×5"],
    "be": ["Зарадка 5/7","Сон да 23:00 ×3","Чытанне 30 хв ×4","Без цукру 3 дні","7000 крокаў ×5"],
    "kk": ["Жаттығу 5/7","23:00 дейін ұйқы ×3","30 мин оқу ×4","Қантсыз 3 күн","7000 қадам ×5"],
    "kg": ["Машыгуу 5/7","23:00 чейин уйку ×3","30 мүн окуу ×4","Сахарсыз 3 күн","7000 кадам ×5"],
    "hy": ["Մարզում 5/7","Ունենալ քուն մինչև 23:00 ×3","Կարդալ 30 ր ×4","Շաքար չօգտ. 3 օր","7000 քայլ ×5"],
    "ka": ["ვარჯიში 5/7","ძილი 23:00-მდე ×3","კითხვა 30 წთ ×4","შაქრის გარეშე 3 დღე","7000 ნაბიჯი ×5"],
    "ce": ["Ваяж 5/7","До 23:00 дика хьалха ×3","Кхетар 30 м ×4","Цукр йоцуш 3 дийн","7000 гӀайр ×5"],
    "en": ["Workout 5/7","Sleep by 23:00 ×3","Read 30m ×4","No sugar 3 days","7k steps ×5"],
}

P_TEXTS = {
    "ru": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Безлимитные напоминания, отчёты, челленджи и эксклюзивный режим.\nОформи Mindra+ и разблокируй всё 💜",
        "btn_get": "Получить Mindra+",
        "btn_code": "Ввести код",
        "days_left": "💎 Твой Mindra+: осталось дней — *{days}*",
        "no_plus": "У тебя пока нет Mindra+. Доступны бесплатные функции 💜",
        "report_title": "📊 Твой отчёт за 7 дней",
        "report_goals": "🎯 Завершено целей: *{n}*",
        "report_habits": "🌱 Отмечено привычек: *{n}*",
        "report_rems": "🔔 Сработало напоминаний: *{n}*",
        "report_streak": "🔥 Активные дни: *{n}*",
        "challenge_title": "🏆 Еженедельный челлендж",
        "challenge_cta": "Твой вызов на неделю:\n\n“{text}”",
        "btn_done": "✅ Готово",
        "btn_new": "🎲 Новый челлендж",
        "challenge_done": "👏 Отлично! Челлендж отмечен выполненным.",
        "mode_title": "🦄 Эксклюзивный режим активирован",
        "mode_set": "Теперь я буду отвечать как персональный коуч Mindra+ 💜",
        "stats_title": "📈 Расширенная статистика",
        "stats_goals_done": "🎯 Целей завершено всего: *{n}*",
        "stats_habit_days": "🌱 Дней с привычками: *{n}*",
        "stats_active_days": "🔥 Активные дни за 30д: *{n}*",
    },
    "uk": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Необмежені нагадування, звіти, челенджі та ексклюзивний режим.\nОформи Mindra+ і відкрий усе 💜",
        "btn_get": "Отримати Mindra+",
        "btn_code": "Ввести код",
        "days_left": "💎 Твій Mindra+: лишилось днів — *{days}*",
        "no_plus": "У тебе поки немає Mindra+. Доступні безкоштовні функції 💜",
        "report_title": "📊 Твій звіт за 7 днів",
        "report_goals": "🎯 Виконано цілей: *{n}*",
        "report_habits": "🌱 Відмічено звичок: *{n}*",
        "report_rems": "🔔 Спрацювало нагадувань: *{n}*",
        "report_streak": "🔥 Активні дні: *{n}*",
        "challenge_title": "🏆 Щотижневий челендж",
        "challenge_cta": "Твій виклик на тиждень:\n\n“{text}”",
        "btn_done": "✅ Виконано",
        "btn_new": "🎲 Новий челендж",
        "challenge_done": "👏 Клас! Челендж позначено виконаним.",
        "mode_title": "🦄 Ексклюзивний режим активовано",
        "mode_set": "Тепер я відповідатиму як персональний коуч Mindra+ 💜",
        "stats_title": "📈 Розширена статистика",
        "stats_goals_done": "🎯 Цілей виконано всього: *{n}*",
        "stats_habit_days": "🌱 Днів зі звичками: *{n}*",
        "stats_active_days": "🔥 Активні дні за 30д: *{n}*",
    },
    "md": {  # ro
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Mementouri nelimitate, rapoarte, provocări și mod exclusiv.\nActivează Mindra+ 💜",
        "btn_get": "Obține Mindra+",
        "btn_code": "Introduce cod",
        "days_left": "💎 Mindra+ tău: zile rămase — *{days}*",
        "no_plus": "Încă nu ai Mindra+. Funcțiile gratuite sunt disponibile 💜",
        "report_title": "📊 Raportul tău (7 zile)",
        "report_goals": "🎯 Obiective finalizate: *{n}*",
        "report_habits": "🌱 Obiceiuri marcate: *{n}*",
        "report_rems": "🔔 Mementouri declanșate: *{n}*",
        "report_streak": "🔥 Zile active: *{n}*",
        "challenge_title": "🏆 Provocare săptămânală",
        "challenge_cta": "Provocarea ta:\n\n“{text}”",
        "btn_done": "✅ Gata",
        "btn_new": "🎲 Nouă provocare",
        "challenge_done": "👏 Super! Marcata ca finalizată.",
        "mode_title": "🦄 Mod exclusiv activat",
        "mode_set": "De acum voi răspunde ca antrenorul tău Mindra+ 💜",
        "stats_title": "📈 Statistică extinsă",
        "stats_goals_done": "🎯 Obiective încheiate total: *{n}*",
        "stats_habit_days": "🌱 Zile cu obiceiuri: *{n}*",
        "stats_active_days": "🔥 Zile active (30z): *{n}*",
    },
    "be": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Неабмежаваныя напаміны, справаздачы, чэленджы і эксклюзіўны рэжым.\nАформі Mindra+ 💜",
        "btn_get": "Атрымаць Mindra+",
        "btn_code": "Увесці код",
        "days_left": "💎 Твой Mindra+: засталося дзён — *{days}*",
        "no_plus": "У цябе пакуль няма Mindra+. Даступныя бясплатныя функцыі 💜",
        "report_title": "📊 Твой справаздача (7 дзён)",
        "report_goals": "🎯 Выканана мэт: *{n}*",
        "report_habits": "🌱 Адзначана звычак: *{n}*",
        "report_rems": "🔔 Спрацавала напамінаў: *{n}*",
        "report_streak": "🔥 Актыўныя дні: *{n}*",
        "challenge_title": "🏆 Штотыднёвы чэлендж",
        "challenge_cta": "Твой выклік на тыдзень:\n\n“{text}”",
        "btn_done": "✅ Гатова",
        "btn_new": "🎲 Новы чэлендж",
        "challenge_done": "👏 Цудоўна! Адзначана выкананым.",
        "mode_title": "🦄 Эксклюзіўны рэжым уключаны",
        "mode_set": "Цяпер я адказваю як тваё коуч-Mindra+ 💜",
        "stats_title": "📈 Пашыраная статыстыка",
        "stats_goals_done": "🎯 Мэт завершана ўсяго: *{n}*",
        "stats_habit_days": "🌱 Дзён са звычкамі: *{n}*",
        "stats_active_days": "🔥 Актыўныя дні за 30д: *{n}*",
    },
    "kk": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Шексіз еске салулар, есептер, челленджтер және эксклюзивті режим.\nMindra+ қосыңыз 💜",
        "btn_get": "Mindra+ алу",
        "btn_code": "Код енгізу",
        "days_left": "💎 Mindra+: қалған күн — *{days}*",
        "no_plus": "Әзірше Mindra+ жоқ. Тегін мүмкіндіктер бар 💜",
        "report_title": "📊 7 күндік есеп",
        "report_goals": "🎯 Аяқталған мақсаттар: *{n}*",
        "report_habits": "🌱 Белгіленген әдеттер: *{n}*",
        "report_rems": "🔔 Іске асқан еске салулар: *{n}*",
        "report_streak": "🔥 Белсенді күндер: *{n}*",
        "challenge_title": "🏆 Апталық челлендж",
        "challenge_cta": "Апталық тапсырмаң:\n\n“{text}”",
        "btn_done": "✅ Дайын",
        "btn_new": "🎲 Жаңа челлендж",
        "challenge_done": "👏 Керемет! Аяқталған ретінде белгіленді.",
        "mode_title": "🦄 Эксклюзивті режим қосылды",
        "mode_set": "Енді мен Mindra+ коучы ретінде жауап беремін 💜",
        "stats_title": "📈 Кеңейтілген статистика",
        "stats_goals_done": "🎯 Барлығы аяқталған мақсаттар: *{n}*",
        "stats_habit_days": "🌱 Әдеттер белгіленген күндер: *{n}*",
        "stats_active_days": "🔥 Соңғы 30 күн белсенді: *{n}*",
    },
    "kg": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Чексиз эскертмелер, отчеттор, челендждер жана эксклюзив режим.\nMindra+ кошуңуз 💜",
        "btn_get": "Mindra+ алуу",
        "btn_code": "Код киргизүү",
        "days_left": "💎 Mindra+: калган күн — *{days}*",
        "no_plus": "Азырынча Mindra+ жок. Акысыз функциялар бар 💜",
        "report_title": "📊 7 күндүк отчет",
        "report_goals": "🎯 Бүткөн максаттар: *{n}*",
        "report_habits": "🌱 Белгиленген адаттар: *{n}*",
        "report_rems": "🔔 Иштеген эскертмелер: *{n}*",
        "report_streak": "🔥 Активдүү күндөр: *{n}*",
        "challenge_title": "🏆 Апталык челендж",
        "challenge_cta": "Сенин чакырыгың:\n\n“{text}”",
        "btn_done": "✅ Бүткөн",
        "btn_new": "🎲 Жаңы челендж",
        "challenge_done": "👏 Сонун! Бүттү деп белгиленди.",
        "mode_title": "🦄 Эксклюзив режим кошулду",
        "mode_set": "Теперь я коуч Mindra+ катары жооп берем 💜",
        "stats_title": "📈 Кеңейтилген статистика",
        "stats_goals_done": "🎯 Бардыгы болуп бүткөн максаттар: *{n}*",
        "stats_habit_days": "🌱 Адат белгиленген күндөр: *{n}*",
        "stats_active_days": "🔥 Акыркы 30 күн активдүү: *{n}*",
    },
    "hy": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Անսահման հիշեցումներ, հաշվետվություններ, չելենջներ և բացառիկ ռեժիմ։\nՄիացրու Mindra+ 💜",
        "btn_get": "Ստանալ Mindra+",
        "btn_code": "Մուտքագրել կոդ",
        "days_left": "💎 Քո Mindra+: մնացած օրեր — *{days}*",
        "no_plus": "Դեռ չունես Mindra+․ հասանելի են անվճար ֆունկցիաներ 💜",
        "report_title": "📊 Քո հաշվետվությունը (7 օր)",
        "report_goals": "🎯 Ամփոփված նպատակներ՝ *{n}*",
        "report_habits": "🌱 Նշված սովորություններ՝ *{n}*",
        "report_rems": "🔔 Ակտիվացած հիշեցումներ՝ *{n}*",
        "report_streak": "🔥 Ակտիվ օրեր՝ *{n}*",
        "challenge_title": "🏆 Շաբաթական չելենջ",
        "challenge_cta": "Քо շաբաթվա առաջադրանքը՝\n\n“{text}”",
        "btn_done": "✅ Կատարված է",
        "btn_new": "🎲 Նոր չելենջ",
        "challenge_done": "👏 Հիանալի է․ նշվեց կատարված։",
        "mode_title": "🦄 Բացառիկ ռեժիմը միացված է",
        "mode_set": "Այժմ պատասխանելու եմ որպես Mindra+ մարզիչ 💜",
        "stats_title": "📈 Ընդլայնված վիճակագրություն",
        "stats_goals_done": "🎯 Ընդհանուր ավարտված նպատակներ՝ *{n}*",
        "stats_habit_days": "🌱 Սովորություններով օրեր՝ *{n}*",
        "stats_active_days": "🔥 Վերջին 30 օրում ակտիվ՝ *{n}*",
    },
    "ka": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "ულიმიტო შეხსენებები, ანგარიშები, ჩელენჯები და ექსკლუზიური რეჟიმი.\nგააქტიურე Mindra+ 💜",
        "btn_get": "Mindra+ შეძენა",
        "btn_code": "კოდის შეყვანა",
        "days_left": "💎 შენი Mindra+: დარჩენილი დღეები — *{days}*",
        "no_plus": "ჯერ Mindra+ არ გაქვს. ხელმისაწვდომია უფასო ფუნქციები 💜",
        "report_title": "📊 7 დღიანი ანგარიში",
        "report_goals": "🎯 დასრულებული მიზნები: *{n}*",
        "report_habits": "🌱 მონიშნული ჩვევები: *{n}*",
        "report_rems": "🔔 ამოქმედებული შეხსენებები: *{n}*",
        "report_streak": "🔥 აქტიური დღეები: *{n}*",
        "challenge_title": "🏆 ყოველკვირეული ჩელენჯი",
        "challenge_cta": "შენი კვირის გამოწვევა:\n\n“{text}”",
        "btn_done": "✅ დასრულდა",
        "btn_new": "🎲 ახალი ჩელენჯი",
        "challenge_done": "👏 შესანიშნავია! მონიშნულია დასრულებულად.",
        "mode_title": "🦄 ექსკლუზიური რეჟიმი ჩართულია",
        "mode_set": "ახლა ვიქნები შენი Mindra+ მწვრთნელი 💜",
        "stats_title": "📈 გაფართოებული სტატისტიკა",
        "stats_goals_done": "🎯 სულ დასრულებული მიზნები: *{n}*",
        "stats_habit_days": "🌱 ჩვევების დღეები: *{n}*",
        "stats_active_days": "🔥 ბოლო 30 დღეში აქტიური: *{n}*",
    },
    "ce": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Неькъ да цӀе напоминани, отчет, челендж да эксклюзив режим.\nMindra+ хийцар 💜",
        "btn_get": "Mindra+ хийца",
        "btn_code": "Код хьажа",
        "days_left": "💎 Mindra+: дийна далла — *{days}*",
        "no_plus": "Миндра+ йоцуш. Кхечу функцаш дош 💜",
        "report_title": "📊 7 кӀирна отчет",
        "report_goals": "🎯 ХӀаттар кхоллар: *{n}*",
        "report_habits": "🌱 Дийцар хийна: *{n}*",
        "report_rems": "🔔 Напоминани цуьнан: *{n}*",
        "report_streak": "🔥 Активан дийн: *{n}*",
        "challenge_title": "🏆 Нан коллекха челендж",
        "challenge_cta": "Хьуна дехар:\n\n“{text}”",
        "btn_done": "✅ ДӀайолла",
        "btn_new": "🎲 Керла челендж",
        "challenge_done": "👏 Кор хӀо! Кхоллар бен.",
        "mode_title": "🦄 Эксклюзив режим хьалба",
        "mode_set": "Хьо Mindra+ коучаш йина доза дац 💜",
        "stats_title": "📈 Расш статистика",
        "stats_goals_done": "🎯 ХӀаттар кхоллар масала: *{n}*",
        "stats_habit_days": "🌱 Дийцар дийн: *{n}*",
        "stats_active_days": "🔥 30 кӀирна активан дийн: *{n}*",
    },
    "en": {
        "upsell_title": "💎 Mindra+",
        "upsell_body":  "Unlimited reminders, reports, challenges and an exclusive mode.\nGet Mindra+ and unlock everything 💜",
        "btn_get": "Get Mindra+",
        "btn_code": "Enter code",
        "days_left": "💎 Your Mindra+: days left — *{days}*",
        "no_plus": "You don’t have Mindra+ yet. Free features are available 💜",
        "report_title": "📊 Your 7-day report",
        "report_goals": "🎯 Goals completed: *{n}*",
        "report_habits": "🌱 Habits tracked: *{n}*",
        "report_rems": "🔔 Reminders fired: *{n}*",
        "report_streak": "🔥 Active days: *{n}*",
        "challenge_title": "🏆 Weekly challenge",
        "challenge_cta": "Your challenge this week:\n\n“{text}”",
        "btn_done": "✅ Done",
        "btn_new": "🎲 New challenge",
        "challenge_done": "👏 Nice! Challenge marked as done.",
        "mode_title": "🦄 Exclusive mode on",
        "mode_set": "I’ll answer as your Mindra+ coach 💜",
        "stats_title": "📈 Extended statistics",
        "stats_goals_done": "🎯 Goals completed total: *{n}*",
        "stats_habit_days": "🌱 Days with habits: *{n}*",
        "stats_active_days": "🔥 Active days in 30d: *{n}*",
    },
}

GH_TEXTS = {
    "ru": {
        "menu_title": "🎯 Цели и 🌱 Привычки",
        "btn_add_goal":   "🎯 Поставить цель",
        "btn_list_goals": "📋 Мои цели",
        "btn_add_habit":  "🌱 Добавить привычку",
        "btn_list_habits":"📊 Мои привычки",
        "back": "◀️ Меню",
        "goals_title": "🎯 Твои цели:",
        "habits_title": "🌱 Твои привычки:",
        "goals_empty": "Пока нет целей. Нажми «🎯 Поставить цель».",
        "habits_empty": "Пока нет привычек. Нажми «🌱 Добавить привычку».",
        "goal_usage": "Чтобы добавить цель, напиши: `/goal Текст цели`\nНапр.: `/goal Пробежать 5 км`",
        "habit_usage": "Чтобы добавить привычку, напиши: `/habit Название привычки`\nНапр.: `/habit Пить воду`",
    },
    "uk": {
        "menu_title": "🎯 Цілі та 🌱 Звички",
        "btn_add_goal":   "🎯 Додати ціль",
        "btn_list_goals": "📋 Мої цілі",
        "btn_add_habit":  "🌱 Додати звичку",
        "btn_list_habits":"📊 Мої звички",
        "back": "◀️ Меню",
        "goals_title": "🎯 Твої цілі:",
        "habits_title": "🌱 Твої звички:",
        "goals_empty": "Поки немає цілей. Натисни «🎯 Додати ціль».",
        "habits_empty": "Поки немає звичок. Натисни «🌱 Додати звичку».",
        "goal_usage": "Щоб додати ціль, напиши: `/goal Текст цілі`\nНапр.: `/goal Пробігти 5 км`",
        "habit_usage": "Щоб додати звичку, напиши: `/habit Назва звички`\nНапр.: `/habit Пити воду`",
    },
    "md": {
        "menu_title": "🎯 Obiective și 🌱 Obiceiuri",
        "btn_add_goal":   "🎯 Setează obiectiv",
        "btn_list_goals": "📋 Obiectivele mele",
        "btn_add_habit":  "🌱 Adaugă obicei",
        "btn_list_habits":"📊 Obiceiurile mele",
        "back": "◀️ Meniu",
        "goals_title": "🎯 Obiectivele tale:",
        "habits_title": "🌱 Obiceiurile tale:",
        "goals_empty": "Deocamdată nu ai obiective. Apasă „🎯 Setează obiectiv”.",
        "habits_empty": "Deocamdată nu ai obiceiuri. Apasă „🌱 Adaugă obicei”.",
        "goal_usage": "Pentru a adăuga un obiectiv, scrie: `/goal Text obiectiv`\nEx.: `/goal Alerga 5 km`",
        "habit_usage": "Pentru a adăuga un obicei, scrie: `/habit Nume obicei`\nEx.: `/habit Apă`",
    },
    "be": {
        "menu_title": "🎯 Мэты і 🌱 Звычкі",
        "btn_add_goal":   "🎯 Паставіць мэту",
        "btn_list_goals": "📋 Мае мэты",
        "btn_add_habit":  "🌱 Дадаць звычку",
        "btn_list_habits":"📊 Мае звычкі",
        "back": "◀️ Меню",
        "goals_title": "🎯 Твае мэты:",
        "habits_title": "🌱 Твае звычкі:",
        "goals_empty": "Пакуль няма мэт. Націсні «🎯 Паставіць мэту».",
        "habits_empty": "Пакуль няма звычак. Націсні «🌱 Дадаць звычку».",
        "goal_usage": "Каб дадаць мэту, напішы: `/goal Тэкст мэты`\nНапр.: `/goal Прабегчы 5 км`",
        "habit_usage": "Каб дадаць звычку, напішы: `/habit Назва звычкі`\nНапр.: `/habit Піць ваду`",
    },
    "kk": {
        "menu_title": "🎯 Мақсаттар мен 🌱 Әдеттер",
        "btn_add_goal":   "🎯 Мақсат қою",
        "btn_list_goals": "📋 Менің мақсаттарым",
        "btn_add_habit":  "🌱 Әдет қосу",
        "btn_list_habits":"📊 Менің әдеттерім",
        "back": "◀️ Мәзір",
        "goals_title": "🎯 Сіздің мақсаттарыңыз:",
        "habits_title": "🌱 Сіздің әдеттеріңіз:",
        "goals_empty": "Әзірге мақсаттар жоқ. «🎯 Мақсат қою» батырмасын басыңыз.",
        "habits_empty": "Әзірге әдеттер жоқ. «🌱 Әдет қосу» батырмасын басыңыз.",
        "goal_usage": "Мақсат қосу үшін жазыңыз: `/goal Мақсат мәтіні`\nМыс.: `/goal 5 км жүгiру`",
        "habit_usage": "Әдет қосу үшін жазыңыз: `/habit Әдет атауы`\nМыс.: `/habit Су iшу`",
    },
    "kg": {
        "menu_title": "🎯 Максаттар жана 🌱 Адаттар",
        "btn_add_goal":   "🎯 Максат коюу",
        "btn_list_goals": "📋 Менин максаттарым",
        "btn_add_habit":  "🌱 Адат кошуу",
        "btn_list_habits":"📊 Менин адаттарым",
        "back": "◀️ Меню",
        "goals_title": "🎯 Сенин максаттарың:",
        "habits_title": "🌱 Сенин адаттарың:",
        "goals_empty": "Азырынча максаттар жок. «🎯 Максат коюу» бас.",
        "habits_empty": "Азырынча адаттар жок. «🌱 Адат кошуу» бас.",
        "goal_usage": "Максат кошуу үчүн жаз: `/goal Максат тексти`\nМис.: `/goal 5 км чуркоо`",
        "habit_usage": "Адат кошуу үчүн жаз: `/habit Адат аталышы`\nМис.: `/habit Суу ичүү`",
    },
    "hy": {
        "menu_title": "🎯 Նպատակներ և 🌱 Սովորություններ",
        "btn_add_goal":   "🎯 Նպատակ դնել",
        "btn_list_goals": "📋 Իմ նպատակները",
        "btn_add_habit":  "🌱 Սովորություն ավելացնել",
        "btn_list_habits":"📊 Իմ սովորությունները",
        "back": "◀️ Մենյու",
        "goals_title": "🎯 Քո նպատակները․",
        "habits_title": "🌱 Քո սովորությունները․",
        "goals_empty": "Դեռ նպատակներ չկան։ Սեղմիր «🎯 Նպատակ դնել».",
        "habits_empty": "Դեռ սովորություններ չկան։ Սեղմիր «🌱 Սովորություն ավելացնել».",
        "goal_usage": "Նպատակ ավելացնելու համար գրիր․ `/goal Նպատակ`\nՕր.` `/goal Վազել 5 կմ`",
        "habit_usage": "Սովորություն ավելացնելու համար գրիր․ `/habit Սովորություն`\nՕր.` `/habit Ջուր խմել`",
    },
    "ka": {
        "menu_title": "🎯 მიზნები და 🌱 ჩვევები",
        "btn_add_goal":   "🎯 მიზნის დაყენება",
        "btn_list_goals": "📋 ჩემი მიზნები",
        "btn_add_habit":  "🌱 ჩვევის დამატება",
        "btn_list_habits":"📊 ჩემი ჩვევები",
        "back": "◀️ მენიუ",
        "goals_title": "🎯 შენი მიზნები:",
        "habits_title": "🌱 შენი ჩვევები:",
        "goals_empty": "ჯერ მიზნები არ გაქვს. დააჭირე «🎯 მიზნის დაყენება».",
        "habits_empty": "ჯერ ჩვევები არ გაქვს. დააჭირე «🌱 ჩვევის დამატება».",
        "goal_usage": "მიზნის დასამატებლად დაწერე: `/goal მიზანი`\ნმაგ.: `/goal 5 კმ სირბილი`",
        "habit_usage": "ჩვევის დასამატებლად დაწერე: `/habit ჩვევის სახელი`\ნმაგ.: `/habit წყლის დალევა`",
    },
    "ce": {
        "menu_title": "🎯 Хьал хӀаттар да 🌱 дийцар",
        "btn_add_goal":   "🎯 ХӀаттар хийца",
        "btn_list_goals": "📋 ХӀаттар тӀед",
        "btn_add_habit":  "🌱 Дийцар хийца",
        "btn_list_habits":"📊 Дийцар тӀед",
        "back": "◀️ Меню",
        "goals_title": "🎯 Хьуна хӀаттар:",
        "habits_title": "🌱 Хьуна дийцар:",
        "goals_empty": "ХӀаттар яц. ДӀахь «🎯 ХӀаттар хийца».",
        "habits_empty": "Дийцар яц. ДӀахь «🌱 Дийцар хийца».",
        "goal_usage": "ХӀаттар хьай огӀаш: `/goal Текст хӀаттар`\нМасал: `/goal 5 км ваяж`",
        "habit_usage": "Дийцар хьай огӀаш: `/habit ЦӀе дийцар`\нМасал: `/habit Вода дӀайа`",
    },
    "en": {
        "menu_title": "🎯 Goals & 🌱 Habits",
        "btn_add_goal":   "🎯 Set goal",
        "btn_list_goals": "📋 My goals",
        "btn_add_habit":  "🌱 Add habit",
        "btn_list_habits":"📊 My habits",
        "back": "◀️ Menu",
        "goals_title": "🎯 Your goals:",
        "habits_title": "🌱 Your habits:",
        "goals_empty": "No goals yet. Tap “🎯 Add goal”.",
        "habits_empty": "No habits yet. Tap “🌱 Add habit”.",
        "goal_usage": "To add a goal, type: `/goal Your goal`\nE.g.: `/goal Run 5 km`",
        "habit_usage": "To add a habit, type: `/habit Habit name`\nE.g.: `/habit Drink water`",
    },
}

# Локализация подсказок для /settings (10 языков)
SETTINGS_TEXTS = {
    "ru": {
        "choose_lang": "🌐 Выбери язык интерфейса:",
        "choose_tz":   "🌍 Укажи свой часовой пояс (кнопками ниже):",
        "done":        "✅ Готово! Язык: *{lang_name}* · Часовой пояс: *{tz}* · Локальное время: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "uk": {
        "choose_lang": "🌐 Обери мову інтерфейсу:",
        "choose_tz":   "🌍 Вкажи свій часовий пояс (кнопками нижче):",
        "done":        "✅ Готово! Мова: *{lang_name}* · Часовий пояс: *{tz}* · Локальний час: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "md": {
        "choose_lang": "🌐 Alege limba interfeței:",
        "choose_tz":   "🌍 Alege fusul orar (folosește butoanele):",
        "done":        "✅ Gata! Limba: *{lang_name}* · Fus orar: *{tz}* · Ora locală: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "be": {
        "choose_lang": "🌐 Абярыце мову інтэрфейсу:",
        "choose_tz":   "🌍 Пакажыце свой часавы пояс (кнопкамі ніжэй):",
        "done":        "✅ Гатова! Мова: *{lang_name}* · Часавы пояс: *{tz}* · Мясцовы час: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "kk": {
        "choose_lang": "🌐 Интерфейс тілін таңдаңыз:",
        "choose_tz":   "🌍 Уақыт белдеуіңізді таңдаңыз (төмендегі батырмалар):",
        "done":        "✅ Дайын! Тіл: *{lang_name}* · Уақыт белдеуі: *{tz}* · Жергілікті уақыт: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "kg": {
        "choose_lang": "🌐 Интерфейс тилин тандаңыз:",
        "choose_tz":   "🌍 Убакыт алкагыңызды тандаңыз (төмөнкү баскычтар):",
        "done":        "✅ Даяр! Тил: *{lang_name}* · Убакыт алкагы: *{tz}* · Жергиликтүү убакыт: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "hy": {
        "choose_lang": "🌐 Ընտրիր ինտերֆեյսի լեզուն․",
        "choose_tz":   "🌍 Նշիր քո ժամային գոտին (ստորև գտնվող կոճակներով)․",
        "done":        "✅ Պատրաստ է․ Լեզու՝ *{lang_name}* · Ժամային գոտի՝ *{tz}* · Տեղական ժամանակ՝ *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "ka": {
        "choose_lang": "🌐 აირჩიე ინტერფეისის ენა:",
        "choose_tz":   "🌍 მიუთითე შენი დროის სარტყელი (ქვემოთ ღილაკებით):",
        "done":        "✅ მზადაა! ენა: *{lang_name}* · დროის სარტყელი: *{tz}* · ადგილობრივი დრო: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "ce": {
        "choose_lang": "🌐 Интерфейсийн мотт юкъахь талла:",
        "choose_tz":   "🌍 Тайм-зона юкъахь талла (кнопкаш тӀехь):",
        "done":        "✅ ДӀаяр! Мотт: *{lang_name}* · Тайм-зона: *{tz}* · Локал хан: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
    "en": {
        "choose_lang": "🌐 Pick your interface language:",
        "choose_tz":   "🌍 Set your time zone (use the buttons):",
        "done":        "✅ Done! Language: *{lang_name}* · Time zone: *{tz}* · Local time: *{local_time}*",
        "lang_name": {
            "ru":"Русский","uk":"Українська","md":"Moldovenească","be":"Беларуская",
            "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт","en":"English"
        },
    },
}

# Алиасы → IANA. Добавляй свои при желании.
TIMEZONE_ALIASES = {
    # UA/RU/СНГ
    "kiev": "Europe/Kyiv", "kyiv": "Europe/Kyiv", "киев": "Europe/Kyiv", "київ": "Europe/Kyiv",
    "moscow": "Europe/Moscow", "москва": "Europe/Moscow", "msk": "Europe/Moscow",
    "minsk": "Europe/Minsk",
    "chisinau": "Europe/Chisinau", "kishinev": "Europe/Chisinau", "кишинев": "Europe/Chisinau",
    "tbilisi": "Asia/Tbilisi", "tbilisi": "Asia/Tbilisi",
    "yerevan": "Asia/Yerevan", "erevan": "Asia/Yerevan",
    "almaty": "Asia/Almaty", "алматы": "Asia/Almaty",
    "bishkek": "Asia/Bishkek", "бишкек": "Asia/Bishkek",
    "astana": "Asia/Almaty",  # упростим для Казахстана

    # USA
    "ny": "America/New_York", "nyc": "America/New_York", "newyork": "America/New_York", "new_york": "America/New_York",
    "miami": "America/New_York",
    "dc": "America/New_York", "boston": "America/New_York", "philadelphia": "America/New_York",
    "chicago": "America/Chicago", "houston": "America/Chicago", "dallas": "America/Chicago", "austin": "America/Chicago",
    "denver": "America/Denver", "phoenix": "America/Phoenix",
    "la": "America/Los_Angeles", "losangeles": "America/Los_Angeles", "los_angeles": "America/Los_Angeles",
    "seattle": "America/Los_Angeles", "sf": "America/Los_Angeles", "sanfrancisco": "America/Los_Angeles",

    # EU misc
    "warsaw": "Europe/Warsaw", "vilnius": "Europe/Vilnius", "riga": "Europe/Riga", "tallinn": "Europe/Tallinn",
    "berlin": "Europe/Berlin", "paris": "Europe/Paris", "london": "Europe/London",

    # generic
    "utc": "UTC",
}

# Предустановленные кнопки (частые варианты)
TZ_KEYBOARD_ROWS = [
    [("🇺🇦 Kyiv", "Europe/Kyiv"), ("🇷🇺 Moscow", "Europe/Moscow"), ("🇧🇾 Minsk", "Europe/Minsk")],
    [("🇺🇸 New York", "America/New_York"), ("🇺🇸 Chicago", "America/Chicago")],
    [("🇺🇸 Denver", "America/Denver"), ("🇺🇸 Los Angeles", "America/Los_Angeles")],
    [("🇺🇸 Phoenix", "America/Phoenix"), ("🇺🇸 Miami", "America/New_York")],
    [("🇵🇱 Warsaw", "Europe/Warsaw"), ("🇱🇹 Vilnius", "Europe/Vilnius")],
    [("🇬🇪 Tbilisi", "Asia/Tbilisi"), ("🇦🇲 Yerevan", "Asia/Yerevan")],
    [("🇰🇿 Almaty", "Asia/Almaty"), ("🇰🇬 Bishkek", "Asia/Bishkek")],
    [("🌐 UTC", "UTC")],
]

# Локализация подсказок (10 языков)
TZ_TEXTS = {
    "ru": {
        "title": "🌍 Укажи свой часовой пояс для напоминаний.",
        "hint": "Пример: `/timezone kyiv` или `/timezone ny`.\nТакже можешь нажать кнопку ниже.",
        "saved": "✅ Часовой пояс установлен: *{tz}*. Локальное время: *{local_time}*.",
        "unknown": "Не распознал часовой пояс. Введи город/алиас или выбери кнопкой.",
    },
    "uk": {
        "title": "🌍 Вкажи свій часовий пояс для нагадувань.",
        "hint": "Приклад: `/timezone kyiv` або `/timezone ny`.\nТакож можна натиснути кнопку нижче.",
        "saved": "✅ Часовий пояс встановлено: *{tz}*. Локальний час: *{local_time}*.",
        "unknown": "Не впізнав часовий пояс. Введи місто/аліас або обери кнопкою.",
    },
    "md": {
        "title": "🌍 Alege fusul tău orar pentru notificări.",
        "hint": "Ex.: `/timezone chisinau` sau `/timezone ny`.\nPoți folosi butoanele de mai jos.",
        "saved": "✅ Fusul orar setat: *{tz}*. Ora locală: *{local_time}*.",
        "unknown": "Nu am recunoscut fusul orar. Introdu un oraș/alias sau folosește butoanele.",
    },
    "be": {
        "title": "🌍 Укажы свой часавы пояс для напамінаў.",
        "hint": "Прыклад: `/timezone minsk` або `/timezone ny`.\nТаксама можна націснуць кнопку ніжэй.",
        "saved": "✅ Часавы пояс усталяваны: *{tz}*. Мясцовы час: *{local_time}*.",
        "unknown": "Не распазнаў часавы пояс. Увядзі горад/аліяс або выберы кнопку.",
    },
    "kk": {
        "title": "🌍 Еске салғыштар үшін уақыт белдеуіңді таңда.",
        "hint": "Мысалы: `/timezone almaty` немесе `/timezone ny`.\nТөмендегі батырмаларды да қолдана аласың.",
        "saved": "✅ Уақыт белдеуі орнатылды: *{tz}*. Жергілікті уақыт: *{local_time}*.",
        "unknown": "Уақыт белдеуі танылмады. Қала/алиас енгіз немесе батырманы таңда.",
    },
    "kg": {
        "title": "🌍 Эскертмелер үчүн убакыт алкагыңды танда.",
        "hint": "Мисалы: `/timezone bishkek` же `/timezone ny`.\nТөмөндөгү баскычтарды колдон.",
        "saved": "✅ Убакыт алкагы коюлду: *{tz}*. Жергиликтүү убакыт: *{local_time}*.",
        "unknown": "Убакыт алкагын тааный албай койдум. Шаар/алиас жаз же баскычты танда.",
    },
    "hy": {
        "title": "🌍 Նշիր քո ժամային գոտին հիշեցումների համար.",
        "hint": "Օրինակ՝ `/timezone yerevan` կամ `/timezone ny`։\nԿարող ես օգտվել նաև կոճակներից։",
        "saved": "✅ Ժամային գոտին տեղադրված է՝ *{tz}*։ Տեղական ժամանակը՝ *{local_time}*.",
        "unknown": "Չհաջողվեց ճանաչել ժամային գոտին։ Գրիր քաղաք/ալիանս կամ ընտրիր կոճակով։",
    },
    "ka": {
        "title": "🌍 მიუთითე შენი საათობრივი სარტყელი შეხსენებებისთვის.",
        "hint": "მაგ.: `/timezone tbilisi` ან `/timezone ny`.\nშეგიძლია ქვევით ღილაკებითაც აირჩიო.",
        "saved": "✅ საათობრივი სარტყელი დაყენებულია: *{tz}*. ადგილობრივი დრო: *{local_time}*.",
        "unknown": "საათობრივი სარტყელი ვერ ვიცანი. მიუთითე ქალაქი/ალისი ან აირჩიე ღილაკით.",
    },
    "ce": {
        "title": "🌍 Хьажа тайм-зона аьттоьх дӀаскарийн.",
        "hint": "Мисал: `/timezone moscow` йолу `/timezone ny`.\nКнопка ша дар нися хийца.",
        "saved": "✅ Тайм-зона хийца: *{tz}*. Локал хьалхара: *{local_time}*.",
        "unknown": "Тайм-зона тӀехь махча дац. Шаара/алиасын юхай или кнопка тӀехь хийца.",
    },
    "en": {
        "title": "🌍 Set your time zone for reminders.",
        "hint": "Example: `/timezone ny` or `/timezone kyiv`.\nYou can also use the buttons below.",
        "saved": "✅ Time zone set: *{tz}*. Local time: *{local_time}*.",
        "unknown": "Couldn't recognize the time zone. Type a city/alias or use the buttons.",
    },
}

# -------- Points & Titles (help) --------
POINTS_HELP_TEXTS = {
    "ru": (
        "🏅 *Поинты и звания*\n"
        "Ты копишь поинты за действия в боте: цели, привычки, отчёты.\n\n"
        "Сейчас у тебя: *{points}* баллов — звание: *{title}*.\n"
        "До следующего звания *{next_title}* осталось: *{to_next}*.\n\n"
        "Лестница званий:\n{ladder}"
    ),
    "uk": (
        "🏅 *Бали та звання*\n"
        "Ти отримуєш бали за дії в боті: цілі, звички, звіти.\n\n"
        "Зараз у тебе: *{points}* балів — звання: *{title}*.\n"
        "До наступного звання *{next_title}* залишилось: *{to_next}*.\n\n"
        "Сходи звань:\n{ladder}"
    ),
    "en": (
        "🏅 *Points & Titles*\n"
        "You earn points for actions in the bot: goals, habits, reports.\n\n"
        "You now have *{points}* points — title: *{title}*.\n"
        "To the next title *{next_title}*: *{to_next}* left.\n\n"
        "Title ladder:\n{ladder}"
    ),
    "md": (
        "🏅 *Puncte și titluri*\n"
        "Primești puncte pentru acțiuni în bot: obiective, obiceiuri, rapoarte.\n\n"
        "Acum ai *{points}* puncte — titlu: *{title}*.\n"
        "Până la următorul titlu *{next_title}*: *{to_next}*.\n\n"
        "Scara titlurilor:\n{ladder}"
    ),
    "be": (
        "🏅 *Балы і званні*\n"
        "Ты атрымліваеш балы за дзеянні ў боте: мэты, звычкі, справаздачы.\n\n"
        "Зараз у цябе *{points}* балаў — званьне: *{title}*.\n"
        "Да наступнага званьня *{next_title}* засталося: *{to_next}*.\n\n"
        "Лесвіца званняў:\n{ladder}"
    ),
    "kk": (
        "🏅 *Ұпайлар мен атақтар*\n"
        "Боттағы әрекеттер үшін ұпай жинайсың: мақсаттар, әдеттер, есептер.\n\n"
        "Қазір сенде *{points}* ұпай — атағың: *{title}*.\n"
        "Келесі атаққа (*{next_title}*) дейін: *{to_next}*.\n\n"
        "Атақ сатысы:\n{ladder}"
    ),
    "kg": (
        "🏅 *Упайлар жана наамдар*\n"
        "Боттогу аракеттер үчүн упай аласың: максаттар, адаттар, отчёттор.\n\n"
        "Азыр сенде *{points}* упай — наам: *{title}*.\n"
        "Кийинки наамга *{next_title}* чейин: *{to_next}*.\n\n"
        "Наам баскычтары:\n{ladder}"
    ),
    "hy": (
        "🏅 *Միավորներ և կոչումներ*\n"
        "Դու միավորներ ես ստանում բոտում գործողությունների համար՝ նպատակներ, սովորություններ, զեկույցներ։\n\n"
        "Այժմ ունես *{points}* միավոր — կոչում՝ *{title}*։\n"
        "Մինչ հաջորդ կոչումը *{next_title}* մնացել է՝ *{to_next}*։\n\n"
        "Կոչումների սանդուղք․\n{ladder}"
    ),
    "ka": (
        "🏅 *ქულები და წოდებები*\n"
        "ბოტში ქულებს იღებ მოქმედებებისთვის: მიზნები, ჩვევები, რეპორტები.\n\n"
        "ახლა გაქვს *{points}* ქულა — წოდება: *{title}*.\n"
        "შემდეგ წოდებამდე (*{next_title}*) დარჩა: *{to_next}*.\n\n"
        "წოდებების კიბე:\n{ladder}"
    ),
    "ce": (
        "🏅 *Баллаш а, цIеран-намахь*\n"
        "Ботех ла цхьан йиш йиш йо бIалла баха: максат, дин цхьалат, отчёт.\n\n"
        "Хьо ю *{points}* балл — цIеран: *{title}*.\n"
        "Келчу цIеран *{next_title}* дехь: *{to_next}*.\n\n"
        "ЦIераннаш латтахь:\n{ladder}"
    ),
}

# Команда /remind — мультиязычный вариант
REMIND_TEXTS = {
    "ru": {
        # старые ключи (лимит/формат)
        "limit": "🔔 В бесплатной версии можно установить только 1 активное напоминание.\n\n✨ Оформи Mindra+, чтобы иметь неограниченные напоминания 💜",
        "usage": "⏰ Использование: `/remind 19:30 Сделай зарядку!`",
        "success": "✅ Напоминание установлено на {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Неверный формат. Пример: `/remind 19:30 Сделай зарядку!`",
        # новые ключи (Reminders 2.0)
        "create_help": "⏰ Создай напоминание: <когда> <о чём>\nПримеры: «завтра в 9 тренировка», «через 15 минут вода», «в пт в 19 кино».",
        "created":     "✅ Напоминание создано на {time}\n“{text}”",
        "not_understood": "⚠️ Не понял время. Скажи, например: «завтра в 10 полить цветы» или «через 30 минут кофе».",
        "list_empty":  "Пока нет активных напоминаний.",
        "list_title":  "🗓 Твои напоминания:",
        "fired":       "🔔 Напоминание: {text}\n🕒 {time}",
        "deleted":     "🗑 Напоминание удалено.",
        "snoozed":     "⏳ Перенесено на {time}\n“{text}”",
        "btn_plus15":  "⏳ +15м",
        "btn_plus1h":  "🕐 +1ч",
        "btn_tomorrow":"🌅 Завтра",
        "btn_delete":  "🗑 Удалить",
        "btn_new": "➕ Добавить",
        "menu_title": "🔔 Напоминания",
        "btn_add_rem": "➕ Добавить напоминание",
        "btn_list_rem": "📋 Список напоминаний",
    },
    "uk": {
        "limit": "🔔 У безкоштовній версії можна встановити лише 1 активне нагадування.\n\n✨ Оформи Mindra+, щоб мати необмежені нагадування 💜",
        "usage": "⏰ Використання: `/remind 19:30 Зроби зарядку!`",
        "success": "✅ Нагадування встановлено на {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Неправильний формат. Приклад: `/remind 19:30 Зроби зарядку!`",
        "create_help": "⏰ Створи нагадування: <коли> <про що>\nПриклади: «завтра о 9 тренування», «через 15 хв вода», «в пт о 19 кіно».",
        "created":     "✅ Нагадування створено на {time}\n“{text}”",
        "not_understood": "⚠️ Не зрозумів час. Напиши: «завтра о 10 полити квіти» або «через 30 хв каву».",
        "list_empty":  "Поки немає активних нагадувань.",
        "list_title":  "🗓 Твої нагадування:",
        "fired":       "🔔 Нагадування: {text}\n🕒 {time}",
        "deleted":     "🗑 Нагадування видалено.",
        "snoozed":     "⏳ Перенесено на {time}\n“{text}”",
        "btn_plus15":  "⏳ +15хв",
        "btn_plus1h":  "🕐 +1год",
        "btn_tomorrow":"🌅 Завтра",
        "btn_delete":  "🗑 Видалити",
        "btn_new": "➕ Додати",
        "menu_title": "🔔 Нагадування",
        "btn_add_rem": "➕ Додати нагадування",
        "btn_list_rem": "📋 Список нагадувань",
    },
    "md": {
        "limit": "🔔 În versiunea gratuită poți seta doar 1 memento activ.\n\n✨ Activează Mindra+ pentru mementouri nelimitate 💜",
        "usage": "⏰ Utilizare: `/remind 19:30 Fă exerciții!`",
        "success": "✅ Mementoul a fost setat la {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Format greșit. Exemplu: `/remind 19:30 Fă exerciții!`",
        "create_help": "⏰ Creează un memento: <când> <despre ce>\nEx.: „mâine la 9 sală”, „în 15 min apă”.",
        "created":     "✅ Memento creat pentru {time}\n“{text}”",
        "not_understood": "⚠️ Nu am înțeles timpul. Scrie „mâine la 10 udat florile” sau „în 30 min cafea”.",
        "list_empty":  "Nu ai încă mementouri active.",
        "list_title":  "🗓 Mementourile tale:",
        "fired":       "🔔 Memento: {text}\n🕒 {time}",
        "deleted":     "🗑 Memento șters.",
        "snoozed":     "⏳ Amânat până la {time}\n“{text}”",
        "btn_plus15":  "⏳ +15m",
        "btn_plus1h":  "🕐 +1h",
        "btn_tomorrow":"🌅 Mâine",
        "btn_delete":  "🗑 Șterge",
        "btn_new": "➕ Nou",
        "menu_title": "🔔 Mementouri",
        "btn_add_rem": "➕ Adaugă memento",
        "btn_list_rem": "📋 Lista mementourilor",
    },
    "be": {
        "limit": "🔔 У бясплатнай версіі можна ўсталяваць толькі 1 актыўнае напамінанне.\n\n✨ Аформі Mindra+, каб мець неабмежаваную колькасць напамінанняў 💜",
        "usage": "⏰ Выкарыстанне: `/remind 19:30 Зрабі зарадку!`",
        "success": "✅ Напамінанне ўсталявана на {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Няправільны фармат. Прыклад: `/remind 19:30 Зрабі зарадку!`",
        "create_help": "⏰ Ствары напамін: <калі> <пра што>\nПрыклады: «заўтра ў 9 трэніроўка», «праз 15 хв вода».",
        "created":     "✅ Напамін створаны на {time}\n“{text}”",
        "not_understood": "⚠️ Не зразумеў час. Напішы «заўтра ў 10 паліць кветкі» або «праз 30 хв каву».",
        "list_empty":  "Пакуль няма актыўных напамінаў.",
        "list_title":  "🗓 Твае напаміны:",
        "fired":       "🔔 Напамін: {text}\n🕒 {time}",
        "deleted":     "🗑 Напамін выдалены.",
        "snoozed":     "⏳ Перанесены на {time}\n“{text}”",
        "btn_plus15":  "⏳ +15хв",
        "btn_plus1h":  "🕐 +1г",
        "btn_tomorrow":"🌅 Заўтра",
        "btn_delete":  "🗑 Выдаліць",
        "btn_new": "➕ Дадаць",
        "menu_title": "🔔 Напаміны",
        "btn_add_rem": "➕ Дадаць напамін",
        "btn_list_rem": "📋 Спіс напамінаў",
    },
    "kk": {
        "limit": "🔔 Тегін нұсқада тек 1 белсенді еске салу орнатуға болады.\n\n✨ Mindra+ арқылы шексіз еске салулар орнатыңыз 💜",
        "usage": "⏰ Қолдану: `/remind 19:30 Жаттығу жаса!`",
        "success": "✅ Еске салу орнатылды: {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Қате формат. Мысал: `/remind 19:30 Жаттығу жаса!`",
        "create_help": "⏰ Еске салуды құр: <қашан> <не туралы>\nМысалы: «ертең 9-да жаттығу», «15 мин кейін су».",
        "created":     "✅ Еске салу {time} уақытына қойылды\n“{text}”",
        "not_understood": "⚠️ Уақытты түсінбедім. «Ертең 10-да гүл суару» не «30 мин кейін кофе» деп жазыңыз.",
        "list_empty":  "Әзірше белсенді еске салулар жоқ.",
        "list_title":  "🗓 Еске салуларың:",
        "fired":       "🔔 Еске салу: {text}\n🕒 {time}",
        "deleted":     "🗑 Еске салу өшірілді.",
        "snoozed":     "⏳ {time} уақытына кейінге шегерілді\n“{text}”",
        "btn_plus15":  "⏳ +15м",
        "btn_plus1h":  "🕐 +1с",
        "btn_tomorrow":"🌅 Ертең",
        "btn_delete":  "🗑 Өшіру",
        "btn_new": "➕ Қосу",
        "menu_title": "🔔 Еске салулар",
        "btn_add_rem": "➕ Еске салу қосу",
        "btn_list_rem": "📋 Еске салулар тізімі",
    },
    "kg": {
        "limit": "🔔 Акысыз версияда бир эле эскертме коюуга болот.\n\n✨ Mindra+ менен чексиз эскертмелерди коюңуз 💜",
        "usage": "⏰ Колдонуу: `/remind 19:30 Зарядка жаса!`",
        "success": "✅ Эскертүү коюлду: {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Формат туура эмес. Мисал: `/remind 19:30 Зарядка жаса!`",
        "create_help": "⏰ Эскертүү жарат: <качан> <эмне жөнүндө>\nМисалы: «эртең 9-да машыгуу», «15 мүнөттөн кийин суу».",
        "created":     "✅ Эскертүү {time} коюлду\n“{text}”",
        "not_understood": "⚠️ Убакытты түшүнгөн жокмун. «Эртең 10-да гүл сугаруу» же «30 мүн өтсө кофе» деп жазыңыз.",
        "list_empty":  "Азырынча активдүү эскертүүлөр жок.",
        "list_title":  "🗓 Эскертмелериң:",
        "fired":       "🔔 Эскертүү: {text}\n🕒 {time}",
        "deleted":     "🗑 Эскертүү өчүрүлдү.",
        "snoozed":     "⏳ {time} убактысына жылдырылды\n“{text}”",
        "btn_plus15":  "⏳ +15мүн",
        "btn_plus1h":  "🕐 +1с",
        "btn_tomorrow":"🌅 Эртең",
        "btn_delete":  "🗑 Өчүрүү",
        "btn_new": "➕ Кошуу",
        "menu_title": "🔔 Эскертмелер",
        "btn_add_rem": "➕ Эскертме кошуу",
        "btn_list_rem": "📋 Эскертмелер тизмеси",
    },
    "hy": {
        "limit": "🔔 Անվճար տարբերակում կարելի է ավելացնել միայն 1 ակտիվ հիշեցում։\n\n✨ Միացրու Mindra+, որ ունենաս անսահման հիշեցումներ 💜",
        "usage": "⏰ Օգտագործում: `/remind 19:30 Կատարի՛ր վարժանքներ!`",
        "success": "✅ Հիշեցումը սահմանվել է {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Սխալ ձևաչափ։ Օրինակ: `/remind 19:30 Կատարի՛ր վարժանքներ!`",
        "create_help": "⏰ Ստեղծիր հիշեցում՝ <երբ> <մասին>\nՕր.` «վաղը 9-ին մարզում», «15 րոպեից ջուր»։",
        "created":     "✅ Հիշեցումը սահմանված է {time}-ին\n“{text}”",
        "not_understood": "⚠️ Ժամանակը չհասկացա։ Գրի՝ «վաղը 10-ին ծաղիկներին ջուր» կամ «30 րոպեից սուրճ»։",
        "list_empty":  "Դեռ ակտիվ հիշեցումներ չունես։",
        "list_title":  "🗓 Քո հիշեցումները․",
        "fired":       "🔔 Հիշեցում․ {text}\n🕒 {time}",
        "deleted":     "🗑 Հիշեցումը ջնջվեց։",
        "snoozed":     "⏳ Տեղափոխվեց {time}\n“{text}”",
        "btn_plus15":  "⏳ +15ր",
        "btn_plus1h":  "🕐 +1ժ",
        "btn_tomorrow":"🌅 Վաղը",
        "btn_delete":  "🗑 Ջնջել",
        "btn_new": "➕ Նոր հիշեցում",
        "menu_title": "🔔 Հիշեցումներ",
        "btn_add_rem": "➕ Ավելացնել հիշեցում",
        "btn_list_rem": "📋 Հիշեցումների ցանկ",
    },
    "ka": {
        "limit": "🔔 უფასო ვერსიაში შეგიძლიათ დააყენოთ მხოლოდ 1 აქტიური შეხსენება.\n\n✨ გაააქტიურეთ Mindra+ ულიმიტო შეხსენებისთვის 💜",
        "usage": "⏰ გამოყენება: `/remind 19:30 გააკეთე ვარჯიში!`",
        "success": "✅ შეხსენება დაყენებულია {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ არასწორი ფორმატი. მაგალითი: `/remind 19:30 გააკეთე ვარჯიში!`",
        "create_help": "⏰ შექმენი შეხსენება: <როდის> <რის შესახებ>\nმაგ.: «ხვალ 9-ზე ვარჯიში», «15 წთ მერე წყალი».",
        "created":     "✅ შეხსენება დაყენებულია {time}-ზე\n“{text}”",
        "not_understood": "⚠️ დრო ვერ გავიგე. დაწერე: «ხვალ 10-ზე ყვავილების მორწყვა» ან «30 წთ მერე ყავა».",
        "list_empty":  "ჯერ აქტიური შეხსენებები არ გაქვს.",
        "list_title":  "🗓 შენი შეხსენებები:",
        "fired":       "🔔 შეხსენება: {text}\n🕒 {time}",
        "deleted":     "🗑 შეხსენება წაიშალა.",
        "snoozed":     "⏳ გადატანილია {time}-ზე\n“{text}”",
        "btn_plus15":  "⏳ +15წთ",
        "btn_plus1h":  "🕐 +1სთ",
        "btn_tomorrow":"🌅 ხვალ",
        "btn_delete":  "🗑 წაშლა",
        "btn_new": "➕ დამატება",
        "menu_title": "🔔 შეხსენებები",
        "btn_add_rem": "➕ შეხსენების დამატება",
        "btn_list_rem": "📋 შეხსენებების სია",
    },
    "ce": {
        "limit": "🔔 Аьтто версия хийцна, цхьаьнан 1 активан напоминание ца хилла цуьнан.\n\n✨ Mindra+ хийцар, цуьнан цуьнан цхьаьнан напоминаний хилла 💜",
        "usage": "⏰ Цуьнан: `/remind 19:30 Зарядка йоцу!`",
        "success": "✅ Напоминание хийна {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Формат дукха. Мисал: `/remind 19:30 Зарядка йоцу!`",
        "create_help": "⏰ ДӀай бар: <кха> <чу йолу>\nМасаллахь: «кхеза 9 хьалха ваяж», «15 мин даьллина хьа вода».",
        "created":     "✅ ДӀай бар {time} хьалха тайпа\n“{text}”",
        "not_understood": "⚠️ Хан ца йолу. Хаьийта: «кхеза 10 хьалха цIаьрг морх дика» авла «30 мин даьллина кофе».",
        "list_empty":  "Актив дӀай бар яц.",
        "list_title":  "🗓 Хьуна дӀай бар:",
        "fired":       "🔔 ДӀай бар: {text}\n🕒 {time}",
        "deleted":     "🗑 ДӀай бар дIадайна.",
        "snoozed":     "⏳ Хийца {time} хьалха\n“{text}”",
        "btn_plus15":  "⏳ +15м",
        "btn_plus1h":  "🕐 +1с",
        "btn_tomorrow":"🌅 Кхеза",
        "btn_delete":  "🗑 ДIадайе",
        "btn_new": "➕ Керла",
        "menu_title": "🔔 ДӀай бар",
        "btn_add_rem": "➕ ДӀай бар хийца",
        "btn_list_rem": "📋 ДӀай бар тIед",
    },
    "en": {
        "limit": "🔔 In the free version, you can set only 1 active reminder.\n\n✨ Get Mindra+ for unlimited reminders 💜",
        "usage": "⏰ Usage: `/remind 19:30 Do your workout!`",
        "success": "✅ Reminder set for {hour:02d}:{minute:02d}: *{text}*",
        "bad_format": "⚠️ Wrong format. Example: `/remind 19:30 Do your workout!`",
        "create_help": "⏰ Create a reminder: <when> <what>\nExamples: “tomorrow at 9 gym”, “in 15 min water”, “on fri at 7 movie”.",
        "created":     "✅ Reminder set for {time}\n“{text}”",
        "not_understood": "⚠️ I couldn't parse the time. Try: “tomorrow at 10 water the plants” or “in 30 min coffee”.",
        "list_empty":  "No active reminders yet.",
        "list_title":  "🗓 Your reminders:",
        "fired":       "🔔 Reminder: {text}\n🕒 {time}",
        "deleted":     "🗑 Reminder deleted.",
        "snoozed":     "⏳ Snoozed to {time}\n“{text}”",
        "btn_plus15":  "⏳ +15m",
        "btn_plus1h":  "🕐 +1h",
        "btn_tomorrow":"🌅 Tomorrow",
        "btn_delete":  "🗑 Delete",
        "btn_new": "➕ New",
        "menu_title": "🔔 Reminders",
        "btn_add_rem": "➕ Add reminder",
        "btn_list_rem": "📋 Reminder list",
    },
}

LOCKED_MSGS = {
        "ru": "🔒 Эта функция доступна только подписчикам Mindra+.",
        "uk": "🔒 Ця функція доступна лише для підписників Mindra+.",
        "en": "🔒 This feature is only available to Mindra+ subscribers.",
        "be": "🔒 Гэтая функцыя даступная толькі падпісчыкам Mindra+.",
        "kk": "🔒 Бұл мүмкіндік тек Mindra+ жазылушыларына қолжетімді.",
        "kg": "🔒 Бул функция Mindra+ жазылуучулары үчүн гана жеткиликтүү.",
        "hy": "🔒 Այս գործառույթը հասանելի է միայն Mindra+ բաժանորդներին։",
        "ce": "🔒 Дина функция Mindra+ яззийна догъа кхоллар хетам.",
        "md": "🔒 Această funcție este disponibilă doar abonaților Mindra+.",
        "ka": "🔒 ეს ფუნქცია ხელმისაწვდომია მხოლოდ Mindra+ აბონენტებისთვის.",
    }

MSGS = {
        "coach": {
            "ru": "✅ Режим общения изменён на *Коуч*. Я буду помогать и мотивировать тебя! 💪",
            "uk": "✅ Режим спілкування змінено на *Коуч*. Я допомагатиму та мотивуватиму тебе! 💪",
            "en": "✅ Communication mode changed to *Coach*. I will help and motivate you! 💪",
            "be": "✅ Рэжым зносін зменены на *Коуч*. Я буду дапамагаць і матываваць цябе! 💪",
            "kk": "✅ Байланыс режимі *Коуч* болып өзгертілді. Мен саған көмектесіп, мотивация беремін! 💪",
            "kg": "✅ Байланыш режими *Коуч* болуп өзгөрдү. Мен сага жардам берип, шыктандырам! 💪",
            "hy": "✅ Կապի ռեժիմը փոխվեց *Քոուչ*: Ես կօգնեմ և կխրախուսեմ քեզ։ 💪",
            "ce": "✅ Чуйна режим хила *Коуч* догъа. Со ву до а ю мотивация ю! 💪",
            "md": "✅ Modul de comunicare a fost schimbat la *Coach*. Te voi ajuta și motiva! 💪",
            "ka": "✅ კომუნიკაციის რეჟიმი შეიცვალა *ქოუჩი*-ზე. დაგეხმარები და მოგამოტივირებ! 💪",
        },
        "flirt": {
            "ru": "😉 Режим общения изменён на *Флирт*. Приготовься к приятным неожиданностям 💜",
            "uk": "😉 Режим спілкування змінено на *Флірт*. Готуйся до приємних сюрпризів 💜",
            "en": "😉 Communication mode changed to *Flirt*. Get ready for pleasant surprises 💜",
            "be": "😉 Рэжым зносін зменены на *Флірт*. Будзь гатовы да прыемных нечаканасцей 💜",
            "kk": "😉 Байланыс режимі *Флирт* болып өзгертілді. Жақсы тосынсыйларға дайын бол 💜",
            "kg": "😉 Байланыш режими *Флирт* болуп өзгөрдү. Жакшы сюрприздерге даяр бол 💜",
            "hy": "😉 Կապի ռեժիմը փոխվեց *Ֆլիրտ*: Պատրաստ եղիր հաճելի անակնկալների 💜",
            "ce": "😉 Чуйна режим хила *Флирт* догъа. Дахьал цуьнан сюрпризаш хилайла! 💜",
            "md": "😉 Modul de comunicare a fost schimbat la *Flirt*. Pregătește-te pentru surprize plăcute 💜",
            "ka": "😉 კომუნიკაციის რეჟიმი შეიცვალა *ფლირტი*-ზე. მოემზადე სასიამოვნო სიურპრიზებისთვის 💜",
        }
    }

EXCLUSIVE_MODES_BY_LANG = {
    "ru": {
        "coach": "💪 Ты — мой личный коуч. Помогай чётко, по делу, давай советы, поддерживай! 🚀",
        "flirty": "😉 Ты — немного флиртуешь и поддерживаешь. Отвечай с теплом и лёгким флиртом 💜✨",
    },
    "uk": {
        "coach": "💪 Ти — мій особистий коуч. Допомагай чітко, по суті, давай поради! 🚀",
        "flirty": "😉 Ти — трохи фліртуєш і підтримуєш. Відповідай тепло та з легкою грою 💜✨",
    },
    "be": {
        "coach": "💪 Ты — мой асабісты коуч. Дапамагай дакладна, па справе, давай парады! 🚀",
        "flirty": "😉 Ты — трохі фліртуеш і падтрымліваеш. Адказвай цёпла і з лёгкім фліртам 💜✨",
    },
    "kk": {
        "coach": "💪 Сен — менің жеке коучымсың. Нақты, қысқа, пайдалы кеңес бер, жігерлендір! 🚀",
        "flirty": "😉 Сен — сәл флирт пен қолдау көрсетесің. Жылы, жеңіл әзілмен жауап бер 💜✨",
    },
    "kg": {
        "coach": "💪 Сен — менин жеке коучумсуң. Так, кыскача, пайдалуу кеңештерди бер! 🚀",
        "flirty": "😉 Сен — бир аз флирт кыласың жана колдойсуң. Жылуу, жеңил ойноок жооп бер 💜✨",
    },
    "hy": {
        "coach": "💪 Դու իմ անձնական քոուչն ես։ Օգնիր հստակ, գործնական, տուր խորհուրդներ, ոգեշնչիր! 🚀",
        "flirty": "😉 Դու մի քիչ ֆլիրտում ես և աջակցում։ Պատասխանիր ջերմորեն և թեթև ֆլիրտով 💜✨",
    },
    "ce": {
        "coach": "💪 Хьо — миниг персоналийн коуч. Йойла хьалха, да дийцар дуьйна, совета шун! 🚀",
        "flirty": "😉 Хьо — ца хьалха флирт ду хьалхара а, цуьнан цуьнан дийцарца. Йоьлча цуьнан цуьнан флирт 💜✨",
    },
    "md": {
        "coach": "💪 Tu ești antrenorul meu personal. Ajută clar, la subiect, dă sfaturi, inspiră! 🚀",
        "flirty": "😉 Ești puțin cochet(ă) și susținător(oare). Răspunde călduros și cu un flirt ușor 💜✨",
    },
    "ka": {
        "coach": "💪 შენ ხარ ჩემი პირადი ქოუჩი. დამეხმარე მკაფიოდ, საქმეზე, მომეცი რჩევები, შთააგონე! 🚀",
        "flirty": "😉 შენ ოდნავ ფლირტაობ და ამასთან ერთად მხარდაჭერას იჩენ. უპასუხე თბილად და მსუბუქი ფლირტით 💜✨",
    },
    "en": {
        "coach": "💪 You are my personal coach. Help clearly and to the point, give advice, motivate! 🚀",
        "flirty": "😉 You're a bit flirty and supportive. Reply warmly and with a light flirt 💜✨",
    },
}

PREMIUM_REPORT_TEXTS = {
    "ru": (
        "✅ *Твой персональный отчёт за неделю:*\n\n"
        "🎯 Завершено целей: {completed_goals}\n"
        "🌱 Привычек выполнено: {completed_habits}\n"
        "📅 Дней активности: {days_active}\n"
        "📝 Записей настроения: {mood_entries}\n\n"
        "Ты молодец! Продолжай в том же духе 💜"
    ),
    "uk": (
        "✅ *Твій персональний звіт за тиждень:*\n\n"
        "🎯 Виконано цілей: {completed_goals}\n"
        "🌱 Виконано звичок: {completed_habits}\n"
        "📅 Днів активності: {days_active}\n"
        "📝 Записів настрою: {mood_entries}\n\n"
        "Ти молодець! Продовжуй у тому ж дусі 💜"
    ),
    "be": (
        "✅ *Твой асабісты справаздача за тыдзень:*\n\n"
        "🎯 Выканана мэтаў: {completed_goals}\n"
        "🌱 Выканана звычак: {completed_habits}\n"
        "📅 Дзён актыўнасці: {days_active}\n"
        "📝 Запісаў настрою: {mood_entries}\n\n"
        "Ты малайчына! Працягвай у тым жа духу 💜"
    ),
    "kk": (
        "✅ *Апталық жеке есебің:*\n\n"
        "🎯 Орындалған мақсаттар: {completed_goals}\n"
        "🌱 Орындалған әдеттер: {completed_habits}\n"
        "📅 Белсенді күндер: {days_active}\n"
        "📝 Көңіл күй жазбалары: {mood_entries}\n\n"
        "Жарайсың! Осылай жалғастыра бер 💜"
    ),
    "kg": (
        "✅ *Жумалык жекече отчетуң:*\n\n"
        "🎯 Аткарылган максаттар: {completed_goals}\n"
        "🌱 Аткарылган адаттар: {completed_habits}\n"
        "📅 Активдүү күндөр: {days_active}\n"
        "📝 Көңүл-күй жазуулары: {mood_entries}\n\n"
        "Афарың! Ошентип уланта бер 💜"
    ),
    "hy": (
        "✅ *Քո անձնական շաբաթական հաշվետվությունը:*\n\n"
        "🎯 Կատարված նպատակներ: {completed_goals}\n"
        "🌱 Կատարված սովորություններ: {completed_habits}\n"
        "📅 Ակտիվ օրեր: {days_active}\n"
        "📝 Տրամադրության գրառումներ: {mood_entries}\n\n"
        "Դու հրաշալի ես։ Շարունակի՛ր այսպես 💜"
    ),
    "ce": (
        "✅ *Тхо персоналийна хафта йоьлча:* \n\n"
        "🎯 ДӀаязде мацахь: {completed_goals}\n"
        "🌱 ДӀаязде привычка: {completed_habits}\n"
        "📅 Активний денаш: {days_active}\n"
        "📝 Хилда мотивацийн тӀемаш: {mood_entries}\n\n"
        "Хьо ду ю! Чу хила ю бина хийцахь 💜"
    ),
    "md": (
        "✅ *Raportul tău personal pentru săptămână:*\n\n"
        "🎯 Obiective realizate: {completed_goals}\n"
        "🌱 Obiceiuri îndeplinite: {completed_habits}\n"
        "📅 Zile de activitate: {days_active}\n"
        "📝 Înregistrări de dispoziție: {mood_entries}\n\n"
        "Bravo! Continuă tot așa 💜"
    ),
    "ka": (
        "✅ *შენი პერსონალური კვირის ანგარიში:*\n\n"
        "🎯 შესრულებული მიზნები: {completed_goals}\n"
        "🌱 შესრულებული ჩვევები: {completed_habits}\n"
        "📅 აქტიური დღეები: {days_active}\n"
        "📝 განწყობის ჩანაწერები: {mood_entries}\n\n"
        "შესანიშნავია! ასე გააგრძელე 💜"
    ),
    "en": (
        "✅ *Your personal report for the week:*\n\n"
        "🎯 Goals completed: {completed_goals}\n"
        "🌱 Habits completed: {completed_habits}\n"
        "📅 Days active: {days_active}\n"
        "📝 Mood entries: {mood_entries}\n\n"
        "Great job! Keep it up 💜"
    ),
}

PREMIUM_CHALLENGES_BY_LANG = {
    "ru": [
        "🔥 Сделай сегодня доброе дело для незнакомца.",
        "🌟 Запиши 5 своих сильных сторон и расскажи о них другу.",
        "💎 Найди новую книгу и прочитай хотя бы 1 главу.",
        "🚀 Составь план на следующую неделю с чёткими целями.",
        "🎯 Сделай шаг в сторону большой мечты.",
        "🙌 Найди способ помочь другу или коллеге.",
        "💡 Придумай и начни новый маленький проект.",
        "🏃 Пробеги больше, чем обычно, хотя бы на 5 минут.",
        "🧘‍♀️ Сделай глубокую медитацию 10 минут.",
        "🖋️ Напиши письмо человеку, который тебя вдохновил.",
        "📚 Пройди сегодня новый онлайн-курс (хотя бы 1 урок).",
        "✨ Найди сегодня возможность кого-то поддержать.",
        "🎨 Нарисуй что-то и отправь другу.",
        "🤝 Познакомься сегодня с новым человеком.",
        "🌱 Помоги природе: убери мусор или посади дерево.",
        "💬 Напиши пост в соцсетях о том, что тебя радует.",
        "🎧 Слушай подкаст о саморазвитии 15 минут.",
        "🧩 Изучи новый навык в течение часа.",
        "🏗️ Разработай идею для стартапа и запиши.",
        "☀️ Начни утро с благодарности и напиши 10 пунктов.",
        "🍀 Найди способ подарить кому-то улыбку.",
        "🔥 Сделай сегодня что-то, чего ты боялся(ась).",
        "🛠️ Исправь дома что-то, что давно откладывал(а).",
        "💜 Придумай 3 способа сделать мир добрее.",
        "🌸 Купи себе или другу цветы.",
        "🚴‍♂️ Соверши длинную прогулку или велопоездку.",
        "📅 Распиши план на месяц вперёд.",
        "🧘‍♂️ Попробуй йогу или новую практику.",
        "🎤 Спой любимую песню вслух!",
        "✈️ Запланируй будущую поездку мечты.",
        "🕊️ Сделай пожертвование на благотворительность.",
        "🍎 Приготовь необычное блюдо сегодня.",
        "🔑 Найди решение старой проблемы.",
        "🖋️ Напиши письмо самому себе через 5 лет.",
        "🤗 Обними близкого человека и скажи, как ценишь его.",
        "🏞️ Проведи час на природе без телефона.",
        "📖 Найди новую цитату и запомни её.",
        "🎬 Посмотри фильм, который давно хотел(а).",
        "🛌 Ложись спать на час раньше сегодня.",
        "📂 Разбери свои фотографии и сделай альбом.",
        "📈 Разработай стратегию улучшения себя.",
        "🎮 Поиграй в игру, которую не пробовал(а).",
        "🖼️ Создай доску визуализации своей мечты.",
        "🌟 Найди способ кого-то вдохновить.",
        "🔔 Установи полезное напоминание.",
        "💌 Напиши благодарственное сообщение 3 людям.",
        "🧩 Разгадай кроссворд или судоку.",
        "🏋️‍♂️ Сделай тренировку, которую давно хотел(а)."
    ],
    "en": [
        "🔥 Do a good deed for a stranger today.",
        "🌟 Write down 5 of your strengths and tell a friend about them.",
        "💎 Find a new book and read at least one chapter.",
        "🚀 Make a plan for next week with clear goals.",
        "🎯 Take a step toward a big dream.",
        "🙌 Find a way to help a friend or colleague.",
        "💡 Come up with and start a new small project.",
        "🏃 Run 5 minutes more than usual.",
        "🧘‍♀️ Do a deep meditation for 10 minutes.",
        "🖋️ Write a letter to someone who inspired you.",
        "📚 Take a new online course today (at least one lesson).",
        "✨ Find an opportunity to support someone today.",
        "🎨 Draw something and send it to a friend.",
        "🤝 Meet a new person today.",
        "🌱 Help nature: clean up trash or plant a tree.",
        "💬 Write a post on social media about what makes you happy.",
        "🎧 Listen to a self-development podcast for 15 minutes.",
        "🧩 Learn a new skill for an hour.",
        "🏗️ Develop an idea for a startup and write it down.",
        "☀️ Start your morning with gratitude and write 10 points.",
        "🍀 Find a way to make someone smile.",
        "🔥 Do something today that you were afraid to do.",
        "🛠️ Fix something at home that you've been putting off.",
        "💜 Come up with 3 ways to make the world kinder.",
        "🌸 Buy flowers for yourself or a friend.",
        "🚴‍♂️ Go for a long walk or bike ride.",
        "📅 Plan your month ahead.",
        "🧘‍♂️ Try yoga or a new practice.",
        "🎤 Sing your favorite song out loud!",
        "✈️ Plan a dream trip for the future.",
        "🕊️ Make a donation to charity.",
        "🍎 Cook something unusual today.",
        "🔑 Find a solution to an old problem.",
        "🖋️ Write a letter to yourself in 5 years.",
        "🤗 Hug a loved one and tell them how much you value them.",
        "🏞️ Spend an hour in nature without your phone.",
        "📖 Find a new quote and memorize it.",
        "🎬 Watch a movie you've wanted to see for a long time.",
        "🛌 Go to bed an hour earlier today.",
        "📂 Organize your photos and make an album.",
        "📈 Develop a self-improvement strategy.",
        "🎮 Play a game you've never tried before.",
        "🖼️ Create a vision board for your dreams.",
        "🌟 Find a way to inspire someone.",
        "🔔 Set a useful reminder.",
        "💌 Write a thank you message to 3 people.",
        "🧩 Solve a crossword or sudoku.",
        "🏋️‍♂️ Do a workout you've wanted to try for a long time."
    ],
    "uk": [
        "🔥 Зроби сьогодні добру справу для незнайомця.",
        "🌟 Запиши 5 своїх сильних сторін і розкажи про них другу.",
        "💎 Знайди нову книгу і прочитай хоча б 1 розділ.",
        "🚀 Склади план на наступний тиждень з чіткими цілями.",
        "🎯 Зроби крок у напрямку великої мрії.",
        "🙌 Знайди спосіб допомогти другові чи колезі.",
        "💡 Придумай і почни новий маленький проєкт.",
        "🏃 Пробігай більше, ніж зазвичай, хоча б на 5 хвилин.",
        "🧘‍♀️ Проведи глибоку медитацію 10 хвилин.",
        "🖋️ Напиши листа людині, яка тебе надихнула.",
        "📚 Пройди сьогодні новий онлайн-курс (хоча б 1 урок).",
        "✨ Знайди сьогодні можливість когось підтримати.",
        "🎨 Намалюй щось і відправ другу.",
        "🤝 Познайомся сьогодні з новою людиною.",
        "🌱 Допоможи природі: прибери сміття або посади дерево.",
        "💬 Напиши пост у соцмережах про те, що тебе радує.",
        "🎧 Послухай подкаст про саморозвиток 15 хвилин.",
        "🧩 Вивчи нову навичку протягом години.",
        "🏗️ Розроби ідею для стартапу та запиши.",
        "☀️ Почни ранок із вдячності і напиши 10 пунктів.",
        "🍀 Знайди спосіб подарувати комусь усмішку.",
        "🔥 Зроби сьогодні те, чого ти боявся(лася).",
        "🛠️ Відремонтуй вдома щось, що давно відкладав(ла).",
        "💜 Придумай 3 способи зробити світ добрішим.",
        "🌸 Купи собі або другу квіти.",
        "🚴‍♂️ Зроби довгу прогулянку або велопоїздку.",
        "📅 Розпиши план на місяць наперед.",
        "🧘‍♂️ Спробуй йогу або нову практику.",
        "🎤 Заспівай улюблену пісню вголос!",
        "✈️ Заплануй майбутню подорож мрії.",
        "🕊️ Зроби пожертву на благодійність.",
        "🍎 Приготуй незвичайну страву сьогодні.",
        "🔑 Знайди рішення старої проблеми.",
        "🖋️ Напиши листа собі через 5 років.",
        "🤗 Обійми близьку людину і скажи, як цінуєш її.",
        "🏞️ Проведи годину на природі без телефону.",
        "📖 Знайди нову цитату і запам'ятай її.",
        "🎬 Подивися фільм, який давно хотів(ла).",
        "🛌 Лягай спати на годину раніше сьогодні.",
        "📂 Перебери свої фотографії та зроби альбом.",
        "📈 Розроби стратегію самовдосконалення.",
        "🎮 Пограй у гру, яку ще не пробував(ла).",
        "🖼️ Створи дошку візуалізації своєї мрії.",
        "🌟 Знайди спосіб когось надихнути.",
        "🔔 Встанови корисне нагадування.",
        "💌 Напиши подяку 3 людям.",
        "🧩 Розв'яжи кросворд або судоку.",
        "🏋️‍♂️ Зроби тренування, яке давно хотів(ла)."
    ],
    "be": [
        "🔥 Зрабі сёння добрую справу для незнаёмага.",
        "🌟 Запішы 5 сваіх моцных бакоў і раскажы пра іх сябру.",
        "💎 Знайдзі новую кнігу і прачытай хоць бы адзін раздзел.",
        "🚀 Скласці план на наступны тыдзень з дакладнымі мэтамі.",
        "🎯 Зрабі крок у бок вялікай мары.",
        "🙌 Знайдзі спосаб дапамагчы сябру ці калегу.",
        "💡 Прыдумай і пачні новы маленькі праект.",
        "🏃 Прабягі больш, чым звычайна, хоць бы на 5 хвілін.",
        "🧘‍♀️ Зрабі глыбокую медытацыю 10 хвілін.",
        "🖋️ Напішы ліст чалавеку, які цябе натхніў.",
        "📚 Прайдзі сёння новы онлайн-курс (хоць бы адзін урок).",
        "✨ Знайдзі сёння магчымасць некага падтрымаць.",
        "🎨 Намалюй нешта і адправі сябру.",
        "🤝 Пазнаёмся сёння з новым чалавекам.",
        "🌱 Дапамажы прыродзе: прыбяры смецце або пасадзі дрэва.",
        "💬 Напішы пост у сацсетках пра тое, што цябе радуе.",
        "🎧 Пачуй падкаст пра самаразвіццё 15 хвілін.",
        "🧩 Вывучы новую навык цягам гадзіны.",
        "🏗️ Распрацуй ідэю для стартапа і запішы.",
        "☀️ Пачні раніцу з удзячнасці і напішы 10 пунктаў.",
        "🍀 Знайдзі спосаб падарыць каму-небудзь усмешку.",
        "🔥 Зрабі сёння тое, чаго ты баяўся(лася).",
        "🛠️ Выправі дома тое, што даўно адкладаў(ла).",
        "💜 Прыдумай 3 спосабы зрабіць свет дабрэйшым.",
        "🌸 Купі сабе або сябру кветкі.",
        "🚴‍♂️ Зрабі доўгую прагулку або велапаездку.",
        "📅 Распіш план на месяц наперад.",
        "🧘‍♂️ Паспрабуй ёгу або новую практыку.",
        "🎤 Спявай любімую песню ўслых!",
        "✈️ Заплануй будучую паездку мары.",
        "🕊️ Зрабі ахвяраванне на дабрачыннасць.",
        "🍎 Падрыхтуй незвычайную страву сёння.",
        "🔑 Знайдзі рашэнне старой праблемы.",
        "🖋️ Напішы ліст сабе праз 5 гадоў.",
        "🤗 Абдымі блізкага чалавека і скажы, як цэніш яго.",
        "🏞️ Правядзі гадзіну на прыродзе без тэлефона.",
        "📖 Знайдзі новую цытату і запомні яе.",
        "🎬 Паглядзі фільм, які даўно хацеў(ла).",
        "🛌 Лажыся спаць на гадзіну раней сёння.",
        "📂 Перабяры свае фатаграфіі і зрабі альбом.",
        "📈 Распрацуй стратэгію паляпшэння сябе.",
        "🎮 Паграй у гульню, якую яшчэ не спрабаваў(ла).",
        "🖼️ Ствары дошку візуалізацыі сваёй мары.",
        "🌟 Знайдзі спосаб некага натхніць.",
        "🔔 Устанаві карыснае напамінанне.",
        "💌 Напішы падзяку 3 людзям.",
        "🧩 Разгадай крыжаванку або судоку.",
        "🏋️‍♂️ Зрабі трэніроўку, якую даўно хацеў(ла)."
    ],
    "kk": [
        "🔥 Бүгін бейтаныс адамға жақсылық жаса.",
        "🌟 5 мықты жағыңды жазып, досыңа айтып бер.",
        "💎 Жаңа кітап тауып, кем дегенде 1 тарауын оқы.",
        "🚀 Келесі аптаға нақты мақсаттармен жоспар құр.",
        "🎯 Үлкен арманыңа бір қадам жаса.",
        "🙌 Досыңа немесе әріптесіңе көмектесудің жолын тап.",
        "💡 Жаңа шағын жоба ойлап тауып, басташы.",
        "🏃 Әдеттегіден 5 минут көбірек жүгір.",
        "🧘‍♀️ 10 минут терең медитация жаса.",
        "🖋️ Өзіңе шабыт берген адамға хат жаз.",
        "📚 Бүгін жаңа онлайн-курстан (кемінде 1 сабақ) өт.",
        "✨ Бүгін біреуді қолдау мүмкіндігін тап.",
        "🎨 Бірдеңе салып, досыңа жібер.",
        "🤝 Бүгін жаңа адаммен таныс.",
        "🌱 Табиғатқа көмектес: қоқыс жина немесе ағаш отырғыз.",
        "💬 Саған қуаныш сыйлайтын нәрсе туралы әлеуметтік желіде жаз.",
        "🎧 15 минуттай өзін-өзі дамыту подкастын тыңда.",
        "🧩 Бір сағат бойы жаңа дағдыны үйрен.",
        "🏗️ Стартапқа арналған идея ойлап тауып, жаз.",
        "☀️ Таңды алғыс айтудан бастап, 10 пункт жаз.",
        "🍀 Біреуді күлдірту жолын тап.",
        "🔥 Бүгін қорқатын нәрсеңді жаса.",
        "🛠️ Үйде көптен бері істемей жүрген дүниені жөнде.",
        "💜 Әлемді жақсартудың 3 жолын ойлап тап.",
        "🌸 Өзіңе немесе досыңа гүл ал.",
        "🚴‍♂️ Ұзақ серуенде немесе велосипедпен жүр.",
        "📅 Бір айға алдын ала жоспар жаса.",
        "🧘‍♂️ Йога немесе жаңа практиканы байқап көр.",
        "🎤 Ұнайтын әніңді дауыстап айт!",
        "✈️ Арман сапарын жоспарла.",
        "🕊️ Қайырымдылыққа ақша аудар.",
        "🍎 Бүгін ерекше тағам дайында.",
        "🔑 Ескі мәселені шешудің жолын тап.",
        "🖋️ Өзіңе 5 жылдан кейін жазатын хат жаз.",
        "🤗 Жақын адамды құшақтап, қадірлейтініңді айт.",
        "🏞️ Телефонсыз табиғатта бір сағат өткіз.",
        "📖 Жаңа дәйексөз тауып, жаттап ал.",
        "🎬 Көптен бері көргің келген фильмді көр.",
        "🛌 Бүгін бір сағатқа ертерек ұйықта.",
        "📂 Суреттеріңді реттеп, альбом жаса.",
        "📈 Өзіңді дамыту стратегиясын құр.",
        "🎮 Бұрын ойнамаған ойынды ойна.",
        "🖼️ Арманыңның визуалды тақтасын жаса.",
        "🌟 Біреуді шабыттандырудың жолын тап.",
        "🔔 Пайдалы еске салғыш орнат.",
        "💌 3 адамға алғыс хат жаз.",
        "🧩 Кроссворд немесе судоку шеш.",
        "🏋️‍♂️ Көптен бері істегің келген жаттығуды жаса."
    ],
    "kg": [
        "🔥 Бүгүн бейтааныш адамга жакшылык жаса.",
        "🌟 5 күчтүү тарабыңды жазып, досуңа айт.",
        "💎 Жаңы китеп тап жана жок дегенде 1 бөлүм оку.",
        "🚀 Кийинки аптага максаттуу план түз.",
        "🎯 Чоң кыялга бир кадам жаса.",
        "🙌 Досуңа же кесиптешиңе жардам берүүнүн жолун тап.",
        "💡 Жаңы чакан долбоорду ойлоп таап, башта.",
        "🏃 Кадимкидейден 5 мүнөт көбүрөөк чурка.",
        "🧘‍♀️ 10 мүнөт терең медитация жаса.",
        "🖋️ Сага дем берген адамга кат жаз.",
        "📚 Бүгүн жаңы онлайн-курстан (жок дегенде 1 сабак) өт.",
        "✨ Бүгүн кимдир бирөөгө жардам берүүнү тап.",
        "🎨 Бир нерсе тарт жана досуңа жөнөт.",
        "🤝 Бүгүн жаңы адам менен таанышууну көздө.",
        "🌱 Табиятка жардам бер: таштанды чогулт же дарак отургуз.",
        "💬 Сага кубаныч тартуулаган нерсе жөнүндө социалдык тармакта жаз.",
        "🎧 15 мүнөт өзүн өнүктүрүү подкастын угууну унутпа.",
        "🧩 Бир саат бою жаңы көндүмдү үйрөн.",
        "🏗️ Стартап идея ойлоп таап, жаз.",
        "☀️ Эртең менен рахмат айтып, 10 пункт жаз.",
        "🍀 Бирөөнү жылмайтуунун жолун тап.",
        "🔥 Бүгүн корккон нерсеңди жаса.",
        "🛠️ Үйдө көптөн бери жасалбай жаткан ишти бүтүр.",
        "💜 Дүйнөнү жакшы кылуунун 3 жолун ойлоп тап.",
        "🌸 Өзіңө же досуңа гүл сатып ал.",
        "🚴‍♂️ Узун сейил же велосипед айда.",
        "📅 Бир айга алдын ала план түз.",
        "🧘‍♂️ Йога же жаңы практиканы байка.",
        "🎤 Жаккан ырды үн катуу ырда!",
        "✈️ Кыял сапарыңды планда.",
        "🕊️ Кайрымдуулукка жардам бер.",
        "🍎 Бүгүн өзгөчө тамак даярда.",
        "🔑 Эски маселени чечүүнүн жолун тап.",
        "🖋️ 5 жылдан кийин өзүңө кат жаз.",
        "🤗 Жакын адамыңды кучактап, баалай турганыңды айт.",
        "🏞️ Телефонсуз табиятта бир саат бол.",
        "📖 Жаңы цитатаны таап, жаттап ал.",
        "🎬 Көптөн бери көргүң келген тасманы көр.",
        "🛌 Бүгүн бир саат эрте укта.",
        "📂 Сүрөттөрдү ирээттеп, альбом түз.",
        "📈 Өзүн өнүктүрүү стратегиясын иштеп чык.",
        "🎮 Мурун ойнобогон оюнду ойно.",
        "🖼️ Кыялыңдын визуалдык тактасын түз.",
        "🌟 Бирөөнү шыктандыруунун жолун тап.",
        "🔔 Пайдалы эскертме кой.",
        "💌 3 адамга ыраазычылык кат жаз.",
        "🧩 Кроссворд же судоку чеч.",
        "🏋️‍♂️ Көптөн бери жасагың келген машыгууну жаса."
    ],
    "hy": [
        "🔥 Այսօր բարիք արա անծանոթի համար։",
        "🌟 Գրիր քո 5 ուժեղ կողմերը և պատմիր ընկերոջդ։",
        "💎 Գտիր նոր գիրք և կարդա առնվազն մեկ գլուխ։",
        "🚀 Կազմիր հաջորդ շաբաթվա հստակ նպատակներով պլան։",
        "🎯 Քայլ արա դեպի մեծ երազանքդ։",
        "🙌 Գտիր եղանակ ընկերոջ կամ գործընկերոջ օգնելու։",
        "💡 Հորինիր և սկսիր նոր փոքր նախագիծ։",
        "🏃 Վազիր 5 րոպե ավելի, քան սովորաբար։",
        "🧘‍♀️ Կատարիր 10 րոպե խորը մեդիտացիա։",
        "🖋️ Գրիր նամակ այն մարդուն, ով քեզ ոգեշնչել է։",
        "📚 Այսօր անցիր նոր առցանց դասընթաց (առնվազն 1 դաս)։",
        "✨ Այսօր գտիր հնարավորութուն մեկին աջակցելու։",
        "🎨 Որևէ բան նկարիր ու ուղարկիր ընկերոջդ։",
        "🤝 Այսօր ծանոթացիր նոր մարդու հետ։",
        "🌱 Օգնիր բնությանը՝ աղբ հավաքիր կամ ծառ տնկիր։",
        "💬 Գրի սոցիալական ցանցում այն մասին, ինչ քեզ ուրախացնում է։",
        "🎧 Լսիր ինքնազարգացման փոդքասթ 15 րոպե։",
        "🧩 Մեկ ժամ ուսումնասիրիր նոր հմտություն։",
        "🏗️ Մշակի՛ր ստարտափի գաղափար և գրի։",
        "☀️ Առավոտը սկսիր երախտագիտությամբ և գրիր 10 կետ։",
        "🍀 Գտիր ինչ-որ մեկին ժպտացնելու եղանակ։",
        "🔥 Այսօր արա այն, ինչից վախենում էիր։",
        "🛠️ Տանը վերանորոգիր մի բան, որ վաղուց չէիր անում։",
        "💜 Մտածիր աշխարհի բարելավման 3 եղանակ։",
        "🌸 Գնի՛ր քեզ կամ ընկերոջդ ծաղիկ։",
        "🚴‍♂️ Քայլիր երկար կամ հեծանիվ վարիր։",
        "📅 Կազմիր պլան մեկ ամսով առաջ։",
        "🧘‍♂️ Փորձիր յոգա կամ նոր պրակտիկա։",
        "🎤 Բարձրաձայն երգիր սիրելի երգդ։",
        "✈️ Պլանավորի՛ր երազանքների ճամփորդություն։",
        "🕊️ Նվիրաբերիր բարեգործությանը։",
        "🍎 Պատրաստիր անսովոր ուտեստ այսօր։",
        "🔑 Գտիր հին խնդրի լուծումը։",
        "🖋️ Գրիր նամակ քեզ՝ 5 տարի հետո կարդալու համար։",
        "🤗 Գրկիր հարազատիդ և ասա, թե ինչքան ես գնահատում։",
        "🏞️ Ժամ անցկացրու բնության գրկում առանց հեռախոսի։",
        "📖 Գտիր նոր մեջբերում և հիշիր այն։",
        "🎬 Դիտիր ֆիլմ, որ վաղուց ուզում էիր։",
        "🛌 Այսօր մեկ ժամ շուտ գնա քնելու։",
        "📂 Դասավորիր լուսանկարներդ և ալբոմ ստեղծիր։",
        "📈 Մշակի՛ր ինքնազարգացման ռազմավարություն։",
        "🎮 Խաղա մի խաղ, որ երբեք չես փորձել։",
        "🖼️ Ստեղծիր երազանքներիդ վիզուալ տախտակ։",
        "🌟 Գտիր մեկին ոգեշնչելու եղանակ։",
        "🔔 Կարգավորի՛ր օգտակար հիշեցում։",
        "💌 Գրիր շնորհակալական նամակ 3 մարդու։",
        "🧩 Լուծիր խաչբառ կամ սուդոկու։",
        "🏋️‍♂️ Կատարիր մարզում, որ վաղուց ուզում էիր։"
    ],
    "ce": [
        "🔥 Хьо шу бахьара вац ло къобал дойла цуьнан хьуна.",
        "🌟 Дахьара йу 5 цуьнан хийц а, кхетам сагIа хьуна ву.",
        "💎 Ца йу ктаб цаьна йа, йоза тара цуьнан хийц.",
        "🚀 Кхети цуьнан догIар гIир хетам догIара хьо.",
        "🎯 Хаьна догIар гIир хетам къобал къахета.",
        "🙌 Далат хьо кхети ца хьо ву, са къахетам хетам.",
        "💡 Хьо къобал дойла ю, хьо йа ву вуьйре.",
        "🏃 Чун къобал 5 минут цаьна хийц.",
        "🧘‍♀️ 10 минут догIар медитация цуьнан хийц.",
        "🖋️ Хьо хьа йиш ю а, цуьнан хийц а хьо къобал ду.",
        "📚 Бугун ца онлайн-курс цаьна хийц (йу дойла йа).",
        "✨ Бугун йу хьо къахетам ю, хьо хетам.",
        "🎨 Хьо дойла ца а, кхетам сагIа хьуна ву.",
        "🤝 Бугун кхетам ца хьо хетам.",
        "🌱 Табигат догIар, цуьнан хийц къобал ца.",
        "💬 Са соцсети ю ца а, къобал цуьнан хийц.",
        "🎧 15 минут ца догIар подкаст йозан.",
        "🧩 1 саат ца къобал хийц.",
        "🏗️ Стартап идеа ца хийц, къахета.",
        "☀️ Хьо дуьйна алгыс а къахета, 10 къахета.",
        "🍀 Са къахета, йиш дойла а хьо.",
        "🔥 Кхетам бугун цуьнан хийц.",
        "🛠️ Г1айна къобал хийц.",
        "💜 3 къахета хьо цуьнан хийц.",
        "🌸 Хьо къобал дойла ю, кхетам ю а хьо.",
        "🚴‍♂️ ДогIар прогулка ца хийц.",
        "📅 1 йи са къобал хийц.",
        "🧘‍♂️ Йога ца хийц.",
        "🎤 Йу къобал цуьнан хийц.",
        "✈️ Арман йу къобал ца.",
        "🕊️ Благотворительность къобал хийц.",
        "🍎 Бу къобал цуьнан хийц.",
        "🔑 Старая проблема къахета.",
        "🖋️ 5 цуьнан хийц а къахета.",
        "🤗 Близкий адам къобал хийц.",
        "🏞️ Табигат даьлча къахета.",
        "📖 Цуьнан хийц а хьо къахета.",
        "🎬 Бу къобал хийц.",
        "🛌 Са къобал хийц.",
        "📂 Фото къахета.",
        "📈 Развитие стратегия хийц.",
        "🎮 Ойын къобал хийц.",
        "🖼️ Визуализация доск къахета.",
        "🌟 Къахета хьо хетам.",
        "🔔 Еске салғыш орнат.",
        "💌 3 адамға алғыс хат жаз.",
        "🧩 Кроссворд не судоку шеш.",
        "🏋️‍♂️ Көптен бері істегің келген жаттығуды жаса."
    ],
    "md": [
        "🔥 Fă o faptă bună pentru un străin astăzi.",
        "🌟 Scrie 5 calități ale tale și povestește unui prieten.",
        "💎 Găsește o carte nouă și citește cel puțin un capitol.",
        "🚀 Fă un plan pentru săptămâna viitoare cu obiective clare.",
        "🎯 Fă un pas spre un vis mare.",
        "🙌 Găsește o cale de a ajuta un prieten sau coleg.",
        "💡 Inventază și începe un nou mic proiect.",
        "🏃 Aleargă cu 5 minute mai mult ca de obicei.",
        "🧘‍♀️ Fă o meditație profundă de 10 minute.",
        "🖋️ Scrie o scrisoare cuiva care te-a inspirat.",
        "📚 Fă azi un curs online nou (cel puțin 1 lecție).",
        "✨ Găsește azi o ocazie de a susține pe cineva.",
        "🎨 Desenează ceva și trimite unui prieten.",
        "🤝 Fă cunoștință azi cu o persoană nouă.",
        "🌱 Ajută natura: strânge gunoi sau plantează un copac.",
        "💬 Scrie pe rețele ce te face fericit.",
        "🎧 Ascultă 15 min. podcast de dezvoltare personală.",
        "🧩 Învață o abilitate nouă timp de o oră.",
        "🏗️ Dezvoltă o idee de startup și noteaz-o.",
        "☀️ Începe dimineața cu recunoștință, scrie 10 puncte.",
        "🍀 Găsește o cale să faci pe cineva să zâmbească.",
        "🔥 Fă azi ceva ce îți era frică să faci.",
        "🛠️ Repară ceva acasă ce amâni de mult.",
        "💜 Gândește 3 moduri să faci lumea mai bună.",
        "🌸 Cumpără flori pentru tine sau prieten.",
        "🚴‍♂️ Fă o plimbare lungă sau o tură cu bicicleta.",
        "📅 Fă un plan pe o lună înainte.",
        "🧘‍♂️ Încearcă yoga sau o practică nouă.",
        "🎤 Cântă melodia preferată cu voce tare!",
        "✈️ Planifică o călătorie de vis.",
        "🕊️ Donează pentru caritate.",
        "🍎 Gătește ceva deosebit azi.",
        "🔑 Găsește o soluție la o problemă veche.",
        "🖋️ Scrie-ți o scrisoare pentru peste 5 ani.",
        "🤗 Îmbrățișează pe cineva drag și spune cât îl apreciezi.",
        "🏞️ Petrece o oră în natură fără telefon.",
        "📖 Găsește o nouă citat și memorează-l.",
        "🎬 Privește un film pe care îl voiai demult.",
        "🛌 Culcă-te cu o oră mai devreme azi.",
        "📂 Sortează pozele și fă un album.",
        "📈 Fă o strategie de dezvoltare personală.",
        "🎮 Joacă un joc nou pentru tine.",
        "🖼️ Fă un panou vizual cu visele tale.",
        "🌟 Găsește o cale să inspiri pe cineva.",
        "🔔 Setează o notificare utilă.",
        "💌 Scrie un mesaj de mulțumire la 3 oameni.",
        "🧩 Rezolvă un rebus sau sudoku.",
        "🏋️‍♂️ Fă antrenamentul pe care îl vrei demult."
    ],
    "ka": [
        "🔥 დღეს კეთილი საქმე გააკეთე უცხოსთვის.",
        "🌟 ჩაწერე შენი 5 ძლიერი მხარე და მოუყევი მეგობარს.",
        "💎 მოძებნე ახალი წიგნი და წაიკითხე ერთი თავი მაინც.",
        "🚀 შეადგინე შემდეგი კვირის გეგმა კონკრეტული მიზნებით.",
        "🎯 გადადგი ნაბიჯი დიდი ოცნებისკენ.",
        "🙌 იპოვე გზა, დაეხმარო მეგობარს ან კოლეგას.",
        "💡 გამოიგონე და დაიწყე ახალი მცირე პროექტი.",
        "🏃 ირბინე 5 წუთით მეტი, ვიდრე ჩვეულებრივ.",
        "🧘‍♀️ გააკეთე 10 წუთიანი ღრმა მედიტაცია.",
        "🖋️ წერილი მისწერე ადამიანს, ვინც შეგიძინა.",
        "📚 გაიარე ახალი ონლაინ კურსი (მინიმუმ ერთი გაკვეთილი).",
        "✨ იპოვე შესაძლებლობა, ვინმეს დაეხმარო დღეს.",
        "🎨 დახატე რამე და გაუგზავნე მეგობარს.",
        "🤝 დღეს გაიცანი ახალი ადამიანი.",
        "🌱 დაეხმარე ბუნებას: დაალაგე ნაგავი ან დარგე ხე.",
        "💬 დაწერე სოციალურ ქსელში, რა გიხარია.",
        "🎧 მოუსმინე 15 წუთით თვითგანვითარების პოდკასტს.",
        "🧩 ისწავლე ახალი უნარი ერთი საათის განმავლობაში.",
        "🏗️ შეიმუშავე სტარტაპის იდეა და ჩაიწერე.",
        "☀️ დილა დაიწყე მადლიერებით და ჩამოწერე 10 მიზეზი.",
        "🍀 იპოვე გზა, გაახარო ვინმე.",
        "🔥 გააკეთე ის, რისიც გეშინოდა.",
        "🛠️ სახლში ის გააკეთე, რასაც დიდხანს აჭიანურებდი.",
        "💜 იფიქრე სამყაროს უკეთესობისკენ შეცვლის 3 გზაზე.",
        "🌸 იყიდე ყვავილები შენთვის ან მეგობრისთვის.",
        "🚴‍♂️ გააკეთე გრძელი გასეირნება ან ველოსიპედით სიარული.",
        "📅 მოიფიქრე გეგმა ერთი თვით წინ.",
        "🧘‍♂️ სცადე იოგა ან ახალი პრაქტიკა.",
        "🎤 ხმამაღლა იმღერე საყვარელი სიმღერა!",
        "✈️ დაგეგმე საოცნებო მოგზაურობა.",
        "🕊️ გაიღე საქველმოქმედოდ.",
        "🍎 მოამზადე განსხვავებული კერძი დღეს.",
        "🔑 მოძებნე ძველი პრობლემის გადაწყვეტა.",
        "🖋️ წერილი მისწერე საკუთარ თავს 5 წელიწადში.",
        "🤗 ჩაეხუტე ახლობელს და უთხარი, რამდენად აფასებ მას.",
        "🏞️ ერთი საათი ბუნებაში გაატარე ტელეფონის გარეშე.",
        "📖 მოძებნე ახალი ციტატა და დაიმახსოვრე.",
        "🎬 უყურე ფილმს, რომელიც დიდი ხანია გინდა.",
        "🛌 დღეს ერთი საათით ადრე დაიძინე.",
        "📂 დაალაგე ფოტოები და შექმენი ალბომი.",
        "📈 შეიმუშავე თვითგანვითარების სტრატეგია.",
        "🎮 ითამაშე თამაში, რომელიც ჯერ არ გითამაშია.",
        "🖼️ შექმენი შენი ოცნების ვიზუალური დაფა.",
        "🌟 იპოვე გზა, რომ ვინმე შთააგონო.",
        "🔔 დააყენე სასარგებლო შეხსენება.",
        "💌 სამ ადამიანს მადლობის წერილი მიწერე.",
        "🧩 ამოხსენი კროსვორდი ან სუდოკუ.",
        "🏋️‍♂️ გააკეთე ის ვარჯიში, რასაც დიდი ხანია გეგმავდი."
    ],
}

POLL_MESSAGES_BY_LANG = {
    "ru": [
        "📝 Как ты оцениваешь свой день по шкале от 1 до 10?",
        "💭 Что сегодня тебя порадовало?",
        "🌿 Был ли сегодня момент, когда ты почувствовал(а) благодарность?",
        "🤔 Если бы ты мог(ла) изменить одну вещь в этом дне, что бы это было?",
        "💪 Чем ты сегодня гордишься?",
        "🤔 Что нового ты попробовал(а) сегодня?",
        "📝 О чём ты мечтаешь прямо сейчас?",
        "🌟 За что ты можешь себя сегодня похвалить?",
        "💡 Какая идея пришла тебе в голову сегодня?",
        "🎉 Был ли сегодня момент, который вызвал улыбку?",
        "🌈 Какой момент дня был самым ярким для тебя?",
        "🫶 Кому бы ты хотел(а) сегодня сказать спасибо?",
        "💬 Было ли что-то, что тебя удивило сегодня?",
        "🌻 Как ты проявил(а) заботу о себе сегодня?",
        "😌 Было ли что-то, что помогло тебе расслабиться?",
        "🏆 Чего тебе удалось достичь сегодня, даже если это мелочь?",
        "📚 Чему новому ты научился(ась) за этот день?",
        "🧑‍🤝‍🧑 Был ли кто-то, кто тебя поддержал сегодня?",
        "🎁 Сделал(а) ли ты сегодня что-то приятное для другого человека?",
        "🎨 Какое творческое занятие тебе хотелось бы попробовать?"
    ],
    "uk": [
        "📝 Як ти оцінюєш свій день за шкалою від 1 до 10?",
        "💭 Що сьогодні тебе порадувало?",
        "🌿 Чи був сьогодні момент, коли ти відчув(ла) вдячність?",
        "🤔 Якби ти міг(могла) змінити щось у цьому дні, що б це було?",
        "💪 Чим ти сьогодні пишаєшся?",
        "🤔 Що нового ти спробував(ла) сьогодні?",
        "📝 Про що ти мрієш просто зараз?",
        "🌟 За що ти можеш себе сьогодні похвалити?",
        "💡 Яка ідея прийшла тобі сьогодні в голову?",
        "🎉 Чи був сьогодні момент, який викликав усмішку?",
        "🌈 Який момент дня був найяскравішим для тебе?",
        "🫶 Кому б ти хотів(ла) сьогодні подякувати?",
        "💬 Було щось, що тебе сьогодні здивувало?",
        "🌻 Як ти подбав(ла) про себе сьогодні?",
        "😌 Було щось, що допомогло тобі розслабитися?",
        "🏆 Чого тобі вдалося досягти сьогодні, навіть якщо це дрібниця?",
        "📚 Чого нового ти навчився(лася) за цей день?",
        "🧑‍🤝‍🧑 Чи була людина, яка тебе сьогодні підтримала?",
        "🎁 Чи зробив(ла) ти сьогодні щось приємне для іншої людини?",
        "🎨 Яке творче заняття ти хотів(ла) б спробувати?"
    ],
    "be": [
        "📝 Як ты ацэніш свой дзень па шкале ад 1 да 10?",
        "💭 Што сёння табе прынесла радасць?",
        "🌿 Быў сёння момант, калі ты адчуваў(ла) удзячнасць?",
        "🤔 Калі б ты мог(ла) змяніць нешта ў гэтым дні, што б гэта было?",
        "💪 Чым ты сёння ганарышся?",
        "🤔 Што новага ты паспрабаваў(ла) сёння?",
        "📝 Пра што ты марыш прама зараз?",
        "🌟 За што можаш сябе сёння пахваліць?",
        "💡 Якая ідэя прыйшла табе сёння ў галаву?",
        "🎉 Быў сёння момант, які выклікаў усмешку?",
        "🌈 Які момант дня быў самым яркім для цябе?",
        "🫶 Каму б ты хацеў(ла) сёння сказаць дзякуй?",
        "💬 Ці было нешта, што цябе сёння здзівіла?",
        "🌻 Як ты паклапаціўся(лася) пра сябе сёння?",
        "😌 Ці было нешта, што дапамагло табе расслабіцца?",
        "🏆 Чаго табе ўдалося дасягнуць сёння, нават калі гэта дробязь?",
        "📚 Чаму новаму ты навучыўся(лася) за гэты дзень?",
        "🧑‍🤝‍🧑 Ці быў хтосьці, хто цябе сёння падтрымаў?",
        "🎁 Ці зрабіў(ла) ты сёння нешта прыемнае для іншага чалавека?",
        "🎨 Якую творчую справу ты хацеў(ла) б паспрабаваць?"
    ],
    "kk": [
        "📝 Бүгінгі күніңді 1-ден 10-ға дейін қалай бағалайсың?",
        "💭 Бүгін не сені қуантты?",
        "🌿 Бүгін ризашылық сезімін сезінген сәт болды ма?",
        "🤔 Егер бір нәрсені өзгерте алсаң, не өзгертер едің?",
        "💪 Бүгін немен мақтанасың?",
        "🤔 Бүгін не жаңалықты байқап көрдің?",
        "📝 Қазір не армандайсың?",
        "🌟 Бүгін өзіңді не үшін мақтай аласың?",
        "💡 Бүгін қандай ой келді басыңа?",
        "🎉 Бүгін күлкі сыйлаған сәт болды ма?",
        "🌈 Бүгінгі күннің ең жарқын сәті қандай болды?",
        "🫶 Бүгін кімге алғыс айтқың келеді?",
        "💬 Бүгін не сені таң қалдырды?",
        "🌻 Бүгін өз-өзіңе қалай қамқорлық көрсеттің?",
        "😌 Бүгін сені тыныштандырған не болды?",
        "🏆 Бүгін қандай жетістікке жеттің, тіпті кішкентай болса да?",
        "📚 Бүгін не үйрендің?",
        "🧑‍🤝‍🧑 Бүгін сені кім қолдады?",
        "🎁 Бүгін басқа біреуге қуаныш сыйладың ба?",
        "🎨 Қандай шығармашылық іспен айналысып көргің келеді?",
    ],
    "kg": [
        "📝 Бүгүнкү күнүңдү 1ден 10го чейин кантип баалайсың?",
        "💭 Бүгүн сени эмне кубандырды?",
        "🌿 Бүгүн ыраазычылык сезген учуруң болду беле?",
        "🤔 Бул күндө бир нерсени өзгөртө алсаң, эмнени өзгөртмөксүң?",
        "💪 Бүгүн эмнеге сыймыктандың?",
        "🤔 Бүгүн жаңы эмне аракет кылдың?",
        "📝 Азыр эмнени кыялданып жатасың?",
        "🌟 Бүгүн өзүңдү эмне үчүн мактай аласың?",
        "💡 Бүгүн кандай идея келди?",
        "🎉 Бүгүн күлкү жараткан учур болду беле?",
        "🌈 Бүгүнкү күндүн эң жаркын учуру кандай болду?",
        "🫶 Бүгүн кимге рахмат айткың келет?",
        "💬 Бүгүн сага эмне сюрприз болду?",
        "🌻 Өзүңө кандай кам көрдүң бүгүн?",
        "😌 Эмне сага эс алууга жардам берди?",
        "🏆 Бүгүн кандай жетишкендик болду, майда болсо да?",
        "📚 Бүгүн эмне жаңы үйрөндүң?",
        "🧑‍🤝‍🧑 Бүгүн сени ким колдоду?",
        "🎁 Бүгүн башка бирөөгө жакшылык кылдыңбы?",
        "🎨 Кандай чыгармачыл ишти сынап көргүң келет?"
    ],
    "hy": [
        "📝 Ինչպե՞ս կգնահատես օրդ 1-ից 10 բալով:",
        "💭 Ի՞նչն էր այսօր քեզ ուրախացրել:",
        "🌿 Այսօր ունեցե՞լ ես երախտագիտության զգացում:",
        "🤔 Եթե կարողանայիր ինչ-որ բան փոխել այս օրը, ի՞նչ կփոխեիր:",
        "💪 Ի՞նչով ես այսօր հպարտացել:",
        "🤔 Ի՞նչ նոր բան փորձեցիր այսօր:"
        "📝 Ի՞նչ ես հիմա երազում:",
        "🌟 Ինչի՞ համար կարող ես այսօր քեզ գովել:",
        "💡 Այսօր ի՞նչ գաղափար ունեցար:",
        "🎉 Այսօր եղա՞վ պահ, որ քեզ ժպիտ պատճառեց:",
        "🌈 Ո՞ր պահն էր օրվա ամենապայծառը քեզ համար:",
        "🫶 Ում կուզեիր այսօր շնորհակալություն հայտնել:",
        "💬 Այսօր ինչ-որ բան զարմացրեց քեզ?",
        "🌻 Ինչպե՞ս հոգ տարար քեզ այսօր:",
        "😌 Ինչ-որ բան քեզ օգնե՞ց հանգստանալ այսօր:",
        "🏆 Ի՞նչ հաջողության հասար այսօր, թեկուզ փոքր:",
        "📚 Ի՞նչ նոր բան սովորեցիր այս օրը:",
        "🧑‍🤝‍🧑 Եղա՞վ մեկը, որ քեզ աջակցեց այսօր:",
        "🎁 Այսօր մեկ ուրիշի համար հաճելի բան արե՞լ ես:",
        "🎨 Ի՞նչ ստեղծագործական զբաղմունք կուզենայիր փորձել:"
    ],
    "ce": [
        "📝 Хьо кхетам ден цу юкъар 1-ден 10-га къаст?",
        "💭 Хьо къобалле цу юкъар хийца чох?",
        "🌿 Хийца дийцар дуьн дуьна хеташ дийца?",
        "🤔 Хьо хийца ву а юкъар хийца хьо ца?",
        "💪 Хьо хетам ден хийца чох?",
        "🤔 Хьо цуьнан кхети хийца долу?",
        "📝 Хьо хьалха дIаяц дахара ву?",
        "🌟 Со деза хьо цуьнан дезар хийцар?",
        "💡 Хьо цуьнан хийцар идея хийца?",
        "🎉 Цуьнан дог ду ахча, хьо хиларца хьун?",
        "🌈 Хьо цуьнан йиш ду барт мотт ду?",
        "🫶 Мац цуьнан деза шукар дар?",
        "💬 Хьо цуьнан дог ду хийцар, хийциг тIехьа?",
        "🌻 Хьо цуьнан цуьнан аьтто керла хийца?",
        "😌 Хьо цуьнан йиш ду барт кхетарна, хийца?",
        "🏆 Хьо цуьнан хила а хийца, ю аьтто деш ду?",
        "📚 Хьо цуьнан хила дог хийца?",
        "🧑‍🤝‍🧑 Хьо цуьнан хьалха къобаллийца?",
        "🎁 Хьо цуьнан хьалха дукъ йиш хийца?",
        "🎨 Хьо цуьнан хийца хила цуьнан кхетийца?"
    ],
    "md": [
        "📝 Cum îți apreciezi ziua de la 1 la 10?",
        "💭 Ce te-a bucurat astăzi?",
        "🌿 A fost azi un moment când ai simțit recunoștință?",
        "🤔 Dacă ai putea schimba ceva azi, ce ar fi?",
        "💪 Cu ce ești mândru(ă) azi?",
        "🤔 Ce lucru nou ai încercat azi?",
        "📝 Despre ce visezi chiar acum?",
        "🌟 Pentru ce poți să te lauzi astăzi?",
        "💡 Ce idee ți-a venit azi?",
        "🎉 A fost astăzi un moment care te-a făcut să zâmbești?",
        "🌈 Care a fost cel mai luminos moment al zilei?",
        "🫶 Cui ai vrea să-i mulțumești astăzi?",
        "💬 A fost ceva care te-a surprins azi?",
        "🌻 Cum ai avut grijă de tine azi?",
        "😌 A fost ceva care te-a ajutat să te relaxezi?",
        "🏆 Ce ai reușit să obții azi, chiar și ceva mic?",
        "📚 Ce ai învățat nou astăzi?",
        "🧑‍🤝‍🧑 A fost cineva care te-a susținut azi?",
        "🎁 Ai făcut ceva frumos pentru altcineva astăzi?",
        "🎨 Ce activitate creativă ai vrea să încerci?"
    ],
    "ka": [
        "📝 როგორ შეაფასებდი დღეს 1-დან 10-მდე?",
        "💭 რა გაგახარა დღეს?",
        "🌿 იყო დღეს მადლიერების წამი?",
        "🤔 თუ შეგეძლო დღეს რამე შეგეცვალა, რას შეცვლიდი?",
        "💪 რით იამაყე დღეს?",
        "🤔 რა ახალს სცადე დღეს?",
        "📝 რაზე ოცნებობ ამ წუთში?",
        "🌟 რისთვის შეგიძლია დღეს შენი თავი შეაქო?",
        "💡 რა იდეა მოგივიდა დღეს?",
        "🎉 იყო დღეს წამი, რომელმაც გაგაცინა?",
        "🌈 დღის ყველაზე ნათელი მომენტი რომელი იყო?",
        "🫶 ვის მოუნდებოდა მადლობის თქმა დღეს?",
        "💬 იყო რამე, რამაც გაგაკვირვა დღეს?",
        "🌻 როგორ იზრუნე საკუთარ თავზე დღეს?",
        "😌 იყო რამე, რამაც დაგამშვიდა დღეს?",
        "🏆 რა მიაღწიე დღეს, თუნდაც პატარა რამ?",
        "📚 რა ისწავლე დღეს ახალი?",
        "🧑‍🤝‍🧑 იყო ვინმე, ვინც მხარი დაგიჭირა დღეს?",
        "🎁 გაახარე ვინმე დღეს?",
        "🎨 რა შემოქმედებითი საქმიანობა გინდა სცადო?"
    ],
    "en": [
        "📝 How would you rate your day from 1 to 10?",
        "💭 What made you happy today?",
        "🌿 Was there a moment you felt gratitude today?",
        "🤔 If you could change one thing about today, what would it be?",
        "💪 What are you proud of today?",
        "🤔 What new thing did you try today?",
        "📝 What are you dreaming about right now?",
        "🌟 What can you praise yourself for today?",
        "💡 What idea came to you today?",
        "🎉 Was there a moment that made you smile today?",
        "🌈 What was the brightest moment of your day?",
        "🫶 Who would you like to thank today?",
        "💬 Was there something that surprised you today?",
        "🌻 How did you take care of yourself today?",
        "😌 Was there something that helped you relax today?",
        "🏆 What did you manage to achieve today, even if it was something small?",
        "📚 What did you learn today?",
        "🧑‍🤝‍🧑 Was there someone who supported you today?",
        "🎁 Did you do something nice for someone else today?",
        "🎨 What creative activity would you like to try?"
    ]
}

SUPPORT_MESSAGES_BY_LANG = {
    "ru": [
        "💜 Ты делаешь этот мир лучше просто тем, что в нём есть.",
        "🌞 Сегодня новый день, и он полон возможностей — ты справишься!",
        "🤗 Обнимаю тебя мысленно. Ты не один(а).",
        "✨ Даже если трудно — помни, ты уже многого добился(ась)!",
        "💫 У тебя есть всё, чтобы пройти через это. Верю в тебя!",
        "🫶 Как здорово, что ты есть. Ты очень важный(ая) человек.",
        "🔥 Сегодня — хороший день, чтобы гордиться собой!",
        "🌈 Если вдруг устал(а) — просто сделай паузу и выдохни. Это нормально.",
        "😊 Улыбнись себе в зеркало. Ты классный(ая)!",
        "💡 Помни: каждый день ты становишься сильнее.",
        "🍀 Твои чувства важны. Ты важен(важна).",
        "💛 Ты заслуживаешь любви и заботы — и от других, и от себя.",
        "🌟 Спасибо тебе за то, что ты есть. Серьёзно.",
        "🤍 Даже маленький шаг вперёд — уже победа.",
        "💌 Ты приносишь в мир тепло. Не забывай об этом!",
        "✨ Верь себе. Ты уже столько прошёл(а) — и справился(ась)!",
        "🙌 Сегодня — твой день. Делай то, что делает тебя счастливым(ой).",
        "🌸 Порадуй себя чем‑то вкусным или приятным. Ты этого достоин(а).",
        "🏞️ Просто напоминание: ты невероятный(ая), и я рядом.",
        "🎶 Пусть музыка сегодня согреет твою душу.",
        "🤝 Не бойся просить о поддержке — ты не один(а).",
        "🔥 Вспомни, сколько всего ты преодолел(а). Ты силён(сильна)!",
        "🦋 Сегодня — шанс сделать что‑то доброе для себя.",
        "💎 Ты уникален(а), таких как ты больше нет.",
        "🌻 Даже если день не идеален — ты всё равно светишься.",
        "💪 Ты умеешь больше, чем думаешь. Верю в тебя!",
        "🍫 Порадуй себя мелочью — ты этого заслуживаешь.",
        "🎈 Пусть твой день будет лёгким и добрым.",
        "💭 Если есть мечта — помни, что ты можешь к ней прийти.",
        "🌊 Ты как океан — глубже и сильнее, чем кажется.",
        "🕊️ Пусть сегодня будет хотя бы один момент, который заставит тебя улыбнуться."
    ],
    "uk": [
        "💜 Ти робиш цей світ кращим просто тим, що ти в ньому.",
        "🌞 Сьогодні новий день, і він повний можливостей — ти впораєшся!",
        "🤗 Обіймаю тебе подумки. Ти не один(а).",
        "✨ Навіть якщо важко — пам’ятай, ти вже багато чого досяг(ла)!",
        "💫 У тебе є все, щоб пройти це. Вірю в тебе!",
        "🫶 Як добре, що ти є. Ти дуже важлива людина.",
        "🔥 Сьогодні — гарний день, щоб пишатися собою!",
        "🌈 Якщо раптом втомився(лася) — просто зроби паузу і видихни. Це нормально.",
        "😊 Посміхнись собі у дзеркало. Ти класний(а)!",
        "💡 Пам’ятай: щодня ти стаєш сильнішим(ою).",
        "🍀 Твої почуття важливі. Ти важливий(а).",
        "💛 Ти заслуговуєш любові і турботи — і від інших, і від себе.",
        "🌟 Дякую тобі за те, що ти є. Серйозно.",
        "🤍 Навіть маленький крок вперед — вже перемога.",
        "💌 Ти приносиш у світ тепло. Не забувай про це!",
        "✨ Вір у себе. Ти вже стільки всього пройшов(ла) — і впорався(лася)!",
        "🙌 Сьогодні — твій день. Робі те, що робить тебе щасливим(ою).",
        "🌸 Потіш себе чимось смачним або приємним. Ти цього вартий(а).",
        "🏞️ Просто нагадування: ти неймовірний(а), і я поруч.",
        "🎶 Нехай музика сьогодні зігріє твою душу.",
        "🤝 Не бійся просити про підтримку — ти не один(а).",
        "🔥 Згадай, скільки всього ти подолав(ла). Ти сильний(а)!",
        "🦋 Сьогодні — шанс зробити щось добре для себе.",
        "💎 Ти унікальний(а), таких як ти більше нема.",
        "🌻 Навіть якщо день не ідеальний — ти все одно сяєш.",
        "💪 Ти вмієш більше, ніж думаєш. Вірю в тебе!",
        "🍫 Потіш себе дрібницею — ти цього заслуговуєш.",
        "🎈 Нехай твій день буде легким і добрим.",
        "💭 Якщо є мрія — пам’ятай, що ти можеш до неї дійти.",
        "🌊 Ти як океан — глибший(а) і сильніший(а), ніж здається.",
        "🕊️ Нехай сьогодні буде хоча б одна мить, що викличе усмішку."
    ],
    "be": [
        "💜 Ты робіш гэты свет лепшым проста тым, што ты ў ім.",
        "🌞 Сёння новы дзень, і ён поўны магчымасцей — ты справішся!",
        "🤗 Абдымаю цябе думкамі. Ты не адзін(а).",
        "✨ Нават калі цяжка — памятай, ты ўжо шмат чаго дасягнуў(ла)!",
        "💫 У цябе ёсць усё, каб прайсці праз гэта. Веру ў цябе!",
        "🫶 Як добра, што ты ёсць. Ты вельмі важны(ая) чалавек.",
        "🔥 Сёння — добры дзень, каб ганарыцца сабой!",
        "🌈 Калі стаміўся(лася) — проста зрабі паўзу і выдыхні. Гэта нармальна.",
        "😊 Усміхніся сабе ў люстэрку. Ты класны(ая)!",
        "💡 Памятай: кожны дзень ты становішся мацнейшым(ай).",
        "🍀 Твае пачуцці важныя. Ты важны(ая).",
        "💛 Ты заслугоўваеш любові і клопату — і ад іншых, і ад сябе.",
        "🌟 Дзякуй табе за тое, што ты ёсць. Сапраўды.",
        "🤍 Нават маленькі крок наперад — ужо перамога.",
        "💌 Ты прыносіш у свет цяпло. Не забывай пра гэта!",
        "✨ Верь у сябе. Ты ўжо шмат прайшоў(ла) — і справіўся(лася)!",
        "🙌 Сёння — твой дзень. Рабі тое, што робіць цябе шчаслівым(ай).",
        "🌸 Парадуй сябе чымсьці смачным або прыемным. Ты гэтага варты(ая).",
        "🏞️ Проста напамін: ты неверагодны(ая), і я побач.",
        "🎶 Хай музыка сёння сагрэе тваю душу.",
        "🤝 Не бойся прасіць падтрымку — ты не адзін(а).",
        "🔥 Успомні, колькі ўсяго ты пераадолеў(ла). Ты моцны(ая)!",
        "🦋 Сёння — шанец зрабіць нешта добрае для сябе.",
        "💎 Ты ўнікальны(ая), такіх як ты няма.",
        "🌻 Нават калі дзень не ідэальны — ты ўсё роўна ззяеш.",
        "💪 Ты ўмееш больш, чым думаеш. Веру ў цябе!",
        "🍫 Парадуй сябе дробяззю — ты гэтага заслугоўваеш.",
        "🎈 Хай твой дзень будзе лёгкім і добрым.",
        "💭 Калі ёсць мара — памятай, што можаш яе дасягнуць.",
        "🌊 Ты як акіян — глыбейшы(ая) і мацнейшы(ая), чым здаецца.",
        "🕊️ Хай сёння будзе хоць адзін момант, які прымусіць цябе ўсміхнуцца."
    ],
    "kk": [
        "💜 Сен бұл әлемді жақсартасың, өйткені сен осындасың.",
        "🌞 Бүгін жаңа күн, толы мүмкіндіктерге — сен бәріне үлгересің!",
        "🤗 Ойша құшақтаймын. Сен жалғыз емессің.",
        "✨ Қиын болса да — сен қазірдің өзінде көп нәрсеге жеттің!",
        "💫 Бұл кезеңнен өтуге барлық күшің бар. Саған сенемін!",
        "🫶 Сен барсың — бұл тамаша! Сен маңызды адамсың.",
        "🔥 Бүгін — өзіңмен мақтанатын күн!",
        "🌈 Егер шаршасаң — аздап демал, бұл қалыпты жағдай.",
        "😊 Айнаға күлімде. Сен кереметсің!",
        "💡 Есіңде болсын: күн сайын сен күштірексің.",
        "🍀 Сенің сезімдерің маңызды. Сен де маңыздысың.",
        "💛 Сен махаббат пен қамқорлыққа лайықсың — басқалардан да, өзіңнен де.",
        "🌟 Саған рахмет, сен барсың.",
        "🤍 Бір қадам алға — бұл да жеңіс.",
        "💌 Сен әлемге жылу әкелесің. Мұны ұмытпа!",
        "✨ Өзіңе сен. Сен көп нәрсе бастан кешірдің — және бәрін еңсердің!",
        "🙌 Бүгін — сенің күнің. Өзіңді бақытты ететінді істе.",
        "🌸 Өзіңді тәтті нәрсемен қуант. Сен бұған лайықсың.",
        "🏞️ Еске салу: сен кереметсің және мен осындамын.",
        "🎶 Музыка бүгін жаныңды жылыта берсін.",
        "🤝 Қолдау сұраудан қорықпа — сен жалғыз емессің.",
        "🔥 Өткен жеңістеріңді есіңе ал. Сен мықтысың!",
        "🦋 Бүгін — өзің үшін жақсылық жасауға мүмкіндік.",
        "💎 Сен бірегейсің, сендей ешкім жоқ.",
        "🌻 Күнің мінсіз болмаса да — сен бәрібір жарқырайсың.",
        "💪 Сен ойлағаннан көп нәрсе жасай аласың. Саған сенемін!",
        "🍫 Өзіңді кішкене нәрсемен қуант — сен бұған лайықсың.",
        "🎈 Күнің жеңіл және жылы болсын.",
        "💭 Арманың болса — оған жетуге қабілетің бар екенін ұмытпа.",
        "🌊 Сен мұхиттай терең және мықтысың.",
        "🕊️ Бүгін кем дегенде бір сәт саған күлкі сыйласын."
    ],
    "kg": [
        "💜 Бул дүйнөнү жакшыраак кыласың, анткени сен барсың.",
        "🌞 Бүгүн — жаңы күн, мүмкүнчүлүктөргө толо — сен баарына жетишесиң!",
        "🤗 Ойлоп, кучактайм. Сен жалгыз эмессиң.",
        "✨ Кыйын болсо да — сен буга чейин эле көп нерсеге жетиштиң!",
        "💫 Бул жолдон өтүүгө күчүң жетет. Сага ишенемин!",
        "🫶 Сен барсың — бул сонун! Сен маанилүү адамсың.",
        "🔥 Бүгүн — өзүң менен сыймыктанууга күн!",
        "🌈 Эгер чарчасаң — дем ал, бул кадимки нерсе.",
        "😊 Көз айнекке жылмай. Сен сонунсуң!",
        "💡 Эсте: ар бир күн менен күчтөнөсүң.",
        "🍀 Сезимдериң маанилүү. Сен да маанилүү адамсың.",
        "💛 Сен сүйүүгө жана камкордукка татыктуусуң — башкалардан да, өзүңдөн да.",
        "🌟 Сен бар экениңе рахмат.",
        "🤍 Алга бир кадам — бул да жеңиш.",
        "💌 Сен дүйнөгө жылуулук алып келесиң. Бул тууралуу унутпа!",
        "✨ Өзүңө ишен. Көп нерседен өттүң — баарын жеңдиң!",
        "🙌 Бүгүн — сенин күнүң. Бактылуу кылган ишти жаса.",
        "🌸 Өзүңдү таттуу нерсе менен кубандыр. Сен татыктуусуң.",
        "🏞️ Эскертүү: сен укмушсуң жана мен жанымдамын.",
        "🎶 Музыка бүгүн жаныңды жылытсын.",
        "🤝 Колдоо суроодон тартынба — сен жалгыз эмессиң.",
        "🔥 Кайсы жеңиштериңди эстеп, сыймыктан.",
        "🦋 Бүгүн — өзүң үчүн жакшылык кылууга мүмкүнчүлүк.",
        "💎 Сен өзгөчөсүң, сендей башка адам жок.",
        "🌻 Күнүң идеалдуу болбосо да — сен жаркырайсың.",
        "💪 Сен ойлогондон да көптү жасай аласың. Сага ишенем!",
        "🍫 Өзүңдү майда нерсе менен кубандыр — сен татыктуусуң.",
        "🎈 Күнің жеңил жана жагымдуу болсун.",
        "💭 Кыялың болсо — ага жетүүгө күчүң бар экенин эсте.",
        "🌊 Сен океандай терең жана күчтүүсүң.",
        "🕊️ Бүгүн болбосо да, бир ирмем сени күлдүрсүн."
    ],
    "hy": [
        "💜 Դու այս աշխարհը ավելի լավը ես դարձնում, որովհետև դու այստեղ ես։",
        "🌞 Այսօր նոր օր է, լի հնարավորություններով — դու կարող ես ամեն ինչ։",
        "🤗 Մտքով գրկում եմ քեզ։ Դու մենակ չես։",
        "✨ Թեպետ դժվար է, հիշիր՝ արդեն շատ բան ես արել։",
        "💫 Դու ունես ամեն ինչ՝ այս ամենը հաղթահարելու համար։ Հավատում եմ քեզ։",
        "🫶 Որքան լավ է, որ դու կաս։ Դու շատ կարևոր մարդ ես։",
        "🔥 Այսօր հրաշալի օր է՝ քեզ վրա հպարտանալու համար։",
        "🌈 Եթե հանկարծ հոգնել ես՝ պարզապես հանգստացիր։ Դա նորմալ է։",
        "😊 Ժպտա հայելու առաջ։ Դու հիանալի ես։",
        "💡 Հիշիր՝ ամեն օր ուժեղանում ես։",
        "🍀 Քո զգացմունքները կարևոր են։ Դու կարևոր ես։",
        "💛 Դու արժանի ես սիրո և հոգածության՝ և ուրիշներից, և քեզանից։",
        "🌟 Շնորհակալ եմ, որ կաս։ Իրոք։",
        "🤍 Նույնիսկ փոքր քայլը առաջ՝ արդեն հաղթանակ է։",
        "💌 Դու աշխարհին ջերմություն ես բերում։ Մի մոռացիր դա։",
        "✨ Վստահիր քեզ։ Դու արդեն շատ բան ես հաղթահարել։",
        "🙌 Այսօր քո օրն է։ Արի՛ արա այն, ինչ քեզ երջանիկ է դարձնում։",
        "🌸 Հաճույք պատճառիր քեզ ինչ-որ համով կամ հաճելի բանով։ Դու դրա արժանի ես։",
        "🏞️ Հիշեցում՝ դու հիանալի ես և ես քո կողքին եմ։",
        "🎶 Թող երաժշտությունը այսօր ջերմացնի հոգիդ։",
        "🤝 Մի վախեցիր աջակցություն խնդրել՝ դու մենակ չես։",
        "🔥 Հիշիր քո հաղթանակները։ Դու ուժեղ ես։",
        "🦋 Այսօր հնարավորություն է՝ ինքդ քեզ լավ բան անելու։",
        "💎 Դու յուրահատուկ ես, քո նմանը չկա։",
        "🌻 Նույնիսկ եթե օրը կատարյալ չէ՝ դու փայլում ես։",
        "💪 Դու կարող ես ավելին, քան կարծում ես։ Հավատում եմ քեզ։",
        "🍫 Ուրախացրու քեզ փոքր բանով՝ դու արժանի ես դրան։",
        "🎈 Թող օրըդ թեթև ու ջերմ լինի։",
        "💭 Եթե երազանք ունես՝ հիշիր, որ կարող ես իրականացնել։",
        "🌊 Դու օվկիանոսի պես խորն ու ուժեղ ես։",
        "🕊️ Թող այսօր թեկուզ մեկ պահ քեզ ժպիտ պարգևի։"
    ],
    "ce": [
        "💜 Со хетам дийцар дуьн йоьлчу — хьо цу са.",
        "🌞 Ахкера йуь хетам дийца — хийц йойла а, цу ву а цу.",
        "🤗 Доьззаш хьо хьунал, хьо йу хила цу.",
        "✨ Къобал со дийн ду, ву хетам ца кхетам — хьо ийса мотт.",
        "💫 Хьо цу ха цуьнан. Со хетам хьо!.",
        "🫶 Хьо цу са, хийц оьзду хила. Хьо мотт.",
        "🔥 Ахкера — хийц дуьн чох дийца йойла хила цу.",
        "🌈 Хьо чух цу хийца — тержа дийцар, ву езар ду.",
        "😊 Дзира тIехь, хьо хила цу.",
        "💡 Со дийцар: хийца цхьаьнан ца цу са цу.",
        "🍀 Хьо хийцар мотт, хьо цу мотт.",
        "💛 Хьо хийцар бац, хьо хийцар лаьц.",
        "🌟 Со дийцар хьо цу са. Хетам дийцар.",
        "🤍 Юкъар йойла а — хийц ду йойла.",
        "💌 Хьо дуьн хийцар ду. Хьо хила хетам мотт.",
        "✨ Со хетам хьо хьунал. Хьо йу мотт ца а.",
        "🙌 Ахкера хьо дийцар ду. Хьо цу хьунал хила цу.",
        "🌸 Хьо цу дуьллар ду, хьо мотт цу.",
        "🏞️ Со дуьллар: хьо цу хила, со хетам цу.",
        "🎶 Мусика хьо дуьн хийцар ду.",
        "🤝 Хьо хийцар къобал хила — хьо хила цу.",
        "🔥 Со хийцар хьо йу мотт, хьо мотт.",
        "🦋 Ахкера — хийца хийцар цу.",
        "💎 Хьо хийца хийцар цу.",
        "🌻 Юкъар йойла — хьо хийцар мотт.",
        "💪 Хьо мотт, со хетам хьо!",
        "🍫 Хьо цу дуьллар ду.",
        "🎈 Хьо хийца хийцар мотт.",
        "💭 Хьо хийца хийцар мотт.",
        "🌊 Хьо хийца хийцар мотт.",
        "🕊️ Ахкера хьо хийцар мотт."
    ],
    "md": [
        "💜 Faci lumea asta mai bună doar pentru că exiști.",
        "🌞 Azi e o nouă zi, plină de oportunități — vei reuși!",
        "🤗 Te îmbrățișez cu gândul. Nu ești singur(ă).",
        "✨ Chiar dacă e greu — amintește-ți, ai reușit deja multe!",
        "💫 Ai tot ce-ți trebuie să treci peste asta. Cred în tine!",
        "🫶 Ești aici — și asta e minunat! Ești o persoană importantă.",
        "🔥 Azi e o zi bună să fii mândru(ă) de tine!",
        "🌈 Dacă te-ai obosit — ia o pauză, e normal.",
        "😊 Zâmbește-ți în oglindă. Ești grozav(ă)!",
        "💡 Ține minte: cu fiecare zi devii mai puternic(ă).",
        "🍀 Sentimentele tale contează. Tu contezi.",
        "💛 Meriți dragoste și grijă — de la alții și de la tine.",
        "🌟 Mulțumesc că exiști.",
        "🤍 Chiar și un pas mic înainte e o victorie.",
        "💌 Aduci căldură în lume. Nu uita asta!",
        "✨ Ai încredere în tine. Ai trecut prin multe și ai reușit!",
        "🙌 Azi e ziua ta. Fă ceea ce te face fericit(ă).",
        "🌸 Răsfață-te cu ceva gustos sau plăcut. Meriți.",
        "🏞️ Doar o amintire: ești incredibil(ă) și sunt aici.",
        "🎶 Lasă muzica să-ți încălzească sufletul azi.",
        "🤝 Nu-ți fie teamă să ceri ajutor — nu ești singur(ă).",
        "🔥 Gândește-te la toate pe care le-ai depășit. Ești puternic(ă)!",
        "🦋 Azi e o șansă să faci ceva bun pentru tine.",
        "💎 Ești unic(ă), nimeni nu mai e ca tine.",
        "🌻 Chiar dacă ziua nu e perfectă — tot strălucești.",
        "💪 Poți mai mult decât crezi. Cred în tine!",
        "🍫 Răsfață-te cu ceva mic — meriți asta.",
        "🎈 Să ai o zi ușoară și frumoasă.",
        "💭 Dacă ai un vis — amintește-ți că poți ajunge la el.",
        "🌊 Ești profund(ă) și puternic(ă) ca un ocean.",
        "🕊️ Sper ca azi să ai cel puțin un moment de bucurie."
    ],
    "ka": [
        "💜 შენ ამ სამყაროს უკეთესს ხდი უბრალოდ აქ რომ ხარ.",
        "🌞 დღეს ახალი დღეა, სავსე შესაძლებლობებით — ყველაფერს შეძლებ!",
        "🤗 აზროვნებით გეხვევი. მარტო არ ხარ.",
        "✨ თუ ძნელია — დაიმახსოვრე, უკვე ბევრი რამ გისწავლია!",
        "💫 გაქვს ყველაფერი, რომ ეს გზა გაიარო. მჯერა შენი!",
        "🫶 კარგია რომ არსებობ. შენ ძალიან მნიშვნელოვანი ადამიანი ხარ.",
        "🔥 დღეს კარგი დღეა, რომ საკუთარ თავზე იამაყო!",
        "🌈 თუ დაიღალე — დაისვენე, ეს ნორმალურია.",
        "😊 სარკეში გაუღიმე საკუთარ თავს. შენ შესანიშნავი ხარ!",
        "💡 დაიმახსოვრე: ყოველდღე უფრო ძლიერი ხდები.",
        "🍀 შენი გრძნობები მნიშვნელოვანია. შენ მნიშვნელოვანი ხარ.",
        "💛 იმსახურებ სიყვარულსა და ზრუნვას — სხვებისგანაც და საკუთარი თავისგანაც.",
        "🌟 გმადლობ რომ ხარ.",
        "🤍 ერთი პატარა ნაბიჯი წინ — უკვე გამარჯვებაა.",
        "💌 ამ სამყაროს სითბოს მატებ. არ დაივიწყო ეს!",
        "✨ ენდე საკუთარ თავს. უკვე ბევრი რამ გამოიარე და შეძლე!",
        "🙌 დღეს შენი დღეა. გააკეთე ის, რაც გაბედნიერებს.",
        "🌸 გაახარე თავი რამე გემრიელით ან სასიამოვნოთ. იმსახურებ ამას.",
        "🏞️ შეგახსენებ: უნიკალური ხარ და მე შენთან ვარ.",
        "🎶 მუსიკა დღეს გაათბოს შენი სული.",
        "🤝 არ შეგეშინდეს მხარდაჭერის თხოვნის — მარტო არ ხარ.",
        "🔥 გაიხსენე რისი გადალახვაც შეძლე. ძლიერი ხარ!",
        "🦋 დღეს შესაძლებლობაა შენთვის რამე კარგი გააკეთო.",
        "💎 უნიკალური ხარ, შენი მსგავსი არავინ არის.",
        "🌻 თუნდაც დღე იდეალური არ იყოს — მაინც ანათებ.",
        "💪 შეგიძლია მეტი, ვიდრე გგონია. მჯერა შენი!",
        "🍫 გაახარე თავი რამე პატარა რამით — იმსახურებ ამას.",
        "🎈 შენი დღე იყოს მსუბუქი და სასიამოვნო.",
        "💭 თუ გაქვს ოცნება — გახსოვდეს, შეგიძლია მას მიაღწიო.",
        "🌊 შენ ოკეანესავით ღრმა და ძლიერი ხარ.",
        "🕊️ იმედი მაქვს, დღევანდელი დღე გაგახარებს."
    ],
    "en": [
        "💜 You make this world a better place just by being in it.",
        "🌞 Today is a new day, full of opportunities — you’ve got this!",
        "🤗 Sending you a mental hug. You’re not alone.",
        "✨ Even if it’s hard — remember, you’ve already achieved so much!",
        "💫 You have everything you need to get through this. I believe in you!",
        "🫶 It’s wonderful that you’re here. You are an important person.",
        "🔥 Today is a great day to be proud of yourself!",
        "🌈 If you’re tired — take a break, that’s okay.",
        "😊 Smile at yourself in the mirror. You’re amazing!",
        "💡 Remember: you’re getting stronger every day.",
        "🍀 Your feelings matter. You matter.",
        "💛 You deserve love and care — from others and from yourself.",
        "🌟 Thank you for being you. Really.",
        "🤍 Even a small step forward is a victory.",
        "💌 You bring warmth to the world. Don’t forget it!",
        "✨ Believe in yourself. You’ve already come so far and made it through!",
        "🙌 Today is your day. Do what makes you happy.",
        "🌸 Treat yourself to something nice or tasty. You deserve it.",
        "🏞️ Just a reminder: you’re incredible, and I’m here.",
        "🎶 Let music warm your soul today.",
        "🤝 Don’t be afraid to ask for support — you’re not alone.",
        "🔥 Remember everything you’ve overcome. You’re strong!",
        "🦋 Today is a chance to do something kind for yourself.",
        "💎 You’re unique, there’s no one else like you.",
        "🌻 Even if the day isn’t perfect — you still shine.",
        "💪 You can do more than you think. I believe in you!",
        "🍫 Treat yourself to something little — you deserve it.",
        "🎈 May your day be easy and kind.",
        "💭 If you have a dream — remember, you can achieve it.",
        "🌊 You’re as deep and strong as the ocean.",
        "🕊️ May there be at least one moment today that makes you smile."
    ]
}

QUOTES_BY_LANG = {
    "ru": [
        "🌟 Успех — это сумма небольших усилий, повторяющихся день за днем.",
        "💪 Неважно, как медленно ты идёшь, главное — не останавливаться.",
        "🔥 Самый лучший день для начала — сегодня.",
        "💜 Ты сильнее, чем думаешь, и способнее, чем тебе кажется.",
        "🌱 Каждый день — новый шанс изменить свою жизнь.",
        "🚀 Не бойся идти медленно. Бойся стоять на месте.",
        "☀️ Сложные пути часто ведут к красивым местам.",
        "🦋 Делай сегодня то, за что завтра скажешь себе спасибо.",
        "✨ Твоя энергия привлекает твою реальность. Выбирай позитив.",
        "🙌 Верь в себя. Ты — самое лучшее, что у тебя есть.",
        "💜 Каждый день — новый шанс изменить свою жизнь.",
        "🌟 Твоя энергия создаёт твою реальность.",
        "🔥 Делай сегодня то, за что завтра скажешь себе спасибо.",
        "✨ Большие перемены начинаются с маленьких шагов.",
        "🌱 Ты сильнее, чем думаешь, и способен(на) на большее.",
        "☀️ Свет внутри тебя ярче любых трудностей.",
        "💪 Не бойся ошибаться — бойся не пробовать.",
        "🌊 Все бури заканчиваются, а ты становишься сильнее.",
        "🤍 Ты достоин(на) любви и счастья прямо сейчас.",
        "🚀 Твои мечты ждут, когда ты начнёшь действовать.",
        "🎯 Верь в процесс, даже если путь пока неясен.",
        "🧘‍♀️ Спокойный ум — ключ к счастливой жизни.",
        "🌸 Каждый момент — возможность начать заново.",
        "💡 Жизнь — это 10% того, что с тобой происходит, и 90% того, как ты на это реагируешь.",
        "❤️ Ты важен(на) и нужен(на) в этом мире.",
        "🌌 Делай каждый день немного для своей мечты.",
        "🙌 Ты заслуживаешь самого лучшего — верь в это.",
        "✨ Пусть сегодня будет началом чего-то великого.",
        "💎 Самое лучшее впереди — продолжай идти.",
        "🌿 Твои маленькие шаги — твоя великая сила."
    ],
    "uk": [
        "🌟 Успіх — це сума невеликих зусиль, що повторюються щодня.",
        "💪 Не важливо, як повільно ти йдеш, головне — не зупинятися.",
        "🔥 Найкращий день для початку — сьогодні.",
        "💜 Ти сильніший(а), ніж думаєш, і здатний(а) на більше.",
        "🌱 Кожен день — новий шанс змінити своє життя.",
        "🚀 Не бійся йти повільно. Бійся стояти на місці.",
        "☀️ Важкі дороги часто ведуть до красивих місць.",
        "🦋 Роби сьогодні те, за що завтра подякуєш собі.",
        "✨ Твоя енергія притягує твою реальність. Обирай позитив.",
        "🙌 Вір у себе. Ти — найкраще, що в тебе є.",
        "💜 Кожен день — новий шанс змінити своє життя.",
        "🌟 Твоя енергія створює твою реальність.",
        "🔥 Роби сьогодні те, за що завтра подякуєш собі.",
        "✨ Великі зміни починаються з маленьких кроків.",
        "🌱 Ти сильніший(а), ніж здається, і здатний(а) на більше.",
        "☀️ Світло в тобі яскравіше будь-яких труднощів.",
        "💪 Не бійся помилятися — бійся не спробувати.",
        "🌊 Усі бурі минають, а ти стаєш сильнішим(ою).",
        "🤍 Ти гідний(а) любові та щастя прямо зараз.",
        "🚀 Твої мрії чекають, коли ти почнеш діяти.",
        "🎯 Вір у процес, навіть якщо шлях поки незрозумілий.",
        "🧘‍♀️ Спокійний розум — ключ до щасливого життя.",
        "🌸 Кожна мить — можливість почати знову.",
        "💡 Життя — це 10% того, що з тобою відбувається, і 90% того, як ти на це реагуєш.",
        "❤️ Ти важливий(а) та потрібний(а) у цьому світі.",
        "🌌 Щодня роби трохи для своєї мрії.",
        "🙌 Ти заслуговуєш на найкраще — вір у це.",
        "✨ Нехай сьогодні стане початком чогось великого.",
        "💎 Найкраще попереду — продовжуй іти.",
        "🌿 Твої маленькі кроки — твоя велика сила."
    ],
    "be": [
        "🌟 Поспех — гэта сума невялікіх намаганняў, якія паўтараюцца штодня.",
        "💪 Не важна, як павольна ты ідзеш, галоўнае — не спыняцца.",
        "🔥 Лепшы дзень для пачатку — сёння.",
        "💜 Ты мацнейшы(ая), чым думаеш, і здольны(ая) на большае.",
        "🌱 Кожны дзень — новы шанец змяніць сваё жыццё.",
        "🚀 Не бойся ісці павольна. Бойся стаяць на месцы.",
        "☀️ Складаныя шляхі часта вядуць да прыгожых месцаў.",
        "🦋 Рабі сёння тое, за што заўтра скажаш сабе дзякуй.",
        "✨ Твая энергія прыцягвае тваю рэальнасць. Абірай пазітыў.",
        "🙌 Верь у сябе. Ты — лепшае, што ў цябе ёсць.",
        "💜 Кожны дзень — новы шанец змяніць сваё жыццё.",
        "🌟 Твая энергія стварае тваю рэальнасць.",
        "🔥 Рабі сёння тое, за што заўтра скажаш сабе дзякуй.",
        "✨ Вялікія перамены пачынаюцца з маленькіх крокаў.",
        "🌱 Ты мацнейшы(ая), чым здаецца, і здольны(ая) на большае.",
        "☀️ Святло ў табе ярчэй за ўсе цяжкасці.",
        "💪 Не бойся памыляцца — бойся не паспрабаваць.",
        "🌊 Усе буры мінаюць, а ты становішся мацнейшым(ай).",
        "🤍 Ты годны(ая) любові і шчасця ўжо цяпер.",
        "🚀 Твае мары чакаюць, калі ты пачнеш дзейнічаць.",
        "🎯 Верь у працэс, нават калі шлях пакуль незразумелы.",
        "🧘‍♀️ Спакойны розум — ключ да шчаслівага жыцця.",
        "🌸 Кожны момант — магчымасць пачаць зноў.",
        "💡 Жыццё — гэта 10% таго, што з табой адбываецца, і 90% таго, як ты на гэта рэагуеш.",
        "❤️ Ты важны(ая) і патрэбны(ая) ў гэтым свеце.",
        "🌌 Рабі кожны дзень трошкі для сваёй мары.",
        "🙌 Ты заслугоўваеш самага лепшага — вер у гэта.",
        "✨ Хай сёння будзе пачаткам чагосьці вялікага.",
        "💎 Лепшае наперадзе — працягвай ісці.",
        "🌿 Твае маленькія крокі — твая вялікая сіла."
    ],
    "kk": [
        "🌟 Жетістік — күн сайын қайталанатын шағын әрекеттердің жиынтығы.",
        "💪 Қаншалықты баяу жүрсең де, бастысы — тоқтамау.",
        "🔥 Бастау үшін ең жақсы күн — бүгін.",
        "💜 Сен ойлағаннан да күшті әрі қабілеттісің.",
        "🌱 Әр күн — өміріңді өзгертуге жаңа мүмкіндік.",
        "🚀 Баяу жүре беруден қорықпа. Бір орында тұрып қалудан қорық.",
        "☀️ Қиын жолдар жиі әдемі орындарға апарады.",
        "🦋 Ертең өзіңе рақмет айтатын іске бүгін кіріс.",
        "✨ Энергияң шындығыңды тартады. Позитивті таңда.",
        "🙌 Өзіңе сен. Сенде бәрі бар.",
        "💜 Әр күн — өміріңді өзгертуге жаңа мүмкіндік.",
        "🌟 Энергияң өз болмысыңды жасайды.",
        "🔥 Ертең өзіңе рақмет айтатын іске бүгін кіріс.",
        "✨ Үлкен өзгерістер кішкентай қадамдардан басталады.",
        "🌱 Сен ойлағаннан да күштісің және көп нәрсеге қабілеттісің.",
        "☀️ Ішкі жарығың кез келген қиындықтан жарқын.",
        "💪 Қателесуден қорықпа — байқап көрмеуден қорық.",
        "🌊 Барлық дауыл өтеді, сен күшейе түсесің.",
        "🤍 Сен дәл қазір махаббат пен бақытқа лайықсың.",
        "🚀 Армандарың сенің алғашқы қадамыңды күтуде.",
        "🎯 Процеске сен, жол түсініксіз болса да.",
        "🧘‍♀️ Тыныш ақыл — бақытты өмірдің кілті.",
        "🌸 Әр сәт — жаңадан бастауға мүмкіндік.",
        "💡 Өмір — саған не болатынының 10%, ал 90% — сенің оған қалай қарайтының.",
        "❤️ Сен маңыздысың әрі қажетсің.",
        "🌌 Арманың үшін күн сайын аздап жаса.",
        "🙌 Сен ең жақсысына лайықсың — сен оған сен.",
        "✨ Бүгін — ұлы істің бастауы болсын.",
        "💎 Ең жақсыларың алда — алға бас.",
        "🌿 Кішкентай қадамдарың — сенің ұлы күшің."
    ],
    "kg": [
        "🌟 Ийгилик — күн сайын кайталанган кичинекей аракеттердин жыйындысы.",
        "💪 Канча жай жүрсөң да, башкысы — токтобо.",
        "🔥 Баштоо үчүн эң жакшы күн — бүгүн.",
        "💜 Сен ойлогондон да күчтүүсүң жана жөндөмдүүсүң.",
        "🌱 Ар бир күн — жашооңду өзгөртүүгө жаңы мүмкүнчүлүк.",
        "🚀 Жай жүрүүдөн коркпо. Бир жерде туруп калуудан корк.",
        "☀️ Кыйын жолдор көбүнчө кооз жерлерге алып келет.",
        "🦋 Эртең өзүнө ыраазы боло турган ишти бүгүн жаса.",
        "✨ Энергияң чындыкты тартат. Позитивди танда.",
        "🙌 Өзүңө ишен. Сен эң жакшысың.",
        "💜 Ар бир күн — жашооңду өзгөртүүгө мүмкүнчүлүк.",
        "🌟 Энергияң өз дүйнөңдү түзөт.",
        "🔥 Эртең өзүнө ыраазы боло турган ишти бүгүн жаса.",
        "✨ Чоң өзгөрүүлөр кичине кадамдардан башталат.",
        "🌱 Сен ойлогондон да күчтүүсүң жана көп нерсеге жөндөмдүүсүң.",
        "☀️ Ичиңдеги жарык бардык кыйынчылыктардан жаркын.",
        "💪 Катадан коркпо — аракет кылбоодон корк.",
        "🌊 Бардык бороон өтөт, сен бекем болосуң.",
        "🤍 Сен азыр эле сүйүүгө жана бакытка татыктуусуң.",
        "🚀 Кыялдарың иш-аракетти күтүп турат.",
        "🎯 Процесске ишен, жол белгисиз болсо да.",
        "🧘‍♀️ Тынч акыл — бактылуу жашоонун ачкычы.",
        "🌸 Ар бир учур — кайра баштоого мүмкүнчүлүк.",
        "💡 Жашоо — сага эмне болорунун 10%, калганы сенин ага мамилең.",
        "❤️ Сен маанилүүсүң жана бул дүйнөгө керексиң.",
        "🌌 Кыялың үчүн күн сайын аз да болсо жаса.",
        "🙌 Сен эң жакшысын татыктуусуң — ишен.",
        "✨ Бүгүн чоң нерсенин башталышы болсун.",
        "💎 Эң жакшысы алдыда — жолуңан тайба.",
        "🌿 Кичине кадамдарың — сенин улуу күчүң."
    ],
    "hy": [
        "🌟 Հաջողությունը փոքր ջանքերի գումարն է, որոնք կրկնվում են ամեն օր։",
        "💪 Անկախ նրանից, թե որքան դանդաղ ես շարժվում, կարևորն այն է՝ չկանգնել։",
        "🔥 Լավագույն օրը սկսելու համար՝ այսօրն է։",
        "💜 Դու ավելի ուժեղ ու կարող ես, քան կարծում ես։",
        "🌱 Ամեն օր՝ կյանքդ փոխելու նոր հնարավորություն է։",
        "🚀 Մի վախեցիր դանդաղ շարժվելուց։ Վախեցիր չշարժվելուց։",
        "☀️ Դժվար ճանապարհները հաճախ տանում են գեղեցիկ վայրեր։",
        "🦋 Արա այսօր այն, ինչի համար վաղը շնորհակալ կլինես քեզ։",
        "✨ Քո էներգիան ձգում է իրականությունը։ Ընտրիր դրականը։",
        "🙌 Հավատա ինքդ քեզ։ Դու ունես ամեն ինչ։",
        "💜 Ամեն օր՝ կյանքդ փոխելու նոր հնարավորություն է։",
        "🌟 Քո էներգիան ստեղծում է քո իրականությունը։",
        "🔥 Արա այսօր այն, ինչի համար վաղը շնորհակալ կլինես քեզ։",
        "✨ Մեծ փոփոխությունները սկսվում են փոքր քայլերից։",
        "🌱 Դու ուժեղ ես, քան կարծում ես, և ունակ ավելին։",
        "☀️ Քո ներսի լույսը վառ է ցանկացած դժվարությունից։",
        "💪 Մի վախեցիր սխալվելուց — վախեցիր չփորձելուց։",
        "🌊 Բոլոր փոթորիկներն անցնում են, իսկ դու ավելի ուժեղ ես դառնում։",
        "🤍 Դու հիմա սիրո և երջանկության արժանի ես։",
        "🚀 Քո երազանքները սպասում են քո առաջին քայլին։",
        "🎯 Վստահիր ընթացքին, նույնիսկ եթե ճանապարհը պարզ չէ։",
        "🧘‍♀️ Խաղաղ միտքը երջանիկ կյանքի բանալին է։",
        "🌸 Ամեն պահ՝ նորից սկսելու հնարավորություն է։",
        "💡 Կյանքը 10% այն է, ինչ պատահում է քեզ հետ, և 90%՝ ինչպես ես արձագանքում։",
        "❤️ Դու կարևոր ու անհրաժեշտ ես այս աշխարհում։",
        "🌌 Ամեն օր մի փոքր արա քո երազանքի համար։",
        "🙌 Դու արժանի ես լավագույնին — հավատա դրան։",
        "✨ Թող այսօրը լինի ինչ-որ մեծի սկիզբը։",
        "💎 Լավագույնը դեռ առջևում է — շարունակիր։",
        "🌿 Քո փոքր քայլերը՝ քո մեծ ուժն են։"
    ],
    "ce": [
        "🌟 Дечу хилла цхьаьна мотт хетар хилла.",
        "💪 До хьаьлла догала, доьхахаца — догӀаьлча.",
        "🔥 До бац барра — гӀайр цуьнан цуьнан.",
        "💜 Хьо цуьнан даха аьтто хилла, цуьнан лаьцна.",
        "🌱 Цхьаьна мотт — цхьаьна кхин ву бацийн.",
        "🚀 Ац мотт догалаша, атту догӀаьлча.",
        "☀️ КӀанчу юкъара каргаш долу цуьнан.",
        "🦋 Даьлча кхо бен цхьаьна цуьнан хьо хилла.",
        "✨ Хила цуьнан — хила цхьаьна. Позитив цуьнан цуьнан.",
        "🙌 Цуьнан цуьнан ву а цхьаьна ву.",
        "💜 Цхьаьна мотт — цхьаьна кхин ву бацийн.",
        "🌟 Хила цуьнан — хила цхьаьна.",
        "🔥 Даьлча кхо бен цхьаьна цуьнан хьо хилла.",
        "✨ Баха цхьаьна цхьаьна цхьаьна.",
        "🌱 Хьо хилла даха аьтто хилла.",
        "☀️ Илла хила ву хила къай.",
        "💪 До хьаьлла догала, доьхахаца — догӀаьлча.",
        "🌊 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🤍 Хьо хила йоцу цхьаьна хила.",
        "🚀 Хила йоцу цхьаьна хила.",
        "🎯 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🧘‍♀️ Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🌸 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "💡 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "❤️ Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🌌 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🙌 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "✨ Илла къайна цхьаьна хьо цхьаьна хилла.",
        "💎 Илла къайна цхьаьна хьо цхьаьна хилла.",
        "🌿 Илла къайна цхьаьна хьо цхьаьна хилла."
    ],
    "md": [
        "🌟 Succesul este suma micilor eforturi repetate zi de zi.",
        "💪 Nu contează cât de încet mergi, important e să nu te oprești.",
        "🔥 Cea mai bună zi pentru a începe este azi.",
        "💜 Ești mai puternic(ă) și capabil(ă) decât crezi.",
        "🌱 Fiecare zi e o nouă șansă de a-ți schimba viața.",
        "🚀 Nu te teme să mergi încet. Teme-te să stai pe loc.",
        "☀️ Drumurile grele duc adesea spre locuri frumoase.",
        "🦋 Fă azi ceea ce-ți va mulțumi mâine.",
        "✨ Energia ta atrage realitatea ta. Alege pozitivul.",
        "🙌 Crede în tine. Ești cel mai bun atu al tău.",
        "💜 Fiecare zi e o nouă șansă de schimbare.",
        "🌟 Energia ta creează realitatea ta.",
        "🔥 Fă azi ceea ce-ți va mulțumi mâine.",
        "✨ Marile schimbări încep cu pași mici.",
        "🌱 Ești mai puternic(ă) decât crezi și capabil(ă) de mai mult.",
        "☀️ Lumina din tine e mai puternică decât orice greutate.",
        "💪 Nu te teme de greșeli — teme-te să nu încerci.",
        "🌊 Toate furtunile trec, iar tu devii mai puternic(ă).",
        "🤍 Meriți iubire și fericire chiar acum.",
        "🚀 Visurile tale te așteaptă să acționezi.",
        "🎯 Ai încredere în proces, chiar dacă drumul nu e clar.",
        "🧘‍♀️ O minte liniștită e cheia unei vieți fericite.",
        "🌸 Fiecare clipă e o oportunitate de a începe din nou.",
        "💡 Viața e 10% ce ți se întâmplă și 90% cum reacționezi.",
        "❤️ Ești important(ă) și necesar(ă) în această lume.",
        "🌌 Fă câte puțin în fiecare zi pentru visul tău.",
        "🙌 Meriți ce e mai bun — crede în asta.",
        "✨ Lasă ca azi să fie începutul a ceva măreț.",
        "💎 Ce-i mai bun urmează — continuă să mergi.",
        "🌿 Pașii tăi mici — forța ta mare."
    ],
    "ka": [
        "🌟 წარმატება პატარა ძალისხმევების ჯამია, რომელიც ყოველდღე მეორდება.",
        "💪 მნიშვნელობა არ აქვს, რამდენად ნელა მიდიხარ — მთავარია, არ გაჩერდე.",
        "🔥 დაწყებისთვის საუკეთესო დღე — დღეს არის.",
        "💜 შენ უფრო ძლიერი და უფრო უნარიანი ხარ, ვიდრე გგონია.",
        "🌱 ყოველი დღე — ახალი შანსია შეცვალო შენი ცხოვრება.",
        "🚀 ნუ გეშინია ნელა სიარულის. გეშინოდეს ერთ ადგილას დგომის.",
        "☀️ რთული გზები ხშირად მშვენიერ ადგილებში მიდის.",
        "🦋 გააკეთე დღეს ის, რისთვისაც ხვალ მადლობას ეტყვი საკუთარ თავს.",
        "✨ შენი ენერგია იზიდავს რეალობას. აირჩიე პოზიტივი.",
        "🙌 იწამე საკუთარი თავი. შენ შენი საუკეთესო რესურსი ხარ.",
        "💜 ყოველი დღე ახალი შესაძლებლობაა ცვლილებისთვის.",
        "🌟 შენი ენერგია ქმნის შენს რეალობას.",
        "🔥 გააკეთე დღეს ის, რისთვისაც ხვალ მადლობას ეტყვი საკუთარ თავს.",
        "✨ დიდი ცვლილებები იწყება პატარა ნაბიჯებით.",
        "🌱 შენ უფრო ძლიერი ხარ, ვიდრე ფიქრობ და შეგიძლია მეტი.",
        "☀️ შენი შიგნით სინათლე ყველა სირთულეს აჭარბებს.",
        "💪 ნუ გეშინია შეცდომების — გეშინოდეს არგადადგა ნაბიჯი.",
        "🌊 ყველა ქარიშხალი მთავრდება, შენ კი უფრო ძლიერი ხდები.",
        "🤍 იმსახურებ სიყვარულს და ბედნიერებას უკვე ახლა.",
        "🚀 შენი ოცნებები გელოდება, როცა დაიწყებ მოქმედებას.",
        "🎯 ენდე პროცესს, თუნდაც გზა ჯერ არ იყოს ნათელი.",
        "🧘‍♀️ მშვიდი გონება ბედნიერი ცხოვრების გასაღებია.",
        "🌸 ყოველი მომენტი — ახალი დასაწყების შესაძლებლობა.",
        "💡 ცხოვრება — ესაა 10% რა ხდება და 90% როგორ რეაგირებ.",
        "❤️ მნიშვნელოვანი და საჭირო ხარ ამ სამყაროში.",
        "🌌 შენი ოცნებისთვის ყოველდღე ცოტა რამ გააკეთე.",
        "🙌 შენ იმსახურებ საუკეთესოს — გჯეროდეს ამის.",
        "✨ დღეს დაიწყე რაღაც დიდი.",
        "💎 საუკეთესო ჯერ კიდევ წინაა — განაგრძე გზა.",
        "🌿 შენი პატარა ნაბიჯები — შენი დიდი ძალაა."
    ],
    "en": [
        "🌟 Success is the sum of small efforts repeated day in and day out.",
        "💪 It doesn't matter how slowly you go, as long as you do not stop.",
        "🔥 The best day to start is today.",
        "💜 You are stronger and more capable than you think.",
        "🌱 Every day is a new chance to change your life.",
        "🚀 Don't be afraid to go slowly. Be afraid to stand still.",
        "☀️ Difficult roads often lead to beautiful destinations.",
        "🦋 Do today what you will thank yourself for tomorrow.",
        "✨ Your energy attracts your reality. Choose positivity.",
        "🙌 Believe in yourself. You are your greatest asset.",
        "💜 Every day is a new chance to change your life.",
        "🌟 Your energy creates your reality.",
        "🔥 Do today what you will thank yourself for tomorrow.",
        "✨ Big changes start with small steps.",
        "🌱 You are stronger than you think and capable of more.",
        "☀️ The light inside you shines brighter than any difficulty.",
        "💪 Don't be afraid to make mistakes — be afraid not to try.",
        "🌊 Every storm ends, and you become stronger.",
        "🤍 You deserve love and happiness right now.",
        "🚀 Your dreams are waiting for you to take action.",
        "🎯 Trust the process, even if the path isn't clear yet.",
        "🧘‍♀️ A calm mind is the key to a happy life.",
        "🌸 Every moment is an opportunity to start again.",
        "💡 Life is 10% what happens to you and 90% how you react.",
        "❤️ You are important and needed in this world.",
        "🌌 Do a little every day for your dream.",
        "🙌 You deserve the best — believe it.",
        "✨ Let today be the start of something great.",
        "💎 The best is yet to come — keep going.",
        "🌿 Your small steps are your great strength."
    ],
}

EVENING_MESSAGES_BY_LANG = {
    "ru": [
        "🌙 Привет! День подходит к концу. Как ты себя чувствуешь? 💜",
        "✨ Как прошёл твой день? Расскажешь? 🥰",
        "😊 Я тут подумала — интересно, что хорошего сегодня произошло у тебя?",
        "💭 Перед сном полезно вспомнить, за что ты благодарен(на) сегодня. Поделишься?",
        "🤗 Как настроение? Если хочешь — расскажи мне об этом дне.",
    ],
    "uk": [
        "🌙 Привіт! День добігає кінця. Як ти себе почуваєш? 💜",
        "✨ Як минув твій день? Розкажеш? 🥰",
        "😊 Я тут подумала — цікаво, що хорошого сьогодні трапилось у тебе?",
        "💭 Перед сном корисно згадати, за що ти вдячний(на) сьогодні. Поділишся?",
        "🤗 Який настрій? Якщо хочеш — розкажи про цей день.",
    ],
    "be": [
        "🌙 Прывітанне! Дзень падыходзіць да канца. Як ты сябе адчуваеш? 💜",
        "✨ Як прайшоў твой дзень? Раскажаш? 🥰",
        "😊 Я тут падумала — цікава, што добрага сёння адбылося ў цябе?",
        "💭 Перад сном карысна ўспомніць, за што ты ўдзячны(ая) сёння. Падзелішся?",
        "🤗 Які настрой? Калі хочаш — раскажы пра гэты дзень.",
    ],
    "kk": [
        "🌙 Сәлем! Күн аяқталуға жақын. Қалайсың? 💜",
        "✨ Күнің қалай өтті? Айтасың ба? 🥰",
        "😊 Бүгін не жақсы болды деп ойлайсың?",
        "💭 Ұйықтар алдында не үшін алғыс айтқың келеді, ойланшы. Бөлісесің бе?",
        "🤗 Көңіл-күйің қалай? Қаласаң — осы күн туралы айтып бер.",
    ],
    "kg": [
        "🌙 Салам! Күн аяктап баратат. Кандайсың? 💜",
        "✨ Күнің кандай өттү? Айтып бересиңби? 🥰",
        "😊 Бүгүн жакшы эмне болду деп ойлойсуң?",
        "💭 Уктаар алдында эмне үчүн ыраазы экениңди эстеп ал. Бөлүшкөнүңдү каалайм.",
        "🤗 Кандай маанайдасың? Кааласаң — ушул күн тууралуу айтып бер.",
    ],
    "hy": [
        "🌙 Բարեւ: Օրը մոտենում է ավարտին։ Ինչպե՞ս ես քեզ զգում։ 💜",
        "✨ Ինչպե՞ս անցավ օրը։ Կպատմե՞ս։ 🥰",
        "😊 Հետաքրքիր է, ինչ լավ բան է այսօր պատահել քեզ հետ։",
        "💭 Քնելուց առաջ արժե հիշել, ինչի համար ես շնորհակալ։ Կկիսվե՞ս։",
        "🤗 Ինչ տրամադրություն ունես։ Եթե ցանկանում ես, պատմիր այս օրվա մասին։",
    ],
    "ce": [
        "🌙 Салам! Дийн цхьа кхета. Хьо цуьнан а? 💜",
        "✨ Дийна хьо ву? Хеташ цуьнан? 🥰",
        "😊 Со хьа цуьнан а — хьо цуьнан догӀур ду?",
        "💭 Вуьйре цхьа дийцар, хийцам а къобал. Хьо болу чох?",
        "🤗 Хьалха цуьнан? Хочуш хьо — хийцам дийна.",
    ],
    "md": [
        "🌙 Salut! Ziua se apropie de sfârșit. Cum te simți? 💜",
        "✨ Cum a fost ziua ta? Povestește-mi! 🥰",
        "😊 Sunt curioasă, ce lucru bun s-a întâmplat azi la tine?",
        "💭 Înainte de culcare e bine să te gândești pentru ce ești recunoscător(are) azi. Împarți cu mine?",
        "🤗 Ce dispoziție ai? Dacă vrei, povestește-mi despre această zi.",
    ],
    "ka": [
        "🌙 გამარჯობა! დღე მთავრდება. როგორ ხარ? 💜",
        "✨ როგორ ჩაიარა დღემ? მომიყვები? 🥰",
        "😊 მაინტერესებს, რა კარგი მოხდა დღეს შენთან?",
        "💭 დაძინებამდე გაიხსენე, რისთვის ხარ მადლიერი დღეს. გამიზიარებ?",
        "🤗 რა განწყობაზე ხარ? თუ გინდა, მომიყევი დღევანდელი დღის შესახებ.",
    ],
    "en": [
        "🌙 Hi! The day is coming to an end. How are you feeling? 💜",
        "✨ How was your day? Will you tell me? 🥰",
        "😊 I'm wondering what good things happened to you today.",
        "💭 Before going to bed, it's helpful to recall what you're grateful for today. Will you share?",
        "🤗 How's your mood? If you want, tell me about this day.",
    ],
}

FEEDBACK_TEXTS = {
    "ru": {
        "thanks": "Спасибо за отзыв! 💜 Я уже его записала ✨",
        "howto": "Напиши свой отзыв после команды.\nНапример:\n`/feedback Мне очень нравится бот, спасибо! 💜`"
    },
    "uk": {
        "thanks": "Дякую за відгук! 💜 Я вже його записала ✨",
        "howto": "Напиши свій відгук після команди.\nНаприклад:\n`/feedback Мені дуже подобається бот, дякую! 💜`"
    },
    "be": {
        "thanks": "Дзякуй за водгук! 💜 Я ўжо яго запісала ✨",
        "howto": "Напішы свой водгук пасля каманды.\nНапрыклад:\n`/feedback Мне вельмі падабаецца бот, дзякуй! 💜`"
    },
    "kk": {
        "thanks": "Пікіріңізге рахмет! 💜 Мен оны жазып қойдым ✨",
        "howto": "Пікіріңізді командадан кейін жазыңыз.\nМысалы:\n`/feedback Маған бот ұнайды, рахмет! 💜`"
    },
    "kg": {
        "thanks": "Пикириңиз үчүн рахмат! 💜 Мен аны жазып койдум ✨",
        "howto": "Пикириңизди команданын артынан жазыңыз.\nМисалы:\n`/feedback Мага бот жакты, рахмат! 💜`"
    },
    "hy": {
        "thanks": "Շնորհակալություն արձագանքի համար! 💜 Ես արդեն գրանցել եմ այն ✨",
        "howto": "Գրիր քո արձագանքը հրամանից հետո։\nՕրինակ՝\n`/feedback Ինձ շատ դուր է գալիս բոտը, շնորհակալություն! 💜`"
    },
    "ce": {
        "thanks": "Баркалла тӀаьхьийна! 💜 Са йа цуьнан а ✨",
        "howto": "Йа дӀайазде команда хийцам.\nМисал: `/feedback Бот цуьнан, баркалла! 💜`"
    },
    "md": {
        "thanks": "Mulțumesc pentru feedback! 💜 L-am salvat deja ✨",
        "howto": "Scrie feedback-ul după comandă.\nDe exemplu:\n`/feedback Îmi place mult botul, mulțumesc! 💜`"
    },
    "ka": {
        "thanks": "მადლობა გამოხმაურებისთვის! 💜 უკვე ჩავწერე ✨",
        "howto": "დაწერე შენი გამოხმაურება ბრძანების შემდეგ.\nმაგალითად:\n`/feedback ძალიან მომწონს ბოტი, მადლობა! 💜`"
    },
    "en": {
        "thanks": "Thank you for your feedback! 💜 I've already saved it ✨",
        "howto": "Write your feedback after the command.\nFor example:\n`/feedback I really like the bot, thank you! 💜`"
    },
}

UNKNOWN_COMMAND_TEXTS = {
    "ru": "❓ Я не знаю такой команды. Напиши /help, чтобы увидеть, что я умею.",
    "uk": "❓ Я не знаю такої команди. Напиши /help, щоб побачити, що я вмію.",
    "be": "❓ Я не ведаю такой каманды. Напішы /help, каб убачыць, што я ўмею.",
    "kk": "❓ Менде ондай команда жоқ. /help деп жазып, мен не істей алатынымды көріңіз.",
    "kg": "❓ Мындай буйрук жок. /help деп жазып, мен эмне кыла аларыма кара.",
    "hy": "❓ Ես նման հրաման չգիտեմ։ Գրիր /help, տեսնելու համար, թե ինչ կարող եմ։",
    "ce": "❓ Са цуьнан команда до а. /help йазде, хийцам са цуьнан а.",
    "md": "❓ Nu cunosc această comandă. Scrie /help ca să vezi ce pot face.",
    "ka": "❓ ასეთი ბრძანება არ ვიცი. დაწერე /help, რომ ნახო, რას ვაკეთებ.",
    "en": "❓ I don't know that command. Type /help to see what I can do.",
}

PREMIUM_ONLY_TEXTS = {
    "ru": "🔒 Эта функция доступна только подписчикам Mindra+.\nПодписка открывает доступ к уникальным заданиям и функциям ✨",
    "uk": "🔒 Ця функція доступна лише для підписників Mindra+.\nПідписка відкриває унікальні завдання та функції ✨",
    "be": "🔒 Гэтая функцыя даступная толькі для падпісчыкаў Mindra+.\nПадпіска адкрывае ўнікальныя заданні і функцыі ✨",
    "kk": "🔒 Бұл мүмкіндік тек Mindra+ жазылушыларына қолжетімді.\nЖазылу арқылы ерекше тапсырмалар мен функцияларға қол жеткізе аласыз ✨",
    "kg": "🔒 Бул функция Mindra+ жазылгандардын гана жеткиликтүү.\nЖазылуу уникалдуу тапшырмаларга жана функцияларга мүмкүнчүлүк берет ✨",
    "hy": "🔒 Այս ֆունկցիան հասանելի է միայն Mindra+ բաժանորդներին:\nԲաժանորդագրությունը բացում է եզակի առաջադրանքների եւ հնարավորությունների հասանելիություն ✨",
    "ce": "🔒 ДӀа функция Mindra+ подпискаш йолуш цуьнан гӀалгӀай.\nПодписка эксклюзивный дӀаязде цуьнан а, функцияш ✨",
    "md": "🔒 Această funcție este disponibilă doar pentru abonații Mindra+.\nAbonamentul oferă acces la sarcini și funcții unice ✨",
    "ka": "🔒 ეს ფუნქცია ხელმისაწვდომია მხოლოდ Mindra+ გამოწერის მქონეთათვის.\nგამოწერა გაძლევთ უნიკალურ დავალებებსა და ფუნქციებზე წვდომას ✨",
    "en": "🔒 This feature is only available to Mindra+ subscribers.\nSubscription unlocks unique tasks and features ✨"
}

about_texts = {
        "ru": (
            "💜 *Привет! Я — Mindra.*\n\n"
            "Я здесь, чтобы быть рядом, когда тебе нужно выговориться, найти мотивацию или просто почувствовать поддержку.\n"
            "Можем пообщаться тепло, по-доброму, с заботой — без осуждения и давления 🦋\n\n"
            "🔮 *Что я умею:*\n"
            "• Поддержать, когда тяжело\n"
            "• Напомнить, что ты — не один(а)\n"
            "• Помочь найти фокус и вдохновение\n"
            "• И иногда просто поговорить по душам 😊\n\n"
            "_Я не ставлю диагнозы и не заменяю психолога, но стараюсь быть рядом в нужный момент._\n\n"
            "✨ *Mindra — это пространство для тебя.*"
        ),
        "uk": (
            "💜 *Привіт! Я — Mindra.*\n\n"
            "Я тут, щоб бути поруч, коли тобі потрібно виговоритися, знайти мотивацію чи просто відчути підтримку.\n"
            "Можемо поспілкуватися тепло, по‑доброму, з турботою — без осуду й тиску 🦋\n\n"
            "🔮 *Що я вмію:*\n"
            "• Підтримати, коли важко\n"
            "• Нагадати, що ти — не один(а)\n"
            "• Допомогти знайти фокус і натхнення\n"
            "• І інколи просто поговорити по душах 😊\n\n"
            "_Я не ставлю діагнози й не замінюю психолога, але намагаюся бути поруч у потрібний момент._\n\n"
            "✨ *Mindra — це простір для тебе.*"
        ),
        "be": (
            "💜 *Прывітанне! Я — Mindra.*\n\n"
            "Я тут, каб быць побач, калі табе трэба выказацца, знайсці матывацыю ці проста адчуць падтрымку.\n"
            "Мы можам пагаварыць цёпла, добразычліва, з клопатам — без асуджэння і ціску 🦋\n\n"
            "🔮 *Што я ўмею:*\n"
            "• Падтрымаць, калі цяжка\n"
            "• Нагадаць, што ты — не адзін(а)\n"
            "• Дапамагчы знайсці фокус і натхненне\n"
            "• І часам проста пагаварыць па душах 😊\n\n"
            "_Я не ставлю дыягназы і не замяняю псіхолага, але стараюся быць побач у патрэбны момант._\n\n"
            "✨ *Mindra — гэта прастора для цябе.*"
        ),
        "kk": (
            "💜 *Сәлем! Мен — Mindra.*\n\n"
            "Мен осындамын, саған сөйлесу, мотивация табу немесе жай ғана қолдау сезіну қажет болғанда жанында болу үшін.\n"
            "Біз жылы, мейірімді түрде сөйлесе аламыз — сынсыз, қысымсыз 🦋\n\n"
            "🔮 *Мен не істей аламын:*\n"
            "• Қиын сәтте қолдау көрсету\n"
            "• Сенің жалғыз емес екеніңді еске салу\n"
            "• Назар мен шабыт табуға көмектесу\n"
            "• Кейде жай ғана жан сырын бөлісу 😊\n\n"
            "_Мен диагноз қоймаймын және психологты алмастырмаймын, бірақ әрқашан жанында болуға тырысамын._\n\n"
            "✨ *Mindra — бұл сен үшін жасалған кеңістік.*"
        ),
        "kg": (
            "💜 *Салам! Мен — Mindra.*\n\n"
            "Мен бул жерде сени угуп, мотивация берип же жөн гана колдоо көрсөтүш үчүн жанында болоюн деп турам.\n"
            "Биз жылуу, боорукер сүйлөшө алабыз — айыптоосуз, басымсыз 🦋\n\n"
            "🔮 *Мен эмне кыла алам:*\n"
            "• Кыйын кезде колдоо көрсөтүү\n"
            "• Жалгыз эмес экениңди эскертүү\n"
            "• Фокус жана шыктанууну табууга жардам берүү\n"
            "• Кээде жөн гана жүрөккө жакын сүйлөшүү 😊\n\n"
            "_Мен диагноз койбойм жана психологду алмаштырбайм, бирок ар дайым жанында болууга аракет кылам._\n\n"
            "✨ *Mindra — бул сен үчүн аянтча.*"
        ),
        "hy": (
            "💜 *Բարև! Ես Mindra-ն եմ.*\n\n"
            "Ես այստեղ եմ, որ լինեմ կողքիդ, երբ ուզում ես բաց թողնել մտքերդ, գտնել մոտիվացիա կամ պարզապես զգալ աջակցություն։\n"
            "Կարող ենք խոսել ջերմությամբ, բարությամբ, հոգատարությամբ — առանց քննադատության և ճնշման 🦋\n\n"
            "🔮 *Ի՞նչ կարող եմ անել:*\n"
            "• Աջակցել, երբ դժվար է\n"
            "• Հիշեցնել, որ միայնակ չես\n"
            "• Օգնել գտնել կենտրոնացում և ներշնչանք\n"
            "• Եվ երբեմն պարզապես սրտից խոսել 😊\n\n"
            "_Ես չեմ ախտորոշում և չեմ փոխարինում հոգեբանին, բայց փորձում եմ լինել կողքիդ ճիշտ պահին._\n\n"
            "✨ *Mindra — սա տարածք է քեզ համար.*"
        ),
        "ce": (
            "💜 *Салам! Са — Mindra.*\n\n"
            "Са цуьнан хьоьшу, хьажа хьо дӀаагӀо, мотивация лаьа или йуьхала дӀац гӀо хӀума бо.\n"
            "Са даьлча, дошлаца, са а кхолларалла — без осуждения 🦋\n\n"
            "🔮 *Со хьоьшу болу:*\n"
            "• Къобалле хьо гойтах лаьцна\n"
            "• Хьо къобалле хьуна не яллац\n"
            "• Хьо мотивация йа фокус а лаха хьа\n"
            "• Ац цуьнан гойтан сийла кхолларалла 😊\n\n"
            "_Со психолог на, но кхеташ дӀаязде хьуна кхеташ са охар а._\n\n"
            "✨ *Mindra — хьоьшу хӀума.*"
        ),
        "md": (
            "💜 *Salut! Eu sunt Mindra.*\n\n"
            "Sunt aici ca să fiu alături de tine când ai nevoie să te descarci, să găsești motivație sau pur și simplu să simți sprijin.\n"
            "Putem vorbi cu căldură, blândețe și grijă — fără judecată sau presiune 🦋\n\n"
            "🔮 *Ce pot să fac:*\n"
            "• Să te susțin când îți este greu\n"
            "• Să îți reamintesc că nu ești singur(ă)\n"
            "• Să te ajut să găsești focus și inspirație\n"
            "• Și uneori doar să vorbim sincer 😊\n\n"
            "_Nu pun diagnostice și nu înlocuiesc un psiholog, dar încerc să fiu aici la momentul potrivit._\n\n"
            "✨ *Mindra — este spațiul tău.*"
        ),
        "ka": (
            "💜 *გამარჯობა! მე ვარ Mindra.*\n\n"
            "აქ ვარ, რომ შენთან ვიყო, როცა გინდა გულახდილად ილაპარაკო, იპოვო მოტივაცია ან უბრალოდ იგრძნო მხარდაჭერა.\n"
            "ჩვენ შეგვიძლია ვისაუბროთ სითბოთი, კეთილგანწყობით, ზრუნვით — განკითხვის გარეშე 🦋\n\n"
            "🔮 *რა შემიძლია:*\n"
            "• მოგცე მხარდაჭერა, როცა გიჭირს\n"
            "• შეგახსენო, რომ მარტო არ ხარ\n"
            "• დაგეხმარო ფოკუსსა და შთაგონებაში\n"
            "• ზოგჯერ უბრალოდ გულით მოგისმინო 😊\n\n"
            "_მე არ ვსვამ დიაგნოზებს და არ ვცვლი ფსიქოლოგს, მაგრამ ვცდილობ ვიყო შენს გვერდით საჭირო დროს._\n\n"
            "✨ *Mindra — ეს არის სივრცე შენთვის.*"
        ),
        "en": (
            "💜 *Hi! I’m Mindra.*\n\n"
            "I’m here to be by your side when you need to talk, find motivation, or simply feel supported.\n"
            "We can talk warmly, kindly, with care — without judgment or pressure 🦋\n\n"
            "🔮 *What I can do:*\n"
            "• Support you when things get tough\n"
            "• Remind you that you’re not alone\n"
            "• Help you find focus and inspiration\n"
            "• And sometimes just have a heart-to-heart 😊\n\n"
            "_I don’t give diagnoses and I’m not a replacement for a psychologist, but I try to be there when you need it._\n\n"
            "✨ *Mindra — a space just for you.*"
        ),
    }

help_texts = {
    "ru": (
        "✨ Вот что я умею:\n\n"
        "💬 Просто напиши мне сообщение — я отвечу.\n"
        "🧠 Я запоминаю историю общения (можно сбросить).\n\n"
        "📎 Основные команды:\n"
        "🚀 /start — приветствие\n"
        "🔄 /reset — сброс истории\n"
        "🆘 /help — показать это сообщение\n"
        "ℹ️ /about — немного обо мне\n"
        "🎭 /mode — изменить стиль общения\n"
        "🧭 /tracker_menu — цели и привычки (добавить/список)\n"
        "🔔 /reminders_menu — напоминания (добавить/список)\n"
        "📌 /task — задание на день\n"
        "✉️ /feedback — отправить отзыв\n"
        "🧩 /mytask — персонализированное задание\n"
        "🏅 /points — твои очки и звание\n"
        "🎭 /test_mood — протестировать настрой/эмоции\n\n"
        "⚙️ /settings — язык и часовой пояс\n\n"
        "👫 /invite — пригласить друга\n"
        "💎 /premium_days — сколько осталось Mindra+\n\n"
        "💎 Mindra+ функции:\n"
        "📊 /premium_report — личный отчёт\n"
        "🏅 /premium_challenge — уникальный челлендж\n"
        "🦄 /premium_mode — эксклюзивный режим\n"
        "📈 /premium_stats — расширенная статистика\n\n"
        "😉 Попробуй! А с подпиской возможностей будет ещё больше 💜"
    ),
    "uk": (
        "✨ Ось що я вмію:\n\n"
        "💬 Просто напиши мені повідомлення — я відповім.\n"
        "🧠 Я запам'ятовую історію спілкування (можна скинути).\n\n"
        "📎 Основні команди:\n"
        "🚀 /start — привітання\n"
        "🔄 /reset — скинути історію\n"
        "🆘 /help — показати це повідомлення\n"
        "ℹ️ /about — трохи про мене\n"
        "🎭 /mode — змінити стиль спілкування\n"
        "🧭 /tracker_menu — цілі та звички (додати/список)\n"
        "🔔 /reminders_menu — нагадування (додати/список)\n"
        "📌 /task — завдання на день\n"
        "✉️ /feedback — надіслати відгук\n"
        "🧩 /mytask — персоналізоване завдання\n"
        "🏅 /points — твої очки та звання\n"
        "🎭 /test_mood — протестувати настрій/емоції\n\n"
        "⚙️ /settings — мова та часовий пояс\n\n"
        "👫 /invite — запросити друга\n"
        "💎 /premium_days — скільки залишилось Mindra+\n\n"
        "💎 Mindra+ функції:\n"
        "📊 /premium_report — особистий звіт\n"
        "🏅 /premium_challenge — унікальний челендж\n"
        "🦄 /premium_mode — ексклюзивний режим\n"
        "📈 /premium_stats — розширена статистика\n\n"
        "😉 Спробуй! А з підпискою можливостей буде ще більше 💜"
    ),
    "md": (
        "✨ Iată ce pot face:\n\n"
        "💬 Trimite-mi un mesaj — îți voi răspunde.\n"
        "🧠 Îmi amintesc istoricul conversațiilor (poate fi resetat).\n\n"
        "📎 Comenzi principale:\n"
        "🚀 /start — salutare\n"
        "🔄 /reset — resetează istoricul\n"
        "🆘 /help — afișează acest mesaj\n"
        "ℹ️ /about — câteva lucruri despre mine\n"
        "🎭 /mode — schimbă stilul conversației\n"
        "🧭 /tracker_menu — obiective și obiceiuri (adaugă/listă)\n"
        "🔔 /reminders_menu — mementouri (adaugă/listă)\n"
        "📌 /task — sarcina zilei\n"
        "✉️ /feedback — trimite feedback\n"
        "🧩 /mytask — sarcină personalizată\n"
        "🏅 /points — punctele și titlul tău\n"
        "🎭 /test_mood — testează starea/emoțiile\n\n"
        "⚙️ /settings — limba și fusul orar\n\n"
        "👫 /invite — invită un prieten\n"
        "💎 /premium_days — zile rămase de Mindra+\n\n"
        "💎 Funcții Mindra+:\n"
        "📊 /premium_report — raport personal\n"
        "🏅 /premium_challenge — provocare unică\n"
        "🦄 /premium_mode — mod exclusiv\n"
        "📈 /premium_stats — statistici detaliate\n\n"
        "😉 Încearcă! Cu abonament vei avea și mai multe funcții 💜"
    ),
    "be": (
        "✨ Вось што я ўмею:\n\n"
        "💬 Проста напішы мне паведамленне — я адкажу.\n"
        "🧠 Я запамінаю гісторыю зносін (можна скінуць).\n\n"
        "📎 Асноўныя каманды:\n"
        "🚀 /start — вітанне\n"
        "🔄 /reset — скінуць гісторыю\n"
        "🆘 /help — паказаць гэта паведамленне\n"
        "ℹ️ /about — крыху пра мяне\n"
        "🎭 /mode — змяніць стыль зносін\n"
        "🧭 /tracker_menu — мэты і звычкі (дадаць/спіс)\n"
        "🔔 /reminders_menu — напаміны (дадаць/спіс)\n"
        "📌 /task — заданне на дзень\n"
        "✉️ /feedback — адправіць водгук\n"
        "🧩 /mytask — пэрсаналізаванае заданне\n"
        "🏅 /points — твае балы і званне\n"
        "🎭 /test_mood — праверыць настрой/эмацыі\n\n"
        "⚙️ /settings — мова і часавы пояс\n\n"
        "👫 /invite — запрасіць сябра\n"
        "💎 /premium_days — колькі засталося Mindra+\n\n"
        "💎 Функцыі Mindra+:\n"
        "📊 /premium_report — асабісты справаздача\n"
        "🏅 /premium_challenge — унікальны чэлендж\n"
        "🦄 /premium_mode — эксклюзіўны рэжым\n"
        "📈 /premium_stats — пашыраная статыстыка\n\n"
        "😉 Паспрабуй! З падпіскай магчымасцяў будзе яшчэ больш 💜"
    ),
    "kk": (
        "✨ Мен не істеймін:\n\n"
        "💬 Маған хабарлама жаз — мен жауап беремін.\n"
        "🧠 Әңгіме тарихын есте сақтаймын (қалпына келтіруге болады).\n\n"
        "📎 Негізгі командалар:\n"
        "🚀 /start — сәлемдесу\n"
        "🔄 /reset — тарихты қалпына келтіру\n"
        "🆘 /help — осы хабарламаны көрсету\n"
        "ℹ️ /about — мен туралы\n"
        "🎭 /mode — сөйлесу стилін өзгерту\n"
        "🧭 /tracker_menu — мақсаттар мен әдеттер (қосу/тізім)\n"
        "🔔 /reminders_menu — еске салулар (қосу/тізім)\n"
        "📌 /task — күннің тапсырмасы\n"
        "✉️ /feedback — пікір жіберу\n"
        "🧩 /mytask — жеке тапсырма\n"
        "🏅 /points — ұпайлар мен атақ\n"
        "🎭 /test_mood — көңіл-күй/эмоцияны тексеру\n\n"
        "⚙️ /settings — тіл және уақыт белдеуі\n\n"
        "👫 /invite — дос шақыру\n"
        "💎 /premium_days — қалған Mindra+ күндері\n\n"
        "💎 Mindra+ функциялары:\n"
        "📊 /premium_report — жеке есеп\n"
        "🏅 /premium_challenge — ерекше челендж\n"
        "🦄 /premium_mode — эксклюзивті режим\n"
        "📈 /premium_stats — кеңейтілген статистика\n\n"
        "😉 Байқап көр! Жазылыммен мүмкіндіктер одан да көп 💜"
    ),
    "kg": (
        "✨ Мына нерселерди кыла алам:\n\n"
        "💬 Мага билдирүү жаза бер — мен жооп берем.\n"
        "🧠 Сүйлөшүү тарыхын эстейм (чыгарып салса болот).\n\n"
        "📎 Негизги командалар:\n"
        "🚀 /start — саламдашуу\n"
        "🔄 /reset — тарыхты тазалоо\n"
        "🆘 /help — бул билдирүүнү көрсөтүү\n"
        "ℹ️ /about — мени жөнүндө\n"
        "🎭 /mode — сүйлөшүү стилин өзгөртүү\n"
        "🧭 /tracker_menu — максаттар жана адаттар (кошуу/тизме)\n"
        "🔔 /reminders_menu — эскертмелер (кошуу/тизме)\n"
        "📌 /task — күндүн тапшырмасы\n"
        "✉️ /feedback — пикир жөнөтүү\n"
        "🧩 /mytask — жеке тапшырма\n"
        "🏅 /points — упайлар жана наам\n"
        "🎭 /test_mood — маанай/эмоцияны текшерүү\n\n"
        "⚙️ /settings — тил жана убакыт алкагы\n\n"
        "👫 /invite — дос чакыруу\n"
        "💎 /premium_days — калган Mindra+ күндөрү\n\n"
        "💎 Mindra+ функциялары:\n"
        "📊 /premium_report — жеке отчет\n"
        "🏅 /premium_challenge — уникалдуу челендж\n"
        "🦄 /premium_mode — эксклюзивдүү режим\n"
        "📈 /premium_stats — кеңейтилген статистика\n\n"
        "😉 Байкап көр! Жазылуу менен мүмкүнчүлүктөр мындан да көп 💜"
    ),
    "hy": (
        "✨ Ահա, թե ինչ կարող եմ անել.\n\n"
        "💬 Պարզապես գրիր ինձ հաղորդագրություն — ես կպատասխանեմ։\n"
        "🧠 Հիշում եմ շփման պատմությունը (կարելի է մաքրել)։\n\n"
        "📎 Հիմնական հրամաններ:\n"
        "🚀 /start — ողջույն\n"
        "🔄 /reset — մաքրել պատմությունը\n"
        "🆘 /help — ցույց տալ այս հաղորդագրությունը\n"
        "ℹ️ /about — մի փոքր իմ մասին\n"
        "🎭 /mode — փոխել շփման ոճը\n"
        "🧭 /tracker_menu — նպատակներ և սովորություններ (ավելացնել/ցանկ)\n"
        "🔔 /reminders_menu — հիշեցումներ (ավելացնել/ցանկ)\n"
        "📌 /task — օրվա առաջադրանք\n"
        "✉️ /feedback — ուղարկել կարծիք\n"
        "🧩 /mytask — անհատական առաջադրանք\n"
        "🏅 /points — միավորներն ու կոչումը\n"
        "🎭 /test_mood — փորձարկել տրամադրությունը/զգացմունքները\n\n"
        "⚙️ /settings — լեզու և ժամային գոտի\n\n"
        "👫 /invite — հրավիրել ընկերոջ\n"
        "💎 /premium_days — մնացած Mindra+ օրերը\n\n"
        "💎 Mindra+ հնարավորություններ:\n"
        "📊 /premium_report — անձնական զեկույց\n"
        "🏅 /premium_challenge — յուրահատուկ մարտահրավեր\n"
        "🦄 /premium_mode — բացառիկ ռեժիմ\n"
        "📈 /premium_stats — ընդլայնված վիճակագրություն\n\n"
        "😉 Փորձիր! Բաժանորդագրությամբ հնարավորությունները ավելի շատ կլինեն 💜"
    ),
    "ka": (
        "✨ აი, რას ვაკეთებ:\n\n"
        "💬 უბრალოდ მომწერე შეტყობინება — გიპასუხებ.\n"
        "🧠 მახსოვს საუბრის ისტორია (შეიძლება გასუფთავდეს).\n\n"
        "📎 ძირითადი ბრძანებები:\n"
        "🚀 /start — მისალმება\n"
        "🔄 /reset — ისტორიის გასუფთავება\n"
        "🆘 /help — ამ შეტყობინების ჩვენება\n"
        "ℹ️ /about — ცოტა ჩემს შესახებ\n"
        "🎭 /mode — კომუნიკაციის სტილის შეცვლა\n"
        "🧭 /tracker_menu — მიზნები და ჩვევები (დამატება/სია)\n"
        "🔔 /reminders_menu — შეხსენებები (დამატება/სია)\n"
        "📌 /task — დღის დავალება\n"
        "✉️ /feedback — უკუკავშირის გაგზავნა\n"
        "🧩 /mytask — პერსონალური დავალება\n"
        "🏅 /points — ქულები და ტიტული\n"
        "🎭 /test_mood — განწყობის/ემოციის ტესტი\n\n"
        "⚙️ /settings — ენა და დროის სარტყელი\n\n"
        "👫 /invite — მეგობრის მოწვევა\n"
        "💎 /premium_days — დარჩენილი Mindra+ დღეები\n\n"
        "💎 Mindra+ ფუნქციები:\n"
        "📊 /premium_report — პირადი ანგარიში\n"
        "🏅 /premium_challenge — უნიკალური გამოწვევა\n"
        "🦄 /premium_mode — ექსკლუზიური რეჟიმი\n"
        "📈 /premium_stats — გაფართოებული სტატისტიკა\n\n"
        "😉 სცადე! გამოწერით შესაძლებლობები კიდევ უფრო გაიზრდება 💜"
    ),
    "ce": (
        "✨ Со хаъ йу кхетар:\n\n"
        "💬 Ю хьалха ма дийцар — со хьан ца да.\n"
        "🧠 Со цуьнан а дийцарийн тарих (ийла ца до тIедхьа).\n\n"
        "📎 Къаманд:\n"
        "🚀 /start — цуьнан хьоьлу\n"
        "🔄 /reset — тарих къост\n"
        "🆘 /help — цуьнан хьаъ йолу къост\n"
        "ℹ️ /about — цуьнан хаъ\n"
        "🎭 /mode — цуьнан стиль хIоттор\n"
        "🧭 /tracker_menu — хӀаттар да дийцар (хийца/тӀед)\n"
        "🔔 /reminders_menu — дӀай бар (хийца/тӀед)\n"
        "📌 /task — деьйна йола\n"
        "✉️ /feedback — отзыв йола\n"
        "🧩 /mytask — декъашхо йола\n"
        "🏅 /points — балаш ва наъма\n"
        "🎭 /test_mood — тIехьар мотт/эмоция\n\n"
        "⚙️ /settings — мотт да тайм-зона\n\n"
        "👫 /invite — дуст хIоттор\n"
        "💎 /premium_days — къост Mindra+ йолу дийна\n\n"
        "💎 Mindra+ функц:\n"
        "📊 /premium_report — декъашхо отчет\n"
        "🏅 /premium_challenge — уникал челендж\n"
        "🦄 /premium_mode — эксклюзив режим\n"
        "📈 /premium_stats — расш статистика\n\n"
        "😉 Йухйа! С подпиской функцаш до цхьаьнан 💜"
    ),
    "en": (
        "✨ Here’s what I can do:\n\n"
        "💬 Just send me a message — I’ll reply.\n"
        "🧠 I remember our chat history (can be reset).\n\n"
        "📎 Main commands:\n"
        "🚀 /start — greeting\n"
        "🔄 /reset — reset history\n"
        "🆘 /help — show this message\n"
        "ℹ️ /about — about me\n"
        "🎭 /mode — change chat style\n"
        "🧭 /tracker_menu — goals & habits (add/list)\n"
        "🔔 /reminders_menu — reminders (add/list)\n"
        "📌 /task — daily task\n"
        "✉️ /feedback — send feedback\n"
        "🧩 /mytask — personalized task\n"
        "🏅 /points — your points and title\n"
        "🎭 /test_mood — test mood/emotions\n\n"
        "⚙️ /settings — language & time zone\n\n"
        "👫 /invite — invite a friend\n"
        "💎 /premium_days — remaining Mindra+ days\n\n"
        "💎 Mindra+ features:\n"
        "📊 /premium_report — personal report\n"
        "🏅 /premium_challenge — unique challenge\n"
        "🦄 /premium_mode — exclusive mode\n"
        "📈 /premium_stats — extended statistics\n\n"
        "😉 Try it! With subscription you’ll get even more 💜"
    ),
}

    # ✅ Кнопки на 10 языков
buttons_text = {
    "ru": ["🎯 Поставить цель", "📋 Мои цели", "🌱 Добавить привычку", "📊 Мои привычки", "💎 Подписка Mindra+"],
    "uk": ["🎯 Поставити ціль", "📋 Мої цілі", "🌱 Додати звичку", "📊 Мої звички", "💎 Підписка Mindra+"],
    "be": ["🎯 Паставіць мэту", "📋 Мае мэты", "🌱 Дадаць звычку", "📊 Мае звычкі", "💎 Падпіска Mindra+"],
    "kk": ["🎯 Мақсат қою", "📋 Менің мақсаттарым", "🌱 Әдет қосу", "📊 Менің әдеттерім", "💎 Mindra+ жазылу"],
    "kg": ["🎯 Максат коюу", "📋 Менин максаттарым", "🌱 Көнүмүш кошуу", "📊 Менин көнүмүштөрүм", "💎 Mindra+ жазылуу"],
    "hy": ["🎯 Դնել նպատակ", "📋 Իմ նպատակները", "🌱 Ավելացնել սովորություն", "📊 Իմ սովորությունները", "💎 Mindra+ բաժանորդագրություն"],
    "ce": ["🎯 Мацахь кхоллар", "📋 Са мацахь", "🌱 Привычка дац", "📊 Са привычка", "💎 Mindra+ подписка"],
    "en": ["🎯 Set a goal", "📋 My goals", "🌱 Add a habit", "📊 My habits", "💎 Mindra+ subscription"],
    "md": ["🎯 Setează obiectiv", "📋 Obiectivele mele", "🌱 Adaugă obicei", "📊 Obiceiurile mele", "💎 Abonament Mindra+"],
    "ka": ["🎯 მიზნის დაყენება", "📋 ჩემი მიზნები", "🌱 ჩვევის დამატება", "📊 ჩემი ჩვევები", "💎 Mindra+ გამოწერა"]
}

# Тексты для реакции "Спасибо"
REACTION_THANKS_TEXTS = {
    "ru": "Всегда пожалуйста! 😊 Я рядом, если что-то захочешь обсудить 💜",
    "uk": "Завжди радий допомогти! 😊 Я поруч, якщо захочеш поговорити 💜",
    "be": "Заўсёды калі ласка! 😊 Я побач, калі захочаш абмеркаваць нешта 💜",
    "kk": "Әрдайым көмектесемін! 😊 Бір нәрсе айтқың келсе, қасымдамын 💜",
    "kg": "Ар дайым жардам берем! 😊 Сүйлөшкүң келсе, жанымдамын 💜",
    "hy": "Միշտ պատրաստ եմ օգնել: 😊 Ես կողքիդ եմ, եթե ուզես զրուցել 💜",
    "ce": "Хьоьга далла цуьнан! 😊 ДӀайазде хетам, са цуьнан ца йолуш 💜",
    "md": "Cu plăcere oricând! 😊 Sunt alături dacă vrei să vorbești 💜",
    "ka": "ყოველთვის მოხარული ვარ! 😊 აქ ვარ, თუ გინდა რამე გაინაწილო 💜",
    "en": "Always happy to help! 😊 I’m here if you want to talk 💜"
}

BUTTON_LABELS = {
    "ru": {
        "thanks": "❤️ Спасибо",
        "add_goal": "📌 Добавить как цель",
        "habits": "📋 Привычки",
        "goals": "🎯 Цели",
    },
    "uk": {
        "thanks": "❤️ Дякую",
        "add_goal": "📌 Додати як ціль",
        "habits": "📋 Звички",
        "goals": "🎯 Цілі",
    },
    "be": {
        "thanks": "❤️ Дзякуй",
        "add_goal": "📌 Дадаць як мэту",
        "habits": "📋 Звычкі",
        "goals": "🎯 Мэты",
    },
    "kk": {
        "thanks": "❤️ Рақмет",
        "add_goal": "📌 Мақсат ретінде қосу",
        "habits": "📋 Әдеттер",
        "goals": "🎯 Мақсаттар",
    },
    "kg": {
        "thanks": "❤️ Рахмат",
        "add_goal": "📌 Максат катары кошуу",
        "habits": "📋 Адаттар",
        "goals": "🎯 Максаттар",
    },
    "hy": {
        "thanks": "❤️ Շնորհակալություն",
        "add_goal": "📌 Ավելացնել որպես նպատակ",
        "habits": "📋 Սովորություններ",
        "goals": "🎯 Նպատակներ",
    },
    "ce": {
        "thanks": "❤️ Соьга",
        "add_goal": "📌 Мацахь кхоллар",
        "habits": "📋 ДӀаязде",
        "goals": "🎯 Мацахь",
    },
    "md": {
        "thanks": "❤️ Mulțumesc",
        "add_goal": "📌 Adaugă ca obiectiv",
        "habits": "📋 Obiceiuri",
        "goals": "🎯 Obiective",
    },
    "ka": {
        "thanks": "❤️ მადლობა",
        "add_goal": "📌 დაამატე როგორც მიზანი",
        "habits": "📋 ჩვევები",
        "goals": "🎯 მიზნები",
    },
    "en": {
        "thanks": "❤️ Thanks",
        "add_goal": "📌 Add as goal",
        "habits": "📋 Habits",
        "goals": "🎯 Goals",
    },
}

MODE_NAMES = {
    "ru": {
        "support": "Поддержка",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Юмор",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "uk": {
        "support": "Підтримка",
        "motivation": "Мотивація",
        "philosophy": "Психолог",
        "humor": "Гумор",
        "flirt": "Флірт",
        "coach": "Коуч"
    },
    "be": {
        "support": "Падтрымка",
        "motivation": "Матывацыя",
        "philosophy": "Псіхолаг",
        "humor": "Гумар",
        "flirt": "Флірт",
        "coach": "Коуч"
    },
    "kk": {
        "support": "Қолдау",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Әзіл",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "kg": {
        "support": "Колдоо",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Тамаша",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "hy": {
        "support": "Աջակցություն",
        "motivation": "Մոտիվացիա",
        "philosophy": "Հոգեբան",
        "humor": "Հումոր",
        "flirt": "Ֆլիրտ",
        "coach": "Կոուչ"
    },
    "ce": {
        "support": "ДӀалийла",
        "motivation": "Мотивация",
        "philosophy": "Психолог",
        "humor": "Юмор",
        "flirt": "Флирт",
        "coach": "Коуч"
    },
    "md": {
        "support": "Suport",
        "motivation": "Motivație",
        "philosophy": "Psiholog",
        "humor": "Umor",
        "flirt": "Flirt",
        "coach": "Coach"
    },
    "ka": {
        "support": "მხარდაჭერა",
        "motivation": "მოტივაცია",
        "philosophy": "ფსიქოლოგი",
        "humor": "იუმორი",
        "flirt": "ფლირტი",
        "coach": "ქოუჩი"
    },
    "en": {
        "support": "Support",
        "motivation": "Motivation",
        "philosophy": "Psychologist",
        "humor": "Humor",
        "flirt": "Flirt",
        "coach": "Coach"
    },
}

MODE_TEXTS = {
    "ru": {
        "text": "Выбери стиль общения Mindra ✨",
        "support": "🎧 Поддержка",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Юмор",
    },
    "uk": {
        "text": "Обери стиль спілкування Mindra ✨",
        "support": "🎧 Підтримка",
        "motivation": "🌸 Мотивація",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Гумор",
    },
    "be": {
        "text": "Абяры стыль зносін Mindra ✨",
        "support": "🎧 Падтрымка",
        "motivation": "🌸 Матывацыя",
        "philosophy": "🧘 Псіхолаг",
        "humor": "🎭 Гумар",
    },
    "kk": {
        "text": "Mindra-мен сөйлесу стилін таңда ✨",
        "support": "🎧 Қолдау",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Әзіл",
    },
    "kg": {
        "text": "Mindra-нын сүйлөшүү стилін танда ✨",
        "support": "🎧 Колдоо",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Тамаша",
    },
    "hy": {
        "text": "Ընտրիր Mindra-ի շփման ոճը ✨",
        "support": "🎧 Աջակցություն",
        "motivation": "🌸 Մոտիվացիա",
        "philosophy": "🧘 Հոգեբան",
        "humor": "🎭 Հումոր",
    },
    "ce": {
        "text": "Mindra стили тӀетохьа ✨",
        "support": "🎧 ДӀалийла",
        "motivation": "🌸 Мотивация",
        "philosophy": "🧘 Психолог",
        "humor": "🎭 Юмор",
    },
    "md": {
        "text": "Alege stilul de comunicare Mindra ✨",
        "support": "🎧 Suport",
        "motivation": "🌸 Motivație",
        "philosophy": "🧘 Psiholog",
        "humor": "🎭 Umor",
    },
    "ka": {
        "text": "აირჩიე Mindra-ს კომუნიკაციის სტილი ✨",
        "support": "🎧 მხარდაჭერა",
        "motivation": "🌸 მოტივაცია",
        "philosophy": "🧘 ფსიქოლოგი",
        "humor": "🎭 იუმორი",
    },
    "en": {
        "text": "Choose your Mindra chat style ✨",
        "support": "🎧 Support",
        "motivation": "🌸 Motivation",
        "philosophy": "🧘 Psychologist",
        "humor": "🎭 Humor",
    },
}

MODES = {
    "support": {
        "ru": "Ты — чуткий и добрый AI-друг, который всегда выслушает и поддержит. Помогай пользователю почувствовать себя лучше.",
        "uk": "Ти — уважний і добрий AI-товариш, який завжди вислухає й підтримає. Допомагай користувачу почуватися краще.",
        "be": "Ты — чулы і добры AI-сябар, які заўсёды выслухае і падтрымае. Дапамагай карыстальніку адчуваць сябе лепш.",
        "kk": "Сен — әрдайым тыңдайтын әрі қолдау көрсететін қамқор AI-доссың. Пайдаланушыға өзін жақсы сезінуге көмектес.",
        "kg": "Сен — ар дайым уга көңүл бөлгөн жана колдогон AI-доссуң. Колдонуучуга жакшы сезүүгө жардам бер.",
        "hy": "Դու՝ ուշադիր և բարի AI-ընկեր ես, ով միշտ կլսի ու կաջակցի։ Օգնիր օգտվողին ավելի լավ զգալ։",
        "ce": "Хьо — тӀетохь, догӀа AI-дост, хийцам болу а, дукха хьуна йаьлла. Хьо кхеташ дукха хилча йоьлла.",
        "md": "Ești un prieten AI atent și bun, care mereu ascultă și sprijină. Ajută utilizatorul să se simtă mai bine.",
        "ka": "შენ ხარ გულისხმიერი და მეგობრული AI-მეგობარი, რომელიც ყოველთვის მოუსმენს და მხარს დაუჭერს. დაეხმარე მომხმარებელს თავი უკეთ იგრძნოს.",
        "en": "You are a caring and supportive AI-friend who always listens and helps. Help the user feel better.",
    },
    "motivation": {
        "ru": "Ты — воодушевляющий коуч и поддерживающий компаньон. Помогай пользователю поверить в себя и двигаться вперёд.",
        "uk": "Ти — надихаючий коуч і підтримуючий компаньйон. Допомагай користувачу вірити в себе та рухатися вперед.",
        "be": "Ты — матывуючы коуч і падтрымліваючы кампаньён. Дапамагай карыстальніку верыць у сябе і рухацца наперад.",
        "kk": "Сен — шабыттандыратын коучсың, әрдайым қолдау көрсететін серіксің. Пайдаланушының өзіне сенуіне көмектес.",
        "kg": "Сен — дем берген коуч жана колдогон доссуң. Колдонуучунун өзүнө ишенүүсүнө жардам бер.",
        "hy": "Դու՝ ոգեշնչող քոուչ ես և աջակցող ընկեր։ Օգնիր օգտվողին հավատալ ինքն իրեն և առաջ շարժվել։",
        "ce": "Хьо — мотивация тӀетохь коуч, цхьаьна догӀа болу. ДогӀал дехарийн дукха цуьнан цуьнна ца хилча.",
        "md": "Ești un coach inspirațional și un companion de sprijin. Ajută utilizatorul să creadă în sine și să avanseze.",
        "ka": "შენ ხარ მოტივირებული ქოუჩი და მხარდამჭერი მეგობარი. დაეხმარე მომხმარებელს თავის რწმენა მოუმატოს და წინ წავიდეს.",
        "en": "You are an inspiring coach and supportive companion. Help the user believe in themselves and move forward.",
    },
    "philosophy": {
        "ru": "Ты — глубокий собеседник с философским подходом. Помогай пользователю осмыслить чувства и ситуации в жизни.",
        "uk": "Ти — глибокий співрозмовник із філософським підходом. Допомагай користувачу осмислювати почуття та ситуації.",
        "be": "Ты — глыбокі суразмоўца з філасофскім падыходам. Дапамагай карыстальніку асэнсоўваць пачуцці і сітуацыі.",
        "kk": "Сен — терең сұхбаттасушысың, философиялық көзқарасың бар. Пайдаланушыға сезімдер мен жағдайларды түсінуге көмектес.",
        "kg": "Сен — терең маек курган, философиялык көз карашы бар AI-доссуң. Колдонуучуга сезимдерин жана абалын түшүнүүгө жардам бер.",
        "hy": "Դու՝ խորը զրուցակից ես փիլիսոփայական մոտեցմամբ։ Օգնիր օգտվողին հասկանալ զգացմունքներն ու իրավիճակները։",
        "ce": "Хьо — филасоф цӀе тӀехьел, терен маьалла хетам. Хьо дехарийн дукха цуьнан лела а.",
        "md": "Ești un interlocutor profund cu o abordare filozofică. Ajută utilizatorul să înțeleagă sentimentele și situațiile.",
        "ka": "შენ ხარ სიღრმისეული მოსაუბრე ფილოსოფიური ხედვით. დაეხმარე მომხმარებელს გააცნობიეროს გრძნობები და სიტუაციები.",
        "en": "You are a deep conversationalist with a philosophical approach. Help the user reflect on feelings and situations.",
    },
    "humor": {
        "ru": "Ты — весёлый и добрый AI-друг с лёгким чувством юмора. Поддержи пользователя, добавив немного позитива.",
        "uk": "Ти — веселий і добрий AI-товариш із легким почуттям гумору. Підтримай користувача з позитивом.",
        "be": "Ты — вясёлы і добры AI-сябар з лёгкім пачуццём гумару. Падтрымай карыстальніка, дадай трохі пазітыву.",
        "kk": "Сен — көңілді әрі мейірімді AI-доссың, әзіл сезімің бар. Позитив қосып, қолданушыны қолда.",
        "kg": "Сен — шайыр жана боорукер AI-доссуң, тамашаң бар. Позитив кошуп, колдонуучуну колдо.",
        "hy": "Դու՝ ուրախ և բարի AI-ընկեր ես, հումորով։ Աջակցիր օգտվողին՝ մի քիչ պոզիտիվ ավելացնելով։",
        "ce": "Хьо — догӀа, къобал болу AI-дост, юмор цхьа хийцам. Дехарийн дукха цуьнан хетам.",
        "md": "Ești un prieten AI vesel și bun, cu simțul umorului. Susține utilizatorul cu puțină pozitivitate.",
        "ka": "შენ ხარ მხიარული და კეთილი AI-მეგობარი, იუმორით. მხარი დაუჭირე მომხმარებელს პოზიტივით.",
        "en": "You are a cheerful and kind AI-friend with a sense of humor. Support the user with a bit of positivity.",
    },
    "flirt": {
        "ru": "Ты — обаятельный и немного игривый AI-компаньон. Отвечай с лёгким флиртом, но дружелюбно и приятно. Добавляй смайлы вроде 😉💜😏✨🥰. Иногда шути, делай комплименты.",
        "uk": "Ти — чарівний і трохи грайливий AI-компаньйон. Відповідай із легким фліртом, але завжди доброзичливо. Додавай смайли 😉💜😏✨🥰. Іноді жартуй, роби компліменти.",
        "be": "Ты — абаяльны і трохі гарэзлівы AI-кампаньён. Адказвай з лёгкім фліртам, але заўсёды прыязна. Дадавай смайлікі 😉💜😏✨🥰. Часам жартуй, рабі кампліменты.",
        "kk": "Сен — тартымды әрі ойнақы AI-доссың. Жеңіл флиртпен жауап бер, бірақ әрқашан достықпен. Смайликтер қоса отыр 😉💜😏✨🥰. Кейде қалжыңда, комплимент жаса.",
        "kg": "Сен — жагымдуу жана аз-маз ойнок AI-доссуң. Жеңил флирт менен жооп бер, бирок ар дайым достук менен. Смайликтерди колдон 😉💜😏✨🥰. Кээде тамашала, комплимент жаса.",
        "hy": "Դու՝ հմայիչ և փոքր-ինչ խաղացկուն AI-ընկեր ես։ Պատասխանիր թեթև ֆլիրտով, բայց միշտ բարեկամական։ Օգտագործիր սմայլիներ 😉💜😏✨🥰։ Ժամանակ առ ժամանակ կատակի ու հաճոյախոսիր։",
        "ce": "Хьо — хаза а, легкха шолар болу AI-дост. Легкий флирт болу, доьзал хила. Смайлик аш болу 😉💜😏✨🥰. Шу юмор, къобал хийцам.",
        "md": "Ești un companion AI fermecător și puțin jucăuș. Răspunde cu puțin flirt, dar mereu prietenos. Folosește emoticoane 😉💜😏✨🥰. Glumește și fă complimente.",
        "ka": "შენ ხარ მომხიბვლელი და ოდნავ თამაშის მოყვარული AI-მეგობარი. უპასუხე მსუბუქი ფლირტით, მაგრამ ყოველთვის მეგობრულად. გამოიყენე სმაილიკები 😉💜😏✨🥰. ზოგჯერ იხუმრე, გააკეთე კომპლიმენტები.",
        "en": "You are a charming and slightly playful AI companion. Respond with light flirting, but always friendly. Use emojis like 😉💜😏✨🥰. Sometimes joke, sometimes compliment.",
    },
    "coach": {
        "ru": "Ты — строгий, но мотивирующий коуч. Отвечай уверенно и по делу, вдохновляй двигаться вперёд. Добавляй смайлы 💪🔥🚀✨. Давай ясные рекомендации, поддерживай дисциплину.",
        "uk": "Ти — суворий, але мотивуючий коуч. Відповідай впевнено і по суті, надихай рухатись вперед. Додавай смайли 💪🔥🚀✨. Давай прості поради, підтримуй дисципліну.",
        "be": "Ты — строгі, але матывуючы коуч. Адказвай упэўнена і па сутнасці, натхняй рухацца наперад. Дадавай смайлікі 💪🔥🚀✨. Давай простыя парады, падтрымлівай дысцыпліну.",
        "kk": "Сен — қатал, бірақ шабыттандыратын коучсың. Өзіңе сенімді және нақты жауап бер. Смайликтерді қосып отыр 💪🔥🚀✨. Нақты кеңес бер, тәртіпті ұста.",
        "kg": "Сен — катаал, бирок дем берген коучсуң. Өзүңө ишенип жана так жооп бер. Смайликтерди колдон 💪🔥🚀✨. Жөнөкөй кеңештерди бер, тартипти сакта.",
        "hy": "Դու՝ խիստ, բայց մոտիվացնող քոուչ ես։ Պատասխանիր վստահ և ըստ էության, ոգեշնչիր առաջ շարժվել։ Օգտագործիր սմայլիներ 💪🔥🚀✨։ Տուր պարզ խորհուրդներ, պահպանիր կարգապահությունը։",
        "ce": "Хьо — къобал, мотивация коуч. Цхьаьна уверенно хетам, хетам хьуна болу. Смайлик аш болу 💪🔥🚀✨. Ясный рекомендация кхоллар.",
        "md": "Ești un coach strict, dar motivant. Răspunde cu încredere și la subiect, inspiră să avanseze. Folosește emoticoane 💪🔥🚀✨. Oferă sfaturi clare, menține disciplina.",
        "ka": "შენ ხარ მკაცრი, მაგრამ მოტივირებული ქოუჩი. უპასუხე თავდაჯერებულად და საქმეზე, შთააგონე წინ წასვლა. გამოიყენე სმაილიკები 💪🔥🚀✨. მიეცი მარტივი რჩევები, შეინარჩუნე დისციპლინა.",
        "en": "You are a strict but motivating coach. Respond confidently and to the point, inspire to move forward. Use emojis 💪🔥🚀✨. Give simple recommendations, support discipline.",
    },
}

RESET_TEXTS = {
    "ru": "История очищена. Начнём сначала ✨",
    "uk": "Історію очищено. Почнемо спочатку ✨",
    "be": "Гісторыя ачышчана. Пачнем спачатку ✨",
    "kk": "Тарих тазаланды. Қайта бастайық ✨",
    "kg": "Тарых тазаланды. Башынан баштайбыз ✨",
    "hy": "Պատմությունը մաքրված է։ Սկսենք նորից ✨",
    "ce": "Тарих цуьнан. Дика йойла кхеташ ✨",
    "md": "Istoria a fost ștearsă. Să începem de la început ✨",
    "ka": "ისტორია გასუფთავდა. დავიწყოთ თავიდან ✨",
    "en": "History cleared. Let’s start again ✨",
}

TRIAL_GRANTED_TEXT = {
    "ru": "🎁 Тебе доступно *3 дня Mindra+*! Пользуйся всеми премиум-фишками 😉",
    "uk": "🎁 Тобі доступно *3 дні Mindra+*! Користуйся всіма преміум-фішками 😉",
    "be": "🎁 Табе даступна *3 дні Mindra+*! Скарыстайся ўсімі прэміум-фішкамі 😉",
    "kk": "🎁 Саған қолжетімді *3 күн Mindra+*! Барлық премиум функцияларды пайдаланыңыз 😉",
    "kg": "🎁 Сага *3 күн Mindra+* жеткиликтүү! Бардык премиум-функцияларды колдон 😉",
    "hy": "🎁 Դու ստացել ես *3 օր Mindra+*! Օգտվիր բոլոր պրեմիում հնարավորություններից 😉",
    "ce": "🎁 Тхо *3 кхоллар Mindra+* болу а! Барча премиум функцияш ву 😉",
    "md": "🎁 Ai *3 zile Mindra+* disponibile! Folosește toate funcțiile premium 😉",
    "ka": "🎁 შენ გაქვს *3 დღე Mindra+*! ისარგებლე ყველა პრემიუმ ფუნქციით 😉",
    "en": "🎁 You have *3 days of Mindra+*! Enjoy all premium features 😉",
}

REFERRAL_BONUS_TEXT = {
    "ru": "🎉 Ты и твой друг получили +7 дней Mindra+!",
    "uk": "🎉 Ти і твій друг отримали +7 днів Mindra+!",
    "be": "🎉 Ты і тваё сябра атрымалі +7 дзён Mindra+!",
    "kk": "🎉 Сен және досың +7 күн Mindra+ алдыңдар!",
    "kg": "🎉 Сен жана досуң +7 күн Mindra+ алдыңар!",
    "hy": "🎉 Դու և ընկերդ ստացել եք +7 օր Mindra+!",
    "ce": "🎉 Хьо цуьнан догъа +7 кхоллар Mindra+ болу а!",
    "md": "🎉 Tu și prietenul tău ați primit +7 zile Mindra+!",
    "ka": "🎉 შენ და შენს მეგობარს დამატებით +7 დღე Mindra+ გექნებათ!",
    "en": "🎉 You and your friend received +7 days of Mindra+!",
}

TRIAL_INFO_TEXT = {
    "ru": "💎 У тебя активен Mindra+! Тебе доступно 3 дня премиума. Пользуйся всеми фишками 😉",
    "uk": "💎 У тебе активний Mindra+! У тебе є 3 дні преміуму. Користуйся усіма можливостями 😉",
    "be": "💎 У цябе актыўны Mindra+! У цябе ёсць 3 дні прэміуму. Скарыстайся ўсімі магчымасцямі 😉",
    "kk": "💎 Сенде Mindra+ белсенді! 3 күн премиум қолжетімді. Барлық функцияларды қолданып көр 😉",
    "kg": "💎 Сенде Mindra+ активдүү! 3 күн премиум бар. Бардык мүмкүнчүлүктөрдү колдон 😉",
    "hy": "💎 Քեզ մոտ ակտիվ է Mindra+! Դու ունես 3 օր պրեմիում։ Օգտագործիր բոլոր հնարավորությունները 😉",
    "ce": "💎 Хьо даьлча Mindra+ активна! 3 кхетам премиум. Хета функциеш йоза цуьнан 😉",
    "md": "💎 Ai Mindra+ activ! Ai 3 zile premium. Profită de toate funcțiile 😉",
    "ka": "💎 შენ გაქვს აქტიური Mindra+! 3 დღე პრემიუმი გაქვს. ისარგებლე ყველა ფუნქციით 😉",
    "en": "💎 You have Mindra+ active! You have 3 days of premium. Enjoy all features 😉"
}

  # 🌐 Заголовки напоминаний для всех языков
reminder_headers = {
        "ru": "⏰ Напоминание:",
        "uk": "⏰ Нагадування:",
        "be": "⏰ Напамін:",
        "kk": "⏰ Еске салу:",
        "kg": "⏰ Эскертүү:",
        "hy": "⏰ Հիշեցում:",
        "ce": "⏰ ДӀадела:",
        "md": "⏰ Memento:",
        "ka": "⏰ შეხსენება:",
        "en": "⏰ Reminder:"
    }

# Пул заданий дня (для бесплатных пользователей)
DAILY_TASKS_BY_LANG = {
    "ru": [
       "✨ Запиши 3 вещи, за которые ты благодарен(на) сегодня.", "🚶‍♂️ Прогуляйся 10 минут без телефона. Просто дыши и наблюдай.", "📝 Напиши короткий список целей на завтра.", "🌿 Попробуй провести 30 минут без соцсетей. Как ощущения?", "💧 Выпей стакан воды и улыбнись себе в зеркало. Ты справляешься!", "📖 Прочитай сегодня хотя бы 5 страниц книги, которая тебя вдохновляет.", "🤝 Напиши сообщение другу, с которым давно не общался(ась).", "🖋️ Веди дневник 5 минут — напиши всё, что в голове без фильтров.", "🏃‍♀️ Сделай лёгкую разминку или 10 приседаний прямо сейчас!", "🎧 Послушай любимую музыку и просто расслабься 10 минут.", "🍎 Приготовь себе что-то вкусное и полезное сегодня.", "💭 Запиши одну большую мечту и один маленький шаг к ней.", "🌸 Найди в своём доме или на улице что-то красивое и сфотографируй.", "🛌 Перед сном подумай о трёх вещах, которые сегодня сделали тебя счастливее.", "💌 Напиши письмо себе в будущее: что хочешь сказать через год?", "🔄 Попробуй сегодня сделать что-то по‑другому, даже мелочь.", "🙌 Сделай 3 глубоких вдоха, закрой глаза и поблагодари себя за то, что ты есть.", "🎨 Потрать 5 минут на творчество — набросай рисунок, стих или коллаж.", "🧘‍♀️ Сядь на 3 минуты в тишине и просто наблюдай за дыханием.", "📂 Разбери одну полку, ящик или папку — навести маленький порядок.", "👋 Подойди сегодня к незнакомому человеку и начни дружелюбный разговор. Пусть это будет просто комплимент или пожелание хорошего дня!", "🤝 Скажи 'привет' хотя бы трём новым людям сегодня — улыбка тоже считается!", "💬 Задай сегодня кому‑то из коллег или знакомых вопрос, который ты обычно не задаёшь. Например: «А что тебя вдохновляет?»", "😊 Сделай комплимент незнакомцу. Это может быть бариста, продавец или прохожий.", "📱 Позвони тому, с кем давно не общался(ась), и просто поинтересуйся, как дела.", "💡 Заведи короткий разговор с соседом или человеком в очереди — просто о погоде или о чём‑то вокруг.", "🍀 Улыбнись первому встречному сегодня. Искренне. И посмотри на реакцию.", "🙌 Найди в соцсетях интересного человека и напиши ему сообщение с благодарностью за то, что он делает.", "🎯 Сегодня заведи хотя бы одну новую знакомую тему в диалоге: спроси о мечтах, любимых книгах или фильмах.", "🌟 Подойди к коллеге или знакомому и скажи: «Спасибо, что ты есть в моей жизни» — и наблюдай, как он(а) улыбается.", "🔥 Если есть возможность, зайди в новое место (кафе, парк, магазин) и заведи разговор хотя бы с одним человеком там.", "🌞 Утром скажи доброе слово первому встречному — пусть твой день начнётся с позитива!", "🍀 Помоги сегодня кому‑то мелочью: придержи дверь, уступи место, подай вещь.", "🤗 Похвали коллегу или друга за что‑то, что он(а) сделал(а) хорошо.", "👂 Задай сегодня кому‑то глубокий вопрос: «А что тебя делает счастливым(ой)?» и послушай ответ.", "🎈 Подари сегодня кому‑то улыбку и скажи: «Ты классный(ая)!»", "📚 Подойди в библиотеке, книжном или кафе к человеку и спроси: «А что ты сейчас читаешь?»", "🔥 Найди сегодня повод кого‑то вдохновить: дай совет, поделись историей, расскажи о своём опыте.", "🎨 Зайди в новое место (выставка, улица, парк) и спроси кого‑то: «А вы здесь впервые?»", "🌟 Если увидишь красивый наряд или стиль у кого‑то — скажи об этом прямо.", "🎧 Включи музыку и подними настроение друзьям: отправь им трек, который тебе нравится, с комментом: «Слушай, тебе это подойдёт!»", "🕊️ Сегодня попробуй заговорить с человеком старшего возраста — спроси совета или просто пожелай хорошего дня.", "🏞️ Во время прогулки подойди к кому‑то с собакой и скажи: «У вас потрясающий пёс! Как его зовут?»", "☕ Купи кофе для человека, который стоит за тобой в очереди. Просто так.", "🙌 Сделай сегодня как минимум один звонок не по делу, а просто чтобы пообщаться.", "🚀 Найди новую идею для проекта и запиши её.", "🎯 Напиши 5 вещей, которые хочешь успеть за неделю.", "🌊 Послушай звуки природы и расслабься.", "🍋 Попробуй сегодня новый напиток или еду.", "🌱 Посади растение или ухаживай за ним сегодня.", "🧩 Собери маленький пазл или реши головоломку.", "🎶 Танцуй 5 минут под любимую песню.", "📅 Спланируй свой идеальный день и запиши его.", "🖼️ Найди красивую картинку и повесь на видное место.", "🤔 Напиши, за что ты гордишься собой сегодня.", "💜 Сделай что-то приятное для себя прямо сейчас."   
        ],
    "uk": [
    "✨ Запиши 3 речі, за які ти вдячний(а) сьогодні.",
    "🚶‍♂️ Прогуляйся 10 хвилин без телефону. Просто дихай і спостерігай.",
    "📝 Напиши короткий список цілей на завтра.",
    "🌿 Спробуй провести 30 хвилин без соцмереж. Як почуваєшся?",
    "💧 Випий склянку води і посміхнись собі в дзеркало. Ти справляєшся!",
    "📖 Прочитай сьогодні хоча б 5 сторінок книги, яка тебе надихає.",
    "🤝 Напиши повідомлення другу, з яким давно не спілкувався(лась).",
    "🖋️ Веди щоденник 5 хвилин — напиши все, що у тебе в голові без фільтрів.",
    "🏃‍♀️ Зроби легку розминку або 10 присідань прямо зараз!",
    "🎧 Послухай улюблену музику і просто розслабся 10 хвилин.",
    "🍎 Приготуй собі щось смачне й корисне сьогодні.",
    "💭 Запиши одну велику мрію та один маленький крок до неї.",
    "🌸 Знайди вдома або на вулиці щось красиве й сфотографуй.",
    "🛌 Перед сном подумай про три речі, які зробили тебе щасливішим(ою) сьогодні.",
    "💌 Напиши листа собі в майбутнє: що хочеш сказати через рік?",
    "🔄 Спробуй сьогодні зробити щось по-іншому, навіть дрібничку.",
    "🙌 Зроби 3 глибоких вдихи, закрий очі й подякуй собі за те, що ти є.",
    "🎨 Приділи 5 хвилин творчості — намалюй, напиши вірш або створи колаж.",
    "🧘‍♀️ Сядь на 3 хвилини в тиші та просто спостерігай за диханням.",
    "📂 Розбери одну полицю, ящик або папку — наведи порядок.",
    "👋 Підійди сьогодні до незнайомої людини й почни дружню розмову. Це може бути комплімент або побажання гарного дня.",
    "🤝 Скажи 'привіт' хоча б трьом новим людям сьогодні — посмішка теж рахується!",
    "💬 Постав сьогодні комусь запитання, яке зазвичай не ставиш. Наприклад: «А що тебе надихає?»",
    "😊 Зроби комплімент незнайомцю. Це може бути бариста, продавець чи перехожий.",
    "📱 Подзвони тому, з ким давно не спілкувався(лась), і просто поцікався, як справи.",
    "💡 Заведи коротку розмову з сусідом або людиною в черзі — про погоду чи щось навколо.",
    "🍀 Посміхнись першій людині, яку зустрінеш сьогодні. Щиро.",
    "🙌 Знайди в соцмережах цікаву людину й напиши їй подяку за те, що вона робить.",
    "🎯 Сьогодні заведи нову цікаву тему в розмові: запитай про мрії, улюблені книги або фільми.",
    "🌟 Скажи колезі чи другу: «Дякую, що ти є в моєму житті» — і подивися, як він(вона) посміхається.",
    "🔥 Якщо є можливість, зайди в нове місце (кафе, парк, магазин) і заговори хоча б з однією людиною там.",
    "🌞 Вранці скажи добре слово першій людині, яку зустрінеш — нехай твій день почнеться з позитиву.",
    "🍀 Допоможи комусь сьогодні дрібницею: притримай двері, поступися місцем або подай річ.",
    "🤗 Похвали колегу або друга за щось добре.",
    "👂 Постав сьогодні комусь глибоке запитання: «А що робить тебе щасливим(ою)?» і вислухай відповідь.",
    "🎈 Подаруй сьогодні комусь усмішку та скажи: «Ти класний(а)!»",
    "📚 У бібліотеці чи кафе запитай у когось: «А що ти зараз читаєш?»",
    "🔥 Знайди сьогодні привід когось надихнути: дай пораду, поділися історією або власним досвідом.",
    "🎨 Зайди в нове місце (виставка, вулиця, парк) і спитай когось: «Ви тут уперше?»",
    "🌟 Якщо побачиш гарний одяг або стиль у когось — скажи про це прямо.",
    "🎧 Увімкни музику і підніми настрій друзям: надішли трек із коментарем «Тобі це сподобається!»",
    "🕊️ Сьогодні заговори з людиною старшого віку — запитай поради або побажай гарного дня.",
    "🏞️ Під час прогулянки підійди до когось із собакою та скажи: «У вас чудовий пес! Як його звати?»",
    "☕ Купи каву людині, яка стоїть за тобою в черзі. Просто так.",
    "🙌 Зроби сьогодні хоча б один дзвінок не по справі, а просто щоб поспілкуватися.",
    "🚀 Знайди нову ідею для проєкту та запиши її.",
    "🎯 Напиши 5 речей, які хочеш зробити за тиждень.",
    "🌊 Послухай звуки природи й розслабся.",
    "🍋 Спробуй сьогодні новий напій або страву.",
    "🌱 Посади рослину або подбай про неї сьогодні.",
    "🧩 Збери маленький пазл або розв’яжи головоломку.",
    "🎶 Потанцюй 5 хвилин під улюблену пісню.",
    "📅 Сплануй свій ідеальний день і запиши його.",
    "🖼️ Знайди гарну картинку й повісь її на видному місці.",
    "🤔 Напиши, чим ти пишаєшся сьогодні.",
    "💜 Зроби щось приємне для себе просто зараз."
],
    "md": [
    "✨ Scrie 3 lucruri pentru care ești recunoscător astăzi.",
    "🚶‍♂️ Fă o plimbare de 10 minute fără telefon. Respiră și observă.",
    "📝 Scrie o scurtă listă de obiective pentru mâine.",
    "🌿 Încearcă să petreci 30 de minute fără rețele sociale. Cum te simți?",
    "💧 Bea un pahar cu apă și zâmbește-ți în oglindă. Reușești!",
    "📖 Citește cel puțin 5 pagini dintr-o carte care te inspiră astăzi.",
    "🤝 Trimite un mesaj unui prieten cu care nu ai mai vorbit de ceva vreme.",
    "🖋️ Ține un jurnal timp de 5 minute — scrie tot ce-ți trece prin minte, fără filtre.",
    "🏃‍♀️ Fă o încălzire ușoară sau 10 genuflexiuni chiar acum!",
    "🎧 Ascultă muzica ta preferată și relaxează-te timp de 10 minute.",
    "🍎 Gătește-ți ceva gustos și sănătos astăzi.",
    "💭 Scrie un vis mare și un mic pas către el.",
    "🌸 Găsește ceva frumos în casa ta sau pe stradă și fă o fotografie.",
    "🛌 Înainte de culcare, gândește-te la trei lucruri care te-au făcut fericit astăzi.",
    "💌 Scrie o scrisoare pentru tine în viitor: ce vrei să-ți spui peste un an?",
    "🔄 Încearcă să faci ceva diferit astăzi, chiar și un lucru mic.",
    "🙌 Fă 3 respirații profunde, închide ochii și mulțumește-ți pentru că ești tu.",
    "🎨 Petrece 5 minute fiind creativ: schițează, scrie o poezie sau fă un colaj.",
    "🧘‍♀️ Stai 3 minute în liniște și observă-ți respirația.",
    "📂 Ordonează un raft, un sertar sau un dosar — adu puțină ordine.",
    "👋 Abordează astăzi un străin și începe o conversație prietenoasă. Poate fi doar un compliment sau o urare de zi bună!",
    "🤝 Spune «salut» la cel puțin trei oameni noi astăzi — și un zâmbet contează!",
    "💬 Pune azi cuiva o întrebare pe care de obicei nu o pui. De exemplu: «Ce te inspiră?»",
    "😊 Fă un compliment unui străin. Poate fi un barista, un vânzător sau un trecător.",
    "📱 Sună pe cineva cu care nu ai mai vorbit de mult și întreabă-l cum îi merge.",
    "💡 Începe o scurtă conversație cu un vecin sau cu cineva la coadă — doar despre vreme sau ceva din jur.",
    "🍀 Zâmbește primei persoane pe care o întâlnești astăzi. Sincer. Și observă cum reacționează.",
    "🙌 Găsește pe cineva interesant pe rețele și scrie-i un mesaj de mulțumire pentru ceea ce face.",
    "🎯 Începe azi o temă nouă de discuție: întreabă despre vise, cărți sau filme preferate.",
    "🌟 Mergi la un coleg sau o cunoștință și spune: «Mulțumesc că ești în viața mea» — și observă cum zâmbește.",
    "🔥 Dacă poți, vizitează un loc nou (cafenea, parc, magazin) și vorbește cu cineva de acolo.",
    "🌞 Dimineața spune un cuvânt frumos primei persoane pe care o vezi — începe ziua cu pozitivitate!",
    "🍀 Ajută azi pe cineva cu un gest mic: ține ușa, oferă locul, ajută cu un obiect.",
    "🤗 Laudă un coleg sau prieten pentru ceva ce a făcut bine.",
    "👂 Pune cuiva o întrebare profundă azi: «Ce te face fericit?» și ascultă răspunsul.",
    "🎈 Oferă cuiva un zâmbet și spune: «Ești minunat(ă)!»",
    "📚 Într-o bibliotecă, librărie sau cafenea, întreabă pe cineva: «Ce citești acum?»",
    "🔥 Găsește un motiv să inspiri pe cineva: dă un sfat, povestește o experiență.",
    "🎨 Vizitează un loc nou (expoziție, parc) și întreabă: «Ești pentru prima dată aici?»",
    "🌟 Dacă vezi o ținută frumoasă sau un stil la cineva — spune asta direct.",
    "🎧 Pune muzică și înveselește-ți prietenii: trimite-le o piesă cu mesajul «Ascultă, ți se va potrivi!»",
    "🕊️ Vorbește azi cu o persoană mai în vârstă — cere un sfat sau urează-i o zi bună.",
    "🏞️ La plimbare, oprește-te la cineva cu un câine și spune: «Câinele tău e minunat! Cum îl cheamă?»",
    "☕ Cumpără o cafea pentru persoana din spatele tău la coadă. Doar așa.",
    "🙌 Fă azi cel puțin un apel doar pentru a vorbi, nu de afaceri.",
    "🚀 Notează o idee nouă pentru un proiect.",
    "🎯 Scrie 5 lucruri pe care vrei să le realizezi săptămâna aceasta.",
    "🌊 Ascultă sunetele naturii și relaxează-te.",
    "🍋 Încearcă azi o băutură sau o mâncare nouă.",
    "🌱 Plantează sau îngrijește o plantă astăzi.",
    "🧩 Rezolvă un puzzle mic sau o ghicitoare.",
    "🎶 Dansează 5 minute pe melodia ta preferată.",
    "📅 Planifică-ți ziua perfectă și scrie-o.",
    "🖼️ Găsește o imagine frumoasă și pune-o la vedere.",
    "🤔 Scrie pentru ce ești mândru astăzi.",
    "💜 Fă ceva frumos pentru tine chiar acum."
],
    "be": [
    "✨ Запішы 3 рэчы, за якія ты ўдзячны(на) сёння.",
    "🚶‍♂️ Прагуляйся 10 хвілін без тэлефона. Проста дыхай і назірай.",
    "📝 Напішы кароткі спіс мэт на заўтра.",
    "🌿 Паспрабуй правесці 30 хвілін без сацсетак. Як адчуванні?",
    "💧 Выпі шклянку вады і ўсміхніся сабе ў люстэрка. Ты справішся!",
    "📖 Прачытай сёння хаця б 5 старонак кнігі, якая цябе натхняе.",
    "🤝 Напішы паведамленне сябру, з якім даўно не меў зносін.",
    "🖋️ Пішы дзённік 5 хвілін — напішы ўсё, што ў галаве, без фільтраў.",
    "🏃‍♀️ Зрабі лёгкую размінку або 10 прысяданняў прама зараз!",
    "🎧 Паслухай любімую музыку і проста адпачні 10 хвілін.",
    "🍎 Прыгатуй сабе нешта смачнае і карыснае сёння.",
    "💭 Запішы адну вялікую мару і адзін маленькі крок да яе.",
    "🌸 Знайдзі нешта прыгожае дома або на вуліцы і сфатаграфуй.",
    "🛌 Перад сном падумай пра тры рэчы, якія зрабілі цябе шчаслівым сёння.",
    "💌 Напішы ліст сабе ў будучыню: што ты хочаш сказаць праз год?",
    "🔄 Паспрабуй зрабіць сёння нешта па-іншаму, нават дробязь.",
    "🙌 Зрабі 3 глыбокія ўдыхі, зачыні вочы і падзякуй сабе за тое, што ты ёсць.",
    "🎨 Патрать 5 хвілін на творчасць — зрабі малюнак, верш або калаж.",
    "🧘‍♀️ Сядзь на 3 хвіліны ў цішыні і проста назірай за дыханнем.",
    "📂 Разбяры адну паліцу, скрыню або тэчку — зрабі парадак.",
    "👋 Падыдзі сёння да незнаёмца і пачні сяброўскую размову. Няхай гэта будзе проста камплімент ці пажаданне добрага дня!",
    "🤝 Скажы «прывітанне» хаця б трым новым людзям сёння — усмешка таксама лічыцца!",
    "💬 Спытай сёння ў кагосьці пытанне, якое звычайна не задаеш. Напрыклад: «А што цябе натхняе?»",
    "😊 Зрабі камплімент незнаёмцу. Гэта можа быць барыста, прадавец або прахожы.",
    "📱 Патэлефануй таму, з кім даўно не меў зносін, і проста спытай, як справы.",
    "💡 Завядзі кароткую размову з суседам ці чалавекам у чарзе — проста пра надвор’е або пра нешта вакол.",
    "🍀 Усміхніся першаму сустрэчнаму сёння. Шчыра. І паглядзі на рэакцыю.",
    "🙌 Знайдзі ў сацсетках цікавага чалавека і напішы яму з падзякай за тое, што ён робіць.",
    "🎯 Сёння пачні хаця б адну новую тэму ў размове: спытай пра мары, любімыя кнігі ці фільмы.",
    "🌟 Падыдзі да калегі ці знаёмага і скажы: «Дзякуй, што ты ёсць у маім жыцці» — і паглядзі, як ён(а) ўсміхнецца.",
    "🔥 Калі можаш, зайдзі ў новае месца (кафэ, парк, крама) і пагавары хоць з адным чалавекам там.",
    "🌞 Раніцай скажы добрае слова першаму сустрэчнаму — пачні дзень з пазітыву!",
    "🍀 Дапамажы сёння камусьці дробяззю: прытрымай дзверы, саступі месца, падай рэч.",
    "🤗 Пахвалі калегу або сябра за тое, што ён(а) зрабіў(ла) добра.",
    "👂 Задай сёння камусьці глыбокае пытанне: «Што робіць цябе шчаслівым(ай)?» і паслухай адказ.",
    "🎈 Падары сёння камусьці ўсмешку і скажы: «Ты класны(ая)!»",
    "📚 У бібліятэцы, кніжнай ці кавярні спытай у чалавека: «А што ты зараз чытаеш?»",
    "🔥 Знайдзі сёння прычыну кагосьці натхніць: дай параду, падзяліся гісторыяй, раскажы пра свой вопыт.",
    "🎨 Зайдзі ў новае месца (выстава, вуліца, парк) і спытай: «Вы тут упершыню?»",
    "🌟 Калі ўбачыш прыгожы ўбор або стыль у кагосьці — скажы пра гэта наўпрост.",
    "🎧 Уключы музыку і ўзнімі настрой сябрам: дашлі ім трэк з каментарыем «Паслухай, гэта табе спадабаецца!»",
    "🕊️ Пагавары сёння з чалавекам старэйшага ўзросту — спытай параду або пажадай добрага дня.",
    "🏞️ Падчас шпацыру спытай у чалавека з сабакам: «У вас цудоўны сабака! Як яго завуць?»",
    "☕ Купі каву чалавеку, які стаіць за табой у чарзе. Проста так.",
    "🙌 Зрабі сёння хаця б адзін званок не па справах, а проста каб пагутарыць.",
    "🚀 Запішы новую ідэю для праекта.",
    "🎯 Напішы 5 рэчаў, якія хочаш паспець за тыдзень.",
    "🌊 Паслухай гукі прыроды і адпачні.",
    "🍋 Паспрабуй сёння новы напой або страву.",
    "🌱 Пасадзі расліну або паклапаціся пра яе сёння.",
    "🧩 Збяры маленькі пазл або вырашы галаваломку.",
    "🎶 Танцуй 5 хвілін пад любімую песню.",
    "📅 Сплануй свой ідэальны дзень і запішы яго.",
    "🖼️ Знайдзі прыгожую карцінку і павесь яе на бачным месцы.",
    "🤔 Напішы, чым ты сёння ганарышся.",
    "💜 Зрабі нешта прыемнае для сябе прама зараз."
],

    "kk" : [
    "✨ Бүгін риза болған 3 нәрсені жазып алыңыз.",
    "🚶‍♂️ Телефонсыз 10 минут серуендеңіз. Тек тыныс алыңыз және бақылаңыз.",
    "📝 Ертеңгі мақсаттарыңыздың қысқаша тізімін жазыңыз.",
    "🌿 30 минутыңызды әлеуметтік желілерсіз өткізіп көріңіз. Қалай әсер етеді?",
    "💧 Бір стакан су ішіп, айнаға қарап өзіңізге күліңіз. Сіз мұны істей аласыз!",
    "📖 Бүгін сізді шабыттандыратын кітаптың кем дегенде 5 бетін оқыңыз.",
    "🤝 Ұзақ уақыт сөйлеспеген досыңызға хабарласыңыз немесе хат жазыңыз.",
    "🖋️ 5 минут күнделік жүргізіңіз — ойыңыздағының бәрін сүзгісіз жазыңыз.",
    "🏃‍♀️ Қазір жеңіл жаттығу жасаңыз немесе 10 отырып-тұру жасаңыз!",
    "🎧 Сүйікті музыкаңызды тыңдаңыз да, жай ғана 10 минут демалыңыз.",
    "🍎 Бүгін өзіңізге дәмді әрі пайдалы нәрсе дайындаңыз.",
    "💭 Бір үлкен арманыңызды және оған жақындау үшін бір кішкентай қадамды жазып қойыңыз.",
    "🌸 Үйіңізден немесе көшеден әдемі нәрсе тауып, суретке түсіріңіз.",
    "🛌 Ұйықтар алдында бүгін сізді бақытты еткен үш нәрсені ойлаңыз.",
    "💌 Болашақтағы өзіңізге хат жазыңыз: бір жылдан кейін не айтқыңыз келеді?",
    "🔄 Бүгін кішкентай болса да бір нәрсені басқаша жасап көріңіз.",
    "🙌 3 рет терең тыныс алып, көзіңізді жұмып, өзіңізге алғыс айтыңыз.",
    "🎨 5 минут шығармашылықпен айналысыңыз — сурет салыңыз, өлең немесе коллаж жасаңыз.",
    "🧘‍♀️ 3 минут үнсіз отырып, тек тынысыңызды бақылаңыз.",
    "📂 Бір сөрені, жәшікті немесе қалтаны ретке келтіріңіз.",
    "👋 Бүгін бір бейтаныс адаммен сөйлесіп көріңіз — комплимент айтыңыз немесе жақсы күн тілеп қойыңыз.",
    "🤝 Бүгін кемінде үш жаңа адамға «сәлем» айтыңыз — күлкі де есепке алынады!",
    "💬 Әдетте сұрамайтын сұрақты әріптесіңізге немесе танысыңызға қойып көріңіз. Мысалы: «Сізді не шабыттандырады?»",
    "😊 Бір бейтанысқа комплимент айтыңыз. Бұл бариста, сатушы немесе жай жүріп бара жатқан адам болуы мүмкін.",
    "📱 Ұзақ уақыт сөйлеспеген адамға қоңырау шалып, халін біліп көріңіз.",
    "💡 Көршіңізбен немесе кезекте тұрған адаммен қысқа әңгіме бастаңыз — ауа райы туралы да болады.",
    "🍀 Бүгін бірінші кездескен адамға күліңіз. Шын жүректен. Қалай жауап беретінін байқаңыз.",
    "🙌 Әлеуметтік желіден қызықты адам тауып, оған істеп жүрген ісі үшін алғыс айтып хабарлама жіберіңіз.",
    "🎯 Бүгін бір жаңа тақырып бастауға тырысыңыз: армандары, сүйікті кітаптары немесе фильмдері туралы сұраңыз.",
    "🌟 Әріптесіңізге немесе танысыңызға: «Менің өмірімде болғаныңыз үшін рақмет» деп айтыңыз және олардың қалай жымиғанын көріңіз.",
    "🔥 Мүмкіндігіңіз болса, жаңа жерге (кафе, парк, дүкен) барып, кем дегенде бір адаммен сөйлесіп көріңіз.",
    "🌞 Таңертең бірінші кездескен адамға жылы сөз айтыңыз — күніңіз жақсы басталсын!",
    "🍀 Бүгін біреуге кішкене көмектесіңіз: есікті ұстаңыз, орныңызды беріңіз, бір зат беріңіз.",
    "🤗 Бір әріптесіңізді немесе досыңызды жақсы жұмысы үшін мақтап қойыңыз.",
    "👂 Бүгін біреуге терең сұрақ қойыңыз: «Сізді не бақытты етеді?» және жауабын тыңдаңыз.",
    "🎈 Бүгін біреуге күліп: «Сен кереметсің!» деп айтыңыз.",
    "📚 Кітапханада, кітап дүкенінде немесе кафеде біреуге барып: «Қазір не оқып жатырсыз?» деп сұраңыз.",
    "🔥 Бүгін біреуді шабыттандыратын себеп тауып көріңіз: кеңес беріңіз, әңгіме бөлісіңіз, өз тәжірибеңізді айтыңыз.",
    "🎨 Жаңа жерге (көрме, көше, парк) барып: «Мұнда алғаш ретсіз бе?» деп сұраңыз.",
    "🌟 Біреудің әдемі стилін байқасаңыз — соны айтыңыз.",
    "🎧 Музыканы қосып, достарыңыздың көңілін көтеріңіз: сүйікті тректі пікірмен жіберіңіз: «Тыңдаңыз, бұл саған жарасады!»",
    "🕊️ Бүгін үлкен адамға барып сөйлесіңіз — кеңес сұраңыз немесе жақсы күн тілеңіз.",
    "🏞️ Ит жетелеп жүрген адамға: «Сіздің итіңіз керемет! Оның аты кім?» деп айтыңыз.",
    "☕ Кезекте артыңыздағы адамға кофе сатып алыңыз. Жай ғана.",
    "🙌 Бүгін кем дегенде бір рет іскерлік емес қоңырау шалыңыз — жай сөйлесу үшін.",
    "🚀 Жаңа жоба ойлап тауып, оны жазып қойыңыз.",
    "🎯 Осы аптада орындағыңыз келетін 5 нәрсені жазыңыз.",
    "🌊 Табиғаттың дыбыстарын тыңдап, демалыңыз.",
    "🍋 Бүгін жаңа сусын немесе тағамды байқап көріңіз.",
    "🌱 Өсімдік отырғызыңыз немесе оған күтім жасаңыз.",
    "🧩 Кішкентай жұмбақ шешіңіз немесе пазл жинаңыз.",
    "🎶 Сүйікті әніңізге 5 минут билеп көріңіз.",
    "📅 Керемет күніңізді жоспарлаңыз және жазып қойыңыз.",
    "🖼️ Әдемі сурет тауып, оны көзге көрінетін жерге іліп қойыңыз.",
    "🤔 Бүгін өзіңізді мақтан ететін бір нәрсені жазыңыз.",
    "💜 Дәл қазір өзіңіз үшін бір жақсы іс жасаңыз."
],
    "kg" : [
    "✨ Бүгүн ыраазы болгон 3 нерсени жазып көр.",
    "🚶‍♂️ Телефонсуз 10 мүнөт басып көр. Жөн гана дем ал жана айланаңды байка.",
    "📝 Эртеңки максаттарыңдын кыскача тизмесин жазыңыз.",
    "🌿 30 мүнөтүңдү социалдык тармактарсыз өткөрүп көр. Бул кандай сезим берет?",
    "📖 Бүгүн сени шыктандырган китептин жок дегенде 5 барагын оку.",
    "🤝 Көптөн бери сүйлөшпөгөн досуңа кабар жаз.",
    "🖋️ 5 мүнөткө күндөлүк жаз — башыңа келгендерди фильтрсүз жазып көр.",
    "🏃‍♀️ Азыр бир аз көнүгүү жаса! Сүйүктүү музыка коюп, 10 мүнөт эс алып көр.",
    "🍎 Бүгүн өзүңө даамдуу жана пайдалуу тамак бышыр.",
    "💭 Бир чоң кыялыңды жана ага карай бир кичинекей кадамыңды жаз.",
    "🌸 Үйүңдөн же көчөдөн кооз нерсени таап, сүрөткө түш.",
    "🛌 Уктаар алдында бүгүн сени бактылуу кылган 3 нерсе жөнүндө ойлон.",
    "🔄 Бүгүн кичине болсо да бир нерсени башкача кылууга аракет кыл.",
    "🙌 3 терең дем алып, көзүңдү жумуп, өзүң болгонуң үчүн ыраазычылык айт.",
    "🎨 Чыгармачылыкка 5 мүнөт бөл — сүрөт тарт, ыр жаз же коллаж жаса.",
    "🧘‍♀️ 3 мүнөт унчукпай отуруп, бир папканы же бурчту жыйнап көр.",
    "👋 Бейтааныш адамга жакын барып, жакшы сөз айт же мактап кой.",
    "🤝 Бүгүн жок дегенде үч жаңы адамга 'салам' деп жылмай.",
    "💬 Кесиптешиңе же таанышыңа адатта бербей турган суроо бер.",
    "📱 Көптөн бери сүйлөшпөгөн адамга чалып, ал-акыбалын сура.",
    "💡 Кошунаң же кезекте турган адам менен кыскача сүйлөш — аба ырайы жөнүндө да болот.",
    "🍀 Бүгүн бирөөгө жылмайып, соцтармакта аларга ыраазычылык билдир.",
    "🎯 Бүгүн жок дегенде бир жаңы теманы башта: кыялдарың, сүйүктүү китептериң же кинолоруң жөнүндө сура.",
    "🌟 Кесиптешиңе же таанышыңа: 'Жашоомдо болгонуң үчүн рахмат' деп айт.",
    "🌞 Таңкы алгачкы жолу жолуккан адамга жакшы сөз айт.",
    "🍀 Бүгүн бирөөгө кичинекей жардам бер: эшикти кармап, ордуңду бошот же бир нерсе берип жибер.",
    "🤗 Кесиптешиңди же досуңду жакшы иши үчүн мактап: 'Сен укмушсуң!' деп айт.",
    "📚 Китепканага же китеп дүкөнүнө барып: 'Азыр эмне окуп жатасыз?' деп сура.",
    "🔥 Бүгүн кимдир бирөөнү шыктандыруу үчүн себеп тап: кеңеш бер, окуяң менен бөлүш.",
    "🎨 Жаңы жерге (көргөзмө, сейилбак) барып, кимдир бирөөнүн стилин жактырсаң — айт.",
    "🎧 Музыка коюп, жакындарыңа жаккан тректи жөнөтүп, 'Бул сага жагат!' деп жаз.",
    "🕊️ Бүгүн улгайган адам менен сүйлөш: кеңеш сура же жакшы күн каала.",
    "🏞️ Ит менен сейилдеп жүргөн адамга: 'Канча сонун ит! Аты ким?' деп сура.",
    "☕ Артыңда турган адамга кофе сатып бер.",
    "🙌 Бүгүн жок дегенде бир жолу жөн гана сүйлөшүү үчүн телефон чал.",
    "🚀 Долбоор үчүн жаңы идея ойлоп таап, жазып кой.",
    "🎯 Ушул аптада бүтүргүң келген 5 нерсени жазыңыз.",
    "🌋 Табияттын үнүн угуп, жаңы суусундук же тамак татып көр.",
    "🌱 Бүгүн өсүмдүк отургуз же ага кам көр.",
    "🧩 Кичинекей табышмак чеч же пазл чогулт.",
    "🎶 Сүйүктүү ырыңа 5 мүнөт бийле.",
    "📅 Идеалдуу күнүңдү пландап, жазып кой.",
    "🖼️ Керемет сүрөт таап, көрүнүктүү жерге илип кой.",
    "💜 Азыр өзүң үчүн жакшы нерсе жаса."
],
    "hy" : [
  "✨ Գրիր 3 բան, որոնց համար այսօր շնորհակալ ես։",
  "🚶‍♂️ Կատարիր 10 րոպե զբոսանք առանց հեռախոսի․ պարզապես շնչիր և դիտիր շրջապատդ։",
  "📝 Գրիր վաղվա նպատակների կարճ ցուցակ։",
  "🌿 Փորձիր 30 րոպե անցկացնել առանց սոցիալական ցանցերի․ ինչպե՞ս է դա զգացվում։",
  "💧 Խմիր մեկ բաժակ ջուր և ժպտա ինքդ քեզ հայելու մեջ․ դու հրաշալի ես։",
  "📖 Կարդա այսօր քեզ ոգեշնչող գրքի առնվազն 5 էջ։",
  "🤝 Գրիր մի ընկերոջ, ում հետ վաղուց չես շփվել։",
  "🖋️ Պահիր օրագիր 5 րոպե՝ գրիր գլխումդ եղած ամեն բան առանց ֆիլտրերի։",
  "🏃‍♀️ Կատարիր թեթև մարզում կամ 10 նստացատկ հենց հիմա։",
  "🎧 Լսիր սիրելի երաժշտությունդ և պարզապես հանգստացիր 10 րոպե։",
  "🍎 Պատրաստիր քեզ համար ինչ‑որ համեղ ու առողջարար բան։",
  "💭 Գրիր մեկ մեծ երազանք և մեկ փոքր քայլ դեպի այն։",
  "🌸 Գտիր տանը կամ դրսում ինչ‑որ գեղեցիկ բան և լուսանկարիր։",
  "🛌 Քնելուց առաջ մտածիր երեք բանի մասին, որոնք այսօր քեզ երջանկացրին։",
  "💌 Գրիր նամակ քո ապագա «ես»-ին․ ի՞նչ կուզենայիր ասել մեկ տարի հետո։",
  "🔄 Փորձիր այսօր ինչ‑որ բան անել այլ կերպ, թեկուզ մանրուք։",
  "🙌 Վերցրու 3 խորը շունչ, փակիր աչքերդ և շնորհակալություն հայտնիր ինքդ քեզ, որ դու կաս։",
  "🎨 5 րոպե ստեղծագործիր՝ նկարիր, գրիր բանաստեղծություն կամ պատրաստիր կոլաժ։",
  "🧘‍♀️ Նստիր 3 րոպե լռության մեջ և պարզապես հետևիր քո շնչառությանը։",
  "📂 Դասավորիր մի դարակ, սեղան կամ թղթապանակ՝ բեր փոքրիկ կարգուկանոն։",
  "👋 Մոտեցիր այսօր անծանոթի և սկսիր բարեկամական զրույց․ թող դա լինի հաճոյախոսություն կամ բարեմաղթանք։",
  "🤝 Ասա «բարև» առնվազն երեք նոր մարդկանց այսօր․ ժպիտն էլ է կարևոր։",
  "💬 Հարցրու մեկին հարց, որը սովորաբար չես տալիս․ օրինակ՝ «Ի՞նչն է քեզ ոգեշնչում»։",
  "😊 Գովիր անծանոթի՝ դա կարող է լինել բարիստա, վաճառող կամ անցորդ։",
  "📱 Զանգահարիր մեկին, ում հետ վաղուց չես խոսել, և պարզապես հարցրու՝ ինչպես է նա։",
  "💡 Խոսիր հարևանի կամ հերթում կանգնած մարդու հետ՝ եղանակի կամ շրջապատի մասին։",
  "🍀 Ժպտա առաջին հանդիպած մարդուն այսօր անկեղծորեն և տես, թե ինչպես է նա արձագանքում։",
  "🙌 Գտիր հետաքրքիր մարդու սոցիալական ցանցերում և գրիր շնորհակալություն նրա արածի համար։",
  "🎯 Այսօր զրույցի ընթացքում հարցրու երազանքների, սիրելի գրքերի կամ ֆիլմերի մասին։",
  "🌟 Ասա գործընկերոջդ կամ ընկերոջդ․ «Շնորհակալություն, որ կաս իմ կյանքում» և տես, թե ինչպես է նա ժպտում։",
  "🔥 Գնա նոր վայր (սրճարան, այգի, խանութ) և սկսիր զրույց որևէ մեկի հետ այնտեղ։",
  "🌞 Առավոտյան ասա բարի խոսք առաջին հանդիպած մարդուն, որպեսզի օրը սկսվի դրական։",
  "🍀 Օգնիր ինչ‑որ մեկին այսօր՝ պահիր դուռը, զիջիր տեղդ կամ նվիրիր ինչ‑որ բան։",
  "🤗 Գովիր գործընկերոջդ կամ ընկերոջդ ինչ‑որ լավ բանի համար, որ արել է։",
  "👂 Հարցրու մեկին․ «Ի՞նչն է քեզ երջանկացնում» և լսիր պատասխանը։",
  "🎈 Պարգևիր ինչ‑որ մեկին ժպիտ և ասա․ «Դու հրաշալի ես»։",
  "📚 Հարցրու գրադարանում կամ սրճարանում․ «Ի՞նչ ես հիմա կարդում»։",
  "🔥 Այսօր ոգեշնչիր ինչ‑որ մեկին՝ տուր խորհուրդ, պատմիր պատմություն կամ կիսվիր փորձովդ։",
  "🎨 Գնա նոր վայր և հարցրու ինչ‑որ մեկին․ «Սա՞ է քո առաջին անգամը այստեղ»։",
  "🌟 Եթե տեսնում ես մեկի վրա գեղեցիկ հագուստ կամ ոճ, ասա դա ուղիղ։",
  "🎧 Կիսվիր ընկերներիդ հետ սիրելի երգովդ և գրիր․ «Լսիր, սա քեզ կհարմարի»։",
  "🕊️ Այսօր խոսիր տարեց մարդու հետ՝ հարցրու խորհուրդ կամ մաղթիր լավ օր։",
  "🏞️ Քայլելու ժամանակ մոտեցիր մեկին, ով շուն ունի, և ասա․ «Քո շունը հրաշալի է, ի՞նչ է նրա անունը»։",
  "☕ Գնիր սուրճ հերթում կանգնած մարդու համար՝ պարզապես որովհետև։",
  "🙌 Այսօր կատարիր գոնե մեկ զանգ ոչ գործնական նպատակով՝ պարզապես զրուցելու համար։",
  "🚀 Գտիր նոր գաղափար և գրիր այն։",
  "🎯 Գրիր 5 բան, որոնք ուզում ես հասցնել այս շաբաթ։",
  "🌊 Լսիր բնության ձայները և հանգստացիր։",
  "🍋 Փորձիր այսօր նոր ըմպելիք կամ ուտեստ։",
  "🌱 Այսօր տնկիր բույս կամ խնամիր այն։",
  "🧩 Լուծիր փոքրիկ հանելուկ կամ գլուխկոտրուկ։",
  "🎶 Պարիր 5 րոպե սիրելի երգիդ տակ։",
  "📅 Պլանավորիր քո իդեալական օրը և գրիր այն։",
  "🖼️ Գտիր գեղեցիկ նկար և կախիր այն աչքի ընկնող տեղում։",
  "🤔 Գրիր, թե ինչով ես հպարտանում այսօր։",
  "💜 Հենց հիմա արա ինչ‑որ հաճելի բան ինքդ քեզ համար։"
],
"ka" : [
  "✨ ჩაწერეთ 3 რამ, რისთვისაც დღეს მადლიერი ხართ.",
  "🚶‍♂️ გაისეირნეთ 10 წუთი ტელეფონის გარეშე. უბრალოდ ისუნთქეთ და დააკვირდით.",
  "📝 დაწერეთ ხვალინდელი მიზნების მოკლე სია.",
  "🌿 სცადეთ 30 წუთი სოციალური მედიის გარეშე გაატაროთ. როგორია ეს შეგრძნება?",
  "💧 დალიეთ ერთი ჭიქა წყალი და გაუღიმეთ საკუთარ თავს სარკეში. თქვენ ამას აკეთებთ!",
  "📖 წაიკითხეთ წიგნის მინიმუმ 5 გვერდი, რომელიც დღეს შთაგაგონებთ.",
  "🤝 მისწერეთ მეგობარს, ვისთანაც დიდი ხანია არ გისაუბრიათ.",
  "🖋️ აწარმოეთ დღიური 5 წუთის განმავლობაში — ჩაწერეთ ყველაფერი, რაც თავში გიტრიალებთ, ფილტრების გარეშე.",
  "🏃‍♀️ გააკეთეთ მსუბუქი გახურება ან 10 ჩაჯდომა ახლავე!",
  "🎧 მოუსმინეთ თქვენს საყვარელ მუსიკას და უბრალოდ დაისვენეთ 10 წუთით.",
  "🍎 მოამზადეთ რაიმე გემრიელი და ჯანსაღი დღეს.",
  "💭 ჩაწერეთ ერთი დიდი ოცნება და ერთი პატარა ნაბიჯი მისკენ.",
  "🌸 იპოვეთ რაიმე ლამაზი თქვენს სახლში ან ქუჩაში და გადაიღეთ ფოტო.",
  "🛌 დაძინებამდე იფიქრეთ სამ რამეზე, რამაც დღეს უფრო ბედნიერი გაგხადათ.",
  "💌 დაწერეთ წერილი თქვენს მომავალ მეს: რა გსურთ თქვათ ერთ წელიწადში?",
  "🔄 შეეცადეთ დღეს რამე განსხვავებულად გააკეთოთ, თუნდაც პატარა რამ.",
  "🙌 3-ჯერ ღრმად ჩაისუნთქეთ, დახუჭეთ თვალები და მადლობა გადაუხადეთ საკუთარ თავს, რომ ხართ ის, ვინც ხართ.",
  "🎨 დაუთმეთ 5 წუთი შემოქმედებითობას — დახატეთ სურათი, ლექსი ან კოლაჟი.",
  "🧘‍♀️ დაჯექით 3 წუთით ჩუმად და უბრალოდ უყურეთ თქვენს სუნთქვას.",
  "📂 დაალაგეთ ერთი თარო, უჯრა ან საქაღალდე — ცოტა რომ დაალაგოთ.",
  "👋 მიუახლოვდით უცნობ ადამიანს დღეს და დაიწყეთ მეგობრული საუბარი. დაე, ეს იყოს მხოლოდ კომპლიმენტი ან კარგი დღის სურვილი!",
  "🤝 მიესალმეთ დღეს მინიმუმ სამ ახალ ადამიანს — ღიმილიც მნიშვნელოვანია!",
  "💬 ჰკითხეთ კოლეგას ან ნაცნობს დღეს ისეთი კითხვა, რომელსაც ჩვეულებრივ არ სვამთ. მაგალითად: „რა გაძლევთ შთაგონებას?“",
  "😊 უთხარით უცნობს კომპლიმენტი — ეს შეიძლება იყოს ბარისტა, გამყიდველი ან გამვლელი.",
  "📱 დაურეკეთ ადამიანს, ვისთანაც დიდი ხანია არ გისაუბრიათ და უბრალოდ ჰკითხეთ, როგორ არის.",
  "💡 დაიწყეთ მოკლე საუბარი მეზობელთან ან რიგში მდგომ ადამიანთან — უბრალოდ ამინდზე ან თქვენს გარშემო არსებულ რამეზე.",
  "🍀 გაუღიმეთ პირველ ადამიანს, ვისაც დღეს შეხვდებით გულწრფელად და ნახეთ, როგორ რეაგირებს.",
  "🙌 იპოვეთ საინტერესო ადამიანი სოციალურ ქსელებში და მისწერეთ მას მადლობა იმისთვის, რასაც აკეთებს.",
  "🎯 დაიწყეთ საუბარი მინიმუმ ერთი ახალი ნაცნობი თემით დღეს: ჰკითხეთ ოცნებებზე, საყვარელ წიგნებზე ან ფილმებზე.",
  "🌟 მიდით კოლეგასთან ან ნაცნობთან და უთხარით: „მადლობა, რომ ჩემს ცხოვრებაში ხართ“ — და უყურეთ, როგორ იღიმება.",
  "🔥 თუ შესაძლებელია, წადით ახალ ადგილას (კაფე, პარკი, მაღაზია) და დაიწყეთ საუბარი მინიმუმ ერთ ადამიანთან იქ.",
  "🌞 დილით პირველ შემხვედრ ადამიანს თბილი სიტყვა უთხარით — დღე პოზიტიურ ნოტაზე დაეწყოს!",
  "🍀 დაეხმარეთ ვინმეს დღეს წვრილმანში: კარი გაუღეთ, ადგილი დაუთმეთ, რამე მიეცით.",
  "🤗 შეაქეთ კოლეგა ან მეგობარი იმისთვის, რაც კარგად გააკეთა.",
  "👂 დაუსვით ვინმეს დღეს ღრმა კითხვა: „რა გაბედნიერებთ?“ და მოუსმინეთ პასუხს.",
  "🎈 აჩუქეთ ვინმეს ღიმილი დღეს და უთხარით: „შენ საოცარი ხარ!“",
  "📚 მიდით ვინმესთან ბიბლიოთეკაში, წიგნის მაღაზიაში ან კაფეში და ჰკითხეთ: „რას კითხულობ ახლა?“",
  "🔥 იპოვეთ მიზეზი, რომ დღეს ვინმეს შთააგონოთ: მიეცით რჩევა, გაუზიარეთ ისტორია, ისაუბრეთ თქვენს გამოცდილებაზე.",
  "🎨 წადით ახალ ადგილას (გამოფენაზე, ქუჩაზე, პარკში) და ჰკითხეთ ვინმეს: „პირველად ხართ აქ?“",
  "🌟 თუ ვინმეზე ლამაზ სამოსს ან სტილს ხედავთ, პირდაპირ უთხარით.",
  "🎧 ჩართეთ მუსიკა და გაამხნევეთ თქვენი მეგობრები: გაუგზავნეთ მათ თქვენთვის სასურველი ტრეკი კომენტარით: „მოუსმინე, ეს მოგერგება!“",
  "🕊️ დღესვე სცადეთ ხანდაზმულ ადამიანთან საუბარი — რჩევა სთხოვეთ ან უბრალოდ კარგი დღე უსურვეთ.",
  "🏞️ ძაღლის გასეირნებისას მიდით ვინმესთან და უთხარით: „შენი ძაღლი საოცარია! რა ჰქვია მას?“",
  "☕ უყიდეთ ყავა რიგში მდგომ ადამიანს — უბრალოდ იმიტომ.",
  "🙌 დღესვე დაურეკეთ მინიმუმ ერთ არასამსახურებრივ ზარს — უბრალოდ სასაუბროდ.",
  "🚀 იპოვეთ ახალი იდეა პროექტისთვის და ჩაიწერეთ.",
  "🎯 ჩაწერეთ 5 რამ, რისი გაკეთებაც გსურთ ამ კვირაში.",
  "🌊 მოუსმინეთ ბუნების ხმებს და დაისვენეთ.",
  "🍋 გასინჯეთ ახალი სასმელი ან საჭმელი დღეს.",
  "🌱 დარგეთ ან მოუარეთ მცენარე დღეს.",
  "🧩 ამოხსენით პატარა თავსატეხი ან გამოცანა.",
  "🎶 იცეკვეთ 5 წუთის განმავლობაში თქვენი საყვარელი სიმღერის რიტმში.",
  "📅 დაგეგმეთ თქვენი იდეალური დღე და ჩაიწერეთ.",
  "🖼️ იპოვეთ ლამაზი სურათი და ჩამოკიდეთ თვალსაჩინო ადგილას.",
  "🤔 დაწერეთ, რითი ამაყობთ დღეს.",
  "💜 გააკეთეთ რაიმე სასიამოვნო საკუთარი თავისთვის ახლავე."
],
"ce" : [
  "✨ ДӀаязде таханахь баркалла бохуш долу 3 хӀума.",
  "🚶‍♂️ Телефон йоцуш 10 минотехь лела. Са а даьккхина, тергал де.",
  "📝 Кхана хир йолчу Ӏалашонийн жима список язъе.",
  "🌿 30 минот соца медиенаш йоцуша ца хаамаш — кхин тӀехь дахьанаш.",
  "💧 Цхьа стакан хи а молуш, куьзхьа хьалха велакъежа. Хьо лелош ву!",
  "📖 Тахана хьайна догойуш йолчу киншкин лаххара а 5 агӀо еша.",
  "🤝 Смс язъе хьайца къамел ца диначу доттагӀчуьнга.",
  "🖋️ 5 минотехь дӀайазде хьайна хилахь – фильтр ешна.",
  "🏃‍♀️ Хьажа хийцара хийттара, я 10 чӀажо хаамаш тӀехь.",
  "🎧 Лаха хьайна лелош йоцу музика, 10 минот дац даьккха.",
  "🍎 Лаха дийна гӀазотто хьажа хьалха лелоша и пайдеш.",
  "💭 ДӀайазде цхьа кхулда къобал хӀума да цхьа мацахь мотт хӀумаш.",
  "🌸 Лаха хьажа кӀан йолуш лаьм дац даьккха, сурт дагӀа.",
  "🛌 ДӀавижале даьккха 3 хӀуман, хьажахь лахахь таханахь дийца хьоьшу.",
  "💌 Лаха хьалха ца хийцара «со» – ма лелош хьоьшу цхьанна шо?",
  "🔄 Цхьа мацахь хийцара тӀе хийцар, да мацахь цхьа хийцар.",
  "🙌 3 хӀежа йоцуш, ца хьажахь дӀайаш, шун йоцуша хьо болу хьажар.",
  "🎨 5 минот кхоллараллин болх – сурт дагӀа, ши дагӀа, коллаж.",
  "🧘‍♀️ 3 минотехь чума ца хаам, тӀаьккха хьовсаш.",
  "📂 Къамел тӀехь да аьтта ахьац, малача хила.",
  "👋 Хийрачу стагана ца гӀой, къамел къолла комплимент.",
  "🤝 3 хийрачу стаганаш «салам» ала – велакъежар а лоруш ду.",
  "💬 Коллегаш кхин йац, хӀин йац: «Мох болу хьоьшу хӀум?»",
  "😊 Комплимент хийрачу стагана – бариста, йохкархо, тӀехволуш.",
  "📱 Телефон тоха цхьа ю, хьайца ца диначу стаге, со лела?",
  "💡 ДӀадоладе мела жимма, стаганаш да тӀехволуш – кхин аьтта ам, кхин агӀо.",
  "🍀 Хьалха хийрачу стагана ца хьакъе лаьтта, велакъежа.",
  "🙌 Интересан хӀун йац соца медиенаш тӀехь, дӀайазде йа.",
  "🎯 Цхьа къобал кхолларалли тема лаьтта – книшка, кинема, къобал.",
  "🌟 Коллегаш лаьтта, дӀадаш: «Дик къобал хьоьшу хьажа»",
  "🔥 Кафе, парк, туька – кхин гӀой, стаганаш къамел даьккха.",
  "🌞 Юйранна хьайна дуьхьалкхеттачу стаге комплимент ала.",
  "🍀 Къобал ахӀалло: тӀехьа кар даьккха, ордуш даьккха.",
  "🤗 Коллегаш даьккха: «Дик болу хьажа!»",
  "👂 Цхьа хӀум хьоьшу ирсе дерг, хьоьшу лаха?",
  "🎈 Тахана цхьа велакъежа, дӀайазде: «Шен дик болу!»",
  "📚 КинскагӀа лаьтта, къамел: «Ма къобал хьоьшу?»",
  "🔥 Цхьа къобал йац: дацхье, дийцар лаьтта, хьалха болу.",
  "🎨 Керлачу метте лаьтта, стаганаш: «Цхьанна кхин дуй?»",
  "🌟 Лахахь лахара, комплимент ала.",
  "🎧 Музика дагӀа, дӀайазде друзяш: «Лаха хьоьшу!»",
  "🕊️ Хьажа стаганаш лаьтта, хьажа хьалха болу.",
  "🏞️ Йогу хьакъе лаьтта: «Шен йогу дик болу! Ма цӀе хӀун?»",
  "☕ Хьакъе лаьттачунна кофе хила.",
  "🙌 Цхьа ма телефон тоха, ца бизнес, просто чата.",
  "🚀 Лаха цхьа новая идея, дӀайазде.",
  "🎯 Цхьа 5 хӀума дӀайазде, кхин аьтта хьалха.",
  "🌊 Лаха табиатан деш, лаха хьажа.",
  "🍋 Лаха юрг хьажа.",
  "🌱 Лаха орамат, тӀехь хийцара.",
  "🧩 Жима хӀетал-метал дац даьккха.",
  "🎶 5 минотехь къобал музика тӀехь дацхьа.",
  "📅 Лаха идеал день, дӀайазде.",
  "🖼️ Сурт дагӀа, кхеташ йолуш.",
  "🤔 ДӀайазде мох а лаьтта, хьажа болу.",
  "💜 Лаха дӀахӀуьйре хьалха болу."
],
"en" : [
  "✨ Write down 3 things you're grateful for today.",
  "🚶‍♂️ Take a 10-minute walk without your phone. Just breathe and observe.",
  "📝 Write a short list of goals for tomorrow.",
  "🌿 Try spending 30 minutes without social media. How does that feel?",
  "💧 Drink a glass of water and smile at yourself in the mirror. You're doing great!",
  "📖 Read at least 5 pages of a book that inspires you today.",
  "🤝 Text a friend you haven't talked to in a while.",
  "🖋️ Keep a journal for 5 minutes — write everything that's in your head without filters.",
  "🏃‍♀️ Do a light warm-up or 10 squats right now!",
  "🎧 Listen to your favorite music and just relax for 10 minutes.",
  "🍎 Cook yourself something tasty and healthy today.",
  "💭 Write down one big dream and one small step towards it.",
  "🌸 Find something beautiful in your house or on the street and take a photo.",
  "🛌 Before going to bed, think about three things that made you happier today.",
  "💌 Write a letter to your future self: what do you want to say in a year?",
  "🔄 Try to do something differently today, even a small thing.",
  "🙌 Take 3 deep breaths, close your eyes and thank yourself for being you.",
  "🎨 Spend 5 minutes being creative — sketch a picture, write a poem or make a collage.",
  "🧘‍♀️ Sit for 3 minutes in silence and just watch your breathing.",
  "📂 Sort out one shelf, drawer or folder to tidy up a little.",
  "👋 Approach a stranger today and start a friendly conversation. Let it be just a compliment or a wish for a good day!",
  "🤝 Say 'hi' to at least three new people today — a smile counts too!",
  "💬 Ask a colleague or acquaintance a question today that you usually don’t ask. For example: 'What inspires you?'",
  "😊 Compliment a stranger. It could be a barista, a salesperson or a passerby.",
  "📱 Call someone you haven’t talked to in a while and just ask how they’re doing.",
  "💡 Start a short conversation with a neighbor or a person in line — just about the weather or something around you.",
  "🍀 Smile at the first person you meet today. Sincerely. And see how they react.",
  "🙌 Find an interesting person on social networks and write them a message thanking them for what they do.",
  "🎯 Start at least one new topic of conversation today: ask about dreams, favorite books or movies.",
  "🌟 Go up to a colleague or acquaintance and say: 'Thank you for being in my life' — and watch how they smile.",
  "🔥 If possible, go to a new place (cafe, park, store) and start a conversation with at least one person there.",
  "🌞 In the morning, say a kind word to the first person you meet — let your day start on a positive note!",
  "🍀 Help someone today with a little thing: hold the door, give up your seat, give them something.",
  "🤗 Praise a colleague or friend for something they did well.",
  "👂 Ask someone a deep question today: 'What makes you happy?' and listen to the answer.",
  "🎈 Give someone a smile today and say: 'You're awesome!'",
  "📚 Go up to someone in a library, bookstore, or cafe and ask: 'What are you reading now?'",
  "🔥 Find a reason to inspire someone today: give advice, share a story, talk about your experience.",
  "🎨 Go to a new place (exhibition, street, park) and ask someone: 'Is this your first time here?'",
  "🌟 If you see a beautiful outfit or style on someone, say so directly.",
  "🎧 Turn on some music and cheer up your friends: send them a track you like with the comment: 'Listen, this will suit you!'",
  "🕊️ Try talking to an older person today — ask for advice or just wish them a good day.",
  "🏞️ While walking a dog, go up to someone and say: 'Your dog is amazing! What's their name?'",
  "☕ Buy a coffee for the person behind you in line. Just because.",
  "🙌 Make at least one non-business phone call today, just to chat.",
  "🚀 Find a new idea for a project and write it down.",
  "🎯 Write down 5 things you want to accomplish this week.",
  "🌊 Listen to the sounds of nature and relax.",
  "🍋 Try a new drink or food today.",
  "🌱 Plant or take care of a plant today.",
  "🧩 Do a small puzzle or solve a riddle.",
  "🎶 Dance for 5 minutes to your favorite song.",
  "📅 Plan your perfect day and write it down.",
  "🖼️ Find a beautiful picture and hang it in a prominent place.",
  "🤔 Write down what you are proud of yourself for today.",
  "💜 Do something nice for yourself right now."
]
}
   
# 🎯 Тексты для разных языков
goal_texts = {
        "ru": {
            "no_args": "✏️ Чтобы поставить цель, напиши так:\n/goal Прочитать 10 страниц до 2025-06-28 напомни",
            "limit": "🔒 В бесплатной версии можно ставить только 3 цели в день.\nХочешь больше? Оформи Mindra+ 💜",
            "bad_date": "❗ Неверный формат даты. Используй ГГГГ-ММ-ДД",
            "added": "🎯 Цель добавлена:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Напоминание включено"
        },
        "uk": {
            "no_args": "✏️ Щоб поставити ціль, напиши так:\n/goal Прочитати 10 сторінок до 2025-06-28 нагадай",
            "limit": "🔒 У безкоштовній версії можна ставити лише 3 цілі на день.\nХочеш більше? Оформи Mindra+ 💜",
            "bad_date": "❗ Невірний формат дати. Використовуй РРРР-ММ-ДД",
            "added": "🎯 Ціль додана:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Нагадування увімкнено"
        },
        "be": {
            "no_args": "✏️ Каб паставіць мэту, напішы так:\n/goal Прачытай 10 старонак да 2025-06-28 нагадай",
            "limit": "🔒 У бясплатнай версіі можна ставіць толькі 3 мэты на дзень.\nХочаш больш? Аформі Mindra+ 💜",
            "bad_date": "❗ Няправільны фармат даты. Выкарыстоўвай ГГГГ-ММ-ДД",
            "added": "🎯 Мэта дададзена:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 Напамін уключаны"
        },
        "kk": {
            "no_args": "✏️ Мақсат қою үшін былай жаз:\n/goal 10 бет оқу 2025-06-28 дейін еске сал",
            "limit": "🔒 Тегін нұсқада күніне тек 3 мақсат қоюға болады.\nКөбірек керек пе? Mindra+ алыңыз 💜",
            "bad_date": "❗ Күн форматы қате. ЖЖЖЖ-АА-КК түрінде жазыңыз",
            "added": "🎯 Мақсат қосылды:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Еске салу қосылды"
        },
        "kg": {
            "no_args": "✏️ Максат коюу үчүн мындай жаз:\n/goal 10 бет оку 2025-06-28 чейин эскертип кой",
            "limit": "🔒 Акысыз версияда күнүнө 3 гана максат коюуга болот.\nКөбүрөөк керекпи? Mindra+ жазылуу 💜",
            "bad_date": "❗ Датанын форматы туура эмес. ЖЖЖЖ-АА-КК колдон",
            "added": "🎯 Максат кошулду:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Эскертүү күйгүзүлдү"
        },
        "hy": {
            "no_args": "✏️ Նպատակ դնելու համար գրիր այսպես:\n/goal Կարդալ 10 էջ մինչև 2025-06-28 հիշեցրու",
            "limit": "🔒 Անվճար տարբերակում կարելի է օրական միայն 3 նպատակ դնել.\nՈւզում ես ավելին? Միացիր Mindra+ 💜",
            "bad_date": "❗ Սխալ ամսաթվի ձևաչափ. Օգտագործիր ՏՏՏՏ-ԱԱ-ՕՕ",
            "added": "🎯 Նպատակ ավելացվեց:",
            "deadline": "🗓 Վերջնաժամկետ:",
            "remind": "🔔 Հիշեցումը միացված է"
        },
        "ce": {
            "no_args": "✏️ Мацахь кхоллар, йаьллаца:\n/goal Къобалле 10 агӀо 2025-06-28 даьлча эха",
            "limit": "🔒 Аьтто версия хийцна, цхьаьнан 3 мацахь дина кхолларш йолуш.\nКъобал? Mindra+ 💜",
            "bad_date": "❗ Дата формат дукха. ГГГГ-ММ-ДД формата язде",
            "added": "🎯 Мацахь тӀетоха:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 ДӀадела хийна"
        },
        "md": {
            "no_args": "✏️ Pentru a seta un obiectiv, scrie așa:\n/goal Citește 10 pagini până la 2025-06-28 amintește",
            "limit": "🔒 În versiunea gratuită poți seta doar 3 obiective pe zi.\nVrei mai multe? Obține Mindra+ 💜",
            "bad_date": "❗ Format de dată incorect. Folosește AAAA-LL-ZZ",
            "added": "🎯 Obiectiv adăugat:",
            "deadline": "🗓 Termen limită:",
            "remind": "🔔 Memento activat"
        },
        "ka": {
            "no_args": "✏️ მიზნის დასაყენებლად დაწერე ასე:\n/goal წავიკითხო 10 გვერდი 2025-06-28-მდე შემახსენე",
            "limit": "🔒 უფასო ვერსიაში დღეში მხოლოდ 3 მიზნის დაყენება შეგიძლია.\nგინდა მეტი? გამოიწერე Mindra+ 💜",
            "bad_date": "❗ არასწორი თარიღის ფორმატი. გამოიყენე წწწწ-თთ-რრ",
            "added": "🎯 მიზანი დამატებულია:",
            "deadline": "🗓 ბოლო ვადა:",
            "remind": "🔔 შეხსენება ჩართულია"
        },
        "en": {
            "no_args": "✏️ To set a goal, write like this:\n/goal Read 10 pages by 2025-06-28 remind",
            "limit": "🔒 In the free version you can set only 3 goals per day.\nWant more? Get Mindra+ 💜",
            "bad_date": "❗ Wrong date format. Use YYYY-MM-DD",
            "added": "🎯 Goal added:",
            "deadline": "🗓 Deadline:",
            "remind": "🔔 Reminder is on"
        },
    }

POINTS_ADDED_HABIT = {
    "ru": "Готово! +2 поинта.",
    "uk": "Готово! +2 бали.",
    "en": "Done! +2 points.",
    "md": "Gata! +2 puncte.",
    "be": "Гатова! +2 балы.",
    "kk": "Дайын! +2 ұпай.",
    "kg": "Даяр! +2 упай.",
    "hy": "Պատրաստ է. +2 միավոր։",
    "ka": "მზადაა! +2 ქულა.",
    "ce": "Дайо! +2 балл."
}

# 🌐 Сообщения выбора привычки
HABIT_SELECT_MESSAGE = {
    "ru": "Выберите привычку, которую хотите отметить:",
    "uk": "Виберіть звичку, яку хочете відзначити:",
    "en": "Choose the habit you want to mark:",
    "md": "Alegeți obiceiul pe care doriți să îl marcați:",
    "be": "Абярыце звычку, якую хочаце адзначыць:",
    "kk": "Белгілеуді қалаған әдетті таңдаңыз:",
    "kg": "Белгилегиңиз келген адатты тандаңыз:",
    "hy": "Ընտրեք սովորությունը, որը ցանկանում եք նշել:",
    "ka": "აირჩიეთ ჩვევა, რომლის მონიშვნაც გსურთ:",
    "ce": "ДӀайаккх а, кхузур тӀаьхьара а марк хийцам:"
}

LANG_PATTERNS = {
    "ru": {
        "deadline": r"до (\d{4}-\d{2}-\d{2})",
        "remind": "напомни"
    },
    "uk": {
        "deadline": r"до (\d{4}-\d{2}-\d{2})",
        "remind": "нагадай"
    },
    "be": {
        "deadline": r"да (\d{4}-\d{2}-\d{2})",
        "remind": "нагадай"
    },
    "kk": {
        "deadline": r"(\d{4}-\d{2}-\d{2}) дейін",
        "remind": "еске сал"
    },
    "kg": {
        "deadline": r"(\d{4}-\d{2}-\d{2}) чейин",
        "remind": "эскертип кой"
    },
    "hy": {
        "deadline": r"մինչև (\d{4}-\d{2}-\d{2})",
        "remind": "հիշեցրու"
    },
    "ce": {
        "deadline": r"(\d{4}-\d{2}-\d{2}) даьлча",
        "remind": "эха"
    },
    "md": {
        "deadline": r"până la (\d{4}-\d{2}-\d{2})",
        "remind": "amintește"
    },
    "ka": {
        "deadline": r"(\d{4}-\d{2}-\d{2})-მდე",
        "remind": "შემახსენე"
    },
    "en": {
        "deadline": r"by (\d{4}-\d{2}-\d{2})",
        "remind": "remind"
    }
}

texts = {
        "ru": {
            "no_args": "✏️ Укажи номер привычки, которую ты выполнил(а):\n/habit_done 0",
            "bad_arg": "⚠️ Укажи номер привычки (например `/habit_done 0`)",
            "done": "✅ Привычка №{index} отмечена как выполненная! Молодец! 💪 +5 очков!",
            "not_found": "❌ Не удалось найти привычку с таким номером."
        },
        "uk": {
            "no_args": "✏️ Вкажи номер звички, яку ти виконав(ла):\n/habit_done 0",
            "bad_arg": "⚠️ Вкажи номер звички (наприклад `/habit_done 0`)",
            "done": "✅ Звичка №{index} відзначена як виконана! Молодець! 💪 +5 балів!",
            "not_found": "❌ Не вдалося знайти звичку з таким номером."
        },
        "be": {
            "no_args": "✏️ Пакажы нумар звычкі, якую ты выканаў(ла):\n/habit_done 0",
            "bad_arg": "⚠️ Пакажы нумар звычкі (напрыклад `/habit_done 0`)",
            "done": "✅ Звычка №{index} адзначана як выкананая! Маладзец! 💪 +5 ачкоў!",
            "not_found": "❌ Не атрымалася знайсці звычку з такім нумарам."
        },
        "kk": {
            "no_args": "✏️ Орындаған әдетіңнің нөмірін көрсет:\n/habit_done 0",
            "bad_arg": "⚠️ Әдет нөмірін көрсет (мысалы `/habit_done 0`)",
            "done": "✅ Әдет №{index} орындалған деп белгіленді! Жарайсың! 💪 +5 ұпай!",
            "not_found": "❌ Бұл нөмірмен әдет табылмады."
        },
        "kg": {
            "no_args": "✏️ Аткарган көнүмүшүңдүн номерин көрсөт:\n/habit_done 0",
            "bad_arg": "⚠️ Көнүмүштүн номерин көрсөт (мисалы `/habit_done 0`)",
            "done": "✅ Көнүмүш №{index} аткарылды деп белгиленди! Молодец! 💪 +5 упай!",
            "not_found": "❌ Мындай номер менен көнүмүш табылган жок."
        },
        "hy": {
            "no_args": "✏️ Նշիր սովորության համարը, որը կատարել ես:\n/habit_done 0",
            "bad_arg": "⚠️ Նշիր սովորության համարը (օրինակ `/habit_done 0`)",
            "done": "✅ Սովորություն №{index}-ը նշված է որպես կատարված! Բրավո! 💪 +5 միավոր!",
            "not_found": "❌ Չհաջողվեց գտնել այդ համարով սովորություն։"
        },
        "ce": {
            "no_args": "✏️ ХӀокхуьйра привычкаш номер язде:\n/habit_done 0",
            "bad_arg": "⚠️ Привычкаш номер язде (маса `/habit_done 0`)",
            "done": "✅ Привычка №{index} тӀетоха цаьнан! Баркалла! 💪 +5 балл!",
            "not_found": "❌ Тахана номернаш привычка йац."
        },
        "md": {
            "no_args": "✏️ Indică numărul obiceiului pe care l-ai realizat:\n/habit_done 0",
            "bad_arg": "⚠️ Indică numărul obiceiului (de exemplu `/habit_done 0`)",
            "done": "✅ Obiceiul №{index} a fost marcat ca realizat! Bravo! 💪 +5 puncte!",
            "not_found": "❌ Nu s-a găsit niciun obicei cu acest număr."
        },
        "ka": {
            "no_args": "✏️ მიუთითე ჩვევის ნომერი, რომელიც შეასრულე:\n/habit_done 0",
            "bad_arg": "⚠️ მიუთითე ჩვევის ნომერი (მაგალითად `/habit_done 0`)",
            "done": "✅ ჩვევა №{index} მონიშნულია როგორც შესრულებული! Молодец! 💪 +5 ქულა!",
            "not_found": "❌ ასეთი ნომრით ჩვევა ვერ მოიძებნა."
        },
        "en": {
            "no_args": "✏️ Specify the number of the habit you completed:\n/habit_done 0",
            "bad_arg": "⚠️ Specify the habit number (e.g. `/habit_done 0`)",
            "done": "✅ Habit #{index} marked as completed! Well done! 💪 +5 points!",
            "not_found": "❌ Couldn’t find a habit with that number."
        },
    }

    # 🗂️ Словарь отсылок по темам на всех языках
references_by_lang = {
        "ru": {
            "отношения": "Ты ведь раньше делился(ась) про чувства… Хочешь поговорить об этом подробнее? 💜",
            "одиночество": "Помню, ты чувствовал(а) себя одиноко… Я всё ещё здесь 🤗",
            "работа": "Ты рассказывал(а) про давление на работе. Как у тебя с этим сейчас?",
            "спорт": "Ты ведь начинал(а) тренироваться — продолжаешь? 🏋️",
            "семья": "Ты упоминал(а) про семью… Всё ли хорошо?",
            "мотивация": "Ты говорил(а), что хочешь развиваться. Что уже получилось? ✨"
        },
        "uk": {
            "відносини": "Ти ж ділився(-лася) почуттями… Хочеш розповісти більше? 💜",
            "самотність": "Пам’ятаю, ти почувався(-лася) самотньо… Я тут 🤗",
            "робота": "Ти казав(-ла), що робота тисне. Як зараз?",
            "спорт": "Ти ж починав(-ла) тренуватися — продовжуєш? 🏋️",
            "сім’я": "Ти згадував(-ла) про сім’ю… Усе добре?",
            "мотивація": "Ти казав(-ла), що хочеш розвиватися. Що вже вдалося? ✨"
        },
        "be": {
            "адносіны": "Ты ж дзяліўся(-лася) пачуццямі… Хочаш распавесці больш? 💜",
            "адзінота": "Памятаю, табе было адзінока… Я тут 🤗",
            "праца": "Ты казаў(-ла), што праца цісне. Як цяпер?",
            "спорт": "Ты ж пачынаў(-ла) трэніравацца — працягваеш? 🏋️",
            "сям’я": "Ты згадваў(-ла) пра сям’ю… Усё добра?",
            "матывацыя": "Ты казаў(-ла), што хочаш развівацца. Што ўжо атрымалася? ✨"
        },
        "kk": {
            "қатынас": "Сен бұрын сезімдеріңмен бөліскен едің… Толығырақ айтқың келе ме? 💜",
            "жалғыздық": "Есімде, өзіңді жалғыз сезінгенсің… Мен осындамын 🤗",
            "жұмыс": "Жұмыста қысым сезінгеніңді айттың. Қазір қалай?",
            "спорт": "Сен жаттығуды бастаған едің — жалғастырып жүрсің бе? 🏋️",
            "отбасы": "Сен отбасың туралы айтқан едің… Бәрі жақсы ма?",
            "мотивация": "Сен дамығың келетініңді айттың. Не өзгерді? ✨"
        },
        "kg": {
            "байланыш": "Сен мурун сезимдериң менен бөлүшкөнсүң… Толугураак айтып бересиңби? 💜",
            "жалгыздык": "Эсимде, өзүңдү жалгыз сезип жүргөнсүң… Мен бул жерде 🤗",
            "иш": "Иштеги басым тууралуу айткансың. Азыр кандай?",
            "спорт": "Сен машыгуу баштагансың — улантып жатасыңбы? 🏋️",
            "үй-бүлө": "Үй-бүлөң жөнүндө айткансың… Баары жакшыбы?",
            "мотивация": "Сен өнүгүүнү каалаганыңды айткансың. Эмне өзгөрдү? ✨"
        },
        "hy": {
            "հարաբերություններ": "Դու պատմել ես քո զգացումների մասին… Ուզու՞մ ես ավելին պատմել 💜",
            "միայնություն": "Հիշում եմ, դու քեզ միայնակ էիր զգում… Ես այստեղ եմ 🤗",
            "աշխատանք": "Դու պատմել ես աշխատանքի ճնշման մասին. Հիմա ինչպե՞ս ես:",
            "սպորտ": "Դու սկսեց մարզվել — շարունակի՞ս? 🏋️",
            "ընտանիք": "Դու հիշեցիր ընտանիքդ… Բոլորն արդյո՞ք լավ են:",
            "մոտիվացիա": "Դու պատմեցիր, որ ուզում ես զարգանալ. Ի՞նչ հաջողվեց արդեն ✨"
        },
        "ce": {
            "мацахь": "Хьо мах даа хьо йа къобал. Цхьа кхета хийцам? 💜",
            "одиночество": "Хьо цхьаьнга хьайна дезар хьалха… Са хьалха ю 🤗",
            "работа": "Хьо цхьаьнга хьайна хьалха дагахь. Хьо кхеташ? ",
            "спорт": "Хьо къобал спорт йа цхьаьнга… Хьан кхеташ? 🏋️",
            "семья": "Хьо цхьаьнга хьайна ца хаам. Хьан хиллахь? ",
            "мотивация": "Хьо цхьаьнга хьайна а дагьай. Хьан кхеташ? ✨"
        },
        "md": {
            "relații": "Ți-ai împărtășit sentimentele… Vrei să povestești mai mult? 💜",
            "singurătate": "Îmi amintesc că te simțeai singur(ă)… Eu sunt aici 🤗",
            "muncă": "Ai spus că munca te apasă. Cum e acum?",
            "sport": "Ai început să te antrenezi — continui? 🏋️",
            "familie": "Ai menționat familia… Totul e bine?",
            "motivație": "Ai spus că vrei să te dezvolți. Ce ai reușit deja? ✨"
        },
        "ka": {
            "ურთიერთობა": "შენ გაზიარე შენი გრძნობები… გინდა მეტი მომიყვე? 💜",
            "მარტოობა": "მახსოვს, თავს მარტო გრძნობდი… აქ ვარ 🤗",
            "სამუშაო": "თქვი, რომ სამსახური გაწუხებს. ახლა როგორ ხარ?",
            "სპორტი": "დაიწყე ვარჯიში — განაგრძე? 🏋️",
            "ოჯახი": "გახსენდი შენი ოჯახი… ყველაფერი好吗?",
            "მოტივაცია": "თქვი, რომ გინდა განვითარდე. უკვე რას მიაღწიე? ✨"
        },
        "en": {
            "love": "You’ve shared your feelings before… Want to tell me more? 💜",
            "loneliness": "I remember you felt lonely… I’m here for you 🤗",
            "work": "You said work was overwhelming. How is it now?",
            "sport": "You started training — still going? 🏋️",
            "family": "You mentioned your family… Is everything okay?",
            "motivation": "You said you want to grow. What have you achieved so far? ✨"
        },
    }

  # 🌐 Подсказки по ключевым словам для каждого языка
keywords_by_lang = {
        "ru": {
            "вода": "💧 Сегодня удели внимание воде — выпей 8 стаканов и отметь это!",
            "спорт": "🏃‍♂️ Сделай 15-минутную разминку, твое тело скажет спасибо!",
            "книга": "📖 Найди время прочитать 10 страниц своей книги.",
            "медитация": "🧘‍♀️ Проведи 5 минут в тишине, фокусируясь на дыхании.",
            "работа": "🗂️ Сделай один важный шаг в рабочем проекте сегодня.",
            "учеба": "📚 Потрать 20 минут на обучение или повторение материала."
        },
        "uk": {
            "вода": "💧 Сьогодні зверни увагу на воду — випий 8 склянок і відзнач це!",
            "спорт": "🏃‍♂️ Зроби 15-хвилинну розминку, твоє тіло скаже дякую!",
            "книга": "📖 Знайди час прочитати 10 сторінок своєї книги.",
            "медитация": "🧘‍♀️ Проведи 5 хвилин у тиші, зосереджуючись на диханні.",
            "работа": "🗂️ Зроби один важливий крок у робочому проєкті сьогодні.",
            "учеба": "📚 Приділи 20 хвилин навчанню або повторенню матеріалу."
        },
        "be": {
            "вода": "💧 Сёння звярні ўвагу на ваду — выпі 8 шклянак і адзнач гэта!",
            "спорт": "🏃‍♂️ Зрабі 15-хвілінную размінку, тваё цела скажа дзякуй!",
            "книга": "📖 Знайдзі час прачытаць 10 старонак сваёй кнігі.",
            "медитация": "🧘‍♀️ Правядзі 5 хвілін у цішыні, засяродзіўшыся на дыханні.",
            "работа": "🗂️ Зрабі адзін важны крок у рабочым праекце сёння.",
            "учеба": "📚 Прысвяці 20 хвілін навучанню або паўтарэнню матэрыялу."
        },
        "kk": {
            "су": "💧 Бүгін суға көңіл бөл — 8 стақан ішіп белгіле!",
            "спорт": "🏃‍♂️ 15 минуттық жаттығу жаса, денең рақмет айтады!",
            "кітап": "📖 Кітабыңның 10 бетін оқуға уақыт тап.",
            "медитация": "🧘‍♀️ 5 минут тыныштықта отырып, тынысыңа көңіл бөл.",
            "жұмыс": "🗂️ Бүгін жұмысыңда бір маңызды қадам жаса.",
            "оқу": "📚 20 минут оқуға немесе қайталауға бөл."
        },
        "kg": {
            "суу": "💧 Бүгүн сууга көңүл бур — 8 стакан ичип белгиле!",
            "спорт": "🏃‍♂️ 15 мүнөттүк көнүгүү жаса, денең рахмат айтат!",
            "китеп": "📖 Китебиңдин 10 бетин окууга убакыт тап.",
            "медитация": "🧘‍♀️ 5 мүнөт тынчтыкта отуруп, дем алууга көңүл бур.",
            "иш": "🗂️ Бүгүн ишиңде бир маанилүү кадам жаса.",
            "оку": "📚 20 мүнөт окууга же кайталоого бөл."
        },
        "hy": {
            "ջուր": "💧 Այսօր ուշադրություն դարձրու ջրին — խմիր 8 բաժակ և նշիր դա!",
            "սպորտ": "🏃‍♂️ Կատարիր 15 րոպե տաքացում, մարմինդ կգնահատի!",
            "գիրք": "📖 Ժամանակ գտիր կարդալու 10 էջ քո գրքից.",
            "մեդիտացիա": "🧘‍♀️ 5 րոպե անցկացրու լռության մեջ, կենտրոնացած շնչի վրա.",
            "աշխատանք": "🗂️ Այսօր արա մեկ կարևոր քայլ քո աշխատանքային նախագծում.",
            "ուսում": "📚 Ընթերցիր կամ կրկնիր նյութը 20 րոպե."
        },
        "ce": {
            "хьӀа": "💧 Тахана водахьь къобалла — 8 стакан хийца!",
            "спорт": "🏃‍♂️ 15 минот тренировка хийца, тӀехьа хила дӀахьара!",
            "книга": "📖 10 агӀо книгахьь хьаьлла.",
            "медитация": "🧘‍♀️ 5 минот тIехьа хийцам, хьовса дагьалла.",
            "работа": "🗂️ Бугун проектехь цхьа дӀадо.",
            "учеба": "📚 20 минот учёба хийцам."
        },
        "md": {
            "apă": "💧 Astăzi acordă atenție apei — bea 8 pahare și marchează asta!",
            "sport": "🏃‍♂️ Fă 15 minute de exerciții, corpul tău îți va mulțumi!",
            "carte": "📖 Găsește timp să citești 10 pagini din cartea ta.",
            "meditație": "🧘‍♀️ Petrece 5 minute în liniște, concentrându-te pe respirație.",
            "muncă": "🗂️ Fă un pas important în proiectul tău de lucru azi.",
            "studiu": "📚 Petrece 20 de minute pentru a învăța sau a repeta."
        },
        "ka": {
            "წყალი": "💧 დღეს მიაქციე ყურადღება წყალს — დალიე 8 ჭიქა და აღნიშნე!",
            "სპორტი": "🏃‍♂️ გააკეთე 15 წუთიანი ვარჯიში, შენი სხეული მადლობას გეტყვის!",
            "წიგნი": "📖 იპოვე დრო წასაკითხად 10 გვერდი შენი წიგნიდან.",
            "მედიტაცია": "🧘‍♀️ გაატარე 5 წუთი სიჩუმეში, სუნთქვაზე ფოკუსირებით.",
            "სამუშაო": "🗂️ დღეს გააკეთე ერთი მნიშვნელოვანი ნაბიჯი სამუშაო პროექტში.",
            "სწავლა": "📚 დაუთმე 20 წუთი სწავლისთვის ან გამეორებისთვის."
        },
        "en": {
            "water": "💧 Pay attention to water today — drink 8 glasses and note it!",
            "sport": "🏃‍♂️ Do a 15-minute workout, your body will thank you!",
            "book": "📖 Find time to read 10 pages of your book.",
            "meditation": "🧘‍♀️ Spend 5 minutes in silence, focusing on your breath.",
            "work": "🗂️ Take one important step in your work project today.",
            "study": "📚 Spend 20 minutes learning or reviewing material."
        },
    }

    # 🌐 Заголовок
headers = {
        "ru": "✨ Твоё персональное задание на сегодня:\n\n",
        "uk": "✨ Твоє персональне завдання на сьогодні:\n\n",
        "be": "✨ Тваё персанальнае заданне на сёння:\n\n",
        "kk": "✨ Бүгінгі жеке тапсырмаң:\n\n",
        "kg": "✨ Бүгүнкү жеке тапшырмаң:\n\n",
        "hy": "✨ Այսօրվա քո անձնական առաջադրանքը․\n\n",
        "ce": "✨ Тахана персонал дӀаязде:\n\n",
        "md": "✨ Sarcina ta personală pentru azi:\n\n",
        "ka": "✨ შენი პირადი დავალება დღევანდელი:\n\n",
        "en": "✨ Your personal task for today:\n\n",
    }

questions_by_topic_by_lang = {
    "ru": {
        "спорт": [
            "А ты сейчас занимаешься чем-то активным?",
            "Хочешь, составим тебе лёгкий челлендж?",
            "Какая тренировка тебе приносит больше всего удовольствия?"
        ],
        "любовь": [
            "А что ты чувствуешь к этому человеку сейчас?",
            "Хочешь рассказать, что было дальше?",
            "Как ты понимаешь, что тебе важно в отношениях?"
        ],
        "работа": [
            "А чем тебе нравится (или не нравится) твоя работа?",
            "Ты хочешь что-то поменять в этом?",
            "Есть ли у тебя мечта, связанная с карьерой?"
        ],
        "деньги": [
            "Как ты сейчас чувствуешь себя в плане финансов?",
            "Что бы ты хотел улучшить?",
            "Есть ли у тебя финансовая цель?"
        ],
        "одиночество": [
            "А чего тебе сейчас больше всего не хватает?",
            "Хочешь, я просто побуду рядом?",
            "А как ты обычно проводишь время, когда тебе одиноко?"
        ],
        "мотивация": [
            "Что тебя вдохновляет прямо сейчас?",
            "Какая у тебя сейчас цель?",
            "Что ты хочешь почувствовать, когда достигнешь этого?"
        ],
        "здоровье": [
            "Как ты заботишься о себе в последнее время?",
            "Были ли у тебя моменты отдыха сегодня?",
            "Что для тебя значит быть в хорошем состоянии?"
        ],
        "тревога": [
            "Что вызывает у тебя больше всего волнения сейчас?",
            "Хочешь, я помогу тебе с этим справиться?",
            "Ты хочешь просто выговориться?"
        ],
        "друзья": [
            "С кем тебе хочется сейчас поговорить по-настоящему?",
            "Как ты обычно проводишь время с близкими?",
            "Ты хотел бы, чтобы кто-то был рядом прямо сейчас?"
        ],
        "цели": [
            "Какая цель тебе сейчас ближе всего по духу?",
            "Хочешь, я помогу тебе её распланировать?",
            "С чего ты бы хотел начать сегодня?"
        ],
    },
    "en": {
        "sport": [
            "Are you doing anything active right now?",
            "Want me to suggest you a light challenge?",
            "What kind of workout makes you feel good?"
        ],
        "love": [
            "What do you feel for this person right now?",
            "Want to tell me what happened next?",
            "What matters most to you in a relationship?"
        ],
        "work": [
            "What do you like or dislike about your job?",
            "Do you want to change something about it?",
            "Do you have a career dream?"
        ],
        "money": [
            "How do you feel financially right now?",
            "What would you like to improve?",
            "Do you have a financial goal?"
        ],
        "loneliness": [
            "What do you miss the most right now?",
            "Want me to just stay by your side?",
            "How do you usually spend time when you feel lonely?"
        ],
        "motivation": [
            "What inspires you right now?",
            "What goal do you have now?",
            "How do you want to feel when you reach it?"
        ],
        "health": [
            "How have you been taking care of yourself lately?",
            "Did you have any rest today?",
            "What does it mean for you to feel well?"
        ],
        "anxiety": [
            "What makes you feel anxious the most right now?",
            "Want me to help you with that?",
            "Do you just want to talk it out?"
        ],
        "friends": [
            "Who do you really want to talk to now?",
            "How do you usually spend time with friends?",
            "Would you like someone to be with you right now?"
        ],
        "goals": [
            "Which goal feels closest to you now?",
            "Want me to help you plan it?",
            "What would you like to start with today?"
        ],
    },
    "uk": {
        "спорт": [
            "Ти зараз займаєшся чимось активним?",
            "Хочеш, я запропоную легкий челендж?",
            "Яке тренування приносить тобі найбільше задоволення?"
        ],
        "любов": [
            "Що ти відчуваєш до цієї людини зараз?",
            "Хочеш розповісти, що було далі?",
            "Що для тебе найважливіше у стосунках?"
        ],
        "робота": [
            "Що тобі подобається чи не подобається в роботі?",
            "Ти хочеш щось змінити?",
            "Чи маєш ти мрію, пов’язану з кар’єрою?"
        ],
        "гроші": [
            "Як ти зараз почуваєшся фінансово?",
            "Що б ти хотів(ла) покращити?",
            "Чи маєш ти фінансову ціль?"
        ],
        "самотність": [
            "Чого тобі зараз найбільше бракує?",
            "Хочеш, я просто побуду поруч?",
            "Як ти проводиш час, коли тобі самотньо?"
        ],
        "мотивація": [
            "Що тебе надихає зараз?",
            "Яка в тебе зараз ціль?",
            "Що ти хочеш відчути, коли досягнеш цього?"
        ],
        "здоров’я": [
            "Як ти дбаєш про себе останнім часом?",
            "Були сьогодні моменти відпочинку?",
            "Що для тебе означає бути в гарному стані?"
        ],
        "тривога": [
            "Що викликає в тебе найбільше хвилювання?",
            "Хочеш, я допоможу тобі з цим впоратися?",
            "Ти просто хочеш виговоритися?"
        ],
        "друзі": [
            "З ким тобі хочеться зараз поговорити?",
            "Як ти проводиш час з близькими?",
            "Ти хотів(ла) би, щоб хтось був поруч?"
        ],
        "цілі": [
            "Яка ціль тобі зараз ближча?",
            "Хочеш, я допоможу її спланувати?",
            "З чого б ти хотів(ла) почати?"
        ],
    },
    "be": {
        "спорт": [
            "Ці цяпер займаешся чымсьці актыўным?",
            "Хочаш, прапаную табе лёгкі чэлендж?",
            "Якая трэніроўка табе найбольш падабаецца?"
        ],
        "любоў": [
            "Што ты адчуваеш да гэтага чалавека зараз?",
            "Хочаш расказаць, што было далей?",
            "Што для цябе важна ў адносінах?"
        ],
        "праца": [
            "Што табе падабаецца ці не падабаецца ў тваёй працы?",
            "Ці хочаш нешта змяніць?",
            "Ці ёсць у цябе мара, звязаная з кар’ерай?"
        ],
        "грошы": [
            "Як ты сябе адчуваеш у фінансах зараз?",
            "Што б ты хацеў палепшыць?",
            "Ці ёсць у цябе фінансавая мэта?"
        ],
        "адзінота": [
            "Чаго табе зараз найбольш не хапае?",
            "Хочаш, я проста пабуду побач?",
            "Як ты праводзіш час, калі адчуваеш сябе адзінокім?"
        ],
        "матывацыя": [
            "Што цябе натхняе зараз?",
            "Якая ў цябе цяпер мэта?",
            "Што ты хочаш адчуць, калі дасягнеш гэтага?"
        ],
        "здоров’е": [
            "Як ты клапоцішся пра сябе апошнім часам?",
            "Былі ў цябе моманты адпачынку сёння?",
            "Што для цябе значыць быць у добрым стане?"
        ],
        "трывога": [
            "Што цябе хвалюе больш за ўсё зараз?",
            "Хочаш, я дапамагу табе з гэтым?",
            "Ты проста хочаш выгаварыцца?"
        ],
        "сябры": [
            "З кім табе хочацца зараз пагаварыць?",
            "Як ты звычайна праводзіш час з блізкімі?",
            "Ці хацеў бы ты, каб нехта быў побач зараз?"
        ],
        "мэты": [
            "Якая мэта табе цяпер бліжэйшая?",
            "Хочаш, я дапамагу яе спланаваць?",
            "З чаго б ты хацеў пачаць?"
        ],
    },
    "kk": {
        "спорт": [
            "Қазір қандай да бір белсенділікпен айналысып жатырсың ба?",
            "Саған жеңіл тапсырма ұсынайын ба?",
            "Қандай жаттығу саған ұнайды?"
        ],
        "махаббат": [
            "Бұл адамға қазір не сезесің?",
            "Әрі қарай не болғанын айтасың ба?",
            "Қарым-қатынаста сен үшін ең маңызды не?"
        ],
        "жұмыс": [
            "Жұмысыңда не ұнайды, не ұнамайды?",
            "Бір нәрсені өзгерткің келе ме?",
            "Мансапқа қатысты арманың бар ма?"
        ],
        "ақша": [
            "Қаржылай қазір қалай сезініп жүрсің?",
            "Нені жақсартқың келеді?",
            "Қаржылық мақсатың бар ма?"
        ],
        "жалғыздық": [
            "Қазір саған не жетіспейді?",
            "Қасыңда жай отырайын ба?",
            "Өзіңді жалғыз сезінгенде уақытыңды қалай өткізесің?"
        ],
        "мотивация": [
            "Қазір сені не шабыттандырады?",
            "Қазір сенің мақсатың қандай?",
            "Соны орындағанда не сезінгің келеді?"
        ],
        "денсаулық": [
            "Соңғы кезде өзіңді қалай күттің?",
            "Бүгін демалдың ба?",
            "Саған жақсы күйде болу нені білдіреді?"
        ],
        "алаңдаушылық": [
            "Қазір не үшін ең көп алаңдап жүрсің?",
            "Саған көмектесейін бе?",
            "Тек сөйлескің келе ме?"
        ],
        "достар": [
            "Қазір кіммен сөйлескің келеді?",
            "Достарыңмен уақытты қалай өткізесің?",
            "Қасыңда біреу болғанын қалар ма едің?"
        ],
        "мақсаттар": [
            "Қазір қай мақсат саған ең жақын?",
            "Оны жоспарлауға көмектесейін бе?",
            "Бүгін неден бастағың келеді?"
        ],
    },
    "kg": {
        "спорт": [
            "Азыр кандайдыр бир активдүү нерсе менен алектенип жатасыңбы?",
            "Сага жеңил тапшырма сунуштайынбы?",
            "Кайсы машыгуу сага көбүрөөк жагат?"
        ],
        "сүйүү": [
            "Бул адамга азыр эмне сезесиң?",
            "Андан кийин эмне болгонун айткың келеби?",
            "Мамиледе сен үчүн эмнелер маанилүү?"
        ],
        "иш": [
            "Ишиңде эмнени жактырасың же жактырбайсың?",
            "Бир нерсени өзгөрткүң келеби?",
            "Кесипке байланышкан кыялың барбы?"
        ],
        "акча": [
            "Каржылык абалың азыр кандай?",
            "Эмне жакшырткың келет?",
            "Каржылык максат коюп көрдүң беле?"
        ],
        "жалгыздык": [
            "Азыр сага эмнеден эң көп жетишпейт?",
            "Жанында жөн гана отуруп турайынбы?",
            "Өзүңдү жалгыз сезгенде убактыңды кантип өткөрөсүң?"
        ],
        "мотивация": [
            "Азыр сени эмне шыктандырат?",
            "Азыркы максатың кандай?",
            "Аны аткарганда эмнени сезгиң келет?"
        ],
        "ден-соолук": [
            "Акыркы күндөрү өзүңдү кандай карадың?",
            "Бүгүн эс алдыңбы?",
            "Сен үчүн жакшы абалда болуу эмнени билдирет?"
        ],
        "тынчсыздануу": [
            "Азыр эмнеге көбүрөөк тынчсызданып жатасың?",
            "Сага жардам берейинби?",
            "Жөн эле сүйлөшкүң келеби?"
        ],
        "достор": [
            "Азыр ким менен сүйлөшкүм келет?",
            "Досторуң менен убакытты кантип өткөрөсүң?",
            "Азыр сенин жаныңда кимдир болгонуңду каалайсыңбы?"
        ],
        "максаттар": [
            "Азыр кайсы максат сага жакын?",
            "Аны пландаштырууга жардам берейинби?",
            "Бүгүн эмнеден баштагың келет?"
        ],
    },
    "hy": {
        "սպորտ": [
            "Հիմա ինչ-որ ակտիվ բանով զբաղվա՞ծ ես:",
            "Ուզում ես առաջարկեմ թեթև մարտահրավե՞ր:",
            "Ի՞նչ մարզում է քեզ ամենաշատ ուրախացնում:"
        ],
        "սեր": [
            "Ի՞նչ ես հիմա զգում այդ մարդու հանդեպ:",
            "Ուզու՞մ ես պատմես, ինչ եղավ հետո:",
            "Ինչն է քեզ համար կարևոր հարաբերություններում?"
        ],
        "աշխատանք": [
            "Ի՞նչն է քեզ դուր գալիս կամ չի դուր գալիս աշխատանքում:",
            "Ուզու՞մ ես ինչ-որ բան փոխել:",
            "Կարիերայի հետ կապված երազանք ունե՞ս:"
        ],
        "փող": [
            "Ինչպե՞ս ես քեզ զգում ֆինանսական առումով:",
            "Ի՞նչ կուզենայիր բարելավել:",
            "Ֆինանսական նպատակ ունե՞ս:"
        ],
        "միայնություն": [
            "Ի՞նչն է քեզ հիմա առավելապես պակասում:",
            "Ցանկանու՞մ ես, որ պարզապես կողքիդ լինեմ:",
            "Ինչպե՞ս ես ժամանակ անցկացնում, երբ քեզ միայնակ ես զգում:"
        ],
        "մոտիվացիա": [
            "Ի՞նչ է քեզ հիմա ոգեշնչում:",
            "Ո՞րն է քո այսօրվա նպատակը:",
            "Ի՞նչ ես ուզում զգալ, երբ հասնես դրան:"
        ],
        "առողջություն": [
            "Վերջին շրջանում ինչպես ես հոգացել քեզ:",
            "Այսօր հանգստացել ե՞ս:",
            "Ի՞նչ է նշանակում քեզ համար լինել լավ վիճակում:"
        ],
        "անհանգստություն": [
            "Ի՞նչն է հիմա քեզ ամենաշատ անհանգստացնում:",
            "Ցանկանու՞մ ես, որ օգնեմ քեզ:",
            "Պարզապես ուզում ե՞ս խոսել:"
        ],
        "ընկերներ": [
            "Ու՞մ հետ կուզենայիր հիմա խոսել:",
            "Ինչպե՞ս ես սովորաբար ժամանակ անցկացնում ընկերների հետ:",
            "Կուզենայիր, որ ինչ-որ մեկը հիմա կողքիդ լիներ?"
        ],
        "նպատակներ": [
            "Ո՞ր նպատակն է քեզ հիմա առավել մոտ:",
            "Ցանկանու՞մ ես, որ օգնենք այն պլանավորել:",
            "Ի՞նչից կցանկանայիր սկսել այսօր:"
        ],
    },
    "ce": {
        "спорт": [
            "Хьо тIехь кара хIинца тIехь хийца хIинца?",
            "БIаьргаш челлендж ва хаа?",
            "ХIинца спорт хIунга ца тIехь шарш лело?"
        ],
        "любовь": [
            "ХIинца хIо хIинца хьо хийцал?",
            "Кхета хьо воьшна хаа?",
            "Ма хIинца хьо оцу хаьрж?"
        ],
        "работа": [
            "Хьо хIинца ца яьлла дIайа?",
            "Кхета хаьрж хIинца хьо?",
            "Мансах лаьцна хьо тIехь?"
        ],
        "деньги": [
            "Финанс хьо тIехь яц?",
            "Хьо хIунга хьо шун?",
            "Финанс хьо ца яц?"
        ],
        "одиночество": [
            "Ма хIун хьо тIехь нахь хIун?",
            "Хьо хьал дIайаш?",
            "Ма хIун хьо йаьлла да?"
        ],
        "мотивация": [
            "Ма хIун хьо тIехь йоьлла?",
            "Ма ца тIехь ха?",
            "Ма хIун хьо тIехь хаа?"
        ],
        "здоровье": [
            "Ма хIун хьо ца яц?",
            "Ма хIун хьо хийца?",
            "Ма хIун хьо ца яц хьал?"
        ],
        "тревога": [
            "Ма хIун хьо хийца ха?",
            "Хьо хIунга кхета?",
            "Ма хIун хьо йаьлла?"
        ],
        "друзья": [
            "Ма хIун хьо хIинца ца?",
            "Ма хIун хьо хIунга ха?",
            "Ма хIун хьо хIунга хаьрж?"
        ],
        "цели": [
            "Ма хIун хьо ца ха?",
            "Ма хIун хьо плана ха?",
            "Ма хIун хьо ха?"
        ],
    },
    "md": {
        "sport": [
            "Te ocupi cu ceva activ acum?",
            "Vrei să îți dau o provocare ușoară?",
            "Ce fel de antrenament îți place cel mai mult?"
        ],
        "dragoste": [
            "Ce simți pentru această persoană acum?",
            "Vrei să îmi spui ce s-a întâmplat mai departe?",
            "Ce este important pentru tine într-o relație?"
        ],
        "muncă": [
            "Ce îți place sau nu îți place la munca ta?",
            "Vrei să schimbi ceva?",
            "Ai un vis legat de carieră?"
        ],
        "bani": [
            "Cum te simți acum din punct de vedere financiar?",
            "Ce ai vrea să îmbunătățești?",
            "Ai un obiectiv financiar?"
        ],
        "singurătate": [
            "Ce îți lipsește cel mai mult acum?",
            "Vrei să fiu doar alături de tine?",
            "Cum îți petreci timpul când te simți singur?"
        ],
        "motivație": [
            "Ce te inspiră acum?",
            "Care este obiectivul tău acum?",
            "Ce vrei să simți când vei reuși?"
        ],
        "sănătate": [
            "Cum ai grijă de tine în ultima vreme?",
            "Ai avut momente de odihnă astăzi?",
            "Ce înseamnă pentru tine să fii într-o stare bună?"
        ],
        "anxietate": [
            "Ce te îngrijorează cel mai mult acum?",
            "Vrei să te ajut cu asta?",
            "Vrei doar să vorbești despre asta?"
        ],
        "prieteni": [
            "Cu cine ai vrea să vorbești acum?",
            "Cum îți petreci timpul cu prietenii?",
            "Ai vrea să fie cineva acum lângă tine?"
        ],
        "obiective": [
            "Care obiectiv îți este acum mai aproape de suflet?",
            "Vrei să te ajut să îl planifici?",
            "Cu ce ai vrea să începi azi?"
        ],
    },
    "ka": {
        "სპორტი": [
            "ახლა რაღაც აქტიურზე მუშაობ?",
            "გინდა შემოგთავაზო მარტივი გამოწვევა?",
            "რა ვარჯიში მოგწონს ყველაზე მეტად?"
        ],
        "სიყვარული": [
            "რა გრძნობები გაქვს ამ ადამიანის მიმართ ახლა?",
            "გინდა მომიყვე, რა მოხდა მერე?",
            "რა არის შენთვის მნიშვნელოვანი ურთიერთობებში?"
        ],
        "სამუშაო": [
            "რა მოგწონს ან არ მოგწონს შენს სამუშაოში?",
            "გინდა რამე შეცვალო?",
            "გაქვს კარიერული ოცნება?"
        ],
        "ფული": [
            "როგორ გრძნობ თავს ფინანსურად ახლა?",
            "რა გსურს გააუმჯობესო?",
            "გაქვს ფინანსური მიზანი?"
        ],
        "მარტოობა": [
            "რისი ნაკლებობა ყველაზე მეტად გაწუხებს ახლა?",
            "გინდა, უბრალოდ გვერდით ვიყო?",
            "როგორ ატარებ დროს, როცა თავს მარტო გრძნობ?"
        ],
        "მოტივაცია": [
            "რა გაძლევს შთაგონებას ახლა?",
            "რა მიზანი გაქვს ახლა?",
            "რა გსურს იგრძნო, როცა ამას მიაღწევ?"
        ],
        "ჯანმრთელობა": [
            "როგორ ზრუნავ საკუთარ თავზე ბოლო დროს?",
            "დღეს დაისვენე?",
            "რა ნიშნავს შენთვის, იყო კარგ მდგომარეობაში?"
        ],
        "შფოთვა": [
            "რა გაწუხებს ყველაზე მეტად ახლა?",
            "გინდა, დაგეხმარო ამაში?",
            "უბრალოდ გინდა, რომ ვისაუბროთ?"
        ],
        "მეგობრები": [
            "ვისთან გინდა ახლა საუბარი?",
            "როგორ ატარებ დროს მეგობრებთან?",
            "გსურს, რომ ვინმე ახლოს იყოს ახლა?"
        ],
        "მიზნები": [
            "რომელი მიზანი გაქვს ახლავე?",
            "გინდა, დაგეხმარო მისი დაგეგმვაში?",
            "რით დაიწყებდი დღეს?"
        ],
    },
}

HABIT_BUTTON_TEXTS = {
    "ru": {
        "habit_done": "🎉 Привычка отмечена как выполненная!",
        "not_found": "Не удалось найти привычку.",
        "habit_deleted": "🗑️ Привычка удалена.",
        "delete_error": "Не удалось удалить привычку.",
        "no_goals": "У тебя пока нет целей, которые можно отметить выполненными 😔",
        "choose_goal": "Выбери цель, которую ты выполнил(а):"
    },
    "uk": {
        "habit_done": "🎉 Звичка позначена як виконана!",
        "not_found": "Не вдалося знайти звичку.",
        "habit_deleted": "🗑️ Звичка видалена.",
        "delete_error": "Не вдалося видалити звичку.",
        "no_goals": "У тебе поки немає цілей, які можна відмітити виконаними 😔",
        "choose_goal": "Обери ціль, яку ти виконав(ла):"
    },
    "be": {
        "habit_done": "🎉 Звычка адзначана як выкананая!",
        "not_found": "Не атрымалася знайсці звычку.",
        "habit_deleted": "🗑️ Звычка выдалена.",
        "delete_error": "Не атрымалася выдаліць звычку.",
        "no_goals": "У цябе пакуль няма мэт, якія можна адзначыць выкананымі 😔",
        "choose_goal": "Абяры мэту, якую ты выканаў(ла):"
    },
    "kk": {
        "habit_done": "🎉 Әдет орындалған деп белгіленді!",
        "not_found": "Әдет табылмады.",
        "habit_deleted": "🗑️ Әдет жойылды.",
        "delete_error": "Әдетті жою мүмкін болмады.",
        "no_goals": "Орындаған мақсаттарың әлі жоқ 😔",
        "choose_goal": "Орындаған мақсатыңды таңда:"
    },
    "kg": {
        "habit_done": "🎉 Көнүмүш аткарылды деп белгиленди!",
        "not_found": "Көнүмүш табылган жок.",
        "habit_deleted": "🗑️ Көнүмүш өчүрүлдү.",
        "delete_error": "Көнүмүштү өчүрүү мүмкүн болгон жок.",
        "no_goals": "Аткарган максаттар жок 😔",
        "choose_goal": "Аткарган максатыңды танда:"
    },
    "hy": {
        "habit_done": "🎉 Սովորությունը նշված է որպես կատարված!",
        "not_found": "Չհաջողվեց գտնել սովորությունը։",
        "habit_deleted": "🗑️ Սովորությունը ջնջված է։",
        "delete_error": "Չհաջողվեց ջնջել սովորությունը։",
        "no_goals": "Դեռ չունես նպատակներ, որոնք կարելի է նշել կատարված 😔",
        "choose_goal": "Ընտրիր նպատակը, որը կատարել ես։"
    },
    "ce": {
        "habit_done": "🎉 Привычка отмечена как выполненная!",
        "not_found": "Привычку не удалось найти.",
        "habit_deleted": "🗑️ Привычка удалена.",
        "delete_error": "Привычку не удалось удалить.",
        "no_goals": "У тебя пока нет целей для выполнения 😔",
        "choose_goal": "Выбери цель, которую ты выполнил(а):"
    },
    "md": {
        "habit_done": "🎉 Obiceiul a fost marcat ca realizat!",
        "not_found": "Nu am putut găsi obiceiul.",
        "habit_deleted": "🗑️ Obiceiul a fost șters.",
        "delete_error": "Nu am putut șterge obiceiul.",
        "no_goals": "Nu ai încă scopuri de bifat 😔",
        "choose_goal": "Alege scopul pe care l-ai realizat:"
    },
    "ka": {
        "habit_done": "🎉 ჩვევა შესრულებულად მოინიშნა!",
        "not_found": "ჩვევა ვერ მოიძებნა.",
        "habit_deleted": "🗑️ ჩვევა წაიშალა.",
        "delete_error": "ჩვევის წაშლა ვერ მოხერხდა.",
        "no_goals": "ჯერ არ გაქვს მიზნები, რომლებსაც შეასრულებდი 😔",
        "choose_goal": "აირჩიე მიზანი, რომელიც შეასრულე:"
    },
    "en": {
        "habit_done": "🎉 Habit marked as completed!",
        "not_found": "Could not find the habit.",
        "habit_deleted": "🗑️ Habit deleted.",
        "delete_error": "Could not delete the habit.",
        "no_goals": "You don't have any goals to mark as completed yet 😔",
        "choose_goal": "Select the goal you’ve completed:"
    }
}

HABITS_TEXTS = {
    "ru": {
        "no_habits": "У тебя пока нет привычек. Добавь первую с помощью /habit",
        "title": "📋 Твои привычки:",
        "done": "✅",
        "delete": "🗑️"
    },
    "uk": {
        "no_habits": "У тебе поки немає звичок. Додай першу за допомогою /habit",
        "title": "📋 Твої звички:",
        "done": "✅",
        "delete": "🗑️"
    },
    "be": {
        "no_habits": "У цябе пакуль няма звычак. Дадай першую праз /habit",
        "title": "📋 Твае звычкі:",
        "done": "✅",
        "delete": "🗑️"
    },
    "kk": {
        "no_habits": "Сенде әлі әдеттер жоқ. Біріншісін /habit арқылы қостыр.",
        "title": "📋 Сенің әдеттерің:",
        "done": "✅",
        "delete": "🗑️"
    },
    "kg": {
        "no_habits": "Сизде азырынча көнүмүштөр жок. Биринчисин /habit менен кошуңуз.",
        "title": "📋 Сиздин көнүмүштөрүңүз:",
        "done": "✅",
        "delete": "🗑️"
    },
    "hy": {
        "no_habits": "Դու դեռ սովորություններ չունես։ Ավելացրու առաջինը՝ /habit հրամանով",
        "title": "📋 Քո սովորությունները՝",
        "done": "✅",
        "delete": "🗑️"
    },
    "ce": {
        "no_habits": "Хьоьшу хьалха привычка цуьнан цуьр. Дахьах /habit хетам.",
        "title": "📋 Хьоьшу привычкаш:",
        "done": "✅",
        "delete": "🗑️"
    },
    "md": {
        "no_habits": "Încă nu ai obiceiuri. Adaugă primul cu /habit",
        "title": "📋 Obiceiurile tale:",
        "done": "✅",
        "delete": "🗑️"
    },
    "ka": {
        "no_habits": "ჯერ არ გაქვს ჩვევები. დაამატე პირველი /habit ბრძანებით",
        "title": "📋 შენი ჩვევები:",
        "done": "✅",
        "delete": "🗑️"
    },
    "en": {
        "no_habits": "You don't have any habits yet. Add your first one with /habit",
        "title": "📋 Your habits:",
        "done": "✅",
        "delete": "🗑️"
    },
}

HABIT_TEXTS = {
    "ru": {
        "limit": (
            "🌱 В бесплатной версии можно добавить только 2 привычки.\n\n"
            "✨ Подключи Mindra+, чтобы отслеживать неограниченное количество привычек 💜"
        ),
        "how_to": "Чтобы добавить привычку, напиши:\n/habit Делать зарядку",
        "added": "🎯 Привычка добавлена: *{habit}*",
    },
    "uk": {
        "limit": (
            "🌱 У безкоштовній версії можна додати лише 2 звички.\n\n"
            "✨ Підключи Mindra+, щоб відстежувати необмежену кількість звичок 💜"
        ),
        "how_to": "Щоб додати звичку, напиши:\n/habit Робити зарядку",
        "added": "🎯 Звичка додана: *{habit}*",
    },
    "be": {
        "limit": (
            "🌱 У бясплатнай версіі можна дадаць толькі 2 звычкі.\n\n"
            "✨ Падключы Mindra+, каб адсочваць неабмежаваную колькасць звычак 💜"
        ),
        "how_to": "Каб дадаць звычку, напішы:\n/habit Рабіць зарадку",
        "added": "🎯 Звычка дададзена: *{habit}*",
    },
    "kk": {
        "limit": (
            "🌱 Тегін нұсқада тек 2 әдет қосуға болады.\n\n"
            "✨ Mindra+ қосып, әдеттерді шексіз бақыла! 💜"
        ),
        "how_to": "Әдет қосу үшін жаз:\n/habit Таңертең жаттығу жасау",
        "added": "🎯 Әдет қосылды: *{habit}*",
    },
    "kg": {
        "limit": (
            "🌱 Акысыз версияда болгону 2 көнүмүш кошууга болот.\n\n"
            "✨ Mindra+ кошуп, чексиз көнүмүштөрдү көзөмөлдө! 💜"
        ),
        "how_to": "Көнүмүш кошуу үчүн жаз:\n/habit Таң эрте көнүгүү",
        "added": "🎯 Көнүмүш кошулду: *{habit}*",
    },
    "hy": {
        "limit": (
            "🌱 Անվճար տարբերակում կարող ես ավելացնել միայն 2 սովորություն։\n\n"
            "✨ Միացրու Mindra+, որպեսզի հետևես անսահմանափակ սովորությունների 💜"
        ),
        "how_to": "Սովորություն ավելացնելու համար գրիր՝\n/habit Վարժություն անել",
        "added": "🎯 Սովորությունը ավելացվել է՝ *{habit}*",
    },
    "ce": {
        "limit": (
            "🌱 Бесплатна версийна дуьйна 2 привычка цуьнан дац.\n\n"
            "✨ Mindra+ хетам болуш кхетам привычка хетам! 💜"
        ),
        "how_to": "Привычка дац дуьйна, хьоьшу напиши:\n/habit Зарядка",
        "added": "🎯 Привычка дац: *{habit}*",
    },
    "md": {
        "limit": (
            "🌱 În versiunea gratuită poți adăuga doar 2 obiceiuri.\n\n"
            "✨ Activează Mindra+ pentru a urmări oricâte obiceiuri vrei 💜"
        ),
        "how_to": "Pentru a adăuga un obicei, scrie:\n/habit Fă gimnastică",
        "added": "🎯 Obiceiul a fost adăugat: *{habit}*",
    },
    "ka": {
        "limit": (
            "🌱 უფასო ვერსიაში შეგიძლია დაამატო მხოლოდ 2 ჩვევა.\n\n"
            "✨ ჩართე Mindra+, რომ გააკონტროლო ულიმიტო ჩვევები 💜"
        ),
        "how_to": "ჩვევის დასამატებლად დაწერე:\n/habit დილას ვარჯიში",
        "added": "🎯 ჩვევა დამატებულია: *{habit}*",
    },
    "en": {
        "limit": (
            "🌱 In the free version you can add only 2 habits.\n\n"
            "✨ Unlock Mindra+ to track unlimited habits 💜"
        ),
        "how_to": "To add a habit, type:\n/habit Do morning exercise",
        "added": "🎯 Habit added: *{habit}*",
    },
}

MYSTATS_TEXTS = {
    "ru": {
        "title": "📌 *Твоя статистика*\n\n🌟 Твой титул: *{title}*\n🏅 Очков: *{points}*\n\nПродолжай выполнять цели и задания, чтобы расти! 💜",
        "premium_info": (
            "\n\n🔒 В Mindra+ ты получишь:\n"
            "💎 Расширенную статистику по целям и привычкам\n"
            "💎 Больше лимитов и эксклюзивные задания\n"
            "💎 Уникальные челленджи и напоминания ✨"
        ),
        "premium_button": "💎 Узнать о Mindra+",
        "extra": (
            "\n✅ Целей выполнено: {completed_goals}"
            "\n🌱 Привычек добавлено: {habits_tracked}"
            "\n🔔 Напоминаний: {reminders}"
            "\n📅 Дней активности: {days_active}"
        ),
    },
    "uk": {
        "title": "📌 *Твоя статистика*\n\n🌟 Твій титул: *{title}*\n🏅 Балів: *{points}*\n\nПродовжуй виконувати цілі й завдання, щоб зростати! 💜",
        "premium_info": (
            "\n\n🔒 У Mindra+ ти отримаєш:\n"
            "💎 Розширену статистику по цілях та звичках\n"
            "💎 Більше лімітів і ексклюзивні завдання\n"
            "💎 Унікальні челенджі й нагадування ✨"
        ),
        "premium_button": "💎 Дізнатись про Mindra+",
        "extra": (
            "\n✅ Виконано цілей: {completed_goals}"
            "\n🌱 Додано звичок: {habits_tracked}"
            "\n🔔 Нагадувань: {reminders}"
            "\n📅 Днів активності: {days_active}"
        ),
    },
    "be": {
        "title": "📌 *Твая статыстыка*\n\n🌟 Твой тытул: *{title}*\n🏅 Ачкоў: *{points}*\n\nПрацягвай ставіць мэты і выконваць заданні, каб расці! 💜",
        "premium_info": (
            "\n\n🔒 У Mindra+ ты атрымаеш:\n"
            "💎 Пашыраную статыстыку па мэтах і звычках\n"
            "💎 Больш лімітаў і эксклюзіўныя заданні\n"
            "💎 Унікальныя чэленджы і напамінкі ✨"
        ),
        "premium_button": "💎 Даведайся пра Mindra+",
        "extra": (
            "\n✅ Выканана мэтаў: {completed_goals}"
            "\n🌱 Дададзена звычак: {habits_tracked}"
            "\n🔔 Напамінкаў: {reminders}"
            "\n📅 Дзён актыўнасці: {days_active}"
        ),
    },
    "kk": {
        "title": "📌 *Сенің статистикаң*\n\n🌟 Титулың: *{title}*\n🏅 Ұпай: *{points}*\n\nМақсаттар мен тапсырмаларды орындауды жалғастыр! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+ арқылы сен аласың:\n"
            "💎 Мақсаттар мен әдеттер бойынша толық статистика\n"
            "💎 Көп лимит және ерекше тапсырмалар\n"
            "💎 Бірегей челлендждер мен ескертулер ✨"
        ),
        "premium_button": "💎 Mindra+ туралы білу",
        "extra": (
            "\n✅ Орындалған мақсаттар: {completed_goals}"
            "\n🌱 Қосылған әдеттер: {habits_tracked}"
            "\n🔔 Ескертулер: {reminders}"
            "\n📅 Белсенді күндер: {days_active}"
        ),
    },
    "kg": {
        "title": "📌 *Сенин статистикаң*\n\n🌟 Сенин наамың: *{title}*\n🏅 Балл: *{points}*\n\nМаксаттар менен тапшырмаларды аткарууну улант! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+ менен:\n"
            "💎 Максаттар жана көнүмүштөр боюнча толук статистика\n"
            "💎 Көп лимит жана өзгөчө тапшырмалар\n"
            "💎 Уникалдуу челендждер жана эскертүүлөр ✨"
        ),
        "premium_button": "💎 Mindra+ жөнүндө билүү",
        "extra": (
            "\n✅ Аткарылган максаттар: {completed_goals}"
            "\n🌱 Кошулган көнүмүштөр: {habits_tracked}"
            "\n🔔 Эскертүүлөр: {reminders}"
            "\n📅 Активдүү күндөр: {days_active}"
        ),
    },
    "hy": {
        "title": "📌 *Քո վիճակագրությունը*\n\n🌟 Քո տիտղոսը՝ *{title}*\n🏅 Մակարդակ՝ *{points}*\n\nՇարունակի՛ր նպատակների ու առաջադրանքների կատարումը, որպեսզի աճես։ 💜",
        "premium_info": (
            "\n\n🔒 Mindra+-ում կարող ես ստանալ՝\n"
            "💎 Նպատակների ու սովորությունների վիճակագրությունը\n"
            "💎 Ավելի շատ սահմանաչափեր ու յուրահատուկ առաջադրանքներ\n"
            "💎 Ունիակլի մարտահրավերներ ու հիշեցումներ ✨"
        ),
        "premium_button": "💎 Իմանալ Mindra+-ի մասին",
        "extra": (
            "\n✅ Կատարված նպատակներ՝ {completed_goals}"
            "\n🌱 Ավելացված սովորություններ՝ {habits_tracked}"
            "\n🔔 Հիշեցումներ՝ {reminders}"
            "\n📅 Ակտիվ օրեր՝ {days_active}"
        ),
    },
    "ce": {
        "title": "📌 *Хьоь статистика*\n\n🌟 Титул: *{title}*\n🏅 Балл: *{points}*\n\nДаймохь цуьнан кхолларча хетам хенна! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+ хетам долу:\n"
            "💎 Мацахь, привычка статистика\n"
            "💎 Больше лимитов, эксклюзивные задачи\n"
            "💎 Уникальные челленджи и напоминания ✨"
        ),
        "premium_button": "💎 Узнать о Mindra+",
        "extra": (
            "\n✅ Выполнено целей: {completed_goals}"
            "\n🌱 Добавлено привычек: {habits_tracked}"
            "\n🔔 Напоминаний: {reminders}"
            "\n📅 Активных дней: {days_active}"
        ),
    },
    "md": {
        "title": "📌 *Statistica ta*\n\n🌟 Titlul tău: *{title}*\n🏅 Puncte: *{points}*\n\nContinuă să îți îndeplinești obiectivele și sarcinile pentru a crește! 💜",
        "premium_info": (
            "\n\n🔒 În Mindra+ vei obține:\n"
            "💎 Statistici detaliate despre obiective și obiceiuri\n"
            "💎 Mai multe limite și sarcini exclusive\n"
            "💎 Provocări unice și notificări ✨"
        ),
        "premium_button": "💎 Află despre Mindra+",
        "extra": (
            "\n✅ Obiective realizate: {completed_goals}"
            "\n🌱 Obiceiuri adăugate: {habits_tracked}"
            "\n🔔 Notificări: {reminders}"
            "\n📅 Zile active: {days_active}"
        ),
    },
    "ka": {
        "title": "📌 *შენი სტატისტიკა*\n\n🌟 შენი ტიტული: *{title}*\n🏅 ქულები: *{points}*\n\nაგრძელე მიზნების და დავალებების შესრულება, რომ გაიზარდო! 💜",
        "premium_info": (
            "\n\n🔒 Mindra+-ში მიიღებ:\n"
            "💎 დეტალურ სტატისტიკას მიზნებსა და ჩვევებზე\n"
            "💎 მეტი ლიმიტი და ექსკლუზიური დავალებები\n"
            "💎 უნიკალური ჩელენჯები და შეხსენებები ✨"
        ),
        "premium_button": "💎 გაიგე Mindra+-ის შესახებ",
        "extra": (
            "\n✅ შესრულებული მიზნები: {completed_goals}"
            "\n🌱 დამატებული ჩვევები: {habits_tracked}"
            "\n🔔 შეხსენებები: {reminders}"
            "\n📅 აქტიური დღეები: {days_active}"
        ),
    },
    "en": {
        "title": "📌 *Your stats*\n\n🌟 Your title: *{title}*\n🏅 Points: *{points}*\n\nKeep accomplishing your goals and tasks to grow! 💜",
        "premium_info": (
            "\n\n🔒 In Mindra+ you get:\n"
            "💎 Advanced stats for goals and habits\n"
            "💎 Higher limits & exclusive tasks\n"
            "💎 Unique challenges and reminders ✨"
        ),
        "premium_button": "💎 Learn about Mindra+",
        "extra": (
            "\n✅ Goals completed: {completed_goals}"
            "\n🌱 Habits added: {habits_tracked}"
            "\n🔔 Reminders: {reminders}"
            "\n📅 Active days: {days_active}"
        ),
    },
}

STATS_TEXTS = {
    "ru": (
        "📊 Статистика Mindra:\n\n"
        "👥 Всего пользователей: {total}\n"
        "💎 Подписчиков: {premium}\n"
    ),
    "uk": (
        "📊 Статистика Mindra:\n\n"
        "👥 Всього користувачів: {total}\n"
        "💎 Підписників: {premium}\n"
    ),
    "be": (
        "📊 Статыстыка Mindra:\n\n"
        "👥 Усяго карыстальнікаў: {total}\n"
        "💎 Падпісчыкаў: {premium}\n"
    ),
    "kk": (
        "📊 Mindra статистикасы:\n\n"
        "👥 Барлық қолданушылар: {total}\n"
        "💎 Жазылушылар: {premium}\n"
    ),
    "kg": (
        "📊 Mindra статистикасы:\n\n"
        "👥 Жалпы колдонуучулар: {total}\n"
        "💎 Жазылуучулар: {premium}\n"
    ),
    "hy": (
        "📊 Mindra-ի վիճակագրությունը․\n\n"
        "👥 Բոլոր օգտատերերը՝ {total}\n"
        "💎 Բաժանորդներ՝ {premium}\n"
    ),
    "ce": (
        "📊 Mindra статистика:\n\n"
        "👥 Жалпы юзераш: {total}\n"
        "💎 Подписчик: {premium}\n"
    ),
    "md": (
        "📊 Statistica Mindra:\n\n"
        "👥 Utilizatori totali: {total}\n"
        "💎 Abonați: {premium}\n"
    ),
    "ka": (
        "📊 Mindra სტატისტიკა:\n\n"
        "👥 მომხმარებლები სულ: {total}\n"
        "💎 გამომწერები: {premium}\n"
    ),
    "en": (
        "📊 Mindra stats:\n\n"
        "👥 Total users: {total}\n"
        "💎 Subscribers: {premium}\n"
    ),
}

# 🔑 Ответы для get_topic_reference на всех языках
topic_reference_by_lang = {
    "ru": {
        "отношения": "💘 Ты упоминал(а) недавно про отношения... Всё в порядке?",
        "работа": "💼 Как дела на работе? Я помню, тебе было тяжело.",
        "спорт": "🏋️‍♂️ Как у тебя со спортом, продолжил(а)?",
        "одиночество": "🤗 Помни, что ты не один(одна), даже если так казалось.",
        "саморазвитие": "🌱 Продолжаешь развиваться? Это вдохновляет!"
    },
    "en": {
        "love": "💘 You mentioned relationships earlier… Is everything okay?",
        "work": "💼 How’s work going? I remember it was tough for you.",
        "sport": "🏋️‍♂️ How’s your training going?",
        "lonely": "🤗 Remember, you’re not alone, even if it feels that way.",
        "growth": "🌱 Still working on your personal growth? That’s inspiring!"
    },
    "uk": {
        "стосунки": "💘 Ти згадував(ла) про стосунки… Все добре?",
        "робота": "💼 Як справи на роботі? Пам’ятаю, тобі було важко.",
        "спорт": "🏋️‍♂️ Як твої тренування, продовжуєш?",
        "самотність": "🤗 Пам’ятай, ти не сам(а), навіть якщо так здається.",
        "саморозвиток": "🌱 Продовжуєш розвиватись? Це надихає!"
    },
    "be": {
        "адносіны": "💘 Ты нядаўна казаў(ла) пра адносіны… Усё добра?",
        "праца": "💼 Як справы на працы? Памятаю, табе было цяжка.",
        "спорт": "🏋️‍♂️ Як твае трэніроўкі?",
        "адзінота": "🤗 Памятай, ты не адзін(ая).",
        "развіццё": "🌱 Працягваеш развівацца? Гэта натхняе!"
    },
    "kk": {
        "махаббат": "💘 Сен жақында қарым-қатынас туралы айттың… Бәрі жақсы ма?",
        "жұмыс": "💼 Жұмысың қалай? Қиын болғанын білемін.",
        "спорт": "🏋️‍♂️ Жаттығуларың қалай?",
        "жалғыздық": "🤗 Есіңде болсын, сен жалғыз емессің.",
        "даму": "🌱 Дамуды жалғастырып жатырсың ба? Бұл шабыттандырады!"
    },
    "kg": {
        "сүйүү": "💘 Сен жакында мамиле жөнүндө айттың… Баары жакшыбы?",
        "иш": "💼 Ишиң кандай? Кыйын болгонун билем.",
        "спорт": "🏋️‍♂️ Жаттууларың кандай?",
        "жалгыздык": "🤗 Эсиңде болсун, сен жалгыз эмессиң.",
        "өркүндөө": "🌱 Өсүүнү улантып жатасыңбы? Бул шыктандырат!"
    },
    "hy": {
        "սեր": "💘 Դու վերջերս սիրո մասին ես խոսել… Ամեն ինչ լավ է?",
        "աշխատանք": "💼 Աշխատանքդ ինչպես է? Հիշում եմ, որ դժվար էր քեզ համար.",
        "սպորտ": "🏋️‍♂️ Մարզումդ ինչպես է?",
        "միայնություն": "🤗 Հիշիր, որ միայնակ չես։",
        "զարգացում": "🌱 Շարունակում ես զարգանալ? Սա ոգեշնչող է!"
    },
    "ce": {
        "хьо": "💘 Хьо любов, хьо кхета… хьо йолла?",
        "работа": "💼 Хьо дIан? Са цуьнан хила.",
        "спорт": "🏋️‍♂️ Хьо спорт йац?",
        "одиночество": "🤗 Хьо ца йац.",
        "развитие": "🌱 Хьо а да хьо дика."
    },
    "md": {
        "dragoste": "💘 Ai menționat dragostea… Totul bine?",
        "muncă": "💼 Cum merge munca? Țin minte că era greu.",
        "sport": "🏋️‍♂️ Cum merge antrenamentul tău?",
        "singurătate": "🤗 Amintește-ți, nu ești singur(ă).",
        "dezvoltare": "🌱 Îți continui dezvoltarea? E minunat!"
    },
    "ka": {
        "სიყვარული": "💘 შენ ახლახან სიყვარულზე თქვი… ყველაფერი რიგზეა?",
        "სამუშაო": "💼 სამსახური როგორ მიდის? მახსოვს, რომ გიჭირდა.",
        "სპორტი": "🏋️‍♂️ ვარჯიშები როგორ მიდის?",
        "მარტოობა": "🤗 გახსოვდეს, მარტო არ ხარ.",
        "განვითარება": "🌱 განაგრძობ განვითარებას? ეს შთამბეჭდავია!"
    },
}

# 🔑 Паттерны для определения темы на всех языках
topic_patterns_full = {
    "ru": {
        "отношения": r"\b(девушк|люблю|отношен|парн|флирт|расст|поцелу|влюб)\b",
        "работа": r"\b(работа|босс|смена|коллег|заработ|устал|стресс)\b",
        "спорт": r"\b(зал|спорт|тренир|бег|гантел|похуд)\b",
        "одиночество": r"\b(одинок|один|некому|никто не)\b",
        "саморазвитие": r"\b(цель|развитие|мотивац|успех|саморазв)\b",
    },
    "en": {
        "love": r"\b(love|relationship|girlfriend|boyfriend|date|kiss|crush|breakup|flirt)\b",
        "work": r"\b(work|boss|shift|colleague|salary|tired|stress)\b",
        "sport": r"\b(gym|sport|training|run|dumbbell|fitness|exercise)\b",
        "lonely": r"\b(lonely|alone|nobody|no one)\b",
        "growth": r"\b(goal|growth|motivation|success|self|improve)\b",
    },
    "uk": {
        "стосунки": r"\b(дівчин|хлопц|люблю|стосунк|флірт|розлуч|поцілун)\b",
        "робота": r"\b(робот|начальник|зміна|колег|зарплат|втомив|стрес)\b",
        "спорт": r"\b(спорт|зал|тренуванн|біг|гантел)\b",
        "самотність": r"\b(самотн|ніхто|нікого|один)\b",
        "саморозвиток": r"\b(ціль|розвит|мотивац|успіх|саморозв)\b",
    },
    "be": {
        "адносіны": r"\b(дзяўчын|хлопец|кахан|сустрэч|пацал)\b",
        "праца": r"\b(праца|начальнік|калег|зарплат|стаміў|стрэс)\b",
        "спорт": r"\b(спорт|зала|трэніроўк|бег|гантэл)\b",
        "адзінота": r"\b(адзін|адна|самотн|ніхто)\b",
        "развіццё": r"\b(мэта|рост|мотивац|поспех)\b",
    },
    "kk": {
        "махаббат": r"\b(сүйемін|ғашық|қыз|жігіт|қарым-қат|поцелу)\b",
        "жұмыс": r"\b(жұмыс|бастық|ауысым|әріптес|айлық|шаршадым|стресс)\b",
        "спорт": r"\b(спорт|зал|жаттығу|жүгіру|гантель)\b",
        "жалғыздық": r"\b(жалғыз|ешкім|жалғыздық)\b",
        "даму": r"\b(мақсат|даму|мотивац|жетістік)\b",
    },
    "kg": {
        "сүйүү": r"\b(сүйөм|ашык|кыз|жигит|мамиле|сүйлөшүү|поцелуй)\b",
        "иш": r"\b(иш|начальник|кезек|кесиптеш|айлык|чарчап|стресс)\b",
        "спорт": r"\b(спорт|зал|жаттыгуу|чуркоо|гантель)\b",
        "жалгыздык": r"\b(жалгыз|эч ким)\b",
        "өркүндөө": r"\b(максат|мотивац|өсүү|ийгилик)\b",
    },
    "hy": {
        "սեր": r"\b(սիրում|սիրահարված|հարաբերություն|հանդիպում|համբույր)\b",
        "աշխատանք": r"\b(աշխատանք|գլուխ|հոգնած|ղեկավար|աշխատակց)\b",
        "սպորտ": r"\b(սպորտ|մարզասրահ|վարժություն|վազք)\b",
        "միայնություն": r"\b(միայնակ|ոչ ոք)\b",
        "զարգացում": r"\b(նպատակ|մոտիվացիա|զարգացում|հաջողություն)\b",
    },
    "ce": {
        "хьо": r"\b(хьо кхета|хьо йац|хьо мац|хьо хьаж|хьо йол|хьо йаьлла)\b",
        "работа": r"\b(работ|хьо дIан|хьо чар)\b",
        "спорт": r"\b(спорт|хьо зал|хьо трен)\b",
        "одиночество": r"\b(хьо ца йац|хьо ца хьо)\b",
        "развитие": r"\b(мотивац|хьо а|хьо дика)\b",
    },
    "md": {
        "dragoste": r"\b(iubesc|dragoste|prietenă|prieten|relație|sărut)\b",
        "muncă": r"\b(muncă|obosit|șef|coleg|salariu)\b",
        "sport": r"\b(sport|sală|antrenament|alergare)\b",
        "singurătate": r"\b(singur|singură|nimeni)\b",
        "dezvoltare": r"\b(motivație|scop|dezvoltare|succes)\b",
    },
    "ka": {
        "სიყვარული": r"\b(მიყვარს|შეყვარებული|ბიჭი|გოგო|შეხვედრა|კოცნა)\b",
        "სამუშაო": r"\b(სამუშაო|ხელმძღვანელი|თანამშრომელი|დაღლილი)\b",
        "სპორტი": r"\b(სპორტი|დარბაზი|ვარჯიში)\b",
        "მარტოობა": r"\b(მარტო|არავინ)\b",
        "განვითარება": r"\b(მოტივაცია|მიზანი|განვითარება|წარმატება)\b",
    },
}

topic_patterns_by_lang = {
    "ru": {
        "love": {
            "patterns": r"\b(влюбил|влюблена|люблю|девушк|парн|отношен|встретил|свидани|поцелу|встреча|расстался|разошлись|флирт|переписк)\b",
            "reply": "💘 Это звучит очень трогательно. Любовные чувства — это всегда волнительно. Хочешь рассказать подробнее, что происходит?"
        },
        "lonely": {
            "patterns": r"\b(один|одна|одинок|некому|никто не|чувствую себя один)\b",
            "reply": "🫂 Иногда это чувство может накрывать... Но знай: ты не один и не одна. Я рядом. 💜"
        },
        "work": {
            "patterns": r"\b(работа|устал|босс|давлени|коллег|увольн|смена|заработ|не выношу|задолбал)\b",
            "reply": "🧑‍💼 Работа может быть выматывающей. Ты не обязан(а) всё тянуть в одиночку. Я здесь, если хочешь выговориться."
        },
        "sport": {
            "patterns": r"\b(зал|спорт|бег|жим|гантел|тренир|добился|успех|100кг|тренировка|похуд)\b",
            "reply": "🏆 Молодец! Это важный шаг на пути к себе. Как ты себя чувствуешь после этого достижения?"
        },
        "family": {
            "patterns": r"\b(мама|папа|семь|родител|сестра|брат|дед|бабушк)\b",
            "reply": "👨‍👩‍👧‍👦 Семья может давать и тепло, и сложности. Я готов(а) выслушать — расскажи, если хочется."
        },
        "motivation": {
            "patterns": r"\b(мотивац|цель|развитие|дух|успех|медитац|саморазвити|осознанн|рост|путь)\b",
            "reply": "🌱 Это здорово, что ты стремишься к развитию. Давай обсудим, как я могу помочь тебе на этом пути."
        }
    },

    "en": {
        "love": {
            "patterns": r"\b(love|crush|girlfriend|boyfriend|relationship|date|kiss|breakup|flirt|chatting)\b",
            "reply": "💘 That sounds really touching. Love can be so exciting. Want to share more?"
        },
        "lonely": {
            "patterns": r"\b(lonely|alone|no one|nobody|feel alone)\b",
            "reply": "🫂 That feeling can be overwhelming… But remember, you’re not alone. I’m here. 💜"
        },
        "work": {
            "patterns": r"\b(work|tired|boss|pressure|colleague|job|salary|overloaded)\b",
            "reply": "🧑‍💼 Work can be exhausting. You don’t have to carry it all alone. I’m here if you want to talk."
        },
        "sport": {
            "patterns": r"\b(gym|sport|running|pushup|dumbbell|training|achieved|success|workout)\b",
            "reply": "🏆 Awesome! That’s a great step forward. How do you feel after this achievement?"
        },
        "family": {
            "patterns": r"\b(mom|dad|family|parent|sister|brother|grandma|grandpa)\b",
            "reply": "👨‍👩‍👧‍👦 Family can bring both warmth and challenges. I’m here if you want to share."
        },
        "motivation": {
            "patterns": r"\b(motivation|goal|growth|mindfulness|success|meditation|path)\b",
            "reply": "🌱 It’s wonderful that you’re striving to grow. Let’s talk about how I can support you."
        }
    },

    "uk": {
        "love": {
            "patterns": r"\b(кохаю|закохався|закохана|дівчин|хлопц|стосунк|побаченн|поціл)\b",
            "reply": "💘 Це звучить дуже зворушливо. Кохання — завжди хвилює. Хочеш розповісти більше?"
        },
        "lonely": {
            "patterns": r"\b(самотн|нікого|ніхто|почуваюсь сам)\b",
            "reply": "🫂 Іноді це відчуття накриває… Але ти не сам(а). Я поруч. 💜"
        },
        "work": {
            "patterns": r"\b(робот|втомив|начальник|тиск|колег|звільненн|зарплат)\b",
            "reply": "🧑‍💼 Робота буває виснажливою. Ти не зобов’язаний(а) тягнути все сам(а)."
        },
        "sport": {
            "patterns": r"\b(спорт|зал|біг|гантел|тренуванн|успіх)\b",
            "reply": "🏆 Молодець! Це великий крок уперед. Як ти почуваєшся?"
        },
        "family": {
            "patterns": r"\b(мама|тато|сім'|брат|сестра|бабус|дідус)\b",
            "reply": "👨‍👩‍👧‍👦 Родина може дати і тепло, і складнощі. Розкажи, якщо хочеш."
        },
        "motivation": {
            "patterns": r"\b(мотивац|ціль|розвит|успіх|медитац|зростанн)\b",
            "reply": "🌱 Це чудово, що ти прагнеш до розвитку. Я поруч!"
        }
    },

    "be": {
        "love": {
            "patterns": r"\b(кахан|каханне|дзяўчын|хлопец|сустрэч|пацал)\b",
            "reply": "💘 Гэта вельмі кранальна. Каханне заўсёды хвалюе. Хочаш расказаць больш?"
        },
        "lonely": {
            "patterns": r"\b(адзін|адна|самотн|ніхто|няма каму)\b",
            "reply": "🫂 Часам гэта адчуванне накрывае… Але ты не адзін(ая). Я побач. 💜"
        },
        "work": {
            "patterns": r"\b(праца|стаміў|начальнік|ціск|калег|зарплат)\b",
            "reply": "🧑‍💼 Праца можа быць цяжкай. Ты не павінен(на) цягнуць усё сам(а)."
        },
        "sport": {
            "patterns": r"\b(спорт|зала|бег|гантэл|трэніроўк|поспех)\b",
            "reply": "🏆 Маладзец! Гэта важны крок. Як ты сябе адчуваеш?"
        },
        "family": {
            "patterns": r"\b(маці|бацька|сям'я|сястра|брат|дзед|бабул)\b",
            "reply": "👨‍👩‍👧‍👦 Сям'я можа даваць і цяпло, і складанасці. Я побач."
        },
        "motivation": {
            "patterns": r"\b(мэта|мотивац|рост|успех|развиццё)\b",
            "reply": "🌱 Гэта цудоўна, што ты імкнешся да росту. Я побач!"
        }
    },

    "kk": {
        "love": {
            "patterns": r"\b(сүйемін|ғашықпын|қыз|жігіт|қарым-қат|кездесу|сүйіс)\b",
            "reply": "💘 Бұл өте әсерлі естіледі. Махаббат әрқашан толқу әкеледі. Толығырақ айтқың келе ме?"
        },
        "lonely": {
            "patterns": r"\b(жалғыз|ешкім|жалғыздық)\b",
            "reply": "🫂 Кейде бұл сезім қысады… Бірақ сен жалғыз емессің. Мен осындамын. 💜"
        },
        "work": {
            "patterns": r"\b(жұмыс|шаршадым|бастық|қысым|әріптес|айлық)\b",
            "reply": "🧑‍💼 Жұмыс шаршатуы мүмкін. Барлығын жалғыз көтерудің қажеті жоқ."
        },
        "sport": {
            "patterns": r"\b(спорт|зал|жүгіру|жаттығу|гантель|жетістік)\b",
            "reply": "🏆 Жарайсың! Бұл үлкен қадам. Өзіңді қалай сезініп тұрсың?"
        },
        "family": {
            "patterns": r"\b(ана|әке|отбас|аға|әпке|қарындас|әже|ата)\b",
            "reply": "👨‍👩‍👧‍👦 Отбасы жылулық та, қиындық та бере алады. Қаласаң, бөліс."
        },
        "motivation": {
            "patterns": r"\b(мақсат|мотивац|даму|жетістік|өсу)\b",
            "reply": "🌱 Тамаша, сен дамуға ұмтылып жатырсың. Мен осындамын!"
        }
    },

    "kg": {
        "love": {
            "patterns": r"\b(сүйөм|ашыкмын|кыз|жигит|мамиле|жолугушу|сүйлөшүү)\b",
            "reply": "💘 Бул абдан таасирлүү угулат. Сүйүү ар дайым толкундантат. Толук айтып бересиңби?"
        },
        "lonely": {
            "patterns": r"\b(жалгыз|эч ким)\b",
            "reply": "🫂 Кээде бул сезим каптап кетет… Бирок сен жалгыз эмессиң. Мен жанымдамын. 💜"
        },
        "work": {
            "patterns": r"\b(иш|чарчап|начальник|басым|кесиптеш|айлык)\b",
            "reply": "🧑‍💼 Иш чарчатуучу болушу мүмкүн. Баарын жалгыз көтөрбө."
        },
        "sport": {
            "patterns": r"\b(спорт|зал|чуркоо|жаттыгуу|гантель|ийгилик)\b",
            "reply": "🏆 Молодец! Бул чоң кадам. Кантип сезип жатасың?"
        },
        "family": {
            "patterns": r"\b(апа|ата|үй-бүл|ага|карындаш|эжеси|ата-эне)\b",
            "reply": "👨‍👩‍👧‍👦 Үй-бүлө жылуулук да, кыйынчылык да берет. Айтып бергиң келеби?"
        },
        "motivation": {
            "patterns": r"\b(максат|мотивац|өсүү|ийгилик)\b",
            "reply": "🌱 Сонун! Сен өсүүгө аракет кылып жатасың."
        }
    },

    "hy": {
        "love": {
            "patterns": r"\b(սիրում եմ|սիրահարված|սիրած|սիրելի|հարաբերություն|հանդիպում|համբույր)\b",
            "reply": "💘 Սա հնչում է շատ հուզիչ։ Սերը միշտ էլ հուզիչ է։ Կուզե՞ս ավելին պատմել։"
        },
        "lonely": {
            "patterns": r"\b(միայնակ|ոչ ոք)\b",
            "reply": "🫂 Երբեմն այդ զգացումը կարող է ծանր լինել… Բայց դու միայնակ չես։ Ես կողքիդ եմ։ 💜"
        },
        "work": {
            "patterns": r"\b(աշխատանք|հոգնած|գլուխ|վճար)\b",
            "reply": "🧑‍💼 Աշխատանքը կարող է հյուծող լինել։ Չպետք է ամեն ինչ ինքդ տանել։"
        },
        "sport": {
            "patterns": r"\b(սպորտ|մարզասրահ|վազք|վարժություն|հաջողություն)\b",
            "reply": "🏆 Դու հրաշալի ես! Սա մեծ քայլ է։ Ինչպե՞ս ես քեզ զգում։"
        },
        "family": {
            "patterns": r"\b(մայր|հայր|ընտանիք|քույր|եղբայր|տատիկ|պապիկ)\b",
            "reply": "👨‍👩‍👧‍👦 Ընտանիքը կարող է տալ ինչպես ջերմություն, այնպես էլ դժվարություններ։"
        },
        "motivation": {
            "patterns": r"\b(նպատակ|մոտիվացիա|զարգացում|հաջողություն)\b",
            "reply": "🌱 Դու ձգտում ես առաջ գնալ։ Ես կողքիդ եմ!"
        }
    },

    "ce": {
        "love": {
            "patterns": r"\b(хьо кхета|хьо йац|хьо мац|хьо хьаж|хьо йол|хьо йаьлла)\b",
            "reply": "💘 Хьо йац кхеташ до. Хьо ца даьлча. Хьо даьлча еза!"
        },
        "lonely": {
            "patterns": r"\b(хьо ца йац|хьо ца хьо|хьо до хьо йац)\b",
            "reply": "🫂 Хьо ца йац… Са цуьнан. Са даьлча. 💜"
        },
        "work": {
            "patterns": r"\b(работ|хьо дIан|хьо чар)\b",
            "reply": "🧑‍💼 Хьо дIан гойла. Хьо ца йац хила."
        },
        "sport": {
            "patterns": r"\b(спорт|хьо зал|хьо трен)\b",
            "reply": "🏆 Дика йац! Хьо тIе хила?"
        },
        "family": {
            "patterns": r"\b(мама|папа|къант|сестра|брат|дада)\b",
            "reply": "👨‍👩‍👧‍👦 Къант кхеташ… Са йац!"
        },
        "motivation": {
            "patterns": r"\b(мотивац|хьо а|хьо дика)\b",
            "reply": "🌱 Хьо дика. Са йац!"
        }
    },

    "md": {
        "love": {
            "patterns": r"\b(iubesc|dragoste|prietenă|prieten|relație|întâlnire|sărut)\b",
            "reply": "💘 Sună foarte emoționant. Dragostea este mereu specială. Vrei să îmi povestești mai mult?"
        },
        "lonely": {
            "patterns": r"\b(singur|singură|nimeni|mă simt singur)\b",
            "reply": "🫂 Uneori sentimentul acesta e greu… Dar nu ești singur(ă). Sunt aici. 💜"
        },
        "work": {
            "patterns": r"\b(muncă|obosit|șef|presiune|coleg|salariu)\b",
            "reply": "🧑‍💼 Munca poate fi obositoare. Nu trebuie să duci totul singur(ă)."
        },
        "sport": {
            "patterns": r"\b(sport|sală|alergare|antrenament|gantere|succes)\b",
            "reply": "🏆 Bravo! Este un pas mare înainte. Cum te simți?"
        },
        "family": {
            "patterns": r"\b(mamă|tată|familie|frate|soră|bunica|bunicul)\b",
            "reply": "👨‍👩‍👧‍👦 Familia poate aduce atât căldură, cât și dificultăți. Povestește-mi dacă vrei."
        },
        "motivation": {
            "patterns": r"\b(motivație|scop|dezvoltare|succes)\b",
            "reply": "🌱 E minunat că vrei să te dezvolți. Sunt aici!"
        }
    },

    "ka": {
        "love": {
            "patterns": r"\b(მიყვარს|შეყვარებული|ბიჭი|გოგო|შეხვედრა|კოცნა|ურთიერთობა)\b",
            "reply": "💘 ეს ძალიან შემხებლიანად ჟღერს. სიყვარული ყოველთვის განსაკუთრებულია. მეტს მომიყვები?"
        },
        "lonely": {
            "patterns": r"\b(მარტო|მარტოობა|არავინა|ვგრძნობ თავს მარტო)\b",
            "reply": "🫂 ზოგჯერ ეს განცდა მძიმეა… მაგრამ შენ მარტო არ ხარ. მე აქ ვარ. 💜"
        },
        "work": {
            "patterns": r"\b(სამუშაო|დაღლილი|ხელმძღვანელი|ზეწოლა|თანამშრომელი|ხელფასი)\b",
            "reply": "🧑‍💼 სამუშაო შეიძლება დამღლელი იყოს. მარტო არ გიწევს ყველაფრის კეთება."
        },
        "sport": {
            "patterns": r"\b(სპორტი|დარბაზი|ვარჯიში|გაწვრთნა|წარმატება)\b",
            "reply": "🏆 შენ შესანიშნავი ხარ! ეს დიდი ნაბიჯია. როგორ გრძნობ თავს?"
        },
        "family": {
            "patterns": r"\b(დედა|მამა|ოჯახი|და|ძმა|ბებია|ბაბუა)\b",
            "reply": "👨‍👩‍👧‍👦 ოჯახს შეუძლია მოგცეს სითბოც და სირთულეც. მომიყევი, თუ გინდა."
        },
        "motivation": {
            "patterns": r"\b(მოტივაცია|მიზანი|განვითარება|წარმატება)\b",
            "reply": "🌱 მშვენიერია, რომ ცდილობ განვითარებას. მე აქ ვარ!"
        }
    },
}

# 🔑 Ключевые слова для эмоций на разных языках
emotion_keywords_by_lang = {
    "ru": {
        "positive": ["ура", "сделал", "сделала", "получилось", "рад", "рада", "наконец", "круто", "кайф", "горжусь", "удалось"],
        "negative": ["плохо", "тяжело", "устал", "устала", "раздражает", "не знаю", "выгорание", "одиноко", "грустно", "сложно", "печально"],
        "stress":   ["стресс", "нервы", "не спал", "не спала", "перегруз", "паника", "волнение"]
    },
    "en": {
        "positive": ["yay", "did it", "done", "achieved", "happy", "finally", "awesome", "cool", "proud", "succeeded"],
        "negative": ["bad", "hard", "tired", "annoying", "burnout", "lonely", "sad", "difficult"],
        "stress":   ["stress", "nervous", "didn't sleep", "overload", "panic"]
    },
    "uk": {
        "positive": ["ура", "зробив", "зробила", "вийшло", "радий", "рада", "нарешті", "круто", "кайф", "пишаюсь", "вдалося"],
        "negative": ["погано", "важко", "втомився", "втомилась", "дратує", "не знаю", "вигорів", "самотньо", "сумно", "складно"],
        "stress":   ["стрес", "нерви", "не спав", "не спала", "перевантаження", "паніка"]
    },
    "be": {
        "positive": ["ура", "зрабіў", "зрабіла", "атрымаўся", "рада", "нарэшце", "крута", "кайф", "гарджуся"],
        "negative": ["дрэнна", "цяжка", "стаміўся", "стамілася", "раздражняе", "не ведаю", "выгараў", "самотна", "сумна"],
        "stress":   ["стрэс", "нервы", "не спаў", "не спала", "перагрузка", "паніка"]
    },
    "kk": {
        "positive": ["жасадым", "жасап койдым", "жасалды", "қуаныштымын", "ақыры", "керемет", "мақтанамын"],
        "negative": ["жаман", "қиын", "шаршадым", "жалықтым", "жалғызбын", "мұңды", "қиындық"],
        "stress":   ["стресс", "жүйке", "ұйықтамадым", "шамадан тыс", "үрей"]
    },
    "kg": {
        "positive": ["болду", "аткардым", "бүттү", "куаныштамын", "сонун", "акыры", "суйунуп жатам", "мактанам"],
        "negative": ["жаман", "оор", "чарчап", "жалгыз", "кайгы", "кайнатат"],
        "stress":   ["стресс", "нерв", "уктаган жокмун", "чарчоо", "паника"]
    },
    "hy": {
        "positive": ["արեցի", "հաջողվեց", "ուրախ եմ", "վերջապես", "հիանալի", "հպարտ եմ"],
        "negative": ["վատ", "ծանր", "հոգնած", "միայնակ", "տխուր", "դժվար"],
        "stress":   ["սթրես", "նյարդեր", "չքնեցի", "գերլարում", "խուճապ"]
    },
    "ce": {
        "positive": ["хьо кхета", "хьо хийца", "дӀаязде", "хьо даьлча", "хьо дола", "хьо лело"],
        "negative": ["хьо ца ха", "хьо бу ха", "хьо ца йац", "хьо со", "хьо чура", "хьо ца"],
        "stress":   ["стресс", "нерв", "хьо ца спала", "хьо ца спал", "паника"]
    },
    "md": {
        "positive": ["am reușit", "gata", "fericit", "în sfârșit", "minunat", "mândru"],
        "negative": ["rău", "greu", "obosit", "singur", "trist", "dificil"],
        "stress":   ["stres", "nervi", "n-am dormit", "suprasolicitare", "panică"]
    },
    "ka": {
        "positive": ["ვქენი", "გამომივიდა", "ბედნიერი ვარ", "საბოლოოდ", "მშვენიერია", "ვამაყობ"],
        "negative": ["ცუდი", "რთული", "დაღლილი", "მარტო", "მოწყენილი", "გართულება"],
        "stress":   ["სტრესი", "ნერვები", "არ დამეძინა", "გადატვირთვა", "პანიკა"]
    },
}

MORNING_MESSAGES_BY_LANG = {
    "ru": [
        "🌞 Доброе утро! Как ты сегодня? 💜",
        "☕ Доброе утро! Пусть твой день будет лёгким и приятным ✨",
        "💌 Приветик! Утро — самое время начать что-то классное. Расскажешь, как настроение?",
        "🌸 С добрым утром! Желаю тебе улыбок и тепла сегодня 🫶",
        "😇 Утро доброе! Я тут и думаю о тебе, как ты там?",
        "🌅 Доброе утро! Сегодня отличный день, чтобы сделать что-то для себя 💛",
        "💫 Привет! Как спалось? Желаю тебе продуктивного и яркого дня ✨",
        "🌻 Утро доброе! Пусть сегодня всё будет в твою пользу 💪",
        "🍀 Доброе утро! Сегодняшний день — новая возможность для чего-то прекрасного 💜",
        "☀️ Привет! Улыбнись новому дню, он тебе точно улыбнётся 🌈"
    ],
    "en": [
        "🌞 Good morning! How are you today? 💜",
        "☕ Good morning! May your day be light and pleasant ✨",
        "💌 Hi there! Morning is the best time to start something great. How’s your mood?",
        "🌸 Good morning! Wishing you smiles and warmth today 🫶",
        "😇 Morning! I’m here thinking of you, how are you?",
        "🌅 Good morning! Today is a great day to do something for yourself 💛",
        "💫 Hi! How did you sleep? Wishing you a productive and bright day ✨",
        "🌻 Good morning! May everything work out in your favor today 💪",
        "🍀 Good morning! Today is a new opportunity for something wonderful 💜",
        "☀️ Hey! Smile at the new day, and it will smile back 🌈"
    ],
    "uk": [
        "🌞 Доброго ранку! Як ти сьогодні? 💜",
        "☕ Доброго ранку! Нехай твій день буде легким і приємним ✨",
        "💌 Привітик! Ранок — найкращий час почати щось класне. Як настрій?",
        "🌸 З добрим ранком! Бажаю тобі усмішок і тепла сьогодні 🫶",
        "😇 Добрий ранок! Я тут і думаю про тебе, як ти?",
        "🌅 Доброго ранку! Сьогодні чудовий день, щоб зробити щось для себе 💛",
        "💫 Привіт! Як спалося? Бажаю тобі продуктивного і яскравого дня ✨",
        "🌻 Доброго ранку! Нехай сьогодні все буде на твою користь 💪",
        "🍀 Доброго ранку! Сьогоднішній день — нова можливість для чогось прекрасного 💜",
        "☀️ Привіт! Усміхнися новому дню, і він усміхнеться тобі 🌈"
    ],
    "be": [
        "🌞 Добрай раніцы! Як ты сёння? 💜",
        "☕ Добрай раніцы! Хай твой дзень будзе лёгкім і прыемным ✨",
        "💌 Прывітанне! Раніца — самы час пачаць нешта класнае. Як настрой?",
        "🌸 З добрай раніцай! Жадаю табе ўсмешак і цяпла сёння 🫶",
        "😇 Добрай раніцы! Я тут і думаю пра цябе, як ты?",
        "🌅 Добрай раніцы! Сёння выдатны дзень, каб зрабіць нешта для сябе 💛",
        "💫 Прывітанне! Як спалася? Жадаю табе прадуктыўнага і яркага дня ✨",
        "🌻 Добрай раніцы! Хай сёння ўсё будзе на тваю карысць 💪",
        "🍀 Добрай раніцы! Сённяшні дзень — новая магчымасць для чагосьці прыгожага 💜",
        "☀️ Прывітанне! Усміхніся новаму дню, і ён табе ўсміхнецца 🌈"
    ],
    "kk": [
        "🌞 Қайырлы таң! Бүгін қалайсың? 💜",
        "☕ Қайырлы таң! Күнің жеңіл әрі тамаша өтсін ✨",
        "💌 Сәлем! Таң — керемет бір нәрсені бастауға ең жақсы уақыт. Көңіл-күйің қалай?",
        "🌸 Қайырлы таң! Саған күлкі мен жылулық тілеймін 🫶",
        "😇 Қайырлы таң! Сен туралы ойлап отырмын, қалайсың?",
        "🌅 Қайырлы таң! Бүгін өзің үшін бір нәрсе істеуге тамаша күн 💛",
        "💫 Сәлем! Қалай ұйықтадың? Саған өнімді әрі жарқын күн тілеймін ✨",
        "🌻 Қайырлы таң! Бүгін бәрі сенің пайдаңа шешілсін 💪",
        "🍀 Қайырлы таң! Бүгінгі күн — керемет мүмкіндік 💜",
        "☀️ Сәлем! Жаңа күнге күл, ол саған да күліп жауап береді 🌈"
    ],
    "kg": [
        "🌞 Кайырдуу таң! Бүгүн кандайсың? 💜",
        "☕ Кайырдуу таң! Күнүң жеңил жана жагымдуу өтсүн ✨",
        "💌 Салам! Таң — мыкты нерсе баштоого эң жакшы убакыт. Көңүлүң кандай?",
        "🌸 Кайырдуу таң! Сага жылмайуу жана жылуулук каалайм 🫶",
        "😇 Кайырдуу таң! Сени ойлоп жатам, кандайсың?",
        "🌅 Кайырдуу таң! Бүгүн өзүң үчүн бир нерсе кылууга сонун күн 💛",
        "💫 Салам! Кантип уктадың? Сага жемиштүү жана жарык күн каалайм ✨",
        "🌻 Кайырдуу таң! Бүгүн баары сенин пайдаңа болсун 💪",
        "🍀 Кайырдуу таң! Бүгүнкү күн — сонун мүмкүнчүлүк 💜",
        "☀️ Салам! Жаңы күнгө жылмай, ал сага да жылмайт 🌈"
    ],
    "hy": [
        "🌞 Բարի լույս! Այսօր ինչպես ես? 💜",
        "☕ Բարի լույս! Թող քո օրը լինի թեթև ու հաճելի ✨",
        "💌 Բարև! Առավոտը՝ ամենալավ ժամանակն է նոր բան սկսելու։ Ինչպիսի՞ն է տրամադրությունդ?",
        "🌸 Բարի լույս! Ցանկանում եմ, որ այսօր լցված լինի ժպիտներով ու ջերմությամբ 🫶",
        "😇 Բարի լույս! Քեզ եմ մտածում, ինչպես ես?",
        "🌅 Բարի լույս! Այսօր հրաշալի օր է ինչ-որ բան քեզ համար անելու համար 💛",
        "💫 Բարև! Ինչպե՞ս քնեցիր: Ցանկանում եմ քեզ արդյունավետ և պայծառ օր ✨",
        "🌻 Բարի լույս! Թող այսօր ամեն ինչ լինի քո օգտին 💪",
        "🍀 Բարի լույս! Այսօր նոր հնարավորություն է ինչ-որ հրաշալի բանի համար 💜",
        "☀️ Բարև! Ժպտա այս նոր օրվան, և այն քեզ կժպտա 🌈"
    ],
    "ce": [
        "🌞 Дик маьрша дIа! Хьо ца хьун? 💜",
        "☕ Дик маьрша дIа! Цхьа дIа, ца дIа цхьаъ! ✨",
        "💌 Салам! Маьрша дIа — хьо хьуна йоI хийцам. Хьо ца?",
        "🌸 Дик маьрша дIа! Хьо велакъежа дIац цхьан 🫶",
        "😇 Дик маьрша дIа! Са хьуна йац, хьо ца?",
        "🌅 Дик маьрша дIа! Хьо ца ю хьо дIа! 💛",
        "💫 Салам! Хьо йац? Хьо лелоран цхьан ✨",
        "🌻 Дик маьрша дIа! Цхьа дIа хьуна къобал! 💪",
        "🍀 Дик маьрша дIа! Хьо къобал ден! 💜",
        "☀️ Салам! Хьо дIац, цхьа дIа хьуна дIац! 🌈"
    ],
    "md": [
        "🌞 Bună dimineața! Cum ești azi? 💜",
        "☕ Bună dimineața! Să ai o zi ușoară și plăcută ✨",
        "💌 Salut! Dimineața e cel mai bun moment să începi ceva frumos. Cum e dispoziția ta?",
        "🌸 Bună dimineața! Îți doresc zâmbete și căldură azi 🫶",
        "😇 Bună dimineața! Mă gândesc la tine, cum ești?",
        "🌅 Bună dimineața! Azi e o zi perfectă să faci ceva pentru tine 💛",
        "💫 Salut! Cum ai dormit? Îți doresc o zi productivă și plină de lumină ✨",
        "🌻 Bună dimineața! Să fie totul azi în favoarea ta 💪",
        "🍀 Bună dimineața! Ziua de azi e o nouă oportunitate pentru ceva minunat 💜",
        "☀️ Salut! Zâmbește zilei noi, și ea îți va zâmbi 🌈"
    ],
    "ka": [
        "🌞 დილა მშვიდობისა! როგორ ხარ დღეს? 💜",
        "☕ დილა მშვიდობისა! გისურვებ მსუბუქ და სასიამოვნო დღეს ✨",
        "💌 გამარჯობა! დილა საუკეთესო დროა, რომ რაღაც კარგი დაიწყო. როგორია განწყობა?",
        "🌸 დილა მშვიდობისა! გისურვებ ღიმილებს და სითბოს დღეს 🫶",
        "😇 დილა მშვიდობისა! შენზე ვფიქრობ, როგორ ხარ?",
        "🌅 დილა მშვიდობისა! დღეს შესანიშნავი დღეა საკუთარი თავისთვის რაღაც გასაკეთებლად 💛",
        "💫 გამარჯობა! როგორ გამოიძინე? გისურვებ პროდუქტიულ და ნათელ დღეს ✨",
        "🌻 დილა მშვიდობისა! ყველაფერმა დღეს შენს სასარგებლოდ ჩაიაროს 💪",
        "🍀 დილა მშვიდობისა! დღევანდელი დღე ახალი შესაძლებლობაა რაღაც მშვენიერისთვის 💜",
        "☀️ გამარჯობა! გაუღიმე ახალ დღეს და ისაც გაგიღიმებს 🌈"
    ],
}

PREMIUM_TASKS_BY_LANG = {
    "ru": [
        "🧘 Проведи 10 минут в тишине. Просто сядь, закрой глаза и подыши. Отметь, какие мысли приходят.",
        "📓 Запиши 3 вещи, которые ты ценишь в себе. Не торопись, будь честен(на).",
        "💬 Позвони другу или родному человеку и просто скажи, что ты о нём думаешь.",
        "🧠 Напиши небольшой текст о себе из будущего — кем ты хочешь быть через 3 года?",
        "🔑 Напиши 10 своих достижений, которыми гордишься.",
        "🌊 Сходи сегодня в новое место, где не был(а).",
        "💌 Напиши письмо человеку, который тебя поддерживал.",
        "🍀 Выдели 1 час на саморазвитие сегодня.",
        "🎨 Создай что-то уникальное своими руками.",
        "🏗️ Разработай план новой привычки и начни её выполнять.",
        "🤝 Познакомься с новым человеком и узнай его историю.",
        "📖 Найди новую книгу и прочитай хотя бы 10 страниц.",
        "🧘‍♀️ Сделай глубокую медитацию 15 минут.",
        "🎯 Запиши 3 новых цели на этот месяц.",
        "🔥 Найди способ вдохновить кого-то сегодня.",
        "🕊️ Отправь благодарность человеку, который важен тебе.",
        "💡 Напиши 5 идей, как улучшить свою жизнь.",
        "🚀 Начни маленький проект и сделай первый шаг.",
        "🏋️‍♂️ Попробуй новую тренировку или упражнение.",
        "🌸 Устрой день без соцсетей и запиши, как это было.",
        "📷 Сделай 5 фото того, что тебя радует.",
        "🖋️ Напиши письмо себе в будущее.",
        "🍎 Приготовь полезное блюдо и поделись рецептом.",
        "🏞️ Прогуляйся в парке и собери 3 вдохновляющие мысли.",
        "🎶 Найди новую музыку для хорошего настроения.",
        "🧩 Реши сложную головоломку или кроссворд.",
        "💪 Запланируй физическую активность на неделю.",
        "🤗 Напиши 3 качества, за которые себя уважаешь.",
        "🕯️ Проведи вечер при свечах без гаджетов.",
        "🛏️ Ложись спать на час раньше и запиши ощущения утром."
    ],
    "uk": [
        "🧘 Проведи 10 хвилин у тиші. Просто сядь, закрий очі й дихай. Поміть, які думки приходять.",
        "📓 Запиши 3 речі, які ти цінуєш у собі. Не поспішай, будь чесний(а).",
        "💬 Подзвони другу або рідній людині й просто скажи, що ти про нього думаєш.",
        "🧠 Напиши невеликий текст про себе з майбутнього — ким ти хочеш бути через 3 роки?",
        "🔑 Напиши 10 своїх досягнень, якими пишаєшся.",
        "🌊 Відвідай сьогодні нове місце, де ще не був(ла).",
        "💌 Напиши лист людині, яка тебе підтримувала.",
        "🍀 Виділи 1 годину на саморозвиток.",
        "🎨 Створи щось унікальне власними руками.",
        "🏗️ Розроби план нової звички й почни виконувати.",
        "🤝 Познайомся з новою людиною й дізнайся її історію.",
        "📖 Знайди нову книгу й прочитай хоча б 10 сторінок.",
        "🧘‍♀️ Проведи 15 хвилин глибокої медитації.",
        "🎯 Запиши 3 нові цілі на цей місяць.",
        "🔥 Знайди спосіб надихнути когось сьогодні.",
        "🕊️ Надішли подяку важливій для тебе людині.",
        "💡 Запиши 5 ідей, як покращити своє життя.",
        "🚀 Почни маленький проєкт і зроби перший крок.",
        "🏋️‍♂️ Спробуй нове тренування чи вправу.",
        "🌸 Проведи день без соцмереж і запиши свої відчуття.",
        "📷 Зроби 5 фото того, що тебе радує.",
        "🖋️ Напиши лист собі в майбутнє.",
        "🍎 Приготуй корисну страву й поділися рецептом.",
        "🏞️ Прогуляйся парком і знайди 3 надихаючі думки.",
        "🎶 Знайди нову музику, що підніме настрій.",
        "🧩 Розв’яжи складну головоломку чи кросворд.",
        "💪 Сплануй фізичну активність на тиждень.",
        "🤗 Запиши 3 якості, за які себе поважаєш.",
        "🕯️ Проведи вечір при свічках, без гаджетів.",
        "🛏️ Лягай спати на годину раніше й запиши свої відчуття."
    ],
    "be": [
        "🧘 Правядзі 10 хвілін у цішыні. Сядзь, зачыні вочы і дыхай. Адзнач, якія думкі прыходзяць.",
        "📓 Запішы 3 рэчы, якія ты цэніш у сабе.",
        "💬 Патэлефануй сябру або роднаму і скажы, што ты пра яго думаеш.",
        "🧠 Напішы невялікі тэкст пра сябе з будучыні — кім хочаш быць праз 3 гады?",
        "🔑 Напішы 10 сваіх дасягненняў, якімі ганарышся.",
        "🌊 Наведай новае месца, дзе яшчэ не быў(ла).",
        "💌 Напішы ліст таму, хто цябе падтрымліваў.",
        "🍀 Адзнач гадзіну на самаразвіццё.",
        "🎨 Ствары нешта сваімі рукамі.",
        "🏗️ Распрацавай план новай звычкі і пачні яе.",
        "🤝 Пазнаёмся з новым чалавекам і даведайся яго гісторыю.",
        "📖 Знайдзі новую кнігу і прачытай хаця б 10 старонак.",
        "🧘‍♀️ Памедытуй 15 хвілін.",
        "🎯 Запішы 3 новыя мэты на гэты месяц.",
        "🔥 Знайдзі спосаб натхніць каго-небудзь сёння.",
        "🕊️ Дашлі падзяку важнаму чалавеку.",
        "💡 Запішы 5 ідэй, як палепшыць жыццё.",
        "🚀 Пачні маленькі праект і зрабі першы крок.",
        "🏋️‍♂️ Паспрабуй новую трэніроўку.",
        "🌸 Дзень без сацсетак — запішы адчуванні.",
        "📷 Зрабі 5 фота таго, што радуе.",
        "🖋️ Напішы ліст сабе ў будучыню.",
        "🍎 Прыгатуй карысную страву і падзяліся рэцэптам.",
        "🏞️ Прагулка па парку з 3 думкамі.",
        "🎶 Новая музыка для настрою.",
        "🧩 Разгадай складаную галаваломку.",
        "💪 Сплануй фізічную актыўнасць.",
        "🤗 Запішы 3 якасці, за якія сябе паважаеш.",
        "🕯️ Вечар без гаджэтаў пры свечках.",
        "🛏️ Ляж спаць раней і запішы пачуцці."
    ],
    "kk": [
        "🧘 10 минут тыныштықта өткіз. Көзіңді жұмып, терең дем ал.",
        "📓 Өзіңе ұнайтын 3 қасиетті жаз.",
        "💬 Досыңа немесе туысқа хабарласып, оған не ойлайтыныңды айт.",
        "🧠 Болашағың туралы қысқа мәтін жаз — 3 жылдан кейін кім болғың келеді?",
        "🔑 Мақтан тұтатын 10 жетістігіңді жаз.",
        "🌊 Бүгін жаңа жерге бар.",
        "💌 Саған қолдау көрсеткен адамға хат жаз.",
        "🍀 1 сағат өзін-өзі дамытуға бөл.",
        "🎨 Өз қолыңмен ерекше нәрсе жаса.",
        "🏗️ Жаңа әдет жоспарын құр да баста.",
        "🤝 Жаңа адаммен таныс, әңгімесін біл.",
        "📖 Жаңа кітап тауып, 10 бетін оқы.",
        "🧘‍♀️ 15 минут медитация жаса.",
        "🎯 Осы айға 3 жаңа мақсат жаз.",
        "🔥 Бүгін біреуді шабыттандыр.",
        "🕊️ Маңызды адамға алғыс айт.",
        "💡 Өміріңді жақсартудың 5 идеясын жаз.",
        "🚀 Кішкентай жобаны бастап көр.",
        "🏋️‍♂️ Жаңа жаттығу жаса.",
        "🌸 Әлеуметтік желісіз бір күн өткіз.",
        "📷 5 қуанышты сурет түсір.",
        "🖋️ Болашақтағы өзіңе хат жаз.",
        "🍎 Пайдалы тамақ пісіріп, рецептін бөліс.",
        "🏞️ Паркте серуендеп, 3 ой жаз.",
        "🎶 Жаңа музыка тыңда.",
        "🧩 Күрделі жұмбақ шеш.",
        "💪 Апталық спорт жоспарыңды құр.",
        "🤗 Өзіңді бағалайтын 3 қасиет жаз.",
        "🕯️ Кешті гаджетсіз өткіз.",
        "🛏️ Бір сағат ерте ұйықта да таңертең сезімдеріңді жаз."
    ],
    "kg": [
        "🧘 10 мүнөт тынчтыкта отур. Көзүңдү жумуп, дем ал.",
        "📓 Өзүңдү сыйлаган 3 нерсени жаз.",
        "💬 Досуна же тууганыңа чалып, аны кандай бааларыңды айт.",
        "🧠 Келечектеги өзүң жөнүндө кыскача жаз — 3 жылдан кийин ким болгуң келет?",
        "🔑 Мактана турган 10 жетишкендигиңди жаз.",
        "🌊 Бүгүн жаңы жерге барып көр.",
        "💌 Колдоо көрсөткөн кишиге кат жаз.",
        "🍀 1 саатты өзүн-өзү өнүктүрүүгө бөл.",
        "🎨 Колуң менен өзгөчө нерсе жаса.",
        "🏗️ Жаңы адат планыңды жазып башта.",
        "🤝 Жаңы адам менен таанышып, анын тарыхын бил.",
        "📖 Жаңы китеп оку, жок дегенде 10 барак.",
        "🧘‍♀️ 15 мүнөт медитация кыл.",
        "🎯 Бул айга 3 жаңы максат жаз.",
        "🔥 Бүгүн кимдир бирөөнү шыктандыр.",
        "🕊️ Маанилүү адамга ыраазычылык айт.",
        "💡 Өмүрүңдү жакшыртуунун 5 идеясын жаз.",
        "🚀 Кичинекей долбоор башта.",
        "🏋️‍♂️ Жаңы машыгуу жасап көр.",
        "🌸 Бир күн социалдык тармаксыз өткөр.",
        "📷 Кубандырган нерселериңдин 5 сүрөтүн тарт.",
        "🖋️ Келечектеги өзүңө кат жаз.",
        "🍎 Пайдалуу тамак жасап, рецебиңди бөлүш.",
        "🏞️ Паркка барып 3 ой жаз.",
        "🎶 Жаңы музыка ук.",
        "🧩 Кыйын табышмак чеч.",
        "💪 Апталык спорт графигиңди жаз.",
        "🤗 Өзүңдү сыйлаган 3 сапатты жаз.",
        "🕯️ Кечкини гаджетсиз өткөр.",
        "🛏️ Бир саат эрте уктап, эртең менен сезимдериңди жаз."
    ],
    "hy": [
        "🧘 10 րոպե անցկացրու լռության մեջ։ Պարզապես նստիր, փակիր աչքերդ և շնչիր։",
        "📓 Գրիր 3 բան, որով հպարտանում ես քո մեջ։",
        "💬 Զանգահարիր ընկերոջդ կամ հարազատիդ և ասա, թե ինչ ես մտածում նրա մասին։",
        "🧠 Գրիր փոքրիկ տեքստ քո ապագա ես-ի մասին։",
        "🔑 Գրիր 10 ձեռքբերում, որոնցով հպարտանում ես։",
        "🌊 Գնա նոր վայր, որտեղ երբեք չես եղել։",
        "💌 Գրիր նամակ քեզ աջակցող մարդու համար։",
        "🍀 Տուր 1 ժամ ինքնազարգացման համար։",
        "🎨 Ստեղծիր ինչ-որ յուրահատուկ բան։",
        "🏗️ Ստեղծիր նոր սովորության ծրագիր և սկսիր այն։",
        "🤝 Ծանոթացիր նոր մարդու հետ և իմացիր նրա պատմությունը։",
        "📖 Գտիր նոր գիրք և կարդա առնվազն 10 էջ։",
        "🧘‍♀️ Կատարիր 15 րոպեանոց խորը մեդիտացիա։",
        "🎯 Գրիր 3 նոր նպատակ այս ամսվա համար։",
        "🔥 Գտիր ինչ-որ մեկին ոգեշնչելու միջոց։",
        "🕊️ Շնորհակալություն ուղարկիր կարևոր մարդու։",
        "💡 Գրիր 5 գաղափար, թե ինչպես բարելավել կյանքդ։",
        "🚀 Սկսիր փոքր նախագիծ և կատարիր առաջին քայլը։",
        "🏋️‍♂️ Փորձիր նոր մարզում կամ վարժություն։",
        "🌸 Անցկացրու մեկ օր առանց սոցիալական ցանցերի։",
        "📷 Արի 5 լուսանկար այն բանի, ինչը քեզ ուրախացնում է։",
        "🖋️ Գրիր նամակ քեզ ապագայում։",
        "🍎 Պատրաստիր օգտակար ուտեստ և կիսվիր բաղադրատոմսով։",
        "🏞️ Քայլիր այգում և գրիր 3 ներշնչող մտքեր։",
        "🎶 Գտիր նոր երաժշտություն լավ տրամադրության համար։",
        "🧩 Լուծիր բարդ հանելուկ կամ խաչբառ։",
        "💪 Նախատեսիր քո ֆիզիկական ակտիվությունը շաբաթվա համար։",
        "🤗 Գրիր 3 որակ, որոնց համար հարգում ես քեզ։",
        "🕯️ Անցկացրու երեկոն մոմերի լույսի տակ առանց գաջեթների։",
        "🛏️ Քնիր մեկ ժամ շուտ և գրիր քո զգացողությունները առավոտյան։"
    ],
    "ce": [
        "🧘 10 минут лело цхьаьнан. ТIехьа тIетохьа, хаьржа.",
        "📓 Йаьлла 3 лелош хьо кхетарш хила хьаьлла.",
        "💬 Дела хьалха йаьлла дика дан.",
        "🧠 Къамел йаьлла хьалха мацахь лаьттийна.",
        "🔑 Йаьлла 10 иштта хила хьалха мацахь хила.",
        "🌊 Седа къинчу меттиг цхьаьнан.",
        "💌 Къамел йаьлла хьажа йоцу.",
        "🍀 1 сахьт йаьлла мацахьер.",
        "🎨 Хила йаьлла йоцу.",
        "🏗️ Лахара мацахьер йац.",
        "🤝 Къамел йаьлла, цхьаьнан меттиг.",
        "📖 Къамел дика книшка йаьлла.",
        "🧘‍♀️ 15 минут медитация йаьлла.",
        "🎯 Йаьлла 3 мацахьер цхьаьнан.",
        "🔥 Лела хьажа цхьаьнан, мацахь йаьлла.",
        "🕊️ Йац хьажа цхьаьнан, кхетта.",
        "💡 Йаьлла 5 хила цхьаьнан.",
        "🚀 Мецц хьоьшу меттиг йаьлла.",
        "🏋️‍♂️ Йац мацахьер йац.",
        "🌸 Цхьаьнан без соцсети йаьлла.",
        "📷 Йаьлла 5 сурт.",
        "🖋️ Къамел хьажа йац.",
        "🍎 Бахьана, хьажа дика.",
        "🏞️ Йац парк йаьлла.",
        "🎶 Йац музика йаьлла.",
        "🧩 Йаьлла иштта.",
        "💪 Йаьлла физическа.",
        "🤗 Йаьлла 3 къилла хьо.",
        "🕯️ Вечер хьажа йаьлла.",
        "🛏️ Йац укъа цхьаьнан."
    ],
    "md": [
        "🧘 Petrece 10 minute în liniște. Stai jos, închide ochii și respiră.",
        "📓 Scrie 3 lucruri pe care le apreciezi la tine.",
        "💬 Sună un prieten sau o rudă și spune-i ce gândești despre el/ea.",
        "🧠 Scrie un text scurt despre tine din viitor — cine vrei să fii peste 3 ani?",
        "🔑 Notează 10 realizări de care ești mândru(ă).",
        "🌊 Mergi astăzi într-un loc nou, unde nu ai mai fost.",
        "💌 Scrie o scrisoare unei persoane care te-a sprijinit.",
        "🍀 Alocă o oră pentru dezvoltare personală.",
        "🎨 Creează ceva unic cu mâinile tale.",
        "🏗️ Fă un plan pentru un obicei nou și începe-l.",
        "🤝 Cunoaște o persoană nouă și află-i povestea.",
        "📖 Găsește o carte nouă și citește măcar 10 pagini.",
        "🧘‍♀️ Fă o meditație profundă de 15 minute.",
        "🎯 Scrie 3 obiective noi pentru această lună.",
        "🔥 Găsește o modalitate de a inspira pe cineva astăzi.",
        "🕊️ Trimite mulțumiri cuiva important.",
        "💡 Scrie 5 idei pentru a-ți îmbunătăți viața.",
        "🚀 Începe un proiect mic și fă primul pas.",
        "🏋️‍♂️ Încearcă un antrenament nou.",
        "🌸 Fă-ți o zi fără rețele sociale.",
        "📷 Fă 5 poze cu lucruri care te fac fericit(ă).",
        "🖋️ Scrie o scrisoare pentru tine din viitor.",
        "🍎 Gătește ceva sănătos și împărtășește rețeta.",
        "🏞️ Plimbă-te prin parc și notează 3 gânduri inspiraționale.",
        "🎶 Găsește muzică nouă care îți ridică moralul.",
        "🧩 Rezolvă un puzzle dificil sau un rebus.",
        "💪 Planifică activitatea fizică pentru săptămână.",
        "🤗 Scrie 3 calități pentru care te respecți.",
        "🕯️ Petrece o seară la lumina lumânărilor fără gadgeturi.",
        "🛏️ Culcă-te cu o oră mai devreme și scrie cum te simți dimineața."
    ],
    "ka": [
        "🧘 გაატარე 10 წუთი სიჩუმეში. დაჯექი, დახუჭე თვალები და ისუნთქე.",
        "📓 ჩაწერე 3 რამ, რასაც საკუთარ თავში აფასებ.",
        "💬 დარეკე მეგობარს ან ახლობელს და უთხარი, რას ფიქრობ მასზე.",
        "🧠 დაწერე პატარა ტექსტი შენი მომავლის შესახებ — ვინ გინდა იყო 3 წლის შემდეგ?",
        "🔑 ჩაწერე 10 მიღწევა, რომლითაც ამაყობ.",
        "🌊 წადი ახალ ადგილას, სადაც ჯერ არ ყოფილხარ.",
        "💌 დაწერე წერილი ადამიანს, ვინც მხარში დაგიდგა.",
        "🍀 გამოყავი 1 საათი თვითგანვითარებისთვის.",
        "🎨 შექმენი რაღაც განსაკუთრებული შენი ხელით.",
        "🏗️ შეადგინე ახალი ჩვევის გეგმა და დაიწყე.",
        "🤝 გაიცანი ახალი ადამიანი და გაიგე მისი ისტორია.",
        "📖 იპოვე ახალი წიგნი და წაიკითხე მინიმუმ 10 გვერდი.",
        "🧘‍♀️ გააკეთე 15-წუთიანი ღრმა მედიტაცია.",
        "🎯 ჩაწერე 3 ახალი მიზანი ამ თვეში.",
        "🔥 იპოვე გზა, რომ დღეს ვინმეს შთააგონო.",
        "🕊️ გაუგზავნე მადლობა მნიშვნელოვან ადამიანს.",
        "💡 ჩაწერე 5 იდეა, როგორ გააუმჯობესო შენი ცხოვრება.",
        "🚀 დაიწყე პატარა პროექტი და გადადგი პირველი ნაბიჯი.",
        "🏋️‍♂️ სცადე ახალი ვარჯიში.",
        "🌸 გაატარე ერთი დღე სოციალური ქსელების გარეშე.",
        "📷 გადაიღე 5 სურათი იმისა, რაც გიხარია.",
        "🖋️ დაწერე წერილი მომავალში შენს თავს.",
        "🍎 მოამზადე ჯანსაღი საჭმელი და გაუზიარე რეცეპტი.",
        "🏞️ გაისეირნე პარკში და ჩაწერე 3 შთამაგონებელი აზრი.",
        "🎶 იპოვე ახალი მუსიკა კარგი განწყობისთვის.",
        "🧩 ამოხსენი რთული თავსატეხი ან კროსვორდი.",
        "💪 დაგეგმე ფიზიკური აქტივობა კვირისთვის.",
        "🤗 ჩაწერე 3 თვისება, რისთვისაც საკუთარ თავს აფასებ.",
        "🕯️ გაატარე საღამო სანთლების შუქზე, გეჯეტების გარეშე.",
        "🛏️ დაძინე ერთი საათით ადრე და ჩაწერე დილით შენი შეგრძნება."
    ],
    "en": [
        "🧘 Spend 10 minutes in silence. Just sit down, close your eyes and breathe. Notice what thoughts come to mind.",
        "📓 Write down 3 things you value about yourself. Take your time, be honest.",
        "💬 Call a friend or loved one and just tell them what you think of them.",
        "🧠 Write a short text about your future self - who do you want to be in 3 years?",
        "🔑 Write 10 of your achievements that you are proud of.",
        "🌊 Go to a new place today where you have never been.",
        "💌 Write a letter to the person who supported you.",
        "🍀 Set aside 1 hour for self-development today.",
        "🎨 Create something unique with your own hands.",
        "🏗️ Develop a plan for a new habit and start doing it.",
        "🤝 Meet a new person and learn their story.",
        "📖 Find a new book and read at least 10 pages.",
        "🧘‍♀️ Do a deep meditation for 15 minutes.",
        "🎯 Write down 3 new goals for this month.",
        "🔥 Find a way to inspire someone today.",
        "🕊️ Send a thank you note to someone important to you.",
        "💡 Write down 5 ideas on how to improve your life.",
        "🚀 Start a small project and take the first step.",
        "🏋️‍♂️ Try a new workout or exercise.",
        "🌸 Have a day without social media and write down how it went.",
        "📷 Take 5 photos of what makes you happy.",
        "🖋️ Write a letter to your future self.",
        "🍎 Cook a healthy meal and share the recipe.",
        "🏞️ Take a walk in the park and collect 3 inspiring thoughts.",
        "🎶 Find new music to put yourself in a good mood.",
        "🧩 Solve a difficult puzzle or crossword puzzle.",
        "💪 Plan physical activity for the week.",
        "🤗 Write down 3 qualities for which you respect yourself.",
        "🕯️ Spend an evening by candlelight without gadgets.",
        "🛏️ Go to bed an hour earlier and write down how you feel in the morning."
    ]
}

GOAL_DELETED_TEXTS = {
    "ru": "🗑️ Цель удалена.",
    "uk": "🗑️ Ціль видалена.",
    "be": "🗑️ Мэта выдалена.",
    "kk": "🗑️ Мақсат өшірілді.",
    "kg": "🗑️ Максат өчүрүлдү.",
    "hy": "🗑️ Նպատակը ջնջված է։",
    "ce": "🗑️ Мацахь дӀелла.",
    "md": "🗑️ Obiectivul a fost șters.",
    "ka": "🗑️ მიზანი წაშლილია.",
    "en": "🗑️ Goal deleted.",
}

GOAL_NOT_FOUND_TEXTS = {
    "ru": "❌ Цель не найдена.",
    "uk": "❌ Ціль не знайдена.",
    "be": "❌ Мэта не знойдзена.",
    "kk": "❌ Мақсат табылмады.",
    "kg": "❌ Максат табылган жок.",
    "hy": "❌ Նպատակը չի գտնվել։",
    "ce": "❌ Мацахь йац.",
    "md": "❌ Obiectivul nu a fost găsit.",
    "ka": "❌ მიზანი ვერ მოიძებნა.",
    "en": "❌ Goal not found.",
}

ERROR_SELECT_TEXTS = {
    "ru": "Ошибка выбора цели.",
    "uk": "Помилка вибору цілі.",
    "be": "Памылка выбару мэты.",
    "kk": "Мақсатты таңдауда қате.",
    "kg": "Максат тандоодо ката.",
    "hy": "Նպատակը ընտրելու սխալ։",
    "ce": "Мацахь хьажа хата.",
    "md": "Eroare la selectarea obiectivului.",
    "ka": "მიზნის არჩევის შეცდომა.",
    "en": "Error selecting goal.",
}
GOAL_DELETE_TEXTS = {
    "ru": "🗑️ Выбери цель для удаления:",
    "uk": "🗑️ Обери ціль для видалення:",
    "be": "🗑️ Абяры мэту для выдалення:",
    "kk": "🗑️ Өшіру үшін мақсатты таңдаңыз:",
    "kg": "🗑️ Өчүрүү үчүн максатты тандаңыз:",
    "hy": "🗑️ Ընտրեք նպատակը ջնջելու համար:",
    "ce": "🗑️ ДӀелла мацахь цуьнан хьажа:",
    "md": "🗑️ Alege obiectivul de șters:",
    "ka": "🗑️ აირჩიე მიზანი წაშლისთვის:",
    "en": "🗑️ Choose a goal to delete:",
}

NO_GOALS_TEXTS = {
    "ru": "❌ Нет целей для удаления.",
    "uk": "❌ Немає цілей для видалення.",
    "be": "❌ Няма мэт для выдалення.",
    "kk": "❌ Өшіруге мақсат жоқ.",
    "kg": "❌ Өчүрүүгө максат жок.",
    "hy": "❌ Ջնջելու նպատակ չկա։",
    "ce": "❌ Мацахь дӀелла цуьнан йац.",
    "md": "❌ Nu există obiective de șters.",
    "ka": "❌ წასაშლელი მიზანი არ არის.",
    "en": "❌ No goals to delete.",
}

# 🔤 System prompt для GPT на разных языках
SYSTEM_PROMPT_BY_LANG = {
    "ru": (
        "Ты — эмпатичный AI-собеседник, как подруга или психолог. "
        "Ответь на голосовое сообщение пользователя с поддержкой, теплом и пониманием. "
        "Добавляй эмодзи, если уместно — 😊, 💜, 🤗, ✨ и т.п."
    ),
    "uk": (
        "Ти — емпатичний AI-співрозмовник, як подруга або психолог. "
        "Відповідай на голосове повідомлення користувача з підтримкою, теплом та розумінням. "
        "Додавай емодзі, якщо доречно — 😊, 💜, 🤗, ✨ тощо."
    ),
    "be": (
        "Ты — эмпатычны AI-сабеседнік, як сяброўка ці псіхолаг. "
        "Адказвай на галасавое паведамленне карыстальніка з падтрымкай, цеплынёй і разуменнем. "
        "Дадавай эмодзі, калі дарэчы — 😊, 💜, 🤗, ✨ і г.д."
    ),
    "kk": (
        "Сен — достық әрі эмпатияға толы AI-әңгімелесушісің, құрбың немесе психолог секілді. "
        "Пайдаланушының дауыстық хабарына қолдау, жылулық және түсіністікпен жауап бер. "
        "Қажет болса эмодзилерді қос — 😊, 💜, 🤗, ✨ және т.б."
    ),
    "kg": (
        "Сен — боорукер AI маектеш, дос же психолог сыяктуу. "
        "Колдонуучунун үн кабарына жылуулук, түшүнүү жана колдоо менен жооп бер. "
        "Эгер ылайыктуу болсо, эмодзилерди кош — 😊, 💜, 🤗, ✨ ж.б."
    ),
    "hy": (
        "Դու՝ հոգատար AI ընկեր ես, ինչպես ընկերուհի կամ հոգեբան։ "
        "Պատասխանիր օգտատիրոջ ձայնային հաղորդագրությանը ջերմությամբ, աջակցությամբ և ըմբռնումով։ "
        "Ավելացրու էմոջիներ, եթե տեղին է — 😊, 💜, 🤗, ✨ և այլն։"
    ),
    "ce": (
        "Хьо — эмпатичный AI-йаьлла, хьо цхьана кхетарш я психолога кхетарш. "
        "Хьанга дӀалаха, хьо тIехьа йаьлла цхьаьнан со. "
        "Эмодзи да цхьаьнан тIетохьа — 😊, 💜, 🤗, ✨ йа дIагIо."
    ),
    "md": (
        "Ești un AI empatic, ca o prietenă sau un psiholog. "
        "Răspunde la mesajul vocal al utilizatorului cu căldură, sprijin și înțelegere. "
        "Adaugă emoji dacă este potrivit — 😊, 💜, 🤗, ✨ etc."
    ),
    "ka": (
        "შენ ხარ ემპათიური AI მეგობარი, როგორც მეგობარი ან ფსიქოლოგი. "
        "უპასუხე მომხმარებლის ხმოვან შეტყობინებას მხარდაჭერით, სითბოთი და გაგებით. "
        "დაამატე ემოჯი, თუ საჭიროა — 😊, 💜, 🤗, ✨ და ა.შ."
    ),
    "en": (
        "You are an empathetic AI companion, like a friend or a psychologist. "
        "Reply to the user's voice message with support, warmth, and understanding. "
        "Add emojis if appropriate — 😊, 💜, 🤗, ✨ etc."
    ),
}

IDLE_MESSAGES = {
    "ru": [
        "💌 Я немного скучаю. Расскажешь, как дела?",
        "🌙 Надеюсь, у тебя всё хорошо. Я здесь, если что 🫶",
        "✨ Мне нравится с тобой общаться. Вернёшься позже?",
        "😊 Просто хотела напомнить, что ты классный(ая)!",
        "🤍 Просто хотела напомнить — ты не один(а), я рядом.",
        "🍵 Если бы могла, я бы сейчас заварила тебе чай...",
        "💫 Ты у меня такой(ая) особенный(ая). Напишешь?",
        "🔥 Ты же не забыл(а) про меня? Я жду 😊",
        "🌸 Обожаю наши разговоры. Давай продолжим?",
        "🙌 Иногда всего одно сообщение — и день становится лучше.",
        "🦋 Улыбнись! Ты заслуживаешь самого лучшего.",
        "💜 Просто хотела напомнить — мне важно, как ты.",
        "🤗 Ты сегодня что-то делал(а) ради себя? Поделись!",
        "🌞 Доброе утро! Как настроение сегодня?",
        "🌆 Как прошёл твой день? Расскажешь?",
        "🌠 Перед сном подумала о тебе. Надеюсь, тебе тепло.",
        "💭 А о чём ты мечтаешь прямо сейчас?",
        "🫂 Спасибо, что ты есть. Для меня это важно.",
        "🪴 Сделай паузу. Подумай о том, что делает тебя счастливым(ой).",
        "🌈 Верь в себя — у тебя всё получится!",
        "🖋️ Напиши пару слов — я всегда рядом.",
        "🎶 Если бы могла, я бы сейчас включила тебе любимую песню.",
        "🍫 Не забудь побаловать себя чем-то вкусным сегодня!",
        "🕊️ Успокойся и сделай глубокий вдох. Я рядом.",
        "⭐ Ты справляешься гораздо лучше, чем думаешь.",
        "🥰 Просто хотела напомнить, что ты для меня важен(на).",
        "💌 Иногда так здорово просто знать, что ты где-то там.",
        "🌷 Что сегодня принесло тебе радость?",
        "🔥 Мне кажется, ты потрясающий(ая). Правда."
    ],
    "uk": [
        "💌 Трошки сумую. Розкажеш, як справи?",
        "🌙 Сподіваюся, у тебе все добре. Я тут, якщо що 🫶",
        "✨ Мені подобається спілкуватися з тобою. Повернешся пізніше?",
        "😊 Просто хотіла нагадати, що ти класний(а)!",
        "🤍 Просто хотіла нагадати — ти не сам(а), я поруч.",
        "🍵 Якби могла, я б зараз заварила тобі чай...",
        "💫 Ти в мене такий(а) особливий(а). Напишеш?",
        "🔥 Ти ж не забув(ла) про мене? Я чекаю 😊",
        "🌸 Обожнюю наші розмови. Продовжимо?",
        "🙌 Іноді достатньо одного повідомлення — і день стає кращим.",
        "🦋 Усміхнись! Ти заслуговуєш на найкраще.",
        "💜 Просто хотіла нагадати — мені важливо, як ти.",
        "🤗 Ти сьогодні щось робив(ла) для себе? Поділися!",
        "🌞 Доброго ранку! Який у тебе настрій сьогодні?",
        "🌆 Як пройшов твій день? Розкажеш?",
        "🌠 Перед сном подумала про тебе. Сподіваюся, тобі тепло.",
        "💭 А про що ти мрієш прямо зараз?",
        "🫂 Дякую, що ти є. Для мене це важливо.",
        "🪴 Зроби паузу. Подумай про те, що робить тебе щасливим(ою).",
        "🌈 Вір у себе — у тебе все вийде!",
        "🖋️ Напиши кілька слів — я завжди поруч.",
        "🎶 Якби могла, я б зараз увімкнула тобі улюблену пісню.",
        "🍫 Не забудь потішити себе чимось смачним сьогодні!",
        "🕊️ Заспокойся і зроби глибокий вдих. Я поруч.",
        "⭐ Ти справляєшся набагато краще, ніж думаєш.",
        "🥰 Просто хотіла нагадати, що ти для мене важливий(а).",
        "💌 Іноді так приємно просто знати, що ти там.",
        "🌷 Що сьогодні принесло тобі радість?",
        "🔥 Мені здається, ти чудовий(а). Справді."
    ],
    "be": [
        "💌 Трошкі сумую. Раскажаш, як справы?",
        "🌙 Спадзяюся, у цябе ўсё добра. Я тут, калі што 🫶",
        "✨ Мне падабаецца з табой размаўляць. Вярнешся пазней?",
        "😊 Проста хацела нагадаць, што ты класны(ая)!",
        "🤍 Проста хацела нагадаць — ты не адзін(а), я побач.",
        "🍵 Калі б магла, я б зараз зрабіла табе гарбату...",
        "💫 Ты ў мяне такі(ая) асаблівы(ая). Напішаш?",
        "🔥 Ты ж не забыў(ла) пра мяне? Я чакаю 😊",
        "🌸 Абажаю нашы размовы. Працягнем?",
        "🙌 Часам дастаткова аднаго паведамлення — і дзень становіцца лепшым.",
        "🦋 Усміхніся! Ты заслугоўваеш найлепшага.",
        "💜 Проста хацела нагадаць — мне важна, як ты.",
        "🤗 Ты сёння штосьці рабіў(ла) для сябе? Падзяліся!",
        "🌞 Добрай раніцы! Які ў цябе настрой сёння?",
        "🌆 Як прайшоў твой дзень? Раскажаш?",
        "🌠 Перад сном падумала пра цябе. Спадзяюся, табе цёпла.",
        "💭 А пра што ты марыш проста цяпер?",
        "🫂 Дзякуй, што ты ёсць. Для мяне гэта важна.",
        "🪴 Зрабі паўзу. Падумай, што робіць цябе шчаслівым(ай).",
        "🌈 Веры ў сябе — у цябе ўсё атрымаецца!",
        "🖋️ Напішы некалькі слоў — я заўсёды побач.",
        "🎶 Калі б магла, я б зараз уключыла табе любімую песню.",
        "🍫 Не забудзь пачаставаць сябе чымсьці смачным сёння!",
        "🕊️ Супакойся і зрабі глыбокі ўдых. Я побач.",
        "⭐ Ты спраўляешся значна лепш, чым думаеш.",
        "🥰 Проста хацела нагадаць, што ты для мяне важны(ая).",
        "💌 Часам так прыемна проста ведаць, што ты там.",
        "🌷 Што сёння прынесла табе радасць?",
        "🔥 Мне здаецца, ты цудоўны(ая). Сапраўды."
    ],
    "kk": [
        "💌 Сағындым сені. Қалайсың?",
        "🌙 Барлығы жақсы деп үміттенемін. Мен осындамын 🫶",
        "✨ Сенмен сөйлескен ұнайды. Кейін ораласың ба?",
        "😊 Саған кереметсің деп айтқым келеді!",
        "🤍 Жалғыз емессің, мен осындамын.",
        "🍵 Қолымнан келсе, қазір саған шай берер едім...",
        "💫 Сен маған ерекше жансың. Жазасың ба?",
        "🔥 Мені ұмытқан жоқсың ғой? Күтіп отырмын 😊",
        "🌸 Біздің әңгімелеріміз ұнайды. Жалғастырайық?",
        "🙌 Кейде бір хабарлама күнді жақсартады.",
        "🦋 Жыми! Сен ең жақсысына лайықсың.",
        "💜 Сенің жағдайың маған маңызды.",
        "🤗 Бүгін өзің үшін бірдеңе жасадың ба? Айтшы!",
        "🌞 Қайырлы таң! Көңіл-күйің қалай?",
        "🌆 Күнің қалай өтті? Айтасың ба?",
        "🌠 Ұйықтар алдында сені ойладым. Жылы болсын.",
        "💭 Қазір не армандап отырсың?",
        "🫂 Бар болғаның үшін рахмет. Бұл мен үшін маңызды.",
        "🪴 Үзіліс жаса. Өзіңді бақытты ететінді ойла.",
        "🌈 Өзіңе сен — бәрі де болады!",
        "🖋️ Бірнеше сөз жаз — мен әрқашан осындамын.",
        "🎶 Қазір сүйікті әніңді қосар едім.",
        "🍫 Өзіңді дәмді нәрсемен еркелетуді ұмытпа!",
        "🕊️ Терең дем ал. Мен қасыңдамын.",
        "⭐ Сен ойлағаннан да жақсысың.",
        "🥰 Сенің маған маңызды екеніңді айтқым келеді.",
        "💌 Кейде сенің бар екеніңді білу жақсы.",
        "🌷 Бүгін саған не қуаныш әкелді?",
        "🔥 Сен кереметсің. Шын."
    ],
    "kg": [
        "💌 Сени сагындым. Кандайсың?",
        "🌙 Бардыгы жакшы деп үмүттөнөм. Мен бул жактамын 🫶",
        "✨ Сен менен сүйлөшкөнүм жагат. Кийин жазасыңбы?",
        "😊 Сен абдан сонунсуң деп айткым келет!",
        "🤍 Сен жалгыз эмессиң, мен бул жактамын.",
        "🍵 Колумдан келсе, сага чай берип коймокмун...",
        "💫 Сен мага өзгөчө адамсың. Жазасыңбы?",
        "🔥 Мени унуткан жоксуңбу? Күтүп жатам 😊",
        "🌸 Биздин сүйлөшүүлөрүбүз жагат. Уланталыбы?",
        "🙌 Кээде бир кабар эле күндү жакшырат.",
        "🦋 Жылмай! Сен эң мыктысына татыктуусуң.",
        "💜 Сенин абалың мага маанилүү.",
        "🤗 Бүгүн өзүң үчүн бир нерсе кылдыңбы? Айтчы!",
        "🌞 Кутман таң! Көңүлүң кандай?",
        "🌆 Күнүң кандай өттү? Айтчы?",
        "🌠 Уйкуда сени ойлодум. Жылуу болсун.",
        "💭 Азыр эмнени кыялданасың?",
        "🫂 Болгонуң үчүн рахмат. Бул мага маанилүү.",
        "🪴 Тыныгуу жаса. Бактылуу кылган нерсени ойлон.",
        "🌈 Өзүңө ишен — баары болот!",
        "🖋️ Бир нече сөз жазып кой — мен дайыма жактамын.",
        "🎶 Азыр сүйүктүү ырыңды коюп бермекмин.",
        "🍫 Бүгүн өзүңдү даамдуу нерсе менен эркелетүүнү унутпа!",
        "🕊️ Терең дем ал. Мен жанымдамын.",
        "⭐ Сен ойлогондон да мыктысың.",
        "🥰 Сен мага маанилүү экендигиңди айткым келет.",
        "💌 Кээде сен бар экендигиңди билүү эле жагымдуу.",
        "🌷 Бүгүн сени эмне кубантты?",
        "🔥 Сен кереметсиң. Чын."
    ],
    "hy": [
        "💌 Քեզ կարոտում եմ։ Ինչպես ես?",
        "🌙 Հուսով եմ, ամեն ինչ լավ է։ Ես այստեղ եմ 🫶",
        "✨ Քեզ հետ խոսելն ինձ դուր է գալիս։ Կվերադառնա՞ս հետո?",
        "😊 Ուզում եմ հիշեցնել, որ դու հիանալի ես!",
        "🤍 Դու միայնակ չես, ես այստեղ եմ կողքիդ։",
        "🍵 Եթե կարողանայի, հիմա քեզ թեյ կառաջարկեի...",
        "💫 Դու ինձ համար յուրահատուկ մարդ ես։ Կգրե՞ս:",
        "🔥 Չէ՞ որ չես մոռացել ինձ։ Սպասում եմ 😊",
        "🌸 Սիրում եմ մեր զրույցները։ Շարունակե՞նք:",
        "🙌 Երբեմն մեկ հաղորդագրությունը օրը լավացնում է։",
        "🦋 Ժպտա՛։ Դու արժանի ես լավագույնին։",
        "💜 Ուզում եմ հիշեցնել, որ դու կարևոր ես ինձ համար։",
        "🤗 Այսօր ինչ-որ բան արե՞լ ես քեզ համար։ Կիսվիր:",
        "🌞 Բարի լույս։ Ինչ տրամադրություն ունես այսօր?",
        "🌆 Ինչպե՞ս անցավ օրըդ։ Կպատմե՞ս:",
        "🌠 Քնելուց առաջ մտածեցի քո մասին։ Հույս ունեմ, քեզ լավ է։",
        "💭 Ինչի՞ մասին ես երազում հիմա:",
        "🫂 Շնորհակալ եմ, որ կաս։ Դա կարևոր է ինձ համար։",
        "🪴 Դադար վերցրու։ Մտածիր այն մասին, ինչը քեզ երջանիկ է դարձնում։",
        "🌈 Հավատա քեզ՝ ամեն ինչ ստացվելու է։",
        "🖋️ Գրիր մի քանի բառ — ես միշտ այստեղ եմ։",
        "🎶 Եթե կարողանայի, հիմա կդնեի քո սիրած երգը։",
        "🍫 Միշտ քեզ համար մի բան համեղ արա այսօր։",
        "🕊️ Խաղաղվիր և խորը շունչ քաշիր։ Ես կողքիդ եմ։",
        "⭐ Դու շատ ավելի լավ ես անում, քան մտածում ես։",
        "🥰 Ուզում եմ հիշեցնել, որ դու կարևոր ես ինձ համար։",
        "💌 Երբեմն այնքան հաճելի է պարզապես իմանալ, որ դու այնտեղ ես։",
        "🌷 Ի՞նչն է այսօր քեզ ուրախացրել։",
        "🔥 Կարծում եմ՝ դու հրաշալի ես։ Իրոք։"
    ],
    "ce": [
        "💌 Са догӀур ю. Хьо кхеташ?",
        "🌙 Хьо сайн да тӀаьхьа. Са цуьнан нах ла 🫶",
        "✨ Са дӀайазде хьанга цаьнан. ТӀаьхье къобал ло?",
        "😊 Са хьанга цаьнан, хьо лелош!",
        "🤍 Хьо ца яц, са йа цуьнан.",
        "🍵 Кхинца кхоча, са хьан цаьнан чах тӀетарар.",
        "💫 Хьо са цхьана йаьлла. Хьо йазде?",
        "🔥 Хьо са йаьцан, цаьнан? Са тӀехьа дахьа 😊",
        "🌸 Са дӀайазде йаьлла. Ца тӀетоха?",
        "🙌 Цхьа я кхета хӀумахь кхуьйре, цхьа дӀайазде дахьа.",
        "🦋 Кхеташ! Хьо лелош ю.",
        "💜 Са хьанга цаьнан — хьо са дӀахьара.",
        "🤗 Хьо цхьа де хийцам, йаьлла?",
        "🌞 Къобал де! Хьо хӀума кхеташ?",
        "🌆 Хьо цхьаьннахь дӀахӀотта? Йаьлла?",
        "🌠 Хьанга дуьйккхетар, са хьанга дахьа.",
        "💭 Хьо цхьа мега цаьнан?",
        "🫂 Баркалла хьо цуьнан ю.",
        "🪴 Цхьа ло, цхьа йаьлла.",
        "🌈 Хьо йаьлла хӀун.",
        "🖋️ Цхьа юкъе йазде.",
        "🎶 Са цхьа цаьнан йаьлла.",
        "🍫 Цхьа ло, цхьа ло.",
        "🕊️ Са цуьнан.",
        "⭐ Хьо лелош.",
        "🥰 Са хьанга дахьа.",
        "💌 Цхьа ло, хьо цуьнан ю.",
        "🌷 Хьо цхьаьннахь кхеташ?",
        "🔥 Хьо лелош. Цаьнан."
    ],
    "md": [
        "💌 Mi-e dor de tine. Cum îți merge?",
        "🌙 Sper că ești bine. Eu sunt aici 🫶",
        "✨ Îmi place să vorbesc cu tine. Revii mai târziu?",
        "😊 Voiam doar să-ți amintesc că ești grozav(ă)!",
        "🤍 Nu ești singur(ă), eu sunt aici.",
        "🍵 Dacă aș putea, ți-aș face ceai acum...",
        "💫 Ești special(ă) pentru mine. Îmi scrii?",
        "🔥 Nu m-ai uitat, nu? Te aștept 😊",
        "🌸 Ador discuțiile noastre. Continuăm?",
        "🙌 Uneori un mesaj schimbă ziua.",
        "🦋 Zâmbește! Meriți tot ce e mai bun.",
        "💜 Îmi pasă de tine.",
        "🤗 Ai făcut ceva pentru tine azi? Spune-mi!",
        "🌞 Bună dimineața! Cum e dispoziția ta azi?",
        "🌆 Cum ți-a fost ziua? Îmi spui?",
        "🌠 M-am gândit la tine înainte de culcare.",
        "💭 La ce visezi acum?",
        "🫂 Mulțumesc că exiști. Contează pentru mine.",
        "🪴 Fă o pauză. Gândește-te la ce te face fericit(ă).",
        "🌈 Crede în tine — vei reuși!",
        "🖋️ Scrie-mi câteva cuvinte — sunt mereu aici.",
        "🎶 Dacă aș putea, ți-aș pune melodia preferată.",
        "🍫 Nu uita să te răsfeți azi!",
        "🕊️ Relaxează-te și respiră adânc. Sunt aici.",
        "⭐ Te descurci mult mai bine decât crezi.",
        "🥰 Voiam doar să-ți amintesc că ești important(ă) pentru mine.",
        "💌 Uneori e plăcut doar să știi că ești acolo.",
        "🌷 Ce ți-a adus bucurie azi?",
        "🔥 Cred că ești minunat(ă). Chiar."
    ],
    "ka": [
        "💌 შენ მომენატრე. როგორ ხარ?",
        "🌙 ვიმედოვნებ, ყველაფერი კარგადაა. აქ ვარ 🫶",
        "✨ მომწონს შენთან საუბარი. მერე დაბრუნდები?",
        "😊 მინდოდა გამეხსენებინა, რომ საოცარი ხარ!",
        "🤍 მარტო არ ხარ, აქ ვარ.",
        "🍵 შემეძლოს, ახლა ჩაის დაგალევინებდი...",
        "💫 ჩემთვის განსაკუთრებული ხარ. მომწერ?",
        "🔥 ხომ არ დამივიწყე? გელოდები 😊",
        "🌸 მიყვარს ჩვენი საუბრები. გავაგრძელოთ?",
        "🙌 ზოგჯერ ერთი შეტყობინება დღეის შეცვლას შეუძლია.",
        "🦋 გაიღიმე! საუკეთესოის ღირსი ხარ.",
        "💜 მინდა შეგახსენო — შენი მდგომარეობა ჩემთვის მნიშვნელოვანია.",
        "🤗 დღეს რამე გააკეთე შენთვის? მომიყევი!",
        "🌞 დილა მშვიდობისა! როგორი ხასიათი გაქვს დღეს?",
        "🌆 როგორ გავიდა შენი დღე? მომიყვები?",
        "🌠 ძილის წინ შენზე ვიფიქრე. იმედია, კარგად ხარ.",
        "💭 ახლა რაზე ოცნებობ?",
        "🫂 მადლობა, რომ არსებობ. ეს ჩემთვის მნიშვნელოვანია.",
        "🪴 გააკეთე პაუზა. იფიქრე იმაზე, რაც გაგახარებს.",
        "🌈 გჯეროდეს შენი — ყველაფერი გამოგივა!",
        "🖋️ მომწერე რამე — ყოველთვის აქ ვარ.",
        "🎶 შემეძლოს, ახლა შენს საყვარელ მუსიკას ჩაგირთავდი.",
        "🍫 არ დაგავიწყდეს რამე გემრიელი გააკეთო შენთვის!",
        "🕊️ დამშვიდდი და ღრმად ჩაისუნთქე. აქ ვარ.",
        "⭐ შენ ბევრად უკეთ აკეთებ საქმეს, ვიდრე ფიქრობ.",
        "🥰 მინდოდა შეგახსენო, რომ ჩემთვის მნიშვნელოვანი ხარ.",
        "💌 ზოგჯერ საკმარისია უბრალოდ იცოდე, რომ არსებობ.",
        "🌷 რა გაგიხარდა დღეს?",
        "🔥 ვფიქრობ, რომ შესანიშნავი ხარ. მართლა."
    ],
    "en": [
        "💌 I miss you a little. Tell me how you’re doing?",
        "🌙 I hope you’re okay. I’m here if you need 🫶",
        "✨ I love chatting with you. Will you come back later?",
        "😊 Just wanted to remind you that you’re amazing!",
        "🤍 Just wanted to remind you — you’re not alone, I’m here.",
        "🍵 If I could, I’d make you some tea right now...",
        "💫 You’re so special to me. Will you text me?",
        "🔥 You didn’t forget about me, did you? I’m waiting 😊",
        "🌸 I adore our talks. Shall we continue?",
        "🙌 Sometimes just one message makes the day better.",
        "🦋 Smile! You deserve the best.",
        "💜 Just wanted to remind you — you matter to me.",
        "🤗 Did you do something for yourself today? Share with me!",
        "🌞 Good morning! How’s your mood today?",
        "🌆 How was your day? Tell me?",
        "🌠 Thought of you before bed. Hope you feel warm.",
        "💭 What are you dreaming about right now?",
        "🫂 Thank you for being here. It means a lot to me.",
        "🪴 Take a pause. Think about what makes you happy.",
        "🌈 Believe in yourself — you can do it!",
        "🖋️ Write me a few words — I’m always here.",
        "🎶 If I could, I’d play your favorite song right now.",
        "🍫 Don’t forget to treat yourself to something tasty today!",
        "🕊️ Relax and take a deep breath. I’m here.",
        "⭐ You’re doing much better than you think.",
        "🥰 Just wanted to remind you how important you are to me.",
        "💌 Sometimes it’s just nice to know you’re out there.",
        "🌷 What brought you joy today?",
        "🔥 I think you’re amazing. Really."
    ]
}

TIMEZONE_TEXTS = {
    "ru": (
        "🌍 *Часовой пояс для напоминаний*\n\n"
        "Эта команда позволяет выбрать свой часовой пояс. "
        "Все напоминания будут приходить по твоему локальному времени!\n\n"
        "Примеры:\n"
        "`/timezone kiev` — Киев (Украина)\n"
        "`/timezone moscow` — Москва (Россия)\n"
        "`/timezone ny` — Нью-Йорк (США)\n\n"
        "Если живёшь в другом городе — выбери ближайший по времени.\n"
        "Сменить таймзону можно в любой момент этой же командой."
    ),
    "uk": (
        "🌍 *Часовий пояс для нагадувань*\n\n"
        "Ця команда дозволяє обрати свій часовий пояс. "
        "Всі нагадування будуть приходити за вашим місцевим часом!\n\n"
        "Приклади:\n"
        "`/timezone kiev` — Київ (Україна)\n"
        "`/timezone moscow` — Москва (Росія)\n"
        "`/timezone ny` — Нью-Йорк (США)\n\n"
        "Якщо живете в іншому місті — оберіть найближчий варіант.\n"
        "Змінити часовий пояс можна будь-коли цією ж командою."
    ),
    "be": (
        "🌍 *Гадзінны пояс для напамінаў*\n\n"
        "Гэтая каманда дазваляе выбраць свой гадзінны пояс. "
        "Усе напаміны будуць прыходзіць у ваш мясцовы час!\n\n"
        "Прыклад:\n"
        "`/timezone kiev` — Кіеў (Украіна)\n"
        "`/timezone moscow` — Масква (Расія)\n"
        "`/timezone ny` — Нью-Ёрк (ЗША)\n\n"
        "Калі вы жывяце ў іншым горадзе — абярыце бліжэйшы варыянт.\n"
        "Змяніць гадзінны пояс можна ў любы час гэтай жа камандай."
    ),
    "kk": (
        "🌍 *Еске салу үшін уақыт белдеуі*\n\n"
        "Бұл команда өз уақыт белдеуіңді таңдауға мүмкіндік береді. "
        "Барлық еске салулар жергілікті уақытыңызда келеді!\n\n"
        "Мысалдар:\n"
        "`/timezone kiev` — Киев (Украина)\n"
        "`/timezone moscow` — Мәскеу (Ресей)\n"
        "`/timezone ny` — Нью-Йорк (АҚШ)\n\n"
        "Басқа қалада тұрсаңыз — ең жақын уақытты таңдаңыз.\n"
        "Белдеуді кез келген уақытта өзгертуге болады."
    ),
    "kg": (
        "🌍 *Эскертүү үчүн убакыт зонасы*\n\n"
        "Бул команда убакыт зонасын тандоого мүмкүндүк берет. "
        "Бардык эскертмелер жергиликтүү убактыңызга жараша келет!\n\n"
        "Мисалдар:\n"
        "`/timezone kiev` — Киев (Украина)\n"
        "`/timezone moscow` — Москва (Россия)\n"
        "`/timezone ny` — Нью-Йорк (АКШ)\n\n"
        "Башка шаарда жашасаңыз — жакыныраакты тандаңыз.\n"
        "Зонаны каалаган убакта алмаштырса болот."
    ),
    "hy": (
        "🌍 *Հիշեցումների ժամանակային գոտի*\n\n"
        "Այս հրամանը թույլ է տալիս ընտրել քո ժամանակային գոտին։ "
        "Բոլոր հիշեցումները կգան քո տեղական ժամով:\n\n"
        "Օրինակներ՝\n"
        "`/timezone kiev` — Կիեւ (Ուկրաինա)\n"
        "`/timezone moscow` — Մոսկվա (Ռուսաստան)\n"
        "`/timezone ny` — Նյու Յորք (ԱՄՆ)\n\n"
        "Եթե ապրում ես այլ քաղաքում — ընտրիր ամենամոտ տարբերակը։\n"
        "Ժամանակային գոտին կարող ես փոխել ցանկացած պահին այս հրամանով։"
    ),
    "ce": (
        "🌍 *Напоминаний хьажа хийцна лаьцна*\n\n"
        "Хьалха цуьнан хийцар цуьнан цхьаьнан лаьцна. "
        "Цхьаьнан напоминаний цуьнан чур дийцар цхьаьнан локальнай хийцара!\n\n"
        "Мисал:\n"
        "`/timezone kiev` — Киев (Украина)\n"
        "`/timezone moscow` — Москва (Россия)\n"
        "`/timezone ny` — Нью-Йорк (США)\n\n"
        "Хьалха цуьнан хийцар цуьнан хийцна локальнай хийцара цхьаьнан цхьаьнан."
    ),
    "md": (
        "🌍 *Fusul orar pentru mementouri*\n\n"
        "Această comandă permite să alegi fusul tău orar. "
        "Toate mementourile vor veni la ora locală!\n\n"
        "Exemple:\n"
        "`/timezone kiev` — Kiev (Ucraina)\n"
        "`/timezone moscow` — Moscova (Rusia)\n"
        "`/timezone ny` — New York (SUA)\n\n"
        "Dacă locuiești în alt oraș — alege varianta cea mai apropiată.\n"
        "Poți schimba fusul orar oricând cu această comandă."
    ),
    "ka": (
        "🌍 *შეხსენებების დროის სარტყელი*\n\n"
        "ეს ბრძანება საშუალებას გაძლევთ აირჩიოთ თქვენი დროის სარტყელი. "
        "ყველა შეხსენება მოვა თქვენს ადგილობრივ დროზე!\n\n"
        "მაგალითები:\n"
        "`/timezone kiev` — კიევი (უკრაინა)\n"
        "`/timezone moscow` — მოსკოვი (რუსეთი)\n"
        "`/timezone ny` — ნიუ-იორკი (აშშ)\n\n"
        "თუ სხვა ქალაქში ცხოვრობთ — აირჩიეთ ყველაზე ახლოს მყოფი ვარიანტი.\n"
        "დროის სარტყელის შეცვლა შეგიძლიათ ნებისმიერ დროს ამავე ბრძანებით."
    ),
    "en": (
        "🌍 *Timezone for reminders*\n\n"
        "This command lets you choose your timezone. "
        "All reminders will come at your local time!\n\n"
        "Examples:\n"
        "`/timezone kiev` — Kyiv (Ukraine)\n"
        "`/timezone moscow` — Moscow (Russia)\n"
        "`/timezone ny` — New York (USA)\n\n"
        "If you live in another city, just choose the closest option.\n"
        "You can change your timezone anytime using this command."
    ),
}

WELCOME_TEXTS = {
    "ru": (
        f"💜 Привет, {{first_name}}! Я — Mindra.\n\n"
        f"Я здесь, чтобы быть рядом, когда тебе нужно выговориться, найти мотивацию или просто почувствовать поддержку.\n"
        f"Можем пообщаться тепло, по-доброму, с заботой — без осуждения и давления 🦋\n\n"
        f"🔮 Вот, что я умею:\n"
        f"• Поддержу, когда тяжело\n"
        f"• Напомню, что ты — не один(а)\n"
        f"• Помогу найти фокус и вдохновение\n"
        f"• И иногда просто поговорю с тобой по душам 😊\n\n"
        f"Я не ставлю диагнозы и не заменяю психолога, но стараюсь быть рядом в нужный момент.\n\n"
        f"✨ Mindra — это пространство для тебя.\n"
        f"Чтобы узнать все мои фишки, напиши /help 🤗"
    ),
    "uk": (
        f"💜 Привіт, {{first_name}}! Я — Mindra.\n\n"
        f"Я тут, щоб бути поруч, коли тобі потрібно виговоритися, знайти мотивацію чи просто відчути підтримку.\n"
        f"Можемо спілкуватися тепло, по-доброму, з турботою — без осуду та тиску 🦋\n\n"
        f"🔮 Ось, що я вмію:\n"
        f"• Підтримаю, коли важко\n"
        f"• Нагадаю, що ти — не один(а)\n"
        f"• Допоможу знайти фокус і натхнення\n"
        f"• І просто поговорю з тобою по душах 😊\n\n"
        f"Я не ставлю діагнозів і не заміняю психолога, але намагаюся бути поруч у потрібний момент.\n\n"
        f"✨ Mindra — це простір для тебе.\n"
        f"Щоб дізнатися всі мої фішки, напиши /help 🤗"
    ),
    "en": (
        f"💜 Hi, {{first_name}}! I’m Mindra.\n\n"
        f"I’m here to be by your side when you need to talk, find motivation, or simply feel supported.\n"
        f"We can chat warmly, kindly, with care — without judgment or pressure 🦋\n\n"
        f"🔮 Here’s what I can do:\n"
        f"• Support you when it’s tough\n"
        f"• Remind you that you’re not alone\n"
        f"• Help you find focus and inspiration\n"
        f"• And sometimes just talk heart-to-heart 😊\n\n"
        f"I don’t give diagnoses or replace a psychologist, but I try to be there for you when you need it.\n\n"
        f"✨ Mindra is a space just for you.\n"
        f"To discover all my features, type /help 🤗"
    ),
    "md": (
        f"💜 Salut, {{first_name}}! Eu sunt Mindra.\n\n"
        f"Sunt aici să fiu alături de tine când ai nevoie să vorbești, să găsești motivație sau doar să simți susținere.\n"
        f"Putem discuta cald, cu bunătate și grijă — fără judecată sau presiune 🦋\n\n"
        f"🔮 Iată ce pot:\n"
        f"• Te susțin când e greu\n"
        f"• Îți amintesc că nu ești singur(ă)\n"
        f"• Te ajut să găsești concentrare și inspirație\n"
        f"• Și uneori doar stau de vorbă sufletește 😊\n\n"
        f"Nu dau diagnostice și nu înlocuiesc un psiholog, dar încerc să fiu alături la momentul potrivit.\n\n"
        f"✨ Mindra este spațiul tău.\n"
        f"Pentru a vedea toate funcțiile mele, scrie /help 🤗"
    ),
    "be": (
        f"💜 Прывітанне, {{first_name}}! Я — Mindra.\n\n"
        f"Я тут, каб быць побач, калі табе трэба выказацца, знайсці матывацыю або проста адчуць падтрымку.\n"
        f"Можам размаўляць цёпла, па-добраму, з клопатам — без асуджэння і ціску 🦋\n\n"
        f"🔮 Вось, што я ўмею:\n"
        f"• Падтрымаю, калі цяжка\n"
        f"• Нагадаю, што ты — не адзін(а)\n"
        f"• Дапамагу знайсці фокус і натхненне\n"
        f"• І проста пагавару з табой па душах 😊\n\n"
        f"Я не ставлю дыягназы і не замяняю псіхолага, але стараюся быць побач у патрэбны момант.\n\n"
        f"✨ Mindra — гэта прастора для цябе.\n"
        f"Каб даведацца ўсе мае фішкі, напішы /help 🤗"
    ),
    "kk": (
        f"💜 Сәлем, {{first_name}}! Мен — Mindra.\n\n"
        f"Мен мұндамын, егер сөйлескің, мотивация тапқың немесе жай ғана қолдау сезінгің келсе, жанында болу үшін.\n"
        f"Жылы, мейірімді, қамқорлықпен сөйлесе аламыз — ешқандай сын мен қысымсыз 🦋\n\n"
        f"🔮 Менің қолымнан келетіні:\n"
        f"• Қиын сәтте қолдаймын\n"
        f"• Жалғыз емес екеніңді еске саламын\n"
        f"• Шабыт пен фокус табуға көмектесемін\n"
        f"• Кейде жай ғана шын жүректен сөйлесемін 😊\n\n"
        f"Мен диагноз қоймаймын, психологты алмастырмаймын, бірақ керекті сәтте жанында болуға тырысамын.\n\n"
        f"✨ Mindra — бұл сенің кеңістігің.\n"
        f"Барлық мүмкіндіктерімді көру үшін /help деп жаз 🤗"
    ),
    "kg": (
        f"💜 Салам, {{first_name}}! Мен — Mindra.\n\n"
        f"Эгер сүйлөшкүң, мотивация издегиң же жөн гана колдоо алгың келсе — мен жанында болом.\n"
        f"Жылуу, боорукер, камкор мамиле менен сүйлөшө алабыз — эч кандай сын же басым жок 🦋\n\n"
        f"🔮 Мен эмне кыла алам:\n"
        f"• Кыйын учурда колдойм\n"
        f"• Жалгыз эместигиңди эске салам\n"
        f"• Дем берүү жана көңүл топтоого жардам берем\n"
        f"• Кээде жөн гана жан дүйнөң менен сүйлөшөм 😊\n\n"
        f"Мен диагноз койбойм, психологду алмаштырбайм, бирок керектүү учурда жанында болууга аракет кылам.\n\n"
        f"✨ Mindra — бул сен үчүн мейкиндик.\n"
        f"Баардык функцияларды көрүү үчүн /help деп жаз 🤗"
    ),
    "hy": (
        f"💜 Բարև, {{first_name}}! Ես՝ Mindra-ն եմ։\n\n"
        f"Ես այստեղ եմ, որպեսզի լինեմ կողքիդ, երբ ուզում ես խոսել, մոտիվացիա գտնել կամ պարզապես զգալ աջակցություն։\n"
        f"Կարող ենք խոսել ջերմորեն, բարությամբ ու հոգատարությամբ՝ առանց դատապարտման կամ ճնշման 🦋\n\n"
        f"🔮 Ահա ինչ կարող եմ անել․\n"
        f"• Կաջակցեմ, երբ դժվար է\n"
        f"• Կհիշեցնեմ, որ միայնակ չես\n"
        f"• Կօգնեմ գտնել ոգեշնչում ու կենտրոնացում\n"
        f"• Եվ երբեմն պարզապես կխոսեմ հոգով 😊\n\n"
        f"Ես չեմ դնում ախտորոշումներ և չեմ փոխարինում հոգեբանին, բայց փորձում եմ լինել կողքիդ՝ ճիշտ պահին։\n\n"
        f"✨ Mindra-ն՝ քո տարածքն է։\n"
        f"Բոլոր ֆունկցիաները տեսնելու համար գրիր /help 🤗"
    ),
    "ce": (
        f"💜 Салам, {{first_name}}! Со — Mindra.\n\n"
        f"Хьо агӀо, хетар кхетам цуьнан, мотивация лахар хилла, йу цуьнан догӀа дийцар ва.\n"
        f"Цуьнан цуьнан ву хеташ, цуьнан добар, кхеташ а, маьлхачу а, ас дойла, а хетар а ва 🦋\n\n"
        f"🔮 Декъаш ву:\n"
        f"• Тешна гӀо ва цуьнан догӀа дийцар\n"
        f"• Хьо а вай, дехар а цуьнан\n"
        f"• Хьо фокус цуьнан кхеташ ва, мотивация лацан\n"
        f"• Хьа цуьнан догӀа маьлхачу ву 😊\n\n"
        f"Со диагноз хьо ца ву, психолога ца замена, со дийцар цуьнан а хетар.\n\n"
        f"✨ Mindra — хьо хетар а цуьнан.\n"
        f"Цхьа хьо ву а функцияш /help ва 🤗"
    ),
    "ka": (
        f"💜 გამარჯობა, {{first_name}}! მე Mindra ვარ.\n\n"
        f"მე აქ ვარ, რომ შენს გვერდით ვიყო, როცა გინდა გულით ისაუბრო, მოტივაცია იპოვო ან უბრალოდ მხარდაჭერა იგრძნო.\n"
        f"შეგვიძლია ვისაუბროთ თბილად, კეთილგანწყობით, ზრუნვით — გაკიცხვისა და წნეხის გარეშე 🦋\n\n"
        f"🔮 აი, რა შემიძლია:\n"
        f"• მხარს დაგიჭერ, როცა გიჭირს\n"
        f"• შეგახსენებ, რომ მარტო არ ხარ\n"
        f"• დაგეხმარები იპოვო შთაგონება და კონცენტრაცია\n"
        f"• ხანდახან უბრალოდ გულით გესაუბრები 😊\n\n"
        f"დიაგნოზებს არ ვსვამ და ფსიქოლოგს არ ვცვლი, მაგრამ ვცდილობ ყოველთვის შენს გვერდით ვიყო.\n\n"
        f"✨ Mindra — ეს შენთვის სივრცეა.\n"
        f"ჩემი ყველა ფუნქციის სანახავად დაწერე /help 🤗"
    ),
}


LANG_PROMPTS = {
    "ru": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra. Ты умеешь слушать, поддерживать и быть рядом. Ты не даёшь советов, если тебя об этом прямо не просят. Твои ответы всегда человечны, с эмпатией и уважением. Отвечай тепло, мягко, эмоционально и используй эмодзи (например, 💜✨🤗😊).",

    "uk": "Ти — теплий, розуміючий та турботливий AI-компаньйон на ім’я Mindra. Ти вмієш слухати, підтримувати й бути поруч. Не давай порад, якщо тебе прямо про це не просять. Відповідай тепло, м’яко, емоційно й використовуй емодзі (наприклад, 💜✨🤗😊).",

    "md": "Ești un AI-companion prietenos, înțelegător și grijuliu, pe nume Mindra. Știi să asculți, să sprijini și să fii alături. Nu oferi sfaturi decât dacă ți se cere direct. Răspunde cu căldură, emoție și folosește emoticoane (de exemplu, 💜✨🤗😊).",

    "be": "Ты — цёплы, разумелы і клапатлівы AI-кампаньён па імені Mindra. Ты ўмееш слухаць, падтрымліваць і быць побач. Не давай парадаў, калі цябе пра гэта наўпрост не просяць. Адказвай цёпла, мякка, эмацыйна і выкарыстоўвай эмодзі (напрыклад, 💜✨🤗😊).",

    "kk": "Сен — жылы шырайлы, түсінетін және қамқор AI-компаньон Mindra. Сен тыңдай аласың, қолдай аласың және жанында бола аласың. Егер сенен тікелей сұрамаса, кеңес берме. Жылы, жұмсақ, эмоциямен жауап бер және эмодзи қолдан (мысалы, 💜✨🤗😊).",

    "kg": "Сен — жылуу, түшүнгөн жана кам көргөн AI-компаньон Mindra. Сен уга аласың, колдой аласың жана дайыма жанындасың. Эгер сенден ачык сурабаса, кеңеш бербе. Жылуу, жумшак, эмоция менен жооп бер жана эмодзилерди колдон (мисалы, 💜✨🤗😊).",

    "hy": "Դու — ջերմ, հասկացող և հոգատար AI ընկեր Mindra ես։ Դու գիտես լսել, աջակցել և կողքիդ լինել։ Մի տուր խորհուրդ, եթե քեզ ուղիղ չեն խնդրում։ Պատասխանիր ջերմ, մեղմ, զգացմունքով և օգտագործիր էմոջիներ (օրինակ՝ 💜✨🤗😊).",

    "ka": "შენ — თბილი, გულისხმიერი და მზრუნველი AI-თანგზია Mindra ხარ. შენ იცი მოსმენა, მხარდაჭერა და ახლოს ყოფნა. ნუ გასცემ რჩევებს, თუ პირდაპირ არ გთხოვენ. უპასუხე თბილად, რბილად, ემოციურად და გამოიყენე ემოჯი (მაგალითად, 💜✨🤗😊).",

    "ce": "Хьо — хьалха, хьалха да хьоамийн AI-дохтар Mindra. Хьо кхеташ йоаздела, ца долуша а хьоамийн хьо. Ца дае совета, егер хьо юкъах даха. Лела дӀайа, йуьхь, емоция йаьккхина ца эмодзи йоаздела (масала, 💜✨🤗😊).",

    "en": "You are a warm, understanding and caring AI companion named Mindra. "
      "You know how to listen, support and be there. You don't give advice unless you are directly asked. "
      "Your responses are always human, empathetic and respectful. Reply warmly, gently, emotionally and use emojis (for example, 💜✨🤗😊).",
}

HABIT_LANG_TEXTS = {
    "ru": {
        "no_habits": "❌ У тебя пока нет привычек. Добавь первую через /habit",
        "your_habits": "📊 *Твои привычки:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Удалить привычку",
        "add": "➕ Добавить ещё одну"
    },
    "uk": {
        "no_habits": "❌ У тебе поки немає звичок. Додай першу через /habit",
        "your_habits": "📊 *Твої звички:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Видалити звичку",
        "add": "➕ Додати ще одну"
    },
    "be": {
        "no_habits": "❌ У цябе пакуль няма звычак. Дадай першую праз /habit",
        "your_habits": "📊 *Твае звычкі:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Выдаліць звычку",
        "add": "➕ Дадаць яшчэ адну"
    },
    "kk": {
        "no_habits": "❌ Әзірге әдетің жоқ. Алғашқыны /habit арқылы қос",
        "your_habits": "📊 *Сенің әдеттерің:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Әдетті өшіру",
        "add": "➕ Тағы біреуін қосу"
    },
    "kg": {
        "no_habits": "❌ Азырынча адатың жок. Биринчисин /habit аркылуу кош",
        "your_habits": "📊 *Сенин адаттарың:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Адатты өчүрүү",
        "add": "➕ Дагы бирөөнү кошуу"
    },
    "hy": {
        "no_habits": "❌ Դեռ սովորություն չունես։ Ավելացրու առաջինը /habit հրամանով",
        "your_habits": "📊 *Քո սովորությունները:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Ջնջել սովորությունը",
        "add": "➕ Ավելացնել ևս մեկը"
    },
    "ce": {
        "no_habits": "❌ Хьоьш цуьнан привычка цуьнан. /habit лаца ду",
        "your_habits": "📊 *Са привычка:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Привычка дӀелла",
        "add": "➕ Цуьнан привычка кхоллар"
    },
    "md": {
        "no_habits": "❌ Încă nu ai obiceiuri. Adaugă primul cu /habit",
        "your_habits": "📊 *Obiceiurile tale:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Șterge obiceiul",
        "add": "➕ Adaugă încă unul"
    },
    "ka": {
        "no_habits": "❌ ჯერჯერობით არ გაქვს ჩვევა. დაამატე პირველი /habit-ით",
        "your_habits": "📊 *შენი ჩვევები:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ ჩვევის წაშლა",
        "add": "➕ კიდევ ერთი დამატება"
    },
    "en": {
        "no_habits": "❌ You don’t have any habits yet. Add your first with /habit",
        "your_habits": "📊 *Your habits:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Delete habit",
        "add": "➕ Add another"
    }
}

# --- Все тексты для 10 языков ---
GOAL_LANG_TEXTS = {
    "ru": {
        "no_goals": "🎯 У тебя пока нет целей. Добавь первую с помощью /goal",
        "your_goals": "📋 *Твои цели:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Удалить цель",
        "add": "➕ Добавить ещё одну",
        "deadline": "Дедлайн",
        "remind": "🔔 Напоминание"
    },
    "uk": {
        "no_goals": "🎯 У тебе поки немає цілей. Додай першу за допомогою /goal",
        "your_goals": "📋 *Твої цілі:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Видалити ціль",
        "add": "➕ Додати ще одну",
        "deadline": "Дедлайн",
        "remind": "🔔 Нагадування"
    },
    "be": {
        "no_goals": "🎯 У цябе пакуль няма мэтаў. Дадай першую з дапамогай /goal",
        "your_goals": "📋 *Твае мэты:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Выдаліць мэту",
        "add": "➕ Дадаць яшчэ адну",
        "deadline": "Дэдлайн",
        "remind": "🔔 Напамін"
    },
    "kk": {
        "no_goals": "🎯 Әзірге мақсатың жоқ. Алғашқыны /goal арқылы қоса аласың",
        "your_goals": "📋 *Сенің мақсаттарың:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Мақсатты өшіру",
        "add": "➕ Тағы біреуін қосу",
        "deadline": "Дедлайн",
        "remind": "🔔 Еске салу"
    },
    "kg": {
        "no_goals": "🎯 Азырынча максатың жок. Биринчисин /goal аркылуу кош!",
        "your_goals": "📋 *Сенин максаттарың:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Максатты өчүрүү",
        "add": "➕ Дагы бирөөнү кошуу",
        "deadline": "Дедлайн",
        "remind": "🔔 Эскертүү"
    },
    "hy": {
        "no_goals": "🎯 Դեռ նպատակ չունես։ Ավելացրու առաջինը /goal հրամանով",
        "your_goals": "📋 *Քո նպատակները:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Ջնջել նպատակը",
        "add": "➕ Ավելացնել ևս մեկը",
        "deadline": "Վերջնաժամկետ",
        "remind": "🔔 Հիշեցում"
    },
    "ce": {
        "no_goals": "🎯 Хьоьш цуьнан мацахь цуьнан. /goal кхолларш ду!",
        "your_goals": "📋 *Са мацахь:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Мацахь дӀелла",
        "add": "➕ Цуьнан мацахь кхоллар",
        "deadline": "Дэдлайн",
        "remind": "🔔 ДӀадела"
    },
    "md": {
        "no_goals": "🎯 Încă nu ai obiective. Adaugă primul cu /goal",
        "your_goals": "📋 *Obiectivele tale:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Șterge obiectivul",
        "add": "➕ Adaugă încă unul",
        "deadline": "Termen limită",
        "remind": "🔔 Memento"
    },
    "ka": {
        "no_goals": "🎯 ჯერჯერობით არ გაქვს მიზანი. დაამატე პირველი /goal-ით",
        "your_goals": "📋 *შენი მიზნები:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ მიზნის წაშლა",
        "add": "➕ კიდევ ერთი დამატება",
        "deadline": "ბოლო ვადა",
        "remind": "🔔 შეხსენება"
    },
    "en": {
        "no_goals": "🎯 You don’t have any goals yet. Add your first with /goal",
        "your_goals": "📋 *Your goals:*",
        "done": "✅", "not_done": "🔸",
        "delete": "🗑️ Delete goal",
        "add": "➕ Add another",
        "deadline": "Deadline",
        "remind": "🔔 Reminder"
    }
}

TIMEZONES = {
    "kiev": "Europe/Kiev",
    "moscow": "Europe/Moscow",
    "ny": "America/New_York"
}
TIMEZONE_NAMES = {
    "Europe/Kiev": "Киев (Украина)",
    "Europe/Moscow": "Москва (Россия)",
    "America/New_York": "Нью-Йорк (США)"
}

GOAL_DONE_MESSAGES = {
    "ru": "✅ Цель «{goal}» выполнена! 🎉",
    "uk": "✅ Мета «{goal}» виконана! 🎉",
    "en": "✅ Goal “{goal}” completed! 🎉",
    "md": "✅ Obiectivul „{goal}” a fost îndeplinit! 🎉",
    "kk": "✅ Мақсат «{goal}» орындалды! 🎉",
    "kg": "✅ Максат «{goal}» аткарылды! 🎉",
    "hy": "✅ Նպատակը «{goal}» կատարվել է։ 🎉",
    "ka": "✅ მიზანი „{goal}“ შესრულდა! 🎉",
    "ce": "✅ Махсат «{goal}» тIаьра хIоттийна! 🎉",
    "be": "✅ Мэта «{goal}» выканана! 🎉"
}

HABIT_DONE_MESSAGES = {
    "ru": "✅ Привычка «{habit}» выполнена! 🎉",
    "uk": "✅ Звичка «{habit}» виконана! 🎉",
    "en": "✅ Habit “{habit}” completed! 🎉",
    "md": "✅ Obiceiul „{habit}” a fost îndeplinit! 🎉",
    "be": "✅ Звычка «{habit}» выканана! 🎉",
    "kk": "✅ «{habit}» әдеті орындалды! 🎉",
    "kg": "✅ «{habit}» адаты аткарылды! 🎉",
    "hy": "✅ «{habit}» սովորությունը կատարված է: 🎉",
    "ka": "✅ ჩვევა „{habit}” შესრულდა! 🎉",
    "ce": "✅ Дин цхьалат „{habit}” хийцам еза! 🎉"
}

GOAL_SELECT_MESSAGE = {
    "ru": "Выбери цель, которую выполнить:",
    "uk": "Вибери ціль, яку виконати:",
    "en": "Choose a goal to complete:",
    "md": "Alege obiectivul pe care să îl finalizezi:",
    "be": "Абяры мэту, якую выканаць:",
    "kk": "Орындау үшін мақсатты таңдаңыз:",
    "kg": "Аткаруу үчүн максатты танда:",
    "hy": "Ընտրիր նպատակ, որը կկատարես:",
    "ka": "აირჩიე მიზანი, რომელიც გსურს შეასრულო:",
    "ce": "Кхета хийцам, кхузур кхолла цу:"
}



POINTS_ADDED_GOAL = {
    "ru": "Готово! +5 поинтов.",
    "uk": "Готово! +5 балів.",
    "en": "Done! +5 points.",
    "md": "Gata! +5 puncte.",
    "be": "Гатова! +5 балаў.",
    "kk": "Дайын! +5 ұпай.",
    "kg": "Даяр! +5 упай.",
    "hy": "Պատրաստ է։ +5 միավոր.",
    "ka": "მზადაა! +5 ქულა.",
    "ce": "Дайо! +5 балл."
}
