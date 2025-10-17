import os
import copy
import json
import logging
import re
import threading
from pathlib import Path

from config import DATA_DIR, client

EDITOR_CHANNEL_ID = -1003012903331

MESSAGE_SETTINGS_TEXTS = {
    "ru": {
        "title": "💌 Сообщения",
        "body_on": "Авто-сообщения включены. Я буду присылать напоминания, задания и подборки даже без запроса.",
        "body_off": "Авто-сообщения выключены. Я отвечаю только когда ты пишешь.",
        "enable": "🔔 Включить авто-сообщения",
        "disable": "🔕 Выключить авто-сообщения",
    },
    "uk": {
        "title": "💌 Повідомлення",
        "body_on": "Авто-повідомлення увімкнено. Я надсилатиму нагадування, поради та новини навіть без запиту.",
        "body_off": "Авто-повідомлення вимкнено. Відповідатиму лише коли ти пишеш.",
        "enable": "🔔 Увімкнути авто-повідомлення",
        "disable": "🔕 Вимкнути авто-повідомлення",
    },
    "en": {
        "title": "💌 Messages",
        "body_on": "Auto-messages are ON. I will send check-ins, tips, and updates on my own.",
        "body_off": "Auto-messages are OFF. I reply only when you write.",
        "enable": "🔔 Turn on auto-messages",
        "disable": "🔕 Turn off auto-messages",
    },
    "es": {
        "title": "💌 Mensajes",
        "body_on": "Los mensajes automáticos están activados. Te enviaré recordatorios, ideas y novedades sin que me escribas.",
        "body_off": "Los mensajes automáticos están desactivados. Solo responderé cuando me escribas.",
        "enable": "🔔 Activar mensajes automáticos",
        "disable": "🔕 Desactivar mensajes automáticos",
    },
    "de": {
        "title": "💌 Nachrichten",
        "body_on": "Automatische Nachrichten sind aktiviert. Ich sende dir Check-ins, Tipps und Updates von selbst.",
        "body_off": "Automatische Nachrichten sind deaktiviert. Ich antworte nur, wenn du schreibst.",
        "enable": "🔔 Automatische Nachrichten einschalten",
        "disable": "🔕 Automatische Nachrichten ausschalten",
    },
    "pl": {
        "title": "💌 Wiadomości",
        "body_on": "Wiadomości automatyczne są włączone. Będę wysyłać przypomnienia, wskazówki i nowości samodzielnie.",
        "body_off": "Wiadomości automatyczne są wyłączone. Odpowiem tylko, gdy do mnie napiszesz.",
        "enable": "🔔 Włącz wiadomości automatyczne",
        "disable": "🔕 Wyłącz wiadomości automatyczne",
    },
    "fr": {
        "title": "💌 Messages",
        "body_on": "Les messages automatiques sont activés. Je t’enverrai spontanément des check-ins, astuces et nouvelles.",
        "body_off": "Les messages automatiques sont désactivés. Je répondrai seulement quand tu écris.",
        "enable": "🔔 Activer les messages automatiques",
        "disable": "🔕 Désactiver les messages automatiques",
    },
    "md": {
        "title": "💌 Mesaje",
        "body_on": "Mesajele automate sunt activate. Îți trimit memento-uri, idei și noutăți din proprie inițiativă.",
        "body_off": "Mesajele automate sunt dezactivate. Răspund doar când îmi scrii.",
        "enable": "🔔 Activează mesajele automate",
        "disable": "🔕 Dezactivează mesajele automate",
    },
    "be": {
        "title": "💌 Паведамленні",
        "body_on": "Аўтапаведамленні ўключаны. Буду дасылаць напаміны, парады і навіны самастойна.",
        "body_off": "Аўтапаведамленні выключаны. Адкажу толькі калі ты напішаш.",
        "enable": "🔔 Уключыць аўтапаведамленні",
        "disable": "🔕 Выключыць аўтапаведамленні",
    },
    "kk": {
        "title": "💌 Хабарламалар",
        "body_on": "Авто-хабарламалар қосулы. Еске салғыштар мен кеңестерді өзім жіберіп тұрамын.",
        "body_off": "Авто-хабарламалар өшірулі. Сен жазғанда ғана жауап беремін.",
        "enable": "🔔 Авто-хабарламаларды қосу",
        "disable": "🔕 Авто-хабарламаларды өшіру",
    },
    "kg": {
        "title": "💌 Билдирүүлөр",
        "body_on": "Авто-билдирүүлөр күйгөн. Эскертүү, кеңеш жана жаңылыктарды өзүм жиберем.",
        "body_off": "Авто-билдирүүлөр өчүк. Сен жазганда гана жооп берем.",
        "enable": "🔔 Авто-билдирүүлөрдү күйгүзүү",
        "disable": "🔕 Авто-билдирүүлөрдү өчүрүү",
    },
    "hy": {
        "title": "💌 Հաղորդագրություններ",
        "body_on": "Ինքնաշխատ հաղորդագրությունները միացված են։ Կուղարկեմ հիշեցումներ, խորհուրդներ և նորություններ առանց խնդրանքի։",
        "body_off": "Ինքնաշխատ հաղորդագրությունները անջատված են։ Կպատասխանեմ միայն երբ գրես։",
        "enable": "🔔 Միացնել ինքնաշխատ հաղորդագրությունները",
        "disable": "🔕 Անջատել ինքնաշխատ հաղորդագրությունները",
    },
    "ka": {
        "title": "💌 შეტყობინებები",
        "body_on": "ავტო-შეტყობინებები ჩართულია. შეგახსენებ, გაგიზიარებ რჩევებს და სიახლეებს თვითონ.",
        "body_off": "ავტო-შეტყობინებები გამორთულია. ვუპასუხებ მხოლოდ როცა მომწერ.",
        "enable": "🔔 ჩართე ავტო-შეტყობინებები",
        "disable": "🔕 გამორთე ავტო-შეტყობინებები",
    },
    "ce": {
        "title": "💌 Хьабарш",
        "body_on": "Авто хьабарш хьалха. Со дош дӀасалаш, мотивацин деш ву кха йу.",
        "body_off": "Авто хьабарш кхолла. Со санна дӀаяздар чу хьо йазде хуьлу.",
        "enable": "🔔 Авто хьабарш хьалха",
        "disable": "🔕 Авто хьабарш кхолла",
    },
}

MOTIVATION_CHANNELS = {
    "ru": "https://t.me/mindra_motivation_ru",
    "en": "https://t.me/mindra_motivation_en",
    "uk": "https://t.me/mindra_motivation_ua",
    "ua": "https://t.me/mindra_motivation_ua",
    "ka": "https://t.me/mindra_motivation_ka",
    "kk": "https://t.me/mindra_motivation_kz",
    "kz": "https://t.me/mindra_motivation_kz",
    "md": "https://t.me/mindra_motivation_ro",
    "ro": "https://t.me/mindra_motivation_ro",
    "hy": "https://t.me/mindra_motivation_hy",
    "es": "https://t.me/mindra_motivation_es",
    "de": "https://t.me/mindra_motivation_de",
    "fr": "https://t.me/mindra_motivation_fr",
    "pl": "https://t.me/mindra_motivation_pl",
}

CHANNEL_INVITE_TEXT = {
    "en": "Join your daily motivation channel: {link}",
    "ru": "Присоединяйся к ежедневному каналу мотивации: {link}",
    "uk": "Долучайся до щоденного каналу мотивації: {link}",
    "ka": "შემოუერთდი ყოველდღიურ მოტივაციის არხს: {link}",
    "kk": "Күнделікті мотивация арнасына қосылыңыз: {link}",
    "md": "Alătură-te canalului zilnic de motivație: {link}",
    "hy": "Միացիր մեր առօրյա մոտիվացիայի ալիքին՝ {link}",
    "es": "Únete a nuestro canal diario de motivación: {link}",
    "de": "Tritt unserem täglichen Motivationskanal bei: {link}",
    "fr": "Rejoins notre canal quotidien de motivation : {link}",
    "pl": "Dołącz do codziennego kanału motywacji: {link}",
}

CHANNEL_BUTTON_TEXT = {
    "en": "Open channel",
    "ru": "Открыть канал",
    "uk": "Відкрити канал",
    "ka": "არხის გახსნა",
    "kk": "Арнаны ашу",
    "md": "Deschide canalul",
    "hy": "Բացել ալիքը",
    "es": "Abrir canal",
    "de": "Kanal öffnen",
    "fr": "Ouvrir le canal",
    "pl": "Otwórz kanał",
}

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
        "es": {"you_said": "📝 Dijiste:", "error": "❌ Error al reconocer la voz, inténtalo más tarde."},
    "de": {"you_said": "📝 Du hast gesagt:", "error": "❌ Fehler bei der Spracherkennung, bitte versuche es später erneut."},
    "pl": {"you_said": "📝 Powiedziałeś/łaś:", "error": "❌ Błąd rozpoznawania mowy, spróbuj później."},
    "fr": {"you_said": "📝 Tu as dit :", "error": "❌ Erreur de reconnaissance vocale, réessaie plus tard."},
}

PCH_DONE_TOAST_TEXTS = {
    "ru": "🔥 Красота! Челлендж закрыт. Хочешь выбрать следующий?",
    "uk": "🔥 Круто! Виклик завершено. Хочеш обрати наступний?",
    "en": "🔥 Awesome! Challenge completed. Want to pick the next one?",
    "md": "🔥 Bravo! Provocarea a fost finalizată. Vrei să alegi următoarea?",
    "be": "🔥 Цудоўна! Чэлендж завершаны. Хочаш абраць наступны?",
    "kk": "🔥 Керемет! Челлендж аяқталды. Келесісін таңдағың келе ме?",
    "kg": "🔥 Сонун! Челлендж бүткөн. Кийинкисин тандагың келеби?",
    "hy": "🔥 Հրաշալի է։ Չելենջը ավարտվեց։ Ցանկանու՞մ ես ընտրել հաջորդը։",
    "ka": "🔥 სუპერ! ჩელენჯი დასრულდა. გინდა შემდეგი აირჩიო?",
    "ce": "🔥 Ловзар! Челлендж тӀеьхна. Хочешь выбрать следующий?",
    "fr": "🔥 Génial ! Défi terminé. Tu veux en choisir le suivant ?",
    "de": "🔥 Stark! Herausforderung abgeschlossen. Möchtest du die nächste auswählen?",
    "pl": "🔥 Super! Wyzwanie ukończone. Chcesz wybrać następne?",
    "es": "🔥 ¡Genial! Desafío completado. ¿Quieres elegir el siguiente?",
}

REMIND_SUGGEST_TEXTS = {
    "ru": {"ask": "Сделать напоминание по этому?", "yes": "Да", "no": "Нет"},
    "uk": {"ask": "Створити нагадування про це?", "yes": "Так", "no": "Ні"},
    "md": {"ask": "Să creez un memento pentru asta?", "yes": "Da", "no": "Nu"},
    "be": {"ask": "Зрабіць напамін пра гэта?", "yes": "Так", "no": "Не"},
    "kk": {"ask": "Осы туралы еске салғыш жасаймыз ба?", "yes": "Иә", "no": "Жоқ"},
    "kg": {"ask": "Мына тууралуу эскертме жасайбызбы?", "yes": "Ооба", "no": "Жок"},
    "hy": {"ask": "Ստեղծե՞մ հիշեցում դրա մասին։", "yes": "Այո", "no": "Ոչ"},
    "ka": {"ask": "შევქმნა შეხსენება ამაზე?", "yes": "დიახ", "no": "არა"},
    "ce": {"ask": "ДӀасалаш дӀаяздой? (напоминание)", "yes": "ХӀа", "no": "Ца"},
    "en": {"ask": "Set a reminder for this?", "yes": "Yes", "no": "No"},
    "fr": {"ask": "Créer un rappel pour ça ?", "yes": "Oui", "no": "Non"},
    "de": {"ask": "Eine Erinnerung dafür erstellen?", "yes": "Ja", "no": "Nein"},
    "es": {"ask": "¿Crear un recordatorio para esto?", "yes": "Sí", "no": "No"},
    "pl": {"ask": "Utworzyć przypomnienie o tym?", "yes": "Tak", "no": "Nie"},
}

REMIND_KEYWORDS = {
    "ru": [r"\bнапомни(шь|те)?\b", r"\bнапоминани[ея]\b", r"\bне забуд[ь|ем]\b"],
    "uk": [r"\bнагадай(еш)?\b", r"\bнагадуванн[я|е]\b", r"\bне забудь\b"],
    "md": [r"\bamint(ește|este)-?mi\b", r"\bmemento\b", r"\bnu uita\b"],
    "be": [r"\bнапа(м|м)ін(і|анне)\b", r"\bнагадай\b", r"\bне забудзь\b"],
    "kk": [r"\bеске\s*сал(шы|ыңыз)?\b", r"\bесте\s*сақта\b", r"\bесіме\s*сал\b"],
    "kg": [r"\bэскертип\b", r"\bэскертме\b", r"\bэсиме\s*сал\b"],
    "hy": [r"\bհիշեցր(ու|եք)\b", r"\bհիշեցում\b"],
    "ka": [r"\bშემახსენე\b", r"\bშეხსენება\b"],
    "ce": [r"\bдӀасалаш\b", r"\bхьо йоьха кхет\b"],  # приблизительно
    "en": [r"\bremind\s+me\b", r"\breminder\b", r"\bdon’t forget\b"],
    "fr": [r"\brappelle[-\s]?moi\b", r"\brappel\b", r"\bn[’']oublie pas\b"],
    "de": [r"\berinnere\s+mich\b", r"\berinnerung\b", r"\bvergiss\s+nicht\b"],
    "es": [r"\brecu[eé]rdame\b", r"\brecordatorio\b", r"\bno te olvides\b"],
    "pl": [r"\bprzypomnij\s+mi\b", r"\bprzypomnienie\b", r"\bnie zapomnij\b"],
}

LANG_TO_TTS = {
    "ru": "ru",
    "uk": "uk",
    "md": "ro",
    "en": "en",
    "fr": "fr",
    "de": "de",
    "es": "es",
    "pl": "pl",
    "kk": "kk",
    "hy": "hy",
    "ka": "ka",
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
        "free_goal":  "⚠️ В бесплатном тарифе доступна только *{limit}* цель.\nСейчас: *{current}/{limit}*.\nОбнови до *Mindra+*, чтобы иметь до *10 целей*.",
        "free_habit": "⚠️ В бесплатном тарифе доступна только *{limit}* привычка.\nСейчас: *{current}/{limit}*.\nОбнови до *Mindra+*, чтобы иметь до *10 привычек*.",
        "plus_goal":  "⚠️ В Mindra+ лимит — *{limit}* целей.\nСейчас: *{current}/{limit}*.\nПерейди на *Mindra Pro*, чтобы снять лимиты.",
        "plus_habit": "⚠️ В Mindra+ лимит — *{limit}* привычек.\nСейчас: *{current}/{limit}*.\nПерейди на *Mindra Pro*, чтобы снять лимиты.",
    },
    "uk": {
        "free_goal":  "⚠️ У безкоштовному тарифі доступна лише *{limit}* ціль.\nЗараз: *{current}/{limit}*.\nОформи *Mindra+*, щоб мати до *10 цілей*.",
        "free_habit": "⚠️ У безкоштовному тарифі доступна лише *{limit}* звичка.\nЗараз: *{current}/{limit}*.\nОформи *Mindra+*, щоб мати до *10 звичок*.",
        "plus_goal":  "⚠️ У Mindra+ ліміт — *{limit}* цілей.\nЗараз: *{current}/{limit}*.\nПерейдіть на *Mindra Pro*, щоб зняти ліміти.",
        "plus_habit": "⚠️ У Mindra+ ліміт — *{limit}* звичок.\nЗараз: *{current}/{limit}*.\nПерейдіть на *Mindra Pro*, щоб зняти ліміти.",
    },
    "es": {
        "free_goal":  "⚠️ En el plan gratuito solo está disponible *{limit}* objetivo.\nAhora: *{current}/{limit}*.\nActualiza a *Mindra+* para tener hasta *10 objetivos*.",
        "free_habit": "⚠️ En el plan gratuito solo está disponible *{limit}* hábito.\nAhora: *{current}/{limit}*.\nActualiza a *Mindra+* para tener hasta *10 hábitos*.",
        "plus_goal":  "⚠️ En *Mindra+* el límite es de *{limit}* objetivos.\nAhora: *{current}/{limit}*.\nPasa a *Mindra Pro* para eliminar los límites.",
        "plus_habit": "⚠️ En *Mindra+* el límite es de *{limit}* hábitos.\nAhora: *{current}/{limit}*.\nPasa a *Mindra Pro* para eliminar los límites.",
    },
    "de": {
        "free_goal":  "⚠️ Im Gratis-Tarif ist nur *{limit}* Ziel verfügbar.\nAktuell: *{current}/{limit}*.\nUpgrade auf *Mindra+*, um bis zu *10 Ziele* zu erhalten.",
        "free_habit": "⚠️ Im Gratis-Tarif ist nur *{limit}* Gewohnheit verfügbar.\nAktuell: *{current}/{limit}*.\nUpgrade auf *Mindra+*, um bis zu *10 Gewohnheiten* zu erhalten.",
        "plus_goal":  "⚠️ In *Mindra+* beträgt das Limit *{limit}* Ziele.\nAktuell: *{current}/{limit}*.\nWechsle zu *Mindra Pro*, um die Limits aufzuheben.",
        "plus_habit": "⚠️ In *Mindra+* beträgt das Limit *{limit}* Gewohnheiten.\nAktuell: *{current}/{limit}*.\nWechsle zu *Mindra Pro*, um die Limits aufzuheben.",
    },
    "pl": {
        "free_goal":  "⚠️ W planie bezpłatnym dostępny jest tylko *{limit}* cel.\nTeraz: *{current}/{limit}*.\nZaktualizuj do *Mindra+*, aby mieć do *10 celów*.",
        "free_habit": "⚠️ W planie bezpłatnym dostępny jest tylko *{limit}* nawyk.\nTeraz: *{current}/{limit}*.\nZaktualizuj do *Mindra+*, aby mieć do *10 nawyków*.",
        "plus_goal":  "⚠️ W *Mindra+* limit to *{limit}* celów.\nTeraz: *{current}/{limit}*.\nPrzejdź na *Mindra Pro*, aby zdjąć limity.",
        "plus_habit": "⚠️ W *Mindra+* limit to *{limit}* nawyków.\nTeraz: *{current}/{limit}*.\nPrzejdź na *Mindra Pro*, aby zdjąć limity.",
    },
    "fr": {
        "free_goal":  "⚠️ Dans l’offre gratuite, seul *{limit}* objectif est disponible.\nActuel : *{current}/{limit}*.\nPasse à *Mindra+* pour avoir jusqu’à *10 objectifs*.",
        "free_habit": "⚠️ Dans l’offre gratuite, seule *{limit}* habitude est disponible.\nActuel : *{current}/{limit}*.\nPasse à *Mindra+* pour avoir jusqu’à *10 habitudes*.",
        "plus_goal":  "⚠️ Dans *Mindra+*, la limite est de *{limit}* objectifs.\nActuel : *{current}/{limit}*.\nPasse à *Mindra Pro* pour lever les limites.",
        "plus_habit": "⚠️ Dans *Mindra+*, la limite est de *{limit}* habitudes.\nActuel : *{current}/{limit}*.\nPasse à *Mindra Pro* pour lever les limites.",
    },
    "en": {
        "free_goal":  "⚠️ Free plan allows only *{limit}* goal.\nNow: *{current}/{limit}*.\nUpgrade to *Mindra+* for up to *10 goals*.",
        "free_habit": "⚠️ Free plan allows only *{limit}* habit.\nNow: *{current}/{limit}*.\nUpgrade to *Mindra+* for up to *10 habits*.",
        "plus_goal":  "⚠️ Mindra+ limit is *{limit}* goals.\nNow: *{current}/{limit}*.\nGo *Mindra Pro* for unlimited.",
        "plus_habit": "⚠️ Mindra+ limit is *{limit}* habits.\nNow: *{current}/{limit}*.\nGo *Mindra Pro* for unlimited.",
    },
    "md": {
        "free_goal":  "⚠️ În planul gratuit este permis doar *{limit}* obiectiv.\nAcum: *{current}/{limit}*.\nTreci la *Mindra+* pentru până la *10 obiective*.",
        "free_habit": "⚠️ În planul gratuit este permis doar *{limit}* obicei.\nAcum: *{current}/{limit}*.\nTreci la *Mindra+* pentru până la *10 obiceiuri*.",
        "plus_goal":  "⚠️ În Mindra+ limita este *{limit}* obiective.\nAcum: *{current}/{limit}*.\nAlege *Mindra Pro* pentru nelimitat.",
        "plus_habit": "⚠️ În Mindra+ limita este *{limit}* obiceiuri.\nAcum: *{current}/{limit}*.\nAlege *Mindra Pro* pentru nelimitat.",
    },
    "be": {
        "free_goal":  "⚠️ У бясплатным тарыфе дазволена толькі *{limit}* мэта.\nЗараз: *{current}/{limit}*.\nАформі *Mindra+*, каб мець да *10 мэт*.",
        "free_habit": "⚠️ У бясплатным тарыфе дазволена толькі *{limit}* звычка.\nЗараз: *{current}/{limit}*.\nАформі *Mindra+*, каб мець да *10 звычак*.",
        "plus_goal":  "⚠️ У Mindra+ ліміт — *{limit}* мэт.\nЗараз: *{current}/{limit}*.\nПераходзь на *Mindra Pro*, каб зняць ліміты.",
        "plus_habit": "⚠️ У Mindra+ ліміт — *{limit}* звычак.\nЗараз: *{current}/{limit}*.\nПераходзь на *Mindra Pro*, каб зняць ліміты.",
    },
    "kk": {
        "free_goal":  "⚠️ Тегін жоспар тек *{limit}* мақсатқа рұқсат етеді.\nҚазір: *{current}/{limit}*.\n*Mindra+* — *10 мақсатқа дейін*.",
        "free_habit": "⚠️ Тегін жоспар тек *{limit}* әдетке рұқсат етеді.\nҚазір: *{current}/{limit}*.\n*Mindra+* — *10 әдетке дейін*.",
        "plus_goal":  "⚠️ Mindra+ лимиті — *{limit}* мақсат.\nҚазір: *{current}/{limit}*.\n*Mindra Pro* — шектеусіз.",
        "plus_habit": "⚠️ Mindra+ лимиті — *{limit}* әдет.\nҚазір: *{current}/{limit}*.\n*Mindra Pro* — шектеусіз.",
    },
    "kg": {
        "free_goal":  "⚠️ Тегин планда болгону *{limit}* максатка уруксат.\nАзыр: *{current}/{limit}*.\n*Mindra+* — *10 максатка чейин*.",
        "free_habit": "⚠️ Тегин планда болгону *{limit}* адатка уруксат.\nАзыр: *{current}/{limit}*.\n*Mindra+* — *10 адатка чейин*.",
        "plus_goal":  "⚠️ Mindra+ лимити — *{limit}* максат.\nАзыр: *{current}/{limit}*.\n*Mindra Pro* — чек жок.",
        "plus_habit": "⚠️ Mindra+ лимити — *{limit}* адат.\nАзыр: *{current}/{limit}*.\n*Mindra Pro* — чек жок.",
    },
    "hy": {
        "free_goal":  "⚠️ Անվճար փաթեթում թույլատրվում է միայն *{limit}* նպատակ։\nՀիմա՝ *{current}/{limit}*։\nՆվազեցրու սահմանափակումները *Mindra+*-ով՝ մինչև *10 նպատակ*։",
        "free_habit": "⚠️ Անվճար փաթեթում թույլատրվում է միայն *{limit}* սովորություն։\nՀիմա՝ *{current}/{limit}*։\n*Mindra+*՝ մինչև *10 սովորություն*։",
        "plus_goal":  "⚠️ Mindra+-ում սահմանը *{limit}* նպատակ է։\nՀիմա՝ *{current}/{limit}*։\n*Mindra Pro* — առանց սահմանների։",
        "plus_habit": "⚠️ Mindra+-ում սահմանը *{limit}* սովորություն է։\nՀիմա՝ *{current}/{limit}*։\n*Mindra Pro* — առանց սահմանների։",
    },
    "ka": {
        "free_goal":  "⚠️ უფასო პაკეტში მხოლოდ *{limit}* მიზანია დაშვებული.\nახლა: *{current}/{limit}*.\n*Mindra+* — *მდე 10 მიზანი*.",
        "free_habit": "⚠️ უფასო პაკეტში მხოლოდ *{limit}* ჩვევაა დაშვებული.\nახლა: *{current}/{limit}*.\n*Mindra+* — *მდე 10 ჩვევა*.",
        "plus_goal":  "⚠️ Mindra+ ლიმიტი — *{limit}* მიზანი.\nახლა: *{current}/{limit}*.\n*Mindra Pro* — შეუზღუდავად.",
        "plus_habit": "⚠️ Mindra+ ლიმიტი — *{limit}* ჩვევა.\nახლა: *{current}/{limit}*.\n*Mindra Pro* — შეუზღუდავად.",
    },
    "ce": {
        "free_goal":  "⚠️ Беплатна хан *{limit}* максат йу.\nХӀинца: *{current}/{limit}*.\n*Mindra+* — до *10* максата.",
        "free_habit": "⚠️ Беплатна хан *{limit}* гӀирс йу.\nХӀинца: *{current}/{limit}*.\n*Mindra+* — до *10* гӀирса.",
        "plus_goal":  "⚠️ Mindra+ да лахар — *{limit}* максата.\nХӀинца: *{current}/{limit}*.\n*Mindra Pro* — дац лахар.",
        "plus_habit": "⚠️ Mindra+ да лахар — *{limit}* гӀирса.\nХӀинца: *{current}/{limit}*.\n*Mindra Pro* — дац лахар.",
    },
}

UPGRADE_TEXTS = {
"ru": {
    "title": "⭐ Обновление",
    "choose": "Выбери подписку и срок:",
    "plus_title": "Mindra+ — комфорт каждый день",
    "pro_title":  "Mindra Pro — максимум без ограничений",
    "period": {
      "1m": "1 месяц", "3m": "3 месяца", "6m": "6 месяцев", "12m": "12 месяцев", "life": "Пожизненно"
    },
    "buy": "Купить",
    "back": "⬅️ Назад",
    "open_payment": "Открыть оплату",
    "check_payment": "Я оплатил(а), проверить ✅",
    "pending": "Если оплата прошла — подписка активируется автоматически за несколько секунд. Если нет — нажми «Проверить».",
    "no_active": "Пока не вижу оплаты. Подожди минуту и нажми «Проверить» ещё раз.",
    "active_now": "Готово! ✨ Подписка активна.",
  },

"es": {
    "title": "⭐ Actualización",
    "choose": "Elige la suscripción y el período:",
    "plus_title": "Mindra+ — comodidad cada día",
    "pro_title":  "Mindra Pro — máximo sin límites",
    "period": {
      "1m": "1 mes", "3m": "3 meses", "6m": "6 meses", "12m": "12 meses", "life": "De por vida"
    },
    "buy": "Comprar",
    "back": "⬅️ Atrás",
    "open_payment": "Abrir pago",
    "check_payment": "Comprobar el pago ✅",
    "pending": "Si el pago se ha realizado, la suscripción se activará automáticamente en unos segundos. Si no, pulsa «Comprobar».",
    "no_active": "Aún no veo el pago. Espera un minuto y pulsa «Comprobar» otra vez.",
    "active_now": "¡Listo! ✨ Suscripción activa.",
},

"de": {
    "title": "⭐ Upgrade",
    "choose": "Wähle Abo und Laufzeit:",
    "plus_title": "Mindra+ — Komfort jeden Tag",
    "pro_title":  "Mindra Pro — Maximum ohne Limits",
    "period": {
      "1m": "1 Monat", "3m": "3 Monate", "6m": "6 Monate", "12m": "12 Monate", "life": "Lebenslang"
    },
    "buy": "Kaufen",
    "back": "⬅️ Zurück",
    "open_payment": "Zahlung öffnen",
    "check_payment": "Bezahlung prüfen ✅",
    "pending": "Wenn die Zahlung erfolgreich war, wird das Abo innerhalb weniger Sekunden automatisch aktiviert. Falls nicht, tippe auf „Prüfen“.",
    "no_active": "Zahlung noch nicht sichtbar. Warte eine Minute und tippe erneut auf „Prüfen“.",
    "active_now": "Fertig! ✨ Abo ist aktiv.",
},

"pl": {
    "title": "⭐ Aktualizacja",
    "choose": "Wybierz subskrypcję i okres:",
    "plus_title": "Mindra+ — komfort każdego dnia",
    "pro_title":  "Mindra Pro — maksimum bez ograniczeń",
    "period": {
      "1m": "1 miesiąc", "3m": "3 miesiące", "6m": "6 miesięcy", "12m": "12 miesięcy", "life": "Dożywotnio"
    },
    "buy": "Kup",
    "back": "⬅️ Wstecz",
    "open_payment": "Otwórz płatność",
    "check_payment": "Sprawdź płatność ✅",
    "pending": "Jeśli płatność przeszła, subskrypcja aktywuje się automatycznie w ciągu kilku sekund. Jeśli nie — kliknij „Sprawdź”.",
    "no_active": "Na razie nie widzę płatności. Poczekaj minutę i kliknij „Sprawdź” ponownie.",
    "active_now": "Gotowe! ✨ Subskrypcja jest aktywna.",
},

"fr": {
    "title": "⭐ Mise à niveau",
    "choose": "Choisis l’abonnement et la durée :",
    "plus_title": "Mindra+ — du confort au quotidien",
    "pro_title":  "Mindra Pro — le maximum sans limites",
    "period": {
      "1m": "1 mois", "3m": "3 mois", "6m": "6 mois", "12m": "12 mois", "life": "À vie"
    },
    "buy": "Acheter",
    "back": "⬅️ Retour",
    "open_payment": "Ouvrir le paiement",
    "check_payment": "Vérifier le paiement ✅",
    "pending": "Si le paiement a réussi, l’abonnement s’activera automatiquement en quelques secondes. Sinon, appuie sur « Vérifier ».",
    "no_active": "Je ne vois pas encore le paiement. Attends une minute puis appuie de nouveau sur « Vérifier ».",
    "active_now": "C’est fait ! ✨ L’abonnement est actif.",
},

  "uk": {
    "title": "⭐ Оновлення",
    "choose": "Обери підписку і строк:",
    "plus_title": "Mindra+ — комфорт щодня",
    "pro_title":  "Mindra Pro — максимум без обмежень",
    "period": {
      "1m": "1 місяць", "3m": "3 місяці", "6m": "6 місяців", "12m": "12 місяців", "life": "Пожиттєво"
    },
    "buy": "Купити",
    "back": "⬅️ Назад",
    "open_payment": "Відкрити оплату",
    "check_payment": "Я оплатив(ла), перевірити ✅",
    "pending": "Якщо оплата пройшла — підписка активується автоматично за кілька секунд. Якщо ні — натисни «Перевірити».",
    "no_active": "Поки не бачу оплати. Зачекай хвилинку і натисни «Перевірити» ще раз.",
    "active_now": "Готово! ✨ Підписку активовано.",
  },

  "en": {
    "title": "⭐ Upgrade",
    "choose": "Pick a plan and duration:",
    "plus_title": "Mindra+ — daily comfort",
    "pro_title":  "Mindra Pro — maximum freedom",
    "period": {
      "1m": "1 month", "3m": "3 months", "6m": "6 months", "12m": "12 months", "life": "Lifetime"
    },
    "buy": "Buy",
    "back": "⬅️ Back",
    "open_payment": "Open payment",
    "check_payment": "I’ve paid, check ✅",
    "pending": "If the payment succeeded, your subscription will activate within a few seconds. If not — tap “Check”.",
    "no_active": "I don't see a payment yet. Wait a minute and tap “Check” again.",
    "active_now": "Done! ✨ Subscription is active.",
  },

  # Moldovenească / Romanian
  "md": {
    "title": "⭐ Upgrade",
    "choose": "Alege abonamentul și perioada:",
    "plus_title": "Mindra+ — confort zilnic",
    "pro_title":  "Mindra Pro — libertate la maximum",
    "period": {
      "1m": "1 lună", "3m": "3 luni", "6m": "6 luni", "12m": "12 luni", "life": "Pe viață"
    },
    "buy": "Cumpără",
    "back": "⬅️ Înapoi",
    "open_payment": "Deschide plata",
    "check_payment": "Am plătit, verifică ✅",
    "pending": "Dacă plata a reușit, abonamentul se activează automat în câteva secunde. Dacă nu — apasă „Verifică”.",
    "no_active": "Încă nu văd plata. Așteaptă un minut și apasă „Verifică” din nou.",
    "active_now": "Gata! ✨ Abonamentul este activ.",
  },

  "be": {
    "title": "⭐ Абнаўленне",
    "choose": "Абяры падпіску і тэрмін:",
    "plus_title": "Mindra+ — камфорт штодня",
    "pro_title":  "Mindra Pro — максімум без абмежаванняў",
    "period": {
      "1m": "1 месяц", "3m": "3 месяцы", "6m": "6 месяцаў", "12m": "12 месяцаў", "life": "Пажыццёва"
    },
    "buy": "Купіць",
    "back": "⬅️ Назад",
    "open_payment": "Адкрыць аплату",
    "check_payment": "Я аплаціў(ла), праверыць ✅",
    "pending": "Калі аплата прайшла — падпіска ўключыцца аўтаматычна за некалькі секунд. Калі не — націсні «Праверыць».",
    "no_active": "Пакуль не бачу аплаты. Пачакай хвіліну і націсні «Праверыць» яшчэ раз.",
    "active_now": "Гатова! ✨ Падпіска актыўная.",
  },

  "kk": {
    "title": "⭐ Жаңарту",
    "choose": "Жазылым мен мерзімді таңдаңыз:",
    "plus_title": "Mindra+ — күнделікті жайлылық",
    "pro_title":  "Mindra Pro — шектеусіз мүмкіндіктер",
    "period": {
      "1m": "1 ай", "3m": "3 ай", "6m": "6 ай", "12m": "12 ай", "life": "Өмір бойы"
    },
    "buy": "Сатып алу",
    "back": "⬅️ Артқа",
    "open_payment": "Төлемді ашу",
    "check_payment": "Төледім, тексеру ✅",
    "pending": "Төлем сәтті болса, жазылым бірнеше секунд ішінде автоматты түрде іске қосылады. Болмаса — «Тексеру» басыңыз.",
    "no_active": "Әзірге төлем көрінбейді. Бір минут күтіп, «Тексеру» түймесін қайта басыңыз.",
    "active_now": "Дайын! ✨ Жазылым қосылды.",
  },

  "kg": {
    "title": "⭐ Жаңыртуу",
    "choose": "Жазылууну жана мөөнөттү тандаңыз:",
    "plus_title": "Mindra+ — күн сайынгы ыңгайлуулук",
    "pro_title":  "Mindra Pro — дээрлик чексиз мүмкүнчүлүк",
    "period": {
      "1m": "1 ай", "3m": "3 ай", "6m": "6 ай", "12m": "12 ай", "life": "Өмүр бою"
    },
    "buy": "Сатып алуу",
    "back": "⬅️ Артка",
    "open_payment": "Төлөм барагын ачуу",
    "check_payment": "Төлөдүм, текшерүү ✅",
    "pending": "Эгер төлөм ийгиликтүү болсо, жазылуу бир нече секундда автоматтык түрдө жанат. Болбосо — «Текшерүү» басыңыз.",
    "no_active": "Азырынча төлөм көрүнгөн жок. Бир аз күткөндөн кийин «Текшерүү» баскычын кайра басыңыз.",
    "active_now": "Болду! ✨ Жазылуу активдүү.",
  },

  "hy": {
    "title": "⭐ Թարմացում",
    "choose": "Ընտրիր փաթեթն ու ժամկետը․",
    "plus_title": "Mindra+ — հարմարավետություն ամեն օր",
    "pro_title":  "Mindra Pro — առավելագույն՝ առանց սահմանների",
    "period": {
      "1m": "1 ամիս", "3m": "3 ամիս", "6m": "6 ամիս", "12m": "12 ամիս", "life": "Ցմահ"
    },
    "buy": "Գնել",
    "back": "⬅️ Վերադառնալ",
    "open_payment": "Բացել վճարումը",
    "check_payment": "Վճարել եմ, ստուգել ✅",
    "pending": "Եթե վճարումը հաջող է, բաժանորդագրությունը կակտիվացվի մի քանի վայրկյանի ընթացքում։ Եթե ոչ՝ սեղմիր «Ստուգել».",
    "no_active": "Վճարումը դեռ չի երևում։ Սպասիր մեկ րոպե և նորից սեղմիր «Ստուգել».",
    "active_now": "Պատրաստ է! ✨ Բաժանորդագրությունը ակտիվ է։",
  },

  "ka": {
    "title": "⭐ განახლება",
    "choose": "აირჩიე პაკეტი და ვადა:",
    "plus_title": "Mindra+ — კომფორტი ყოველდღე",
    "pro_title":  "Mindra Pro — მაქსიმუმი შეზღუდვების გარეშე",
    "period": {
      "1m": "1 თვე", "3m": "3 თვე", "6m": "6 თვე", "12m": "12 თვე", "life": "სამუდამოდ"
    },
    "buy": "ყიდვა",
    "back": "⬅️ უკან",
    "open_payment": "გადახდის გახსნა",
    "check_payment": "გადახდა შევასრულე, შეამოწმე ✅",
    "pending": "თუ გადახდა წარმატებულია, გამოწერა ავტომატურად აქტიურდება რამდენიმე წამში. თუ არა — დააჭირე „შემოწმებას“.",
    "no_active": "ჯერ გადახდა არ ჩანს. მოიცადე წუთით და კიდევ სცადე „შემოწმება“.",
    "active_now": "მზადაა! ✨ გამოწერა გააქტიურებულია.",
  },

  # Чеченский — используем нейтральные формулировки (при необходимости подправим)
  "ce": {
    "title": "⭐ Обновление",
    "choose": "Выбери подписку и срок:",
    "plus_title": "Mindra+ — комфорт каждый день",
    "pro_title":  "Mindra Pro — максимум без ограничений",
    "period": {
      "1m": "1 месяц", "3m": "3 месяца", "6m": "6 месяцев", "12m": "12 месяцев", "life": "Пожизненно"
    },
    "buy": "Купить",
    "back": "⬅️ Назад",
    "open_payment": "Открыть оплату",
    "check_payment": "Я оплатил(а), проверить ✅",
    "pending": "Если оплата прошла — подписка активируется автоматически за несколько секунд. Если нет — нажми «Проверить».",
    "no_active": "Пока не вижу оплаты. Подожди минуту и нажми «Проверить» ещё раз.",
    "active_now": "Готово! ✨ Подписка активна.",
  },
}

SUBSCRIPTION_CONFIRM_TEXTS = {
    "ru": {
        "template": "Благодарим за покупку подписки {plan} на {duration}! ✨ Подписка активна.",
        "durations": {
            "1m": "1 месяц",
            "3m": "3 месяца",
            "6m": "6 месяцев",
            "12m": "12 месяцев",
            "life": "всю жизнь",
        },
    },
    "uk": {
        "template": "Дякуємо за покупку підписки {plan} на {duration}! ✨ Підписку активовано.",
        "durations": {
            "1m": "1 місяць",
            "3m": "3 місяці",
            "6m": "6 місяців",
            "12m": "12 місяців",
            "life": "все життя",
        },
    },
    "en": {
        "template": "Thank you for purchasing the {plan} subscription for {duration}! ✨ It's now active.",
        "durations": {
            "1m": "1 month",
            "3m": "3 months",
            "6m": "6 months",
            "12m": "12 months",
            "life": "a lifetime",
        },
    },
    "es": {
        "template": "¡Gracias por comprar la suscripción {plan} por {duration}! ✨ Ya está activa.",
        "durations": {
            "1m": "1 mes",
            "3m": "3 meses",
            "6m": "6 meses",
            "12m": "12 meses",
            "life": "toda la vida",
        },
    },
    "de": {
        "template": "Danke für den Kauf des {plan}-Abos für {duration}! ✨ Es ist jetzt aktiv.",
        "durations": {
            "1m": "1 Monat",
            "3m": "3 Monate",
            "6m": "6 Monate",
            "12m": "12 Monate",
            "life": "die ganze Lebenszeit",
        },
    },
    "pl": {
        "template": "Dziękujemy za zakup subskrypcji {plan} na {duration}! ✨ Subskrypcja jest już aktywna.",
        "durations": {
            "1m": "1 miesiąc",
            "3m": "3 miesiące",
            "6m": "6 miesięcy",
            "12m": "12 miesięcy",
            "life": "całe życie",
        },
    },
    "fr": {
        "template": "Merci d’avoir acheté l’abonnement {plan} pour {duration} ! ✨ Il est désormais actif.",
        "durations": {
            "1m": "1 mois",
            "3m": "3 mois",
            "6m": "6 mois",
            "12m": "12 mois",
            "life": "toute la vie",
        },
    },
    "md": {
        "template": "Mulțumim pentru achiziția abonamentului {plan} pentru {duration}! ✨ Este acum activ.",
        "durations": {
            "1m": "1 lună",
            "3m": "3 luni",
            "6m": "6 luni",
            "12m": "12 luni",
            "life": "toată viața",
        },
    },
    "be": {
        "template": "Дзякуй за пакупку падпіскі {plan} на {duration}! ✨ Падпіска актыўная.",
        "durations": {
            "1m": "1 месяц",
            "3m": "3 месяцы",
            "6m": "6 месяцаў",
            "12m": "12 месяцаў",
            "life": "усё жыццё",
        },
    },
    "kk": {
        "template": "Жазылым {plan}-ды {duration} сатып алғаныңыз үшін рақмет! ✨ Жазылым қосылды.",
        "durations": {
            "1m": "1 айға",
            "3m": "3 айға",
            "6m": "6 айға",
            "12m": "12 айға",
            "life": "өмір бойы",
        },
    },
    "kg": {
        "template": "{plan} жазылуусун {duration} сатып алганыңыз үчүн рахмат! ✨ Жазылуу активдүү.",
        "durations": {
            "1m": "1 айга",
            "3m": "3 айга",
            "6m": "6 айга",
            "12m": "12 айга",
            "life": "өмүр бою",
        },
    },
    "hy": {
        "template": "Շնորհակալ ենք {plan} բաժանորդագրությունը {duration} գնելու համար։ ✨ Այն ակտիվ է։",
        "durations": {
            "1m": "1 ամսով",
            "3m": "3 ամսով",
            "6m": "6 ամսով",
            "12m": "12 ամսով",
            "life": "ցմահ",
        },
    },
    "ka": {
        "template": "გმადლობთ {plan} გამოწერის შეძენისთვის {duration}! ✨ გამოწერა უკვე აქტიურია.",
        "durations": {
            "1m": "1 თვიანი ვადით",
            "3m": "3 თვიანი ვადით",
            "6m": "6 თვიანი ვადით",
            "12m": "12 თვიანი ვადით",
            "life": "სამუდამო წვდომით",
        },
    },
    "ce": {
        "template": "Баркалла хьуна, що купил(а) подписку {plan} на {duration}! ✨ Подписка активна.",
        "durations": {
            "1m": "1 месяц",
            "3m": "3 месяца",
            "6m": "6 месяцев",
            "12m": "12 месяцев",
            "life": "пожизненно",
        },
    },
}

MENU_LABELS = {
    "ru": {"upgrade": "⭐ Обновить"},
    "uk": {"upgrade": "⭐ Оновити"},
    "es": {"upgrade": "⭐ Actualizar"},
    "de": {"upgrade": "⭐ Upgrade"},
    "pl": {"upgrade": "⭐ Ulepsz"},
    "fr": {"upgrade": "⭐ Mise à niveau"},
    "en": {"upgrade": "⭐ Upgrade"},
    "md": {"upgrade": "⭐ Actualizare"},
    "be": {"upgrade": "⭐ Абнаўленне"},
    "kk": {"upgrade": "⭐ Жаңарту"},
    "kg": {"upgrade": "⭐ Жаңыртуу"},
    "hy": {"upgrade": "⭐ Բարձրացում"},
    "ka": {"upgrade": "⭐ განახლება"},
    "ce": {"upgrade": "⭐ Обновление"},
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
        "feat_daily_task": "📅 Задание дня",

        # Премиум-функции
        "plus_title": "💠 Премиум-функции",
        "plus_body": "Доступно в Mindra+:",
        "plus_voice_mode": "🔊 Озвучка сообщений",
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
        "premium_site": "🌐 Сайт Mindra",
        "premium_motivation": "📣 Канал мотивации",

        # Настройки
        "set_title": "⚙️ Настройки",
        "set_body": "Что настроить?",
        "set_lang": "🌐 Язык",
        "set_tz": "🕒 Часовой пояс",
        "set_messages": "💌 Сообщения",
        "set_feedback": "💌 Оставить отзыв",
        "feedback_ask": "Напиши сюда отзыв, идею или баг — я передам его разработчику 💜",
        "feedback_thx": "Спасибо за отзыв! ✨",
    },

    # MENU_TEXTS — блоки для новых языков
"es": {
    "title": "🏠 Menú principal",
    "premium_until": "💎 Premium hasta: *{until}*",
    "premium_none": "💎 Premium: *no*",
    "features": "🧰 Funciones",
    "plus_features": "💠 Funciones premium",
    "premium": "💎 Premium",
    "settings": "⚙️ Ajustes",
    "back": "⬅️ Atrás",
    "close": "✖️ Cerrar",

    "feat_title": "🧰 Funciones",
    "feat_body": "Elige una sección:",
    "feat_tracker": "🎯 Tracker (metas y hábitos)",
    "feat_reminders": "⏰ Recordatorios",
    "feat_points": "⭐️ Puntos/Título",
    "feat_mood": "🧪 Test de ánimo",
    "features_mode": "🎛 Modo de conversación (/mode)",
    "feat_daily_task": "📅 Tarea del día",

    "plus_title": "💠 Funciones premium",
    "plus_body": "Disponible en Mindra+:",
    "plus_voice_mode": "🔊 Voz para mensajes",
    "plus_voice": "🎙 Voz",
    "plus_sleep": "😴 Sonidos para dormir",
    "plus_story": "📖 Cuento",
    "plus_pmode": "🟣 Modo Premium",
    "plus_pstats": "📊 Estadísticas Premium",
    "plus_preport": "📝 Informe Premium",
    "plus_pchallenge": "🏆 Desafío Premium",

    "prem_title": "💎 Premium",
    "premium_days": "¿Cuánto queda?",
    "invite": "Invitar a un amigo (+7 días)",
    "premium_site": "🌐 Sitio de Mindra",
    "premium_motivation": "📣 Canal de motivación",

    "set_title": "⚙️ Ajustes",
    "set_body": "¿Qué configurar?",
    "set_lang": "🌐 Idioma",
    "set_tz": "🕒 Zona horaria",
    "set_messages": "💌 Mensajes",
    "set_feedback": "💌 Dejar opinión",
    "feedback_ask": "Escribe aquí tu opinión, idea o bug — se la pasaré al desarrollador 💜",
    "feedback_thx": "¡Gracias por tu opinión! ✨",
},

"de": {
    "title": "🏠 Hauptmenü",
    "premium_until": "💎 Premium bis: *{until}*",
    "premium_none": "💎 Premium: *kein*",
    "features": "🧰 Funktionen",
    "plus_features": "💠 Premium-Funktionen",
    "premium": "💎 Premium",
    "settings": "⚙️ Einstellungen",
    "back": "⬅️ Zurück",
    "close": "✖️ Schließen",

    "feat_title": "🧰 Funktionen",
    "feat_body": "Wähle einen Bereich:",
    "feat_tracker": "🎯 Tracker (Ziele & Gewohnheiten)",
    "feat_reminders": "⏰ Erinnerungen",
    "feat_points": "⭐️ Punkte/Titel",
    "feat_mood": "🧪 Stimmungstest",
    "features_mode": "🎛 Dialogmodus (/mode)",
    "feat_daily_task": "📅 Tagesaufgabe",

    "plus_title": "💠 Premium-Funktionen",
    "plus_body": "Verfügbar in Mindra+:",
    "plus_voice_mode": "🔊 Sprachausgabe für Nachrichten",
    "plus_voice": "🎙 Sprachausgabe",
    "plus_sleep": "😴 Einschlafklänge",
    "plus_story": "📖 Märchen",
    "plus_pmode": "🟣 Premium-Modus",
    "plus_pstats": "📊 Premium-Statistiken",
    "plus_preport": "📝 Premium-Bericht",
    "plus_pchallenge": "🏆 Premium-Challenge",

    "prem_title": "💎 Premium",
    "premium_days": "Wie viel bleibt noch?",
    "invite": "Freund einladen (+7 Tage)",
    "premium_site": "🌐 Mindra-Website",
    "premium_motivation": "📣 Motivationskanal",

    "set_title": "⚙️ Einstellungen",
    "set_body": "Was möchtest du einstellen?",
    "set_lang": "🌐 Sprache",
    "set_tz": "🕒 Zeitzone",
    "set_messages": "💌 Nachrichten",
    "set_feedback": "💌 Feedback geben",
    "feedback_ask": "Schreib hier dein Feedback, eine Idee oder einen Bug — ich leite es an den Entwickler weiter 💜",
    "feedback_thx": "Danke für dein Feedback! ✨",
},

"pl": {
    "title": "🏠 Główne menu",
    "premium_until": "💎 Premium do: *{until}*",
    "premium_none": "💎 Premium: *brak*",
    "features": "🧰 Funkcje",
    "plus_features": "💠 Funkcje premium",
    "premium": "💎 Premium",
    "settings": "⚙️ Ustawienia",
    "back": "⬅️ Wstecz",
    "close": "✖️ Zamknij",

    "feat_title": "🧰 Funkcje",
    "feat_body": "Wybierz sekcję:",
    "feat_tracker": "🎯 Tracker (cele i nawyki)",
    "feat_reminders": "⏰ Przypomnienia",
    "feat_points": "⭐️ Punkty/Tytuł",
    "feat_mood": "🧪 Test nastroju",
    "features_mode": "🎛 Tryb rozmowy (/mode)",
    "feat_daily_task": "📅 Zadanie dnia",

    "plus_title": "💠 Funkcje premium",
    "plus_body": "Dostępne w Mindra+:",
    "plus_voice_mode": "🔊 Głos do wiadomości",
    "plus_voice": "🎙 Lektor",
    "plus_sleep": "😴 Dźwięki do snu",
    "plus_story": "📖 Bajka",
    "plus_pmode": "🟣 Tryb Premium",
    "plus_pstats": "📊 Statystyki Premium",
    "plus_preport": "📝 Raport Premium",
    "plus_pchallenge": "🏆 Wyzwanie Premium",

    "prem_title": "💎 Premium",
    "premium_days": "Ile pozostało?",
    "invite": "Zaproś znajomego (+7 dni)",
    "premium_site": "🌐 Strona Mindra",
    "premium_motivation": "📣 Kanał motywacji",

    "set_title": "⚙️ Ustawienia",
    "set_body": "Co chcesz ustawić?",
    "set_lang": "🌐 Język",
    "set_tz": "🕒 Strefa czasowa",
    "set_messages": "💌 Wiadomości",
    "set_feedback": "💌 Zostaw opinię",
    "feedback_ask": "Napisz tutaj opinię, pomysł lub błąd — przekażę to deweloperowi 💜",
    "feedback_thx": "Dzięki za opinię! ✨",
},

"fr": {
    "title": "🏠 Menu principal",
    "premium_until": "💎 Premium jusqu’au : *{until}*",
    "premium_none": "💎 Premium : *aucun*",
    "features": "🧰 Fonctions",
    "plus_features": "💠 Fonctionnalités Premium",
    "premium": "💎 Premium",
    "settings": "⚙️ Paramètres",
    "back": "⬅️ Retour",
    "close": "✖️ Fermer",

    "feat_title": "🧰 Fonctions",
    "feat_body": "Choisis une section :",
    "feat_tracker": "🎯 Suivi (objectifs & habitudes)",
    "feat_reminders": "⏰ Rappels",
    "feat_points": "⭐️ Points/Titre",
    "feat_mood": "🧪 Test d’humeur",
    "features_mode": "🎛 Mode de conversation (/mode)",
    "feat_daily_task": "📅 Tâche du jour",

    "plus_title": "💠 Fonctionnalités Premium",
    "plus_body": "Disponible dans Mindra+ :",
    "plus_voice_mode": "🔊 Lecture des messages",
    "plus_voice": "🎙 Voix",
    "plus_sleep": "😴 Sons pour dormir",
    "plus_story": "📖 Conte",
    "plus_pmode": "🟣 Mode Premium",
    "plus_pstats": "📊 Statistiques Premium",
    "plus_preport": "📝 Rapport Premium",
    "plus_pchallenge": "🏆 Défi Premium",

    "prem_title": "💎 Premium",
    "premium_days": "Combien reste-t-il ?",
    "invite": "Inviter un ami (+7 jours)",
    "premium_site": "🌐 Site Mindra",
    "premium_motivation": "📣 Canal de motivation",

    "set_title": "⚙️ Paramètres",
    "set_body": "Que veux-tu configurer ?",
    "set_lang": "🌐 Langue",
    "set_tz": "🕒 Fuseau horaire",
    "set_messages": "💌 Messages",
    "set_feedback": "💌 Laisser un avis",
    "feedback_ask": "Écris ici ton avis, une idée ou un bug — je le transmettrai au développeur 💜",
    "feedback_thx": "Merci pour ton avis ! ✨",
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
        "feat_daily_task": "📅 Завдання дня",

        "plus_title": "💠 Преміум-функції",
        "plus_body": "Доступно в Mindra+:",
        "plus_voice_mode": "🔊 Озвучення повідомлень",
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
        "premium_site": "🌐 Сайт Mindra",
        "premium_motivation": "📣 Канал мотивації",

        "set_title": "⚙️ Налаштування",
        "set_body": "Що налаштувати?",
        "set_lang": "🌐 Мова",
        "set_tz": "🕒 Часовий пояс",
        "set_messages": "💌 Повідомлення",
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
        "feat_daily_task": "📅 Daily task",

        "plus_title": "💠 Premium features",
        "plus_body": "Included in Mindra+:",
        "plus_voice_mode": "🔊 Voice replies",
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
        "premium_site": "🌐 Mindra website",
        "premium_motivation": "📣 Motivation channel",

        "set_title": "⚙️ Settings",
        "set_body": "What to configure?",
        "set_lang": "🌐 Language",
        "set_tz": "🕒 Time zone",
        "set_messages": "💌 Messages",
        "set_feedback": "💌 Leave feedback",
        "feedback_ask": "Type your feedback or idea — I’ll pass it to the developer 💜",
        "feedback_thx": "Thanks for your feedback! ✨",
    },

    "md": {  # Romanian / Română
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
        "feat_daily_task": "📅 Sarcina zilei",

        "plus_title": "💠 Funcții Premium",
        "plus_body": "Incluse în Mindra+:",
        "plus_voice_mode": "🔊 Răspuns vocal",
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
        "premium_site": "🌐 Site-ul Mindra",
        "premium_motivation": "📣 Canal de motivație",

        "set_title": "⚙️ Setări",
        "set_body": "Ce dorești să configurezi?",
        "set_lang": "🌐 Limba",
        "set_tz": "🕒 Fus orar",
        "set_messages": "💌 Mesaje",
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
        "feat_daily_task": "📅 Күннің тапсырмасы",

        "plus_title": "💠 Прэміум-функцыі",
        "plus_body": "Даступна ў Mindra+:",
        "plus_voice_mode": "🔊 Голасавыя адказы",
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
        "premium_site": "🌐 Сайт Mindra",
        "premium_motivation": "📣 Канал матывацыі",

        "set_title": "⚙️ Налады",
        "set_body": "Што наладзіць?",
        "set_lang": "🌐 Мова",
        "set_tz": "🕒 Часавы пояс",
        "set_messages": "💌 Паведамленні",
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
        "feat_daily_task": "📅 Күннің тапсырмасы",

        "plus_title": "💠 Премиум-функциялар",
        "plus_body": "Mindra+ құрамында:",
        "plus_voice_mode": "🔊 Дыбыстық жауаптар",
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
        "premium_site": "🌐 Mindra сайты",
        "premium_motivation": "📣 Мотивация арнасы",

        "set_title": "⚙️ Баптаулар",
        "set_body": "Нені баптаймыз?",
        "set_lang": "🌐 Тіл",
        "set_tz": "🕒 Уақыт белдеуі",
        "set_messages": "💌 Хабарламалар",
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
        "plus_voice_mode": "🔊 Үн менен жооп",
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
        "premium_site": "🌐 Mindra сайты",
        "premium_motivation": "📣 Мотивация каналы",

        "set_title": "⚙️ Жөндөөлөр",
        "set_body": "Эмне жөндөйбүз?",
        "set_lang": "🌐 Тил",
        "set_tz": "🕒 Саат алкагы",
        "set_messages": "💌 Билдирүүлөр",
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
        "feat_daily_task": "📅 Օրվա հանձնարարությունը",

        "plus_title": "💠 Պրեմիում ֆունկցիաներ",
        "plus_body": "Mindra+ փաթեթում՝",
        "plus_voice_mode": "🔊 Ձայնային պատասխաններ",
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
        "premium_site": "🌐 Mindra կայք",
        "premium_motivation": "📣 Մոտիվացիայի ալիք",

        "set_title": "⚙️ Կարգավորումներ",
        "set_body": "Ի՞նչ կարգավորել։",
        "set_lang": "🌐 Լեզու",
        "set_tz": "🕒 Ժամային գոտի",
        "set_messages": "💌 Հաղորդագրություններ",
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
        "feat_daily_task": "📅 დღის დავალება",

        "plus_title": "💠 პრემიუმ-ფუნქციები",
        "plus_body": "Mindra+-ში შედის:",
        "plus_voice_mode": "🔊 ხმოვანი რეჟიმი",
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
        "premium_site": "🌐 Mindra საიტი",
        "premium_motivation": "📣 მოტივაციის არხი",

        "set_title": "⚙️ პარამეტრები",
        "set_body": "რას ვანstellოთ?",
        "set_lang": "🌐 ენა",
        "set_tz": "🕒 დროის სარტყელი",
        "set_messages": "💌 შეტყობინებები",
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
        "plus_voice_mode": "🔊 Хьалха режим",
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
        "premium_site": "🌐 Mindra сайт",
        "premium_motivation": "📣 Мотивацин канал",

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
    "es": {
        "title": "Se requiere suscripción",
        "feature_story_voice": "La narración de cuentos por voz está disponible en {plus} y {pro}. Descubre historias mágicas con voz y fondo 🌙",
        "feature_eleven":     "Las voces premium de ElevenLabs están disponibles en {plus} y {pro}.",
        "feature_bgm":        "Los sonidos de fondo sobre la voz están disponibles en {plus}/{pro}.",
        "feature_sleep_long": "Duración del modo sueño superior a {min} min — en {plus}/{pro}.",
        "feature_story_long": "Cuentos medianos y largos — en {plus}/{pro}.",
        "feature_quota_msg":  "Se alcanzó el límite diario de mensajes ({n}). Más — en {plus}/{pro}.",
        "feature_goals":      "Más objetivos — en {plus}/{pro}.",
        "feature_habits":     "Más hábitos — en {plus}/{pro}.",
        "feature_reminders":  "Más recordatorios — en {plus}/{pro}.",
        "cta": "Suscribirse → /premium",
    },

    "de": {
        "title": "Abonnement erforderlich",
        "feature_story_voice": "Märchen-Vertonung mit Stimme ist in {plus} und {pro} verfügbar. Entdecke zauberhafte Geschichten mit Stimme und Hintergrund 🌙",
        "feature_eleven":     "Premium-Stimmen von ElevenLabs sind in {plus} und {pro} verfügbar.",
        "feature_bgm":        "Hintergrundklänge über der Stimme sind in {plus}/{pro} verfügbar.",
        "feature_sleep_long": "Schlafmodus-Dauer über {min} Min — in {plus}/{pro}.",
        "feature_story_long": "Mittlere und lange Märchen — in {plus}/{pro}.",
        "feature_quota_msg":  "Tageslimit für Nachrichten erreicht ({n}). Mehr — in {plus}/{pro}.",
        "feature_goals":      "Mehr Ziele — in {plus}/{pro}.",
        "feature_habits":     "Mehr Gewohnheiten — in {plus}/{pro}.",
        "feature_reminders":  "Mehr Erinnerungen — in {plus}/{pro}.",
        "cta": "Abonnieren → /premium",
    },

"pl": {
        "title": "Wymagana subskrypcja",
        "feature_story_voice": "Odtwarzanie bajek głosem dostępne w {plus} i {pro}. Odkryj magiczne historie z głosem i tłem 🌙",
        "feature_eleven":     "Głosy premium ElevenLabs dostępne w {plus} i {pro}.",
        "feature_bgm":        "Dźwięki tła nałożone na głos dostępne w {plus}/{pro}.",
        "feature_sleep_long": "Czas trybu snu powyżej {min} min — w {plus}/{pro}.",
        "feature_story_long": "Średnie i długie bajki — w {plus}/{pro}.",
        "feature_quota_msg":  "Osiągnięto dzienny limit wiadomości ({n}). Więcej — w {plus}/{pro}.",
        "feature_goals":      "Więcej celów — w {plus}/{pro}.",
        "feature_habits":     "Więcej nawyków — w {plus}/{pro}.",
        "feature_reminders":  "Więcej przypomnień — w {plus}/{pro}.",
        "cta": "Subskrybuj → /premium",
    },

    "fr": {
        "title": "Abonnement requis",
        "feature_story_voice": "La narration des contes est disponible dans {plus} et {pro}. Découvre des histoires magiques avec voix et fond sonore 🌙",
        "feature_eleven":     "Les voix premium d’ElevenLabs sont disponibles dans {plus} et {pro}.",
        "feature_bgm":        "Les sons d’arrière-plan par-dessus la voix sont disponibles dans {plus}/{pro}.",
        "feature_sleep_long": "Durée du mode sommeil au-delà de {min} min — dans {plus}/{pro}.",
        "feature_story_long": "Contes moyens et longs — dans {plus}/{pro}.",
        "feature_quota_msg":  "Limite quotidienne de messages atteinte ({n}). Plus — dans {plus}/{pro}.",
        "feature_goals":      "Plus d’objectifs — dans {plus}/{pro}.",
        "feature_habits":     "Plus d’habitudes — dans {plus}/{pro}.",
        "feature_reminders":  "Plus de rappels — dans {plus}/{pro}.",
        "cta": "S’abonner → /premium",
    },
}

PLAN_LABELS = {
    "ru": {PLAN_FREE:"Бесплатно",      PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "uk": {PLAN_FREE:"Безкоштовно",    PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "md": {PLAN_FREE:"Gratuit",        PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "be": {PLAN_FREE:"Бясплатна",      PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "kk": {PLAN_FREE:"Тегін",          PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "kg": {PLAN_FREE:"Акысыз",         PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "hy": {PLAN_FREE:"Անվճար",        PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "ka": {PLAN_FREE:"უფასო",          PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "ce": {PLAN_FREE:"Биллийнан",      PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "en": {PLAN_FREE:"Free",           PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},

    # New
    "es": {PLAN_FREE:"Gratis",         PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "de": {PLAN_FREE:"Kostenlos",      PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "pl": {PLAN_FREE:"Darmowy",        PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
    "fr": {PLAN_FREE:"Gratuit",        PLAN_PLUS:"Mindra+", PLAN_PRO:"Mindra Pro"},
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
        "tracker_unlimited": True,
        "reminders_unlimited": True,
    },
}

# ==== QUOTAS (числовые лимиты по планам) ====
QUOTAS = {
    PLAN_FREE: {
        "daily_messages": 10,   # хватит «познакомиться», но быстро кончится
        "goals_max": 3,
        "habits_max": 3,
        "reminders_active": 3,  # одновременно активных
        "reminders_max": 3,     # если где-то считаешь общее число
        "sleep_max_minutes": 15,
        "story_max_paras": 4,   # короткие истории
        "eleven_daily_seconds": 0,
    },
    PLAN_PLUS: {
        "daily_messages": 50,    # 0 → без лимита
        "goals_max": 10,
        "habits_max": 10,
        "reminders_active": 10,
        "reminders_max": 10,
        "sleep_max_minutes": 60,
        "story_max_paras": 8,   # medium
        "eleven_daily_seconds": 10 * 60,
    },
    PLAN_PRO: {
        # «почти безлимит», но оставим технический потолок, чтобы себя защитить
        "daily_messages": 0,  # для пользователя это ≈безлим
        "goals_max": 0,
        "habits_max": 0,
        "reminders_active": 0,
        "reminders_max": 0,
        "sleep_max_minutes": 0,
        "story_max_paras": 12,  # long
        "eleven_daily_seconds": 0,
    },
}

SLEEP_UI_TEXTS = {
    "es": {
        "title": "😴 Sonidos para dormir",
        "sound": "Sonido: *{sound}*",
        "duration": "Duración: *{min} min*",
        "gain": "Volumen: *{db} dB*",
        "pick_sound": "Sonido",
        "pick_duration": "Tiempo",
        "pick_gain": "Volumen",
        "start": "▶️ Iniciar",
        "stop": "⏹ Detener",
        "started": "Reproduzco el sonido *{sound}* durante *{min} min*… Que descanses 🌙",
        "stopped": "Listo, detenido.",
        "err_ffmpeg": "No se encontró ffmpeg — no puedo preparar el audio.",
        "err_missing": "Archivo de sonido no encontrado. Revisa la ruta en BGM_PRESETS.",
    },
    "de": {
        "title": "😴 Einschlafklänge",
        "sound": "Klang: *{sound}*",
        "duration": "Dauer: *{min} Min*",
        "gain": "Lautstärke: *{db} dB*",
        "pick_sound": "Klang",
        "pick_duration": "Zeit",
        "pick_gain": "Lautstärke",
        "start": "▶️ Starten",
        "stop": "⏹ Stopp",
        "started": "Starte *{sound}* für *{min} Min*… Schlaf gut 🌙",
        "stopped": "Okay, gestoppt.",
        "err_ffmpeg": "ffmpeg nicht gefunden — Audio kann nicht vorbereitet werden.",
        "err_missing": "Audiodatei nicht gefunden. Prüfe den Pfad in BGM_PRESETS.",
    },
    "pl": {
        "title": "😴 Dźwięki do snu",
        "sound": "Dźwięk: *{sound}*",
        "duration": "Czas: *{min} min*",
        "gain": "Głośność: *{db} dB*",
        "pick_sound": "Dźwięk",
        "pick_duration": "Czas",
        "pick_gain": "Głośność",
        "start": "▶️ Start",
        "stop": "⏹ Stop",
        "started": "Uruchamiam *{sound}* na *{min} min*… Miłego odpoczynku 🌙",
        "stopped": "Okej, zatrzymałem.",
        "err_ffmpeg": "Nie znaleziono ffmpeg — nie mogę przygotować audio.",
        "err_missing": "Nie znaleziono pliku dźwięku. Sprawdź ścieżkę w BGM_PRESETS.",
    },
    "fr": {
        "title": "😴 Sons pour dormir",
        "sound": "Son : *{sound}*",
        "duration": "Durée : *{min} min*",
        "gain": "Volume : *{db} dB*",
        "pick_sound": "Son",
        "pick_duration": "Durée",
        "pick_gain": "Volume",
        "start": "▶️ Lancer",
        "stop": "⏹ Arrêter",
        "started": "Je lance *{sound}* pendant *{min} min*… Bonne détente 🌙",
        "stopped": "D’accord, arrêté.",
        "err_ffmpeg": "ffmpeg introuvable — impossible de préparer l’audio.",
        "err_missing": "Fichier audio introuvable. Vérifie le chemin dans BGM_PRESETS.",
    },
    "ru": {
        "title": "😴 Звуки для сна",
        "sound": "Звук: *{sound}*",
        "duration": "Длительность: *{min} мин*",
        "gain": "Громкость: *{db} dB*",
        "pick_sound":"Звук",
        "pick_duration":"Время",
        "pick_gain":"Громкость",
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
        "pick_sound":"Звук",
        "pick_duration":"Час",
        "pick_gain":"Гучн.",
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
        "pick_sound":"Sunet",
        "pick_duration":"Durată",
        "pick_gain":"Volum",
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
        "pick_sound":"Гук",
        "pick_duration":"Час",
        "pick_gain":"Гучн.",
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
        "pick_sound":"Дыбыс",
        "pick_duration":"Уақыты",
        "pick_gain":"Көлем",
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
        "pick_sound":"Үн",
        "pick_duration":"Убакыт",
        "pick_gain":"Деңгээл",
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
        "pick_sound":"Ձայն",
        "pick_duration":"Ժամ.",
        "pick_gain":"Ծավալ",
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
        "pick_sound":"ხმა",
        "pick_duration":"დრო",
        "pick_gain":"დონე",
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
        "pick_sound":"Хьалха",
        "pick_duration":"Хатта",
        "pick_gain":"Лела",
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
        "pick_sound":"Sound",
        "pick_duration":"Time",
        "pick_gain":"Volume",
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
    "es": {
        "title": "🎙 Ajustes de voz",
        "engine": "Motor: *{engine}*",
        "voice": "Voz: *{voice}*",
        "speed": "Velocidad: *{speed}x*",
        "voice_only": "Solo voz: *{v}*",
        "auto_story": "Narración automática de cuentos: *{v}*",
        "on": "activado", "off": "desactivado",
        "mode_on_btn": "🔊 Activar",
        "mode_off_btn": "🔇 Desactivar",
        "btn_engine": "⚙️ Motor",
        "btn_voice": "🗣 Voz",
        "btn_speed": "⏱ Velocidad",
        "btn_beh": "🎛 Comportamiento",
        "btn_bg": "🎧 Fondo",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Elige una voz:",
        "no_eleven_key": "⚠️ Falta la clave de ElevenLabs — solo está disponible gTTS.",
        "bgm": "Fondo: *{bg}* ({db} dB)",
    },
    "de": {
        "title": "🎙 Stimmeinstellungen",
        "engine": "Engine: *{engine}*",
        "voice": "Stimme: *{voice}*",
        "speed": "Geschwindigkeit: *{speed}x*",
        "voice_only": "Nur Stimme: *{v}*",
        "auto_story": "Automatische Märchenvertonung: *{v}*",
        "on": "an", "off": "aus",
        "mode_on_btn": "🔊 Aktivieren",
        "mode_off_btn": "🔇 Deaktivieren",
        "btn_engine": "⚙️ Engine",
        "btn_voice": "🗣 Stimme",
        "btn_speed": "⏱ Geschwindigkeit",
        "btn_beh": "🎛 Verhalten",
        "btn_bg": "🎧 Hintergrund",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Wähle eine Stimme:",
        "no_eleven_key": "⚠️ ElevenLabs-Schlüssel nicht gefunden — nur gTTS verfügbar.",
        "bgm": "Hintergrund: *{bg}* ({db} dB)",
    },
    "pl": {
        "title": "🎙 Ustawienia głosu",
        "engine": "Silnik: *{engine}*",
        "voice": "Głos: *{voice}*",
        "speed": "Prędkość: *{speed}x*",
        "voice_only": "Tylko głos: *{v}*",
        "auto_story": "Automatyczne czytanie bajek: *{v}*",
        "on": "wł.", "off": "wył.",
        "mode_on_btn": "🔊 Włączyć",
        "mode_off_btn": "🔇 Wyłączyć",
        "btn_engine": "⚙️ Silnik",
        "btn_voice": "🗣 Głos",
        "btn_speed": "⏱ Prędkość",
        "btn_beh": "🎛 Zachowanie",
        "btn_bg": "🎧 Tło",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Wybierz głos:",
        "no_eleven_key": "⚠️ Nie znaleziono klucza ElevenLabs — dostępny jest tylko gTTS.",
        "bgm": "Tło: *{bg}* ({db} dB)",
    },
    "fr": {
        "title": "🎙 Réglages de la voix",
        "engine": "Moteur : *{engine}*",
        "voice": "Voix : *{voice}*",
        "speed": "Vitesse : *{speed}x*",
        "voice_only": "Voix seule : *{v}*",
        "auto_story": "Narration automatique des contes : *{v}*",
        "on": "activé", "off": "désactivé",
        "mode_on_btn": "🔊 Activer",
        "mode_off_btn": "🔇 Désactiver",
        "btn_engine": "⚙️ Moteur",
        "btn_voice": "🗣 Voix",
        "btn_speed": "⏱ Vitesse",
        "btn_beh": "🎛 Comportement",
        "btn_bg": "🎧 Fond",
        "engine_eleven": "ElevenLabs",
        "engine_gtts": "gTTS",
        "pick_voice": "Choisis une voix :",
        "no_eleven_key": "⚠️ Clé ElevenLabs introuvable — seul gTTS est disponible.",
        "bgm": "Fond : *{bg}* ({db} dB)",
    },
    "ru": {
        "title": "🎙 Настройки голоса",
        "engine": "Движок: *{engine}*",
        "voice": "Голос: *{voice}*",
        "speed": "Скорость: *{speed}x*",
        "voice_only": "Только голос: *{v}*",
        "auto_story": "Авто-озвучка сказок: *{v}*",
        "on": "вкл", "off": "выкл",
        "mode_on_btn": "🔊 Включить",
        "mode_off_btn": "🔇 Выключить",
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
        "mode_on_btn": "🔊 Увімкнути",
        "mode_off_btn": "🔇 Вимкнути",
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
        "mode_on_btn": "🔊 Pornește",
        "mode_off_btn": "🔇 Oprește",
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
        "mode_on_btn": "🔊 Уключыць",
        "mode_off_btn": "🔇 Выключыць",
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
        "mode_on_btn": "🔊 Қосу",
        "mode_off_btn": "🔇 Өшіру",
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
        "mode_on_btn": "🔊 Күйгүз",
        "mode_off_btn": "🔇 Өчүр",
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
        "mode_on_btn": "🔊 Միացնել",
        "mode_off_btn": "🔇 Անջատել",
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
        "mode_on_btn": "🔊 ჩართვა",
        "mode_off_btn": "🔇 გამორთვა",
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
        "mode_on_btn": "🔊 Вкл",
        "mode_off_btn": "🔇 Выкл",
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
        "mode_on_btn": "🔊 Enable",
        "mode_off_btn": "🔇 Disable",
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

ELEVEN_LIMIT_INFO_TEXTS = {
    "ru": "{plus} — до 240 минут ElevenLabs в месяц.\n{pro} — без ограничений ElevenLabs.",
    "uk": "{plus} — до 240 хв ElevenLabs на місяць.\n{pro} — без обмежень ElevenLabs.",
    "en": "{plus}: up to 240 min/month of ElevenLabs.\n{pro}: unlimited ElevenLabs.",
    "md": "{plus}: până la 240 de minute ElevenLabs pe lună.\n{pro}: ElevenLabs nelimitat.",
    "be": "{plus} — да 240 хвілін ElevenLabs у месяц.\n{pro} — без абмежаванняў ElevenLabs.",
    "kk": "{plus} — ElevenLabs айына 240 минутқа дейін.\n{pro} — ElevenLabs шектеусіз.",
    "kg": "{plus} — ElevenLabs айына 240 мүнөткө чейин.\n{pro} — ElevenLabs чексиз.",
    "hy": "{plus} — ElevenLabs՝ ամսական մինչև 240 րոպե.\n{pro} — ElevenLabs առանց սահմանափակման.",
    "ka": "{plus} — თვეში მაქსიმუმ 240 წუთი ElevenLabs.\n{pro} — ElevenLabs შეზღუდვების გარეშე.",
    "ce": "{plus} — ElevenLabs 240 минут/йиш кхечу.\n{pro} — ElevenLabs без лимита.",
    # ELEVEN_LIMIT_INFO_TEXTS — новые языки
    "es": "{plus}: hasta 240 min/mes de ElevenLabs.\n{pro}: ElevenLabs sin límites.",
    "de": "{plus}: bis zu 240 Min./Monat ElevenLabs.\n{pro}: ElevenLabs ohne Begrenzung.",
    "pl": "{plus}: do 240 min/mies. ElevenLabs.\n{pro}: ElevenLabs bez limitu.",
    "fr": "{plus} : jusqu’à 240 min/mois d’ElevenLabs.\n{pro} : ElevenLabs illimité.",
}

ELEVEN_LIMIT_REACHED_TEXTS = {
    "ru": "⚠️ Лимит ElevenLabs в {plus} — 240 минут в месяц. {pro} даёт безлимит.",
    "uk": "⚠️ Ліміт ElevenLabs у {plus} — 240 хв на місяць. {pro} — без обмежень.",
    "en": "⚠️ ElevenLabs on {plus} is limited to 240 min per month. {pro} is unlimited.",
    "md": "⚠️ În {plus}, ElevenLabs este limitat la 240 de minute pe lună. {pro} este nelimitat.",
    "be": "⚠️ Ліміт ElevenLabs у {plus} — 240 хвілін у месяц. {pro} — без абмежаванняў.",
    "kk": "⚠️ {plus} жоспарында ElevenLabs айына 240 минутпен шектеледі. {pro} — шектеусіз.",
    "kg": "⚠️ {plus} тарифинде ElevenLabs айына 240 мүнөт менен чектелет. {pro} — чексиз.",
    "hy": "⚠️ {plus}-ում ElevenLabs-ը սահմանափակվում է ամսական 240 րոպեով, {pro}-ում՝ առանց սահմանափակման.",
    "ka": "⚠️ {plus}-ში ElevenLabs თვეში 240 წუთით არის შეზღუდული. {pro} — შეზღუდვების გარეშე.",
    "ce": "⚠️ {plus}-да ElevenLabs 240 минут йиш хьоца. {pro}-да — без лимита.",
    # ELEVEN_LIMIT_REACHED_TEXTS — новые языки
    "es": "⚠️ En {plus}, ElevenLabs está limitado a 240 min/mes. {pro} es ilimitado.",
    "de": "⚠️ In {plus} ist ElevenLabs auf 240 Min. pro Monat begrenzt. {pro} ist unbegrenzt.",
    "pl": "⚠️ W {plus} ElevenLabs jest ograniczone do 240 min miesięcznie. {pro} jest nielimitowany.",
    "fr": "⚠️ Dans {plus}, ElevenLabs est limité à 240 min par mois. {pro} est illimité.",
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
    "es": [
        ("👩 Femenina (Eleven)",  "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Masculina (Eleven)", "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Femenina (gTTS)",    "gTTS",   ""),
    ],
    "de": [
        ("👩 Weiblich (Eleven)",  "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Männlich (Eleven)",  "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Weiblich (gTTS)",    "gTTS",   ""),
    ],
    "pl": [
        ("👩 Żeński (Eleven)",    "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Męski (Eleven)",     "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Żeński (gTTS)",      "gTTS",   ""),
    ],
    "fr": [
        ("👩 Féminin (Eleven)",   "eleven", DEFAULT_ELEVEN_FEMALE),
        ("👨 Masculin (Eleven)",  "eleven", DEFAULT_ELEVEN_MALE),
        ("👩 Féminin (gTTS)",     "gTTS",   ""),
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
    # STORY_INTENT — новые языки
    "es": ["cuento","historia","historia para dormir","de buenas noches",
           "cuéntame un cuento","cuento de hadas","relato"],
    "de": ["geschichte","märchen","gute-nacht-geschichte","schlafenszeit",
           "erzähl mir eine geschichte","märchen erzählen"],
    "pl": ["bajka","opowieść","baśń","na dobranoc","opowiedz bajkę","opowiedz historię"],
    "fr": ["histoire","conte","conte de fées","histoire du soir",
           "raconte une histoire","histoire pour dormir"],
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
    # STORY_TEXTS — новые языки
    "es": {
        "title": "📖 Cuento de Mindra",
        "usage": "Uso: `/story tema | nombre=Mila | longitud=corta|media|larga | voz=on`\nEj.: `/story espacio nombre=Mila voz=on`",
        "making": "✨ Estoy creando una historia…",
        "ready": "¡Listo! ¿Quieres otra?",
        "btn_more": "🎲 Otra",
        "btn_voice": "🔊 Con voz",
        "btn_close": "✖️ Cerrar",
        "suggest": "¿Quieres que invente un cuento sobre este tema y te lo cuente?",
        "btn_ok": "✅ Sí",
        "btn_no": "❌ No",
    },
    "de": {
        "title": "📖 Geschichte von Mindra",
        "usage": "Benutzung: `/story thema | name=Mila | länge=kurz|mittel|lang | stimme=on`\nZ. B.: `/story weltraum name=Mila stimme=on`",
        "making": "✨ Ich erfinde eine Geschichte…",
        "ready": "Fertig! Möchtest du noch eine?",
        "btn_more": "🎲 Noch eine",
        "btn_voice": "🔊 Mit Stimme",
        "btn_close": "✖️ Schließen",
        "suggest": "Soll ich zu diesem Thema eine Geschichte erfinden und erzählen?",
        "btn_ok": "✅ Ja",
        "btn_no": "❌ Nein",
    },
    "pl": {
        "title": "📖 Bajka od Mindry",
        "usage": "Użycie: `/story temat | imię=Mila | długość=krótka|średnia|długa | głos=on`\nNp.: `/story kosmos imię=Mila głos=on`",
        "making": "✨ Wymyślam historię…",
        "ready": "Gotowe! Chcesz jeszcze jedną?",
        "btn_more": "🎲 Jeszcze jedną",
        "btn_voice": "🔊 Głosem",
        "btn_close": "✖️ Zamknij",
        "suggest": "Chcesz, żebym wymyślił bajkę na ten temat i ją opowiedział?",
        "btn_ok": "✅ Tak",
        "btn_no": "❌ Nie",
    },
    "fr": {
        "title": "📖 Conte de Mindra",
        "usage": "Utilisation : `/story thème | nom=Mila | longueur=courte|moyenne|longue | voix=on`\nEx. : `/story espace nom=Mila voix=on`",
        "making": "✨ J’imagine une histoire…",
        "ready": "C’est prêt ! Tu en veux une autre ?",
        "btn_more": "🎲 Encore",
        "btn_voice": "🔊 À voix haute",
        "btn_close": "✖️ Fermer",
        "suggest": "Veux-tu que j’invente un conte sur ce thème et te le raconte ?",
        "btn_ok": "✅ Oui",
        "btn_no": "❌ Non",
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
    "es": {
      "on":   "🔊 Modo de voz activado. Enviaré las respuestas con voz.",
      "off":  "🔇 Modo de voz desactivado.",
      "help": "Uso: /voice_mode on|off",
      "err":  "⚠️ Indica on|off. Ejemplo: /voice_mode on",
    },
    "de": {
      "on":   "🔊 Sprachmodus aktiviert. Ich sende Antworten mit Stimme.",
      "off":  "🔇 Sprachmodus deaktiviert.",
      "help": "Verwendung: /voice_mode on|off",
      "err":  "⚠️ Gib on|off an. Beispiel: /voice_mode on",
    },
    "pl": {
      "on":   "🔊 Tryb głosowy włączony. Będę wysyłać odpowiedzi głosem.",
      "off":  "🔇 Tryb głosowy wyłączony.",
      "help": "Użycie: /voice_mode on|off",
      "err":  "⚠️ Podaj on|off. Przykład: /voice_mode on",
    },
    "fr": {
      "on":   "🔊 Mode vocal activé. J’enverrai les réponses en audio.",
      "off":  "🔇 Mode vocal désactivé.",
      "help": "Utilisation : /voice_mode on|off",
      "err":  "⚠️ Indique on|off. Exemple : /voice_mode on",
    },
}

CHALLENGE_BANK = {
    "en": [
      "Workout 4/7",
      "Workout 5/7",
      "Workout 6/7",
      "Sleep by 23:00 ×4",
      "Read 20 min ×4",
      "Read 30 min ×3",
      "Read 40 min ×3",
      "No sugar 4 days",
      "No sugar 3 days",
      "No sugar 5 days",
      "6k steps ×4",
      "7k steps ×3",
      "8k steps ×3",
      "9k steps ×5",
      "10k steps ×3",
      "Meditate 5 min ×3",
      "Meditate 10 min ×3",
      "Meditate 15 min ×4",
      "Journal 5 lines ×4",
      "Journal 5 lines ×3",
      "Wake up by 07:00 ×5",
      "Screen-free 30 min before bed ×4",
      "Cold shower ×3",
      "Cold shower ×5",
      "Stretch 10 min ×3",
      "Stretch 10 min ×5",
      "Gratitude: 3 things ×3",
      "Gratitude: 3 things ×4",
      "Gratitude: 3 things ×5",
      "Plan tomorrow tonight ×5",
      "Plan tomorrow tonight ×3",
      "No social apps 1h after wake ×3",
      "No social apps 1h after wake ×4",
      "No social apps 1h after wake ×5",
      "Protein with every meal ×3",
      "Protein with every meal ×5",
      "Vegetables 2 servings ×3",
      "Vegetables 2 servings ×5",
      "Drink 6 glasses of water ×5",
      "Drink 8 glasses of water ×3",
      "Drink 10 glasses of water ×5",
      "Push-ups 20 ×4",
      "Push-ups 25 ×3",
      "Push-ups 30 ×5",
      "Push-ups 40 ×4",
      "Plank 30s ×3",
      "Plank 45s ×4",
      "Plank 60s ×4",
      "Plank 90s ×5",
      "Morning sunlight 10 min ×3",
      "Morning sunlight 15 min ×5",
      "Walk outside 20 min ×3",
      "Walk outside 30 min ×3",
      "Breathing 4-7-8 ×4",
      "Breathing box 4×4 ×5",
      "3 Pomodoros focus ×3",
      "3 Pomodoros focus ×4",
      "Declutter 5 items ×4",
      "Declutter 10 items ×5",
      "Declutter 15 items ×5",
      "No caffeine after 3pm ×5",
      "No caffeine after 3pm ×3",
      "In bed by 23:00 ×4",
      "In bed by 23:00 ×5",
      "No food 3h before bed ×4",
      "No food 3h before bed ×5",
      "Call a friend/family ×3",
      "Call a friend/family ×5",
      "Learn for 20 min ×5",
      "Learn for 20 min ×4",
      "Posture check every hour ×3",
      "Posture check every hour ×4",
      "Posture check every hour ×5",
      "Workout 4/7",
      "Workout 5/7",
      "Workout 6/7",
      "Sleep by 23:00 ×4",
      "Read 20 min ×4",
      "Read 30 min ×3",
      "Read 40 min ×3"
    ],
    "ru": [
      "Тренировка 4/7",
      "Тренировка 5/7",
      "Тренировка 6/7",
      "Ко сну до 23:00 ×4",
      "Ко сну до 22:30 ×4",
      "Чтение 20 мин ×4",
      "Чтение 30 мин ×3",
      "Чтение 40 мин ×3",
      "Без сахара 4 дня",
      "Без сахара 3 дня",
      "6000 шагов ×4",
      "7000 шагов ×5",
      "8000 шагов ×5",
      "9000 шагов ×5",
      "10000 шагов ×3",
      "Медитация 5 мин ×3",
      "Медитация 10 мин ×3",
      "Медитация 15 мин ×5",
      "Дневник: 5 строк ×3",
      "Дневник: 5 строк ×5",
      "Подъём до 08:00 ×3",
      "Без экрана за 30 мин до сна ×4",
      "Холодный душ ×5",
      "Холодный душ ×3",
      "Холодный душ ×4",
      "Растяжка 10 мин ×4",
      "Растяжка 10 мин ×3",
      "Благодарности: 3 пункта ×4",
      "Благодарности: 3 пункта ×5",
      "План на завтра вечером ×5",
      "План на завтра вечером ×3",
      "Без соцсетей 1ч после подъёма ×5",
      "Без соцсетей 1ч после подъёма ×3",
      "Без соцсетей 1ч после подъёма ×4",
      "Белок в каждом приёме пищи ×4",
      "Белок в каждом приёме пищи ×5",
      "Белок в каждом приёме пищи ×3",
      "Овощи 2 порции ×5",
      "Вода: 6 стаканов ×5",
      "Вода: 8 стаканов ×5",
      "Вода: 10 стаканов ×4",
      "Отжимания 20 ×4",
      "Отжимания 25 ×3",
      "Отжимания 30 ×5",
      "Отжимания 40 ×3",
      "Планка 30 с ×3",
      "Планка 45 с ×4",
      "Планка 60 с ×5",
      "Планка 90 с ×4",
      "Утреннее солнце 10 мин ×5",
      "Утреннее солнце 15 мин ×4",
      "Прогулка 20 мин ×4",
      "Прогулка 30 мин ×4",
      "Дыхание 4-7-8 ×3",
      "Дыхание box 4×4 ×4",
      "3 сессии помодоро ×3",
      "3 сессии помодоро ×5",
      "Разбор 5 вещей ×3",
      "Разбор 10 вещей ×4",
      "Разбор 15 вещей ×3",
      "Без кофеина после 15:00 ×3",
      "Без кофеина после 15:00 ×4",
      "В кровати до 22:30 ×4",
      "В кровати до 23:00 ×5",
      "Без еды за 3ч до сна ×3",
      "Без еды за 3ч до сна ×5",
      "Без еды за 3ч до сна ×4",
      "Позвонить другу/родным ×5",
      "Позвонить другу/родным ×4",
      "Позвонить другу/родным ×3",
      "Учёба 20 мин ×4",
      "Учёба 20 мин ×3",
      "Осадка спины каждый час ×4",
      "Осадка спины каждый час ×5",
      "Тренировка 4/7",
      "Тренировка 5/7",
      "Тренировка 6/7",
      "Ко сну до 23:00 ×4",
      "Ко сну до 22:30 ×4",
      "Чтение 20 мин ×4"
    ],
    "uk": [
      "Тренування 4/7",
      "Тренування 5/7",
      "Тренування 6/7",
      "Сон до 22:30 ×3",
      "Сон до 23:00 ×5",
      "Читання 20 хв ×5",
      "Читання 30 хв ×4",
      "Читання 40 хв ×3",
      "Без цукру 3 дні",
      "Без цукру 5 дні",
      "6000 кроків ×5",
      "7000 кроків ×4",
      "8000 кроків ×3",
      "9000 кроків ×4",
      "10000 кроків ×3",
      "Медитація 5 хв ×5",
      "Медитація 10 хв ×5",
      "Медитація 15 хв ×4",
      "Щоденник: 5 рядків ×5",
      "Підйом до 08:00 ×4",
      "Без екрана за 30 хв до сну ×5",
      "Без екрана за 30 хв до сну ×4",
      "Холодний душ ×3",
      "Холодний душ ×5",
      "Розтяжка 10 хв ×4",
      "Розтяжка 10 хв ×3",
      "Подяка: 3 пункти ×3",
      "План на завтра ввечері ×4",
      "План на завтра ввечері ×5",
      "План на завтра ввечері ×3",
      "Без соцмереж 1 год після підйому ×3",
      "Без соцмереж 1 год після підйому ×5",
      "Білок у кожному прийомі їжі ×3",
      "Білок у кожному прийомі їжі ×5",
      "Овочі 2 порції ×5",
      "Овочі 2 порції ×4",
      "Вода: 6 склянок ×3",
      "Вода: 8 склянок ×5",
      "Вода: 10 склянок ×5",
      "Віджимання 20 ×4",
      "Віджимання 25 ×4",
      "Віджимання 30 ×3",
      "Віджимання 40 ×3",
      "Планка 30 с ×3",
      "Планка 45 с ×3",
      "Планка 60 с ×5",
      "Планка 90 с ×5",
      "Ранкове сонце 10 хв ×5",
      "Ранкове сонце 15 хв ×5",
      "Прогулянка 20 хв ×3",
      "Прогулянка 30 хв ×5",
      "Дихання 4-7-8 ×3",
      "Дихання box 4×4 ×3",
      "3 сесії помодоро ×5",
      "3 сесії помодоро ×3",
      "Розбір 5 речей ×5",
      "Розбір 10 речей ×4",
      "Розбір 15 речей ×5",
      "Без кофеїну після 15:00 ×5",
      "Без кофеїну після 15:00 ×3",
      "В ліжку до 22:30 ×3",
      "В ліжку до 23:00 ×4",
      "Без їжі за 3 год до сну ×3",
      "Без їжі за 3 год до сну ×4",
      "Зателефонувати другові/рідним ×5",
      "Навчання 20 хв ×3",
      "Навчання 20 хв ×4",
      "Постава — перевірка щогодини ×4",
      "Постава — перевірка щогодини ×3",
      "Тренування 4/7",
      "Тренування 5/7",
      "Тренування 6/7",
      "Сон до 22:30 ×3",
      "Сон до 23:00 ×5",
      "Читання 20 хв ×5",
      "Читання 30 хв ×4",
      "Читання 40 хв ×3",
      "Без цукру 3 дні",
      "Без цукру 5 дні",
      "6000 кроків ×5"
    ],
    "ka": [
      "ვარჯიში 4/7",
      "ვარჯიში 5/7",
      "ვარჯიში 6/7",
      "ძილი 22:30-მდე ×5",
      "ძილი 22:30-მდე ×4",
      "კითხვა 20 წთ ×4",
      "კითხვა 30 წთ ×5",
      "კითხვა 40 წთ ×5",
      "შაქრის გარეშე 3 დღე",
      "შაქრის გარეშე 4 დღე",
      "6000 ნაბიჯი ×3",
      "7000 ნაბიჯი ×3",
      "8000 ნაბიჯი ×3",
      "9000 ნაბიჯი ×3",
      "10000 ნაბიჯი ×4",
      "მედიტაცია 5 წთ ×4",
      "მედიტაცია 10 წთ ×4",
      "მედიტაცია 15 წთ ×4",
      "ჟურნალი: 5 სტრიქონი ×4",
      "ჟურნალი: 5 სტრიქონი ×5",
      "გაღვიძება 07:00-მდე ×4",
      "გაღვიძება 08:00-მდე ×3",
      "ეკრანის გარეშე ძილის წინ 30 წთ ×4",
      "ეკრანის გარეშე ძილის წინ 30 წთ ×3",
      "ცივი შხაპი ×3",
      "ცივი შხაპი ×4",
      "გაწელვა 10 წთ ×3",
      "გაწელვა 10 წთ ×5",
      "მადლიერება: 3 რამ ×4",
      "ხვალის გეგმა საღამოს ×5",
      "სოციალური აპები არა 1ს გაღვიძების შემდეგ ×3",
      "ცილა ყოველი კვება ×5",
      "ცილა ყოველი კვება ×4",
      "ბოსტნეული 2 პორცია ×3",
      "ბოსტნეული 2 პორცია ×5",
      "წყალი: 6 ჭიქა ×5",
      "წყალი: 8 ჭიქა ×3",
      "წყალი: 10 ჭიქა ×3",
      "დათვირა 20 ×4",
      "დათვირა 25 ×5",
      "დათვირა 30 ×5",
      "დათვირა 40 ×4",
      "პლანკა 30 წმ ×5",
      "პლანკა 45 წმ ×3",
      "პლანკა 60 წმ ×4",
      "პლანკა 90 წმ ×3",
      "დილის მზე 10 წთ ×5",
      "დილის მზე 15 წთ ×4",
      "გასეირნება 20 წთ ×5",
      "გასეირნება 30 წთ ×5",
      "სუნთქვა 4-7-8 ×4",
      "სუნთქვა box 4×4 ×4",
      "3 პომოდორო სესია ×3",
      "3 პომოდორო სესია ×4",
      "დალაგება 5 ნივთი ×3",
      "დალაგება 10 ნივთი ×4",
      "დალაგება 15 ნივთი ×3",
      "კოფეინი არა 15:00-ს შემდეგ ×3",
      "კოფეინი არა 15:00-ს შემდეგ ×5",
      "საწოლში 22:30-მდე ×5",
      "საწოლში 22:30-მდე ×3",
      "ჭამა არა ძილის წინ 3ს ×5",
      "ჭამა არა ძილის წინ 3ს ×3",
      "ჭამა არა ძილის წინ 3ს ×4",
      "მეილი/დარეკე მეგობარს ×5",
      "სწავლა 20 წთ ×5",
      "სწავლა 20 წთ ×4",
      "სწავლა 20 წთ ×3",
      "მდგომარეობა — შემოწმება საათში ერთხელ ×4",
      "მდგომარეობა — შემოწმება საათში ერთხელ ×3",
      "ვარჯიში 4/7",
      "ვარჯიში 5/7",
      "ვარჯიში 6/7",
      "ძილი 22:30-მდე ×5",
      "ძილი 22:30-მდე ×4",
      "კითხვა 20 წთ ×4",
      "კითხვა 30 წთ ×5",
      "კითხვა 40 წთ ×5",
      "შაქრის გარეშე 3 დღე",
      "შაქრის გარეშე 4 დღე"
    ],
    "kk": [
      "Жаттығу 4/7",
      "Жаттығу 5/7",
      "Жаттығу 6/7",
      "23:00-ге дейін ұйықтау ×3",
      "Оқу 20 мин ×5",
      "Оқу 30 мин ×3",
      "Оқу 40 мин ×5",
      "Қантсыз 3 күн",
      "6000 қадам ×4",
      "7000 қадам ×4",
      "8000 қадам ×3",
      "9000 қадам ×3",
      "10000 қадам ×4",
      "Медитация 5 мин ×3",
      "Медитация 10 мин ×4",
      "Медитация 15 мин ×5",
      "Күнделік: 5 жол ×5",
      "Күнделік: 5 жол ×4",
      "08:00-ге дейін ояну ×3",
      "07:00-ге дейін ояну ×4",
      "Ұйқы алдында 30 мин экрансыз ×3",
      "Салқын душ ×4",
      "Созылу 10 мин ×5",
      "Созылу 10 мин ×3",
      "Алғыс: 3 нәрсе ×5",
      "Алғыс: 3 нәрсе ×3",
      "Алғыс: 3 нәрсе ×4",
      "Ертеңгі жоспар кешке ×4",
      "Ертеңгі жоспар кешке ×5",
      "Әлеум. желі жоқ оянғаннан кейін 1 сағ ×4",
      "Әлеум. желі жоқ оянғаннан кейін 1 сағ ×5",
      "Әлеум. желі жоқ оянғаннан кейін 1 сағ ×3",
      "Әр тамақта ақуыз ×5",
      "Әр тамақта ақуыз ×3",
      "Көкөніс 2 порция ×3",
      "Көкөніс 2 порция ×5",
      "Су: 6 стақан ×4",
      "Су: 8 стақан ×4",
      "Су: 10 стақан ×5",
      "Жатып-тұрғы 20 ×3",
      "Жатып-тұрғы 25 ×4",
      "Жатып-тұрғы 30 ×4",
      "Жатып-тұрғы 40 ×4",
      "Планка 30 с ×4",
      "Планка 45 с ×3",
      "Планка 60 с ×3",
      "Планка 90 с ×5",
      "Таңғы күн 10 мин ×5",
      "Таңғы күн 15 мин ×5",
      "Серуен 20 мин ×4",
      "Серуен 30 мин ×4",
      "Тыныс 4-7-8 ×3",
      "Тыныс box 4×4 ×5",
      "3 помодоро сессия ×3",
      "3 помодоро сессия ×5",
      "Артық 5 заттан арылу ×5",
      "Артық 10 заттан арылу ×3",
      "Артық 15 заттан арылу ×4",
      "Кофеин жоқ 15:00-ден кейін ×4",
      "Төсекте 23:00-ге дейін ×4",
      "Төсекте 22:30-ге дейін ×3",
      "Ұйқыдан 3 сағ бұрын тамақ жоқ ×3",
      "Ұйқыдан 3 сағ бұрын тамақ жоқ ×5",
      "Ұйқыдан 3 сағ бұрын тамақ жоқ ×4",
      "Досыңа қоңырау шал ×5",
      "Досыңа қоңырау шал ×4",
      "Оқу/үйрену 20 мин ×4",
      "Оқу/үйрену 20 мин ×5",
      "Арқа түзуін тексеру ×3",
      "Арқа түзуін тексеру ×4",
      "Жаттығу 4/7",
      "Жаттығу 5/7",
      "Жаттығу 6/7",
      "23:00-ге дейін ұйықтау ×3",
      "Оқу 20 мин ×5",
      "Оқу 30 мин ×3",
      "Оқу 40 мин ×5",
      "Қантсыз 3 күн",
      "6000 қадам ×4",
      "7000 қадам ×4"
    ],
    "md": [
      "Exerciții 4/7",
      "Exerciții 5/7",
      "Exerciții 6/7",
      "Somn până la 23:00 ×5",
      "Somn până la 23:00 ×3",
      "Citit 20 min ×4",
      "Citit 30 min ×5",
      "Citit 40 min ×5",
      "Fără zahăr 3 zile",
      "Fără zahăr 4 zile",
      "Fără zahăr 5 zile",
      "6000 pași ×5",
      "7000 pași ×3",
      "8000 pași ×5",
      "9000 pași ×5",
      "10000 pași ×4",
      "Meditație 5 min ×4",
      "Meditație 10 min ×4",
      "Meditație 15 min ×4",
      "Jurnal: 5 rânduri ×3",
      "Jurnal: 5 rânduri ×5",
      "Jurnal: 5 rânduri ×4",
      "Trezire până la 08:00 ×5",
      "Trezire până la 07:00 ×4",
      "Fără ecran cu 30 min înainte de somn ×3",
      "Fără ecran cu 30 min înainte de somn ×5",
      "Duș rece ×3",
      "Duș rece ×5",
      "Duș rece ×4",
      "Stretching 10 min ×5",
      "Stretching 10 min ×3",
      "Recunoștință: 3 lucruri ×5",
      "Recunoștință: 3 lucruri ×3",
      "Recunoștință: 3 lucruri ×4",
      "Planul de mâine seara ×4",
      "Planul de mâine seara ×3",
      "Fără rețele 1h după trezire ×5",
      "Fără rețele 1h după trezire ×3",
      "Proteine la fiecare masă ×3",
      "Proteine la fiecare masă ×5",
      "Legume 2 porții ×5",
      "Apă: 6 pahare ×3",
      "Apă: 8 pahare ×4",
      "Apă: 10 pahare ×3",
      "Flotări 20 ×5",
      "Flotări 25 ×4",
      "Flotări 30 ×5",
      "Flotări 40 ×3",
      "Plank 30 s ×4",
      "Plank 45 s ×4",
      "Plank 60 s ×4",
      "Plank 90 s ×4",
      "Soare de dimineață 10 min ×4",
      "Soare de dimineață 15 min ×5",
      "Plimbare 20 min ×3",
      "Plimbare 30 min ×3",
      "Respirație 4-7-8 ×5",
      "Respirație box 4×4 ×5",
      "3 sesiuni Pomodoro ×4",
      "3 sesiuni Pomodoro ×3",
      "Decluttering 5 obiecte ×4",
      "Decluttering 10 obiecte ×3",
      "Decluttering 15 obiecte ×4",
      "Fără cofeină după 15:00 ×4",
      "Fără cofeină după 15:00 ×5",
      "La culcare până la 23:00 ×5",
      "La culcare până la 23:00 ×4",
      "Fără mâncare cu 3h înainte de somn ×3",
      "Fără mâncare cu 3h înainte de somn ×4",
      "Sună un prieten ×5",
      "Sună un prieten ×3",
      "Învățare 20 min ×3",
      "Învățare 20 min ×4",
      "Verifică postura la fiecare oră ×5",
      "Verifică postura la fiecare oră ×4",
      "Exerciții 4/7",
      "Exerciții 5/7",
      "Exerciții 6/7",
      "Somn până la 23:00 ×5",
      "Somn până la 23:00 ×3"
    ],
    "hy": [
      "Մարզում 4/7",
      "Մարզում 5/7",
      "Մարզում 6/7",
      "Քուն մինչև 22:30 ×3",
      "Քուն մինչև 22:30 ×5",
      "Կարդալ 20 րոպե ×3",
      "Կարդալ 30 րոպե ×3",
      "Կարդալ 40 րոպե ×3",
      "Առանց շաքարի 3 օր",
      "Առանց շաքարի 5 օր",
      "6000 քայլ ×4",
      "7000 քայլ ×4",
      "8000 քայլ ×4",
      "9000 քայլ ×3",
      "10000 քայլ ×5",
      "Մեդիտացիա 5 րոպե ×5",
      "Մեդիտացիա 10 րոպե ×4",
      "Մեդիտացիա 15 րոպե ×5",
      "Օրագիր՝ 5 տող ×3",
      "Օրագիր՝ 5 տող ×4",
      "Օրագիր՝ 5 տող ×5",
      "Արթնանալ մինչև 07:00 ×5",
      "Արթնանալ մինչև 07:00 ×4",
      "Առանց էկրանների քնից 30 ր առաջ ×5",
      "Առանց էկրանների քնից 30 ր առաջ ×3",
      "Առանց էկրանների քնից 30 ր առաջ ×4",
      "Սառը ցնցուղ ×3",
      "Սառը ցնցուղ ×4",
      "Ձգումներ 10 րոպե ×3",
      "Ձգումներ 10 րոպե ×4",
      "Շնորհակալություն՝ 3 բան ×5",
      "Շնորհակալություն՝ 3 բան ×4",
      "Վաղվա պլանը երեկոյան ×5",
      "Առանց սոցցանցերի 1 ժ արթնանալուց հետո ×5",
      "Առանց սոցցանցերի 1 ժ արթնանալուց հետո ×4",
      "Սպիտակուց ամեն ուտելիս ×4",
      "Սպիտակուց ամեն ուտելիս ×3",
      "Բանջարեղեն 2 բաժին ×3",
      "Բանջարեղեն 2 բաժին ×4",
      "Ջուր՝ 6 բաժակ ×4",
      "Ջուր՝ 8 բաժակ ×3",
      "Ջուր՝ 10 բաժակ ×3",
      "Սեղմումներ 20 ×3",
      "Սեղմումներ 25 ×4",
      "Սեղմումներ 30 ×4",
      "Սեղմումներ 40 ×4",
      "Փլಾಂկ 30 վ ×3",
      "Փլಾಂկ 45 վ ×3",
      "Փլಾಂկ 60 վ ×4",
      "Փլಾಂկ 90 վ ×3",
      "Առավոտյան արև 10 ր ×3",
      "Առավոտյան արև 15 ր ×4",
      "Քայլք 20 ր ×4",
      "Քայլք 30 ր ×4",
      "Շնչառություն 4-7-8 ×4",
      "Շնչառություն box 4×4 ×5",
      "3 պոմոդորո սեսիա ×5",
      "3 պոմոդորո սեսիա ×4",
      "Ապրափակում 5 իր ×5",
      "Ապրափակում 10 իր ×4",
      "Ապրափակում 15 իր ×5",
      "Կոֆեին՝ ոչ 15:00-ից հետո ×4",
      "Կոֆեին՝ ոչ 15:00-ից հետո ×3",
      "Կոֆեին՝ ոչ 15:00-ից հետո ×5",
      "Մինչև 23:00 մահճամբարում ×4",
      "Մինչև 23:00 մահճամբարում ×5",
      "Սնունդ՝ ոչ քնից 3 ժ առաջ ×3",
      "Սնունդ՝ ոչ քնից 3 ժ առաջ ×5",
      "Զանգահարել ընկերոջը ×4",
      "Սովորել 20 ր ×4",
      "Սովորել 20 ր ×3",
      "Կեցվածք՝ ստուգել ամեն ժամ ×4",
      "Կեցվածք՝ ստուգել ամեն ժամ ×5",
      "Մարզում 4/7",
      "Մարզում 5/7",
      "Մարզում 6/7",
      "Քուն մինչև 22:30 ×3",
      "Քուն մինչև 22:30 ×5",
      "Կարդալ 20 րոպե ×3",
      "Կարդալ 30 րոպե ×3"
    ],
    "es": [
      "Entrenamiento 4/7",
      "Entrenamiento 5/7",
      "Entrenamiento 6/7",
      "Dormir antes de 23:00 ×5",
      "Leer 20 min ×5",
      "Leer 30 min ×4",
      "Leer 40 min ×5",
      "Sin azúcar 3 días",
      "Sin azúcar 5 días",
      "6000 pasos ×3",
      "7000 pasos ×4",
      "8000 pasos ×5",
      "9000 pasos ×4",
      "10000 pasos ×3",
      "Meditar 5 min ×5",
      "Meditar 10 min ×3",
      "Meditar 15 min ×4",
      "Diario: 5 líneas ×3",
      "Diario: 5 líneas ×4",
      "Levantarse antes de 07:00 ×4",
      "Levantarse antes de 07:00 ×5",
      "Sin pantallas 30 min antes de dormir ×5",
      "Sin pantallas 30 min antes de dormir ×3",
      "Sin pantallas 30 min antes de dormir ×4",
      "Ducha fría ×5",
      "Ducha fría ×3",
      "Estiramientos 10 min ×5",
      "Estiramientos 10 min ×4",
      "Gratitud: 3 cosas ×5",
      "Gratitud: 3 cosas ×4",
      "Plan de mañana por la noche ×4",
      "Sin redes 1h tras despertar ×5",
      "Sin redes 1h tras despertar ×3",
      "Proteína en cada comida ×3",
      "Proteína en cada comida ×5",
      "Proteína en cada comida ×4",
      "Verduras 2 raciones ×5",
      "Verduras 2 raciones ×4",
      "Agua: 6 vasos ×5",
      "Agua: 8 vasos ×4",
      "Agua: 10 vasos ×5",
      "Flexiones 20 ×3",
      "Flexiones 25 ×5",
      "Flexiones 30 ×5",
      "Flexiones 40 ×5",
      "Plancha 30 s ×3",
      "Plancha 45 s ×5",
      "Plancha 60 s ×4",
      "Plancha 90 s ×3",
      "Luz solar matinal 10 min ×4",
      "Luz solar matinal 15 min ×3",
      "Paseo 20 min ×3",
      "Paseo 30 min ×4",
      "Respiración 4-7-8 ×5",
      "Respiración box 4×4 ×5",
      "3 sesiones Pomodoro ×4",
      "3 sesiones Pomodoro ×3",
      "Ordenar 5 objetos ×5",
      "Ordenar 10 objetos ×4",
      "Ordenar 15 objetos ×4",
      "Sin cafeína después de 15:00 ×5",
      "Sin cafeína después de 15:00 ×4",
      "En cama antes de 23:00 ×3",
      "En cama antes de 22:30 ×5",
      "Sin comida 3h antes de dormir ×5",
      "Sin comida 3h antes de dormir ×4",
      "Llamar a un amigo/familia ×4",
      "Llamar a un amigo/familia ×3",
      "Llamar a un amigo/familia ×5",
      "Aprender 20 min ×5",
      "Aprender 20 min ×4",
      "Postura: revisar cada hora ×3",
      "Postura: revisar cada hora ×5",
      "Entrenamiento 4/7",
      "Entrenamiento 5/7",
      "Entrenamiento 6/7",
      "Dormir antes de 23:00 ×5",
      "Leer 20 min ×5",
      "Leer 30 min ×4",
      "Leer 40 min ×5"
    ],
    "de": [
      "Workout 4/7",
      "Workout 5/7",
      "Workout 6/7",
      "Schlaf bis 23:00 ×5",
      "Schlaf bis 22:30 ×4",
      "Lesen 20 Min ×4",
      "Lesen 30 Min ×4",
      "Lesen 40 Min ×4",
      "Kein Zucker 4 Tage",
      "Kein Zucker 3 Tage",
      "Kein Zucker 5 Tage",
      "6000 Schritte ×5",
      "7000 Schritte ×3",
      "8000 Schritte ×3",
      "9000 Schritte ×4",
      "10000 Schritte ×5",
      "Meditation 5 Min ×3",
      "Meditation 10 Min ×4",
      "Meditation 15 Min ×3",
      "Tagebuch: 5 Zeilen ×3",
      "Aufstehen bis 07:00 ×3",
      "Aufstehen bis 07:00 ×5",
      "30 Min ohne Bildschirm vor dem Schlafen ×4",
      "30 Min ohne Bildschirm vor dem Schlafen ×5",
      "Kaltdusche ×4",
      "Kaltdusche ×3",
      "Dehnen 10 Min ×3",
      "Dehnen 10 Min ×4",
      "Dehnen 10 Min ×5",
      "Dankbarkeit: 3 Dinge ×5",
      "Plan für morgen am Abend ×3",
      "Plan für morgen am Abend ×4",
      "Keine Social Apps 1h nach dem Aufstehen ×4",
      "Keine Social Apps 1h nach dem Aufstehen ×3",
      "Protein zu jeder Mahlzeit ×3",
      "Protein zu jeder Mahlzeit ×4",
      "Gemüse 2 Portionen ×4",
      "Wasser: 6 Gläser ×3",
      "Wasser: 8 Gläser ×5",
      "Wasser: 10 Gläser ×4",
      "Liegestütze 20 ×4",
      "Liegestütze 25 ×5",
      "Liegestütze 30 ×5",
      "Liegestütze 40 ×3",
      "Plank 30 s ×3",
      "Plank 45 s ×3",
      "Plank 60 s ×5",
      "Plank 90 s ×4",
      "Morgensonne 10 Min ×3",
      "Morgensonne 15 Min ×3",
      "Spaziergang 20 Min ×4",
      "Spaziergang 30 Min ×4",
      "Atmung 4-7-8 ×4",
      "Atmung box 4×4 ×3",
      "3 Pomodoro-Sessions ×4",
      "3 Pomodoro-Sessions ×3",
      "Entrümpeln 5 Dinge ×4",
      "Entrümpeln 10 Dinge ×3",
      "Entrümpeln 15 Dinge ×3",
      "Kein Koffein nach 15:00 ×3",
      "Kein Koffein nach 15:00 ×4",
      "Kein Koffein nach 15:00 ×5",
      "Im Bett bis 22:30 ×3",
      "Keine Mahlzeit 3h vor dem Schlaf ×5",
      "Keine Mahlzeit 3h vor dem Schlaf ×3",
      "Freund/Familie anrufen ×3",
      "Freund/Familie anrufen ×5",
      "20 Min lernen ×4",
      "20 Min lernen ×3",
      "20 Min lernen ×5",
      "Haltung stündlich prüfen ×3",
      "Haltung stündlich prüfen ×4",
      "Workout 4/7",
      "Workout 5/7",
      "Workout 6/7",
      "Schlaf bis 23:00 ×5",
      "Schlaf bis 22:30 ×4",
      "Lesen 20 Min ×4",
      "Lesen 30 Min ×4",
      "Lesen 40 Min ×4"
    ],
    "fr": [
      "Entraînement 4/7",
      "Entraînement 5/7",
      "Entraînement 6/7",
      "Au lit avant 23:00 ×3",
      "Au lit avant 22:30 ×3",
      "Lire 20 min ×5",
      "Lire 30 min ×5",
      "Lire 40 min ×5",
      "Sans sucre 3 jours",
      "Sans sucre 4 jours",
      "6000 pas ×3",
      "7000 pas ×5",
      "8000 pas ×3",
      "9000 pas ×3",
      "10000 pas ×5",
      "Méditer 5 min ×3",
      "Méditer 10 min ×3",
      "Méditer 15 min ×4",
      "Journal : 5 lignes ×4",
      "Journal : 5 lignes ×3",
      "Réveil avant 08:00 ×3",
      "Réveil avant 08:00 ×4",
      "30 min sans écran avant de dormir ×5",
      "30 min sans écran avant de dormir ×3",
      "Douche froide ×5",
      "Douche froide ×4",
      "Étirements 10 min ×3",
      "Étirements 10 min ×5",
      "Gratitude : 3 choses ×3",
      "Gratitude : 3 choses ×4",
      "Plan de demain le soir ×5",
      "Plan de demain le soir ×3",
      "Pas de réseaux 1h après le réveil ×3",
      "Pas de réseaux 1h après le réveil ×4",
      "Protéines à chaque repas ×5",
      "Protéines à chaque repas ×4",
      "Légumes 2 portions ×4",
      "Légumes 2 portions ×3",
      "Eau : 6 verres ×3",
      "Eau : 8 verres ×3",
      "Eau : 10 verres ×4",
      "Pompes 20 ×5",
      "Pompes 25 ×5",
      "Pompes 30 ×3",
      "Pompes 40 ×4",
      "Gainage 30 s ×4",
      "Gainage 45 s ×4",
      "Gainage 60 s ×5",
      "Gainage 90 s ×3",
      "Lumière du matin 10 min ×5",
      "Lumière du matin 15 min ×3",
      "Marche 20 min ×4",
      "Marche 30 min ×5",
      "Respiration 4-7-8 ×4",
      "Respiration box 4×4 ×4",
      "3 sessions Pomodoro ×4",
      "3 sessions Pomodoro ×3",
      "3 sessions Pomodoro ×5",
      "Désencombrer 5 objets ×3",
      "Désencombrer 10 objets ×3",
      "Désencombrer 15 objets ×3",
      "Pas de caféine après 15h ×3",
      "Pas de caféine après 15h ×5",
      "Pas de repas 3h avant le coucher ×3",
      "Pas de repas 3h avant le coucher ×5",
      "Appeler un ami/la famille ×4",
      "Appeler un ami/la famille ×3",
      "Apprendre 20 min ×3",
      "Apprendre 20 min ×5",
      "Posture : vérifier chaque heure ×4",
      "Posture : vérifier chaque heure ×3",
      "Posture : vérifier chaque heure ×5",
      "Entraînement 4/7",
      "Entraînement 5/7",
      "Entraînement 6/7",
      "Au lit avant 23:00 ×3",
      "Au lit avant 22:30 ×3",
      "Lire 20 min ×5",
      "Lire 30 min ×5",
      "Lire 40 min ×5"
    ],
    "pl": [
      "Trening 4/7",
      "Trening 5/7",
      "Trening 6/7",
      "Sen do 23:00 ×4",
      "Czytanie 20 min ×4",
      "Czytanie 30 min ×5",
      "Czytanie 40 min ×3",
      "Bez cukru 3 dni",
      "Bez cukru 4 dni",
      "Bez cukru 5 dni",
      "6000 kroków ×5",
      "7000 kroków ×5",
      "8000 kroków ×4",
      "9000 kroków ×4",
      "10000 kroków ×3",
      "Medytacja 5 min ×5",
      "Medytacja 10 min ×5",
      "Medytacja 15 min ×4",
      "Dziennik: 5 zdań ×3",
      "Dziennik: 5 zdań ×5",
      "Dziennik: 5 zdań ×4",
      "Pobudka do 07:00 ×4",
      "Pobudka do 08:00 ×4",
      "30 min bez ekranu przed snem ×5",
      "30 min bez ekranu przed snem ×3",
      "Zimny prysznic ×5",
      "Zimny prysznic ×3",
      "Zimny prysznic ×4",
      "Rozciąganie 10 min ×4",
      "Rozciąganie 10 min ×3",
      "Rozciąganie 10 min ×5",
      "Wdzięczność: 3 rzeczy ×3",
      "Plan na jutro wieczorem ×4",
      "Plan na jutro wieczorem ×5",
      "Bez sociali 1h po pobudce ×4",
      "Białko w każdym posiłku ×5",
      "Białko w każdym posiłku ×3",
      "Warzywa 2 porcje ×5",
      "Warzywa 2 porcje ×4",
      "Woda: 6 szklanki ×3",
      "Woda: 8 szklanki ×3",
      "Woda: 10 szklanki ×4",
      "Pompki 20 ×3",
      "Pompki 25 ×3",
      "Pompki 30 ×3",
      "Pompki 40 ×4",
      "Deska 30 s ×5",
      "Deska 45 s ×4",
      "Deska 60 s ×3",
      "Deska 90 s ×5",
      "Poranne słońce 10 min ×4",
      "Poranne słońce 15 min ×3",
      "Spacer 20 min ×4",
      "Spacer 30 min ×4",
      "Oddychanie 4-7-8 ×3",
      "Oddychanie box 4×4 ×5",
      "3 sesje pomodoro ×5",
      "3 sesje pomodoro ×4",
      "Odgracanie 5 rzeczy ×5",
      "Odgracanie 10 rzeczy ×4",
      "Odgracanie 15 rzeczy ×3",
      "Bez kofeiny po 15:00 ×3",
      "Bez kofeiny po 15:00 ×5",
      "W łóżku do 22:30 ×3",
      "W łóżku do 22:30 ×4",
      "Bez jedzenia 3h przed snem ×3",
      "Bez jedzenia 3h przed snem ×4",
      "Zadzwoń do przyjaciela/rodziny ×4",
      "Zadzwoń do przyjaciela/rodziny ×3",
      "Nauka 20 min ×3",
      "Nauka 20 min ×4",
      "Postawa — kontrola co godzinę ×3",
      "Postawa — kontrola co godzinę ×4",
      "Trening 4/7",
      "Trening 5/7",
      "Trening 6/7",
      "Sen do 23:00 ×4",
      "Czytanie 20 min ×4",
      "Czytanie 30 min ×5",
      "Czytanie 40 min ×3"
    ]
  }


P_TEXTS = {
    "ru": {
        "upsell_title": "💎 Mindra+/Pro",
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
    "es": {
    "upsell_title": "💎 Mindra+/Pro",
    "upsell_body":  "Recordatorios ilimitados, informes, desafíos y modo exclusivo.\nActiva Mindra+ y desbloquéalo todo 💜",
    "btn_get": "Obtener Mindra+",
    "btn_code": "Introducir código",
    "days_left": "💎 Tu Mindra+: quedan — *{days}* días",
    "no_plus": "Aún no tienes Mindra+. Las funciones gratuitas están disponibles 💜",
    "report_title": "📊 Tu informe de 7 días",
    "report_goals": "🎯 Metas completadas: *{n}*",
    "report_habits": "🌱 Hábitos marcados: *{n}*",
    "report_rems": "🔔 Recordatorios activados: *{n}*",
    "report_streak": "🔥 Días activos: *{n}*",
    "challenge_title": "🏆 Desafío semanal",
    "challenge_cta": "Tu reto para la semana:\n\n“{text}”",
    "btn_done": "✅ Listo",
    "btn_new": "🎲 Nuevo desafío",
    "challenge_done": "👏 ¡Genial! Desafío marcado como completado.",
    "mode_title": "🦄 Modo exclusivo activado",
    "mode_set": "Desde ahora responderé como tu coach personal de Mindra+ 💜",
    "stats_title": "📈 Estadísticas ampliadas",
    "stats_goals_done": "🎯 Metas completadas en total: *{n}*",
    "stats_habit_days": "🌱 Días con hábitos: *{n}*",
    "stats_active_days": "🔥 Días activos en 30d: *{n}*",
},
    "de": {
    "upsell_title": "💎 Mindra+/Pro",
    "upsell_body":  "Unbegrenzte Erinnerungen, Berichte, Challenges und der exklusive Modus.\nHol dir Mindra+ und schalte alles frei 💜",
    "btn_get": "Mindra+ holen",
    "btn_code": "Code eingeben",
    "days_left": "💎 Dein Mindra+: verbleibende Tage — *{days}*",
    "no_plus": "Du hast noch kein Mindra+. Kostenlose Funktionen sind verfügbar 💜",
    "report_title": "📊 Dein 7-Tage-Bericht",
    "report_goals": "🎯 Abgeschlossene Ziele: *{n}*",
    "report_habits": "🌱 Markierte Gewohnheiten: *{n}*",
    "report_rems": "🔔 Ausgelöste Erinnerungen: *{n}*",
    "report_streak": "🔥 Aktive Tage: *{n}*",
    "challenge_title": "🏆 Wöchentliche Challenge",
    "challenge_cta": "Deine Challenge für die Woche:\n\n“{text}”",
    "btn_done": "✅ Erledigt",
    "btn_new": "🎲 Neue Challenge",
    "challenge_done": "👏 Stark! Challenge als erledigt markiert.",
    "mode_title": "🦄 Exklusiver Modus aktiviert",
    "mode_set": "Ab jetzt antworte ich wie dein persönlicher Mindra+-Coach 💜",
    "stats_title": "📈 Erweiterte Statistiken",
    "stats_goals_done": "🎯 Ziele insgesamt abgeschlossen: *{n}*",
    "stats_habit_days": "🌱 Tage mit Gewohnheiten: *{n}*",
    "stats_active_days": "🔥 Aktive Tage in 30T: *{n}*",
},
    "pl": {
    "upsell_title": "💎 Mindra+/Pro",
    "upsell_body":  "Nielimitowane przypomnienia, raporty, wyzwania i ekskluzywny tryb.\nWłącz Mindra+ i odblokuj wszystko 💜",
    "btn_get": "Zdobądź Mindra+",
    "btn_code": "Wprowadź kod",
    "days_left": "💎 Twój Mindra+: pozostało dni — *{days}*",
    "no_plus": "Nie masz jeszcze Mindra+. Dostępne są funkcje darmowe 💜",
    "report_title": "📊 Twój raport z 7 dni",
    "report_goals": "🎯 Ukończonych celów: *{n}*",
    "report_habits": "🌱 Odhaczonych nawyków: *{n}*",
    "report_rems": "🔔 Zadziałało przypomnień: *{n}*",
    "report_streak": "🔥 Aktywne dni: *{n}*",
    "challenge_title": "🏆 Cotygodniowe wyzwanie",
    "challenge_cta": "Twoje wyzwanie na tydzień:\n\n“{text}”",
    "btn_done": "✅ Gotowe",
    "btn_new": "🎲 Nowe wyzwanie",
    "challenge_done": "👏 Świetnie! Wyzwanie oznaczone jako ukończone.",
    "mode_title": "🦄 Tryb ekskluzywny aktywowany",
    "mode_set": "Od teraz będę odpowiadać jak Twój osobisty coach Mindra+ 💜",
    "stats_title": "📈 Rozszerzone statystyki",
    "stats_goals_done": "🎯 Celów ukończonych łącznie: *{n}*",
    "stats_habit_days": "🌱 Dni z nawykami: *{n}*",
    "stats_active_days": "🔥 Aktywne dni w 30d: *{n}*",
},
    "fr": {
    "upsell_title": "💎 Mindra+/Pro",
    "upsell_body":  "Rappels illimités, rapports, défis et mode exclusif.\nActive Mindra+ et débloque tout 💜",
    "btn_get": "Obtenir Mindra+",
    "btn_code": "Saisir le code",
    "days_left": "💎 Ton Mindra+ : il reste — *{days}* jours",
    "no_plus": "Tu n’as pas encore Mindra+. Les fonctions gratuites sont disponibles 💜",
    "report_title": "📊 Ton rapport sur 7 jours",
    "report_goals": "🎯 Objectifs terminés : *{n}*",
    "report_habits": "🌱 Habitudes cochées : *{n}*",
    "report_rems": "🔔 Rappels déclenchés : *{n}*",
    "report_streak": "🔥 Jours actifs : *{n}*",
    "challenge_title": "🏆 Défi hebdomadaire",
    "challenge_cta": "Ton défi pour la semaine :\n\n“{text}”",
    "btn_done": "✅ Terminé",
    "btn_new": "🎲 Nouveau défi",
    "challenge_done": "👏 Super ! Défi marqué comme terminé.",
    "mode_title": "🦄 Mode exclusif activé",
    "mode_set": "Désormais, je répondrai comme ton coach personnel Mindra+ 💜",
    "stats_title": "📈 Statistiques avancées",
    "stats_goals_done": "🎯 Objectifs terminés au total : *{n}*",
    "stats_habit_days": "🌱 Jours avec habitudes : *{n}*",
    "stats_active_days": "🔥 Jours actifs sur 30 j : *{n}*",
},
    "uk": {
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
        "upsell_title": "💎 Mindra+/Pro",
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
    "es": {
    "menu_title": "🎯 Metas y 🌱 Hábitos",
    "btn_add_goal":   "🎯 Fijar meta",
    "btn_list_goals": "📋 Mis metas",
    "btn_add_habit":  "🌱 Añadir hábito",
    "btn_list_habits":"📊 Mis hábitos",
    "back": "◀️ Menú",
    "goals_title": "🎯 Tus metas:",
    "habits_title": "🌱 Tus hábitos:",
    "goals_empty": "Aún no hay metas. Pulsa «🎯 Fijar meta».",
    "habits_empty": "Aún no hay hábitos. Pulsa «🌱 Añadir hábito».",
    "goal_usage": "Para añadir una meta, escribe: `/goal Texto de la meta`\nEj.: `/goal Correr 5 km`",
    "habit_usage": "Para añadir un hábito, escribe: `/habit Nombre del hábito`\nEj.: `/habit Beber agua`",
},
"de": {
    "menu_title": "🎯 Ziele und 🌱 Gewohnheiten",
    "btn_add_goal":   "🎯 Ziel setzen",
    "btn_list_goals": "📋 Meine Ziele",
    "btn_add_habit":  "🌱 Gewohnheit hinzufügen",
    "btn_list_habits":"📊 Meine Gewohnheiten",
    "back": "◀️ Menü",
    "goals_title": "🎯 Deine Ziele:",
    "habits_title": "🌱 Deine Gewohnheiten:",
    "goals_empty": "Noch keine Ziele. Tippe «🎯 Ziel setzen».",
    "habits_empty": "Noch keine Gewohnheiten. Tippe «🌱 Gewohnheit hinzufügen».",
    "goal_usage": "Um ein Ziel hinzuzufügen, schreibe: `/goal Zieltext`\nZ. B.: `/goal 5 km laufen`",
    "habit_usage": "Um eine Gewohnheit hinzuzufügen, schreibe: `/habit Name der Gewohnheit`\nZ. B.: `/habit Wasser trinken`",
},
"pl": {
    "menu_title": "🎯 Cele i 🌱 Nawyki",
    "btn_add_goal":   "🎯 Ustaw cel",
    "btn_list_goals": "📋 Moje cele",
    "btn_add_habit":  "🌱 Dodaj nawyk",
    "btn_list_habits":"📊 Moje nawyki",
    "back": "◀️ Menu",
    "goals_title": "🎯 Twoje cele:",
    "habits_title": "🌱 Twoje nawyki:",
    "goals_empty": "Na razie brak celów. Naciśnij „🎯 Ustaw cel”.",
    "habits_empty": "Na razie brak nawyków. Naciśnij „🌱 Dodaj nawyk”.",
    "goal_usage": "Aby dodać cel, napisz: `/goal Treść celu`\nNp.: `/goal Przebiec 5 km`",
    "habit_usage": "Aby dodać nawyk, napisz: `/habit Nazwa nawyku`\nNp.: `/habit Pić wodę`",
},
"fr": {
    "menu_title": "🎯 Objectifs et 🌱 Habitudes",
    "btn_add_goal":   "🎯 Fixer un objectif",
    "btn_list_goals": "📋 Mes objectifs",
    "btn_add_habit":  "🌱 Ajouter une habitude",
    "btn_list_habits":"📊 Mes habitudes",
    "back": "◀️ Menu",
    "goals_title": "🎯 Tes objectifs :",
    "habits_title": "🌱 Tes habitudes :",
    "goals_empty": "Pas encore d’objectifs. Appuie sur « 🎯 Fixer un objectif ».",
    "habits_empty": "Pas encore d’habitudes. Appuie sur « 🌱 Ajouter une habitude ».",
    "goal_usage": "Pour ajouter un objectif, écris : `/goal Texte de l’objectif`\nEx. : `/goal Courir 5 km`",
    "habit_usage": "Pour ajouter une habitude, écris : `/habit Nom de l’habitude`\nEx. : `/habit Boire de l’eau`",
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
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "es": {
    "choose_lang": "🌐 Elige el idioma de la interfaz:",
    "choose_tz":   "🌍 Indica tu zona horaria (con los botones abajo):",
    "done":        "✅ ¡Listo! Idioma: *{lang_name}* · Zona horaria: *{tz}* · Hora local: *{local_time}*",
    "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
    },
},
"de": {
    "choose_lang": "🌐 Wähle die Sprache der Oberfläche:",
    "choose_tz":   "🌍 Gib deine Zeitzone an (mit den Tasten unten):",
    "done":        "✅ Fertig! Sprache: *{lang_name}* · Zeitzone: *{tz}* · Ortszeit: *{local_time}*",
    "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
    },
},
"pl": {
    "choose_lang": "🌐 Wybierz język interfejsu:",
    "choose_tz":   "🌍 Podaj swoją strefę czasową (przyciskami poniżej):",
    "done":        "✅ Gotowe! Język: *{lang_name}* · Strefa czasowa: *{tz}* · Czas lokalny: *{local_time}*",
    "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
    },
},
"fr": {
    "choose_lang": "🌐 Choisis la langue de l’interface :",
    "choose_tz":   "🌍 Indique ton fuseau horaire (avec les boutons ci-dessous) :",
    "done":        "✅ C’est fait ! Langue : *{lang_name}* · Fuseau horaire : *{tz}* · Heure locale : *{local_time}*",
    "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
    },
},
    "uk": {
        "choose_lang": "🌐 Обери мову інтерфейсу:",
        "choose_tz":   "🌍 Вкажи свій часовий пояс (кнопками нижче):",
        "done":        "✅ Готово! Мова: *{lang_name}* · Часовий пояс: *{tz}* · Локальний час: *{local_time}*",
             "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "md": {
        "choose_lang": "🌐 Alege limba interfeței:",
        "choose_tz":   "🌍 Alege fusul orar (folosește butoanele):",
        "done":        "✅ Gata! Limba: *{lang_name}* · Fus orar: *{tz}* · Ora locală: *{local_time}*",
        "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "be": {
        "choose_lang": "🌐 Абярыце мову інтэрфейсу:",
        "choose_tz":   "🌍 Пакажыце свой часавы пояс (кнопкамі ніжэй):",
        "done":        "✅ Гатова! Мова: *{lang_name}* · Часавы пояс: *{tz}* · Мясцовы час: *{local_time}*",
 "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "kk": {
        "choose_lang": "🌐 Интерфейс тілін таңдаңыз:",
        "choose_tz":   "🌍 Уақыт белдеуіңізді таңдаңыз (төмендегі батырмалар):",
        "done":        "✅ Дайын! Тіл: *{lang_name}* · Уақыт белдеуі: *{tz}* · Жергілікті уақыт: *{local_time}*",
         "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "kg": {
        "choose_lang": "🌐 Интерфейс тилин тандаңыз:",
        "choose_tz":   "🌍 Убакыт алкагыңызды тандаңыз (төмөнкү баскычтар):",
        "done":        "✅ Даяр! Тил: *{lang_name}* · Убакыт алкагы: *{tz}* · Жергиликтүү убакыт: *{local_time}*",
         "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "hy": {
        "choose_lang": "🌐 Ընտրիր ինտերֆեյսի լեզուն․",
        "choose_tz":   "🌍 Նշիր քո ժամային գոտին (ստորև գտնվող կոճակներով)․",
        "done":        "✅ Պատրաստ է․ Լեզու՝ *{lang_name}* · Ժամային գոտի՝ *{tz}* · Տեղական ժամանակ՝ *{local_time}*",
         "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "ka": {
        "choose_lang": "🌐 აირჩიე ინტერფეისის ენა:",
        "choose_tz":   "🌍 მიუთითე შენი დროის სარტყელი (ქვემოთ ღილაკებით):",
        "done":        "✅ მზადაა! ენა: *{lang_name}* · დროის სარტყელი: *{tz}* · ადგილობრივი დრო: *{local_time}*",
         "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "ce": {
        "choose_lang": "🌐 Интерфейсийн мотт юкъахь талла:",
        "choose_tz":   "🌍 Тайм-зона юкъахь талла (кнопкаш тӀехь):",
        "done":        "✅ ДӀаяр! Мотт: *{lang_name}* · Тайм-зона: *{tz}* · Локал хан: *{local_time}*",
         "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
    "en": {
        "choose_lang": "🌐 Pick your interface language:",
        "choose_tz":   "🌍 Set your time zone (use the buttons):",
        "done":        "✅ Done! Language: *{lang_name}* · Time zone: *{tz}* · Local time: *{local_time}*",
         "lang_name": {
        "ru":"Русский","uk":"Українська","md":"Română","be":"Беларуская",
        "kk":"Қазақша","kg":"Кыргызча","hy":"Հայերեն","ka":"ქართული","ce":"Нохчийн мотт",
        "en":"English","es":"Español","de":"Deutsch","pl":"Polski","fr":"Français"
        },
    },
}

# Алиасы → IANA. Добавляй свои при желании.
TIMEZONE_ALIASES = {
    # UA/RU/СНГ
    "kiev": "Europe/Kyiv", "kyiv": "Europe/Kyiv", "киев": "Europe/Kyiv", "київ": "Europe/Kyiv",
    "moscow": "Europe/Moscow", "москва": "Europe/Moscow", "msk": "Europe/Moscow",
    "chisinau": "Europe/Chisinau", "kishinev": "Europe/Chisinau", "кишинев": "Europe/Chisinau",
    "tbilisi": "Asia/Tbilisi", "tbilisi": "Asia/Tbilisi",
    "yerevan": "Asia/Yerevan", "erevan": "Asia/Yerevan",
    "almaty": "Asia/Almaty", "алматы": "Asia/Almaty",
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
    "warsaw": "Europe/Warsaw", "riga": "Europe/Riga", "tallinn": "Europe/Tallinn",
    "berlin": "Europe/Berlin", "paris": "Europe/Paris", "london": "Europe/London",
    "madrid": "Europe/Madrid", "barcelona": "Europe/Madrid",
    "germany": "Europe/Berlin", "france": "Europe/Paris", "spain": "Europe/Madrid",
    
    # generic
    "utc": "UTC",
}

# Предустановленные кнопки (частые варианты)
TZ_KEYBOARD_ROWS = [
    [("🇺🇦 Kyiv", "Europe/Kyiv"), ("🇷🇺 Moscow", "Europe/Moscow")],
    [("🇫🇷 Paris", "Europe/Paris"), ("🇩🇪 Berlin", "Europe/Berlin")],
    [("🇪🇸 Madrid", "Europe/Madrid"), ("🇵🇱 Warsaw", "Europe/Warsaw")],
    [("🇺🇸 New York", "America/New_York"), ("🇺🇸 Chicago", "America/Chicago")],
    [("🇺🇸 Denver", "America/Denver"), ("🇺🇸 Los Angeles", "America/Los_Angeles")],
    [("🇺🇸 Phoenix", "America/Phoenix"), ("🇺🇸 Miami", "America/New_York")],
    [("🇬🇪 Tbilisi", "Asia/Tbilisi"), ("🇦🇲 Yerevan", "Asia/Yerevan")],
    [("🇰🇿 Almaty", "Asia/Almaty")],
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
    "es": {
    "title": "🌍 Indica tu zona horaria para los recordatorios.",
    "hint": "Ejemplo: `/timezone madrid` o `/timezone ny`.\nTambién puedes pulsar el botón de abajo.",
    "saved": "✅ Zona horaria establecida: *{tz}*. Hora local: *{local_time}*.",
    "unknown": "No reconozco esa zona horaria. Escribe una ciudad/alias o elige con el botón.",
},
"de": {
    "title": "🌍 Gib deine Zeitzone für Erinnerungen an.",
    "hint": "Beispiel: `/timezone berlin` oder `/timezone ny`.\nDu kannst auch den Button unten verwenden.",
    "saved": "✅ Zeitzone gesetzt: *{tz}*. Ortszeit: *{local_time}*.",
    "unknown": "Zeitzone nicht erkannt. Gib eine Stadt/einen Alias ein oder wähle per Button.",
},
"pl": {
    "title": "🌍 Podaj swoją strefę czasową dla przypomnień.",
    "hint": "Przykład: `/timezone warsaw` albo `/timezone ny`.\nMożesz też użyć przycisku poniżej.",
    "saved": "✅ Ustawiono strefę czasową: *{tz}*. Czas lokalny: *{local_time}*.",
    "unknown": "Nie rozpoznano strefy czasowej. Wpisz miasto/alias lub wybierz przyciskiem.",
},
"fr": {
    "title": "🌍 Indique ton fuseau horaire pour les rappels.",
    "hint": "Exemple : `/timezone paris` ou `/timezone ny`.\nTu peux aussi appuyer sur le bouton ci-dessous.",
    "saved": "✅ Fuseau horaire défini : *{tz}*. Heure locale : *{local_time}*.",
    "unknown": "Je ne reconnais pas ce fuseau. Saisis une ville/un alias ou utilise le bouton.",
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
    "es": (
    "🏅 *Puntos y rangos*\n"
    "Vas acumulando puntos por tus acciones en el bot: metas, hábitos, informes.\n\n"
    "Ahora tienes: *{points}* puntos — rango: *{title}*.\n"
    "Para el siguiente rango *{next_title}* te faltan: *{to_next}*.\n\n"
    "Escalera de rangos:\n{ladder}"
),

"de": (
    "🏅 *Punkte und Titel*\n"
    "Du sammelst Punkte für Aktionen im Bot: Ziele, Gewohnheiten, Berichte.\n\n"
    "Aktuell hast du: *{points}* Punkte — Titel: *{title}*.\n"
    "Bis zum nächsten Titel *{next_title}* fehlen: *{to_next}*.\n\n"
    "Rangliste der Titel:\n{ladder}"
),

"pl": (
    "🏅 *Punkty i tytuły*\n"
    "Zbierasz punkty za działania w bocie: cele, nawyki, raporty.\n\n"
    "Masz teraz: *{points}* pkt — tytuł: *{title}*.\n"
    "Do następnego tytułu *{next_title}* brakuje: *{to_next}*.\n\n"
    "Drabinka tytułów:\n{ladder}"
),

"fr": (
    "🏅 *Points et titres*\n"
    "Tu gagnes des points pour tes actions dans le bot : objectifs, habitudes, rapports.\n\n"
    "Tu as actuellement : *{points}* points — titre : *{title}*.\n"
    "Il te reste *{to_next}* pour atteindre le prochain titre *{next_title}*.\n\n"
    "Échelle des titres :\n{ladder}"
),
}

# Команда /remind — мультиязычный вариант
REMIND_TEXTS = {
    "ru": {
        # старые ключи (лимит/формат)
        "limit": "🔔 В бесплатной версии можно установить до 3 активных напоминаний.\n\n✨ Оформи Mindra+, чтобы иметь до 10 активных напоминаний 💜",
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
        "limit": "🔔 У безкоштовній версії можна встановити до 3 активних нагадувань.\n\n✨ Оформи Mindra+, щоб мати до 10 активних нагадувань 💜",
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
        "limit": "🔔 În versiunea gratuită poți seta până la 3 mementouri active.\n\n✨ Activează Mindra+ pentru până la 10 mementouri active 💜",
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
        "limit": "🔔 У бясплатнай версіі можна ўсталяваць да 3 актыўных напамінаў.\n\n✨ Аформі Mindra+, каб мець да 10 актыўных напамінаў 💜",
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
        "limit": "🔔 Тегін нұсқада тек 3 белсенді еске салу орнатуға болады.\n\n✨ Mindra+ арқылы 10 белсенді еске салу орнатыңыз 💜",
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
        "limit": "🔔 Акысыз версияда эң көп 3 активдүү эскертме коюуга болот.\n\n✨ Mindra+ менен 10 активдүү эскертмеге чейин коюңуз 💜",
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
        "limit": "🔔 Անվճար տարբերակում կարելի է ավելացնել մինչև 3 ակտիվ հիշեցում։\n\n✨ Միացրու Mindra+, որ ունենաս մինչև 10 ակտիվ հիշեցում 💜",
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
        "limit": "🔔 უფასო ვერსიაში შეგიძლიათ დააყენოთ მაქსიმუმ 3 აქტიური შეხსენება.\n\n✨ გაააქტიურეთ Mindra+ — მაქსიმუმ 10 აქტიური შეხსენებისთვის 💜",
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
        "limit": "🔔 Аьтто версия хийцна, цхьаьнан 3 активан напоминание ца хилла цуьнан.\n\n✨ Mindra+ хийцар, цуьнан до 10 активан напоминаний хилла 💜",
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
        "limit": "🔔 In the free version, you can set only 3 active reminder.\n\n✨ Get Mindra+ for unlimited reminders 💜",
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
    "es": {
    # antiguos (límite/formato)
    "limit": "🔔 En la versión gratuita puedes configurar hasta 3 recordatorios activos.\n\n✨ Activa Mindra+ para tener hasta 10 recordatorios activos 💜",
    "usage": "⏰ Uso: `/remind 19:30 ¡Haz ejercicio!`",
    "success": "✅ Recordatorio fijado para {hour:02d}:{minute:02d}: *{text}*",
    "bad_format": "⚠️ Formato no válido. Ej.: `/remind 19:30 ¡Haz ejercicio!`",
    # nuevos (Reminders 2.0)
    "create_help": "⏰ Crea un recordatorio: <cuándo> <sobre qué>\nEjemplos: «mañana a las 9 entrenamiento», «en 15 minutos agua», «vie a las 19 cine».",
    "created":     "✅ Recordatorio creado para {time}\n“{text}”",
    "not_understood": "⚠️ No entendí la hora. Di, por ejemplo: «mañana a las 10 regar las plantas» o «en 30 minutos café».",
    "list_empty":  "Por ahora no hay recordatorios activos.",
    "list_title":  "🗓 Tus recordatorios:",
    "fired":       "🔔 Recordatorio: {text}\n🕒 {time}",
    "deleted":     "🗑 Recordatorio eliminado.",
    "snoozed":     "⏳ Pospuesto hasta {time}\n“{text}”",
    "btn_plus15":  "⏳ +15m",
    "btn_plus1h":  "🕐 +1h",
    "btn_tomorrow":"🌅 Mañana",
    "btn_delete":  "🗑 Eliminar",
    "btn_new":     "➕ Añadir",
    "menu_title":  "🔔 Recordatorios",
    "btn_add_rem": "➕ Añadir recordatorio",
    "btn_list_rem":"📋 Lista de recordatorios",
},
"de": {
    # alt (Limit/Format)
    "limit": "🔔 In der Gratis-Version kannst du bis zu 3 aktive Erinnerungen setzen.\n\n✨ Hol dir Mindra+, um bis zu 10 aktive Erinnerungen zu haben 💜",
    "usage": "⏰ Verwendung: `/remind 19:30 Gymnastik!`",
    "success": "✅ Erinnerung gesetzt für {hour:02d}:{minute:02d}: *{text}*",
    "bad_format": "⚠️ Falsches Format. Beispiel: `/remind 19:30 Gymnastik!`",
    # neu (Reminders 2.0)
    "create_help": "⏰ Erstelle eine Erinnerung: <wann> <worum>\nBeispiele: „morgen um 9 Training“, „in 15 Minuten Wasser“, „Fr um 19 Kino“.",
    "created":     "✅ Erinnerung erstellt für {time}\n„{text}“",
    "not_understood": "⚠️ Zeit nicht erkannt. Sag z. B.: „morgen um 10 Blumen gießen“ oder „in 30 Minuten Kaffee“.",
    "list_empty":  "Noch keine aktiven Erinnerungen.",
    "list_title":  "🗓 Deine Erinnerungen:",
    "fired":       "🔔 Erinnerung: {text}\n🕒 {time}",
    "deleted":     "🗑 Erinnerung gelöscht.",
    "snoozed":     "⏳ Verschoben auf {time}\n„{text}“",
    "btn_plus15":  "⏳ +15 Min",
    "btn_plus1h":  "🕐 +1 Std",
    "btn_tomorrow":"🌅 Morgen",
    "btn_delete":  "🗑 Löschen",
    "btn_new":     "➕ Hinzufügen",
    "menu_title":  "🔔 Erinnerungen",
    "btn_add_rem": "➕ Erinnerung hinzufügen",
    "btn_list_rem":"📋 Erinnerungen anzeigen",
},
"pl": {
    # stare (limit/format)
    "limit": "🔔 W wersji bezpłatnej możesz ustawić do 3 aktywnych przypomnień.\n\n✨ Włącz Mindra+, aby mieć do 10 aktywnych przypomnień 💜",
    "usage": "⏰ Użycie: `/remind 19:30 Zrób rozgrzewkę!`",
    "success": "✅ Ustawiono przypomnienie na {hour:02d}:{minute:02d}: *{text}*",
    "bad_format": "⚠️ Nieprawidłowy format. Przykład: `/remind 19:30 Zrób rozgrzewkę!`",
    # nowe (Reminders 2.0)
    "create_help": "⏰ Utwórz przypomnienie: <kiedy> <o czym>\nPrzykłady: „jutro o 9 trening”, „za 15 minut woda”, „pt o 19 kino”.",
    "created":     "✅ Przypomnienie utworzone na {time}\n„{text}”",
    "not_understood": "⚠️ Nie rozumiem czasu. Powiedz np.: „jutro o 10 podlać kwiaty” lub „za 30 minut kawa”.",
    "list_empty":  "Brak aktywnych przypomnień.",
    "list_title":  "🗓 Twoje przypomnienia:",
    "fired":       "🔔 Przypomnienie: {text}\n🕒 {time}",
    "deleted":     "🗑 Przypomnienie usunięte.",
    "snoozed":     "⏳ Przełożono na {time}\n„{text}”",
    "btn_plus15":  "⏳ +15 min",
    "btn_plus1h":  "🕐 +1 h",
    "btn_tomorrow":"🌅 Jutro",
    "btn_delete":  "🗑 Usuń",
    "btn_new":     "➕ Dodaj",
    "menu_title":  "🔔 Przypomnienia",
    "btn_add_rem": "➕ Dodaj przypomnienie",
    "btn_list_rem":"📋 Lista przypomnień",
},
"fr": {
    # anciens (limite/format)
    "limit": "🔔 Dans la version gratuite, tu peux créer jusqu’à 3 rappels actifs.\n\n✨ Active Mindra+ pour en avoir jusqu’à 10 💜",
    "usage": "⏰ Utilisation : `/remind 19:30 Faire des étirements !`",
    "success": "✅ Rappel programmé pour {hour:02d}:{minute:02d} : *{text}*",
    "bad_format": "⚠️ Format invalide. Exemple : `/remind 19:30 Faire des étirements !`",
    # nouveaux (Reminders 2.0)
    "create_help": "⏰ Crée un rappel : <quand> <quoi>\nExemples : « demain à 9 entraînement », « dans 15 min eau », « ven à 19 ciné ».",
    "created":     "✅ Rappel créé pour {time}\n« {text} »",
    "not_understood": "⚠️ Je n’ai pas compris l’heure. Dis par exemple : « demain à 10 arroser les plantes » ou « dans 30 min café ».",
    "list_empty":  "Pas encore de rappels actifs.",
    "list_title":  "🗓 Tes rappels :",
    "fired":       "🔔 Rappel : {text}\n🕒 {time}",
    "deleted":     "🗑 Rappel supprimé.",
    "snoozed":     "⏳ Reporté à {time}\n« {text} »",
    "btn_plus15":  "⏳ +15 min",
    "btn_plus1h":  "🕐 +1 h",
    "btn_tomorrow":"🌅 Demain",
    "btn_delete":  "🗑 Supprimer",
    "btn_new":     "➕ Ajouter",
    "menu_title":  "🔔 Rappels",
    "btn_add_rem": "➕ Ajouter un rappel",
    "btn_list_rem":"📋 Liste des rappels",
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
        "es": "🔒 Esta función solo está disponible para suscriptores de Mindra+.",
        "de": "🔒 Diese Funktion ist nur für Mindra+-Abonnenten verfügbar.",
        "pl": "🔒 Ta funkcja jest dostępna tylko dla abonentów Mindra+.",
        "fr": "🔒 Cette fonctionnalité est réservée aux abonnés Mindra+.",
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
             "es": "✅ El modo de comunicación cambió a *Coach*. ¡Te ayudaré y te motivaré! 💪",
    "de": "✅ Kommunikationsmodus auf *Coach* geändert. Ich werde dir helfen und dich motivieren! 💪",
    "pl": "✅ Tryb rozmowy zmieniono na *Coach*. Będę Ci pomagać i motywować! 💪",
    "fr": "✅ Mode de communication passé à *Coach*. Je vais t’aider et te motiver ! 💪",
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
            "es": "😉 El modo de comunicación cambió a *Flirt*. Prepárate para agradables sorpresas 💜",
    "de": "😉 Kommunikationsmodus auf *Flirt* geändert. Mach dich auf angenehme Überraschungen gefasst 💜",
    "pl": "😉 Tryb rozmowy zmieniono na *Flirt*. Przygotuj się na miłe niespodzianki 💜",
    "fr": "😉 Mode de communication passé à *Flirt*. Prépare-toi à de belles surprises 💜",
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
    "es": {
        "coach": "💪 Eres mi coach personal. Ayúdame con indicaciones claras y directas, da consejos y motívame. 🚀",
        "flirty": "😉 Flirteas un poquito y me apoyas. Responde con calidez y un toque ligero de coqueteo 💜✨",
    },
    "de": {
        "coach": "💪 Du bist mein persönlicher Coach. Hilf mir klar und auf den Punkt, gib Ratschläge und motiviere mich! 🚀",
        "flirty": "😉 Du flirtest ein wenig und unterstützt mich. Antworte warm und mit einem leichten Flirt 💜✨",
    },
    "pl": {
        "coach": "💪 Jesteś moim osobistym coachem. Pomagaj jasno i konkretnie, dawaj wskazówki i motywuj! 🚀",
        "flirty": "😉 Lekko flirtujesz i wspierasz. Odpowiadaj ciepło i z delikatnym flirtem 💜✨",
    },
    "fr": {
        "coach": "💪 Tu es mon coach personnel. Aide-moi avec des conseils clairs et précis, motive-moi et soutiens-moi ! 🚀",
        "flirty": "😉 Tu flirtes un peu et tu me soutiens. Réponds avec chaleur et une touche légère de flirt 💜✨",
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
    "es": (
    "✅ *Tu informe personal de la semana:*\n\n"
    "🎯 Metas completadas: {completed_goals}\n"
    "🌱 Hábitos cumplidos: {completed_habits}\n"
    "📅 Días de actividad: {days_active}\n"
    "📝 Registros de ánimo: {mood_entries}\n\n"
    "¡Muy bien! Sigue así 💜"
),

"de": (
    "✅ *Dein persönlicher Wochenbericht:*\n\n"
    "🎯 Abgeschlossene Ziele: {completed_goals}\n"
    "🌱 Erledigte Gewohnheiten: {completed_habits}\n"
    "📅 Aktive Tage: {days_active}\n"
    "📝 Stimmungseinträge: {mood_entries}\n\n"
    "Stark! Mach weiter so 💜"
),

"pl": (
    "✅ *Twój osobisty raport tygodnia:*\n\n"
    "🎯 Ukończone cele: {completed_goals}\n"
    "🌱 Wykonane nawyki: {completed_habits}\n"
    "📅 Dni aktywności: {days_active}\n"
    "📝 Zapisy nastroju: {mood_entries}\n\n"
    "Świetna robota! Tak trzymaj 💜"
),

"fr": (
    "✅ *Ton rapport personnel de la semaine :*\n\n"
    "🎯 Objectifs terminés : {completed_goals}\n"
    "🌱 Habitudes réalisées : {completed_habits}\n"
    "📅 Jours d’activité : {days_active}\n"
    "📝 Entrées d’humeur : {mood_entries}\n\n"
    "Bravo ! Continue comme ça 💜"
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
    "es": [
    "📝 ¿Cómo valorarías tu día del 1 al 10?",
    "💭 ¿Qué te alegró hoy?",
    "🌿 ¿Hubo un momento en el que sentiste gratitud hoy?",
    "🤔 Si pudieras cambiar una cosa de este día, ¿cuál sería?",
    "💪 ¿De qué te sientes orgulloso/a hoy?",
    "🤔 ¿Qué nuevo probaste hoy?",
    "📝 ¿Con qué sueñas ahora mismo?",
    "🌟 ¿Por qué puedes felicitarte hoy?",
    "💡 ¿Qué idea se te ocurrió hoy?",
    "🎉 ¿Hubo hoy un momento que te sacó una sonrisa?",
    "🌈 ¿Cuál fue el momento más brillante de tu día?",
    "🫶 ¿A quién te gustaría dar las gracias hoy?",
    "💬 ¿Hubo algo que te sorprendió hoy?",
    "🌻 ¿Cómo te cuidaste hoy?",
    "😌 ¿Hubo algo que te ayudó a relajarte?",
    "🏆 ¿Qué lograste hoy, aunque fuera algo pequeño?",
    "📚 ¿Qué nuevo aprendiste hoy?",
    "🧑‍🤝‍🧑 ¿Hubo alguien que te apoyó hoy?",
    "🎁 ¿Hiciste hoy algo agradable por otra persona?",
    "🎨 ¿Qué actividad creativa te gustaría probar?"
],

"de": [
    "📝 Wie würdest du deinen Tag auf einer Skala von 1 bis 10 bewerten?",
    "💭 Was hat dich heute gefreut?",
    "🌿 Gab es heute einen Moment, in dem du Dankbarkeit gespürt hast?",
    "🤔 Wenn du eine Sache an diesem Tag ändern könntest, welche wäre es?",
    "💪 Worauf bist du heute stolz?",
    "🤔 Was hast du heute Neues ausprobiert?",
    "📝 Wovon träumst du gerade?",
    "🌟 Wofür kannst du dich heute loben?",
    "💡 Welche Idee ist dir heute gekommen?",
    "🎉 Gab es heute einen Moment, der dich zum Lächeln gebracht hat?",
    "🌈 Welcher Moment des Tages war für dich der hellste?",
    "🫶 Wem möchtest du heute Danke sagen?",
    "💬 Hat dich heute etwas überrascht?",
    "🌻 Wie hast du heute für dich selbst gesorgt?",
    "😌 Gab es etwas, das dir beim Entspannen geholfen hat?",
    "🏆 Was hast du heute erreicht, auch wenn es nur etwas Kleines war?",
    "📚 Was hast du heute Neues gelernt?",
    "🧑‍🤝‍🧑 Gab es jemanden, der dich heute unterstützt hat?",
    "🎁 Hast du heute etwas Nettes für jemanden getan?",
    "🎨 Welche kreative Tätigkeit würdest du gern ausprobieren?"
],

"pl": [
    "📝 Jak ocenisz swój dzień w skali od 1 do 10?",
    "💭 Co cię dziś ucieszyło?",
    "🌿 Czy był dziś moment, w którym poczułeś/aś wdzięczność?",
    "🤔 Gdybyś mógł/mogła zmienić jedną rzecz w tym dniu, co by to było?",
    "💪 Z czego dziś jesteś dumny/a?",
    "🤔 Czego nowego dziś spróbowałeś/aś?",
    "📝 O czym teraz marzysz?",
    "🌟 Za co możesz się dziś pochwalić?",
    "💡 Jaki pomysł przyszedł ci dziś do głowy?",
    "🎉 Czy był dziś moment, który wywołał uśmiech?",
    "🌈 Jaki moment dnia był dla ciebie najjaśniejszy?",
    "🫶 Komu chciał(a)byś dziś powiedzieć „dziękuję”?",
    "💬 Czy coś cię dziś zaskoczyło?",
    "🌻 Jak zadbałeś/aś dziś o siebie?",
    "😌 Czy było coś, co pomogło ci się zrelaksować?",
    "🏆 Co udało ci się dziś osiągnąć, nawet jeśli to drobiazg?",
    "📚 Czego nowego nauczyłeś/aś się dziś?",
    "🧑‍🤝‍🧑 Czy był ktoś, kto cię dziś wsparł?",
    "🎁 Czy zrobiłeś/aś dziś coś miłego dla kogoś?",
    "🎨 Jaką kreatywną aktywność chciał(a)byś wypróbować?"
],

"fr": [
    "📝 Comment évalues-tu ta journée sur une échelle de 1 à 10 ?",
    "💭 Qu’est-ce qui t’a réjoui aujourd’hui ?",
    "🌿 Y a-t-il eu un moment où tu as ressenti de la gratitude aujourd’hui ?",
    "🤔 Si tu pouvais changer une chose dans cette journée, laquelle serait-ce ?",
    "💪 De quoi es-tu fier/fière aujourd’hui ?",
    "🤔 Qu’as-tu essayé de nouveau aujourd’hui ?",
    "📝 À quoi rêves-tu en ce moment ?",
    "🌟 Pour quoi peux-tu te féliciter aujourd’hui ?",
    "💡 Quelle idée t’est venue aujourd’hui ?",
    "🎉 Y a-t-il eu un moment qui t’a fait sourire aujourd’hui ?",
    "🌈 Quel a été le moment le plus marquant de ta journée ?",
    "🫶 À qui voudrais-tu dire merci aujourd’hui ?",
    "💬 Y a-t-il quelque chose qui t’a surpris aujourd’hui ?",
    "🌻 Comment as-tu pris soin de toi aujourd’hui ?",
    "😌 Y a-t-il quelque chose qui t’a aidé(e) à te détendre ?",
    "🏆 Qu’as-tu réussi aujourd’hui, même si c’est une petite chose ?",
    "📚 Qu’as-tu appris de nouveau aujourd’hui ?",
    "🧑‍🤝‍🧑 Y a-t-il quelqu’un qui t’a soutenu(e) aujourd’hui ?",
    "🎁 As-tu fait quelque chose d’agréable pour quelqu’un aujourd’hui ?",
    "🎨 Quelle activité créative aimerais-tu essayer ?"
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
    "ru": [
    "💜 Ты делаешь этот мир лучше просто тем, что ты в нём.",
    "🌞 Сегодня новый день, и он полон возможностей — ты справишься!",
    "🤗 Обнимаю тебя мысленно. Ты не один(одна).",
    "✨ Даже если нелегко — помни, ты уже многого достиг(ла)!",
    "💫 У тебя есть всё, чтобы пройти через это. Верю в тебя!",
    "🫶 Как хорошо, что ты есть. Ты очень важный человек.",
    "🔥 Сегодня — хороший день, чтобы гордиться собой!",
    "🌈 Если вдруг устал(а) — просто сделай паузу и выдохни. Это нормально.",
    "😊 Улыбнись себе в зеркало. Ты классный(ая)!",
    "💡 Помни: каждый день ты становишься сильнее.",
    "🍀 Твои чувства важны. Ты важен(важна).",
    "💛 Ты заслуживаешь любви и заботы — и от других, и от себя.",
    "🌟 Спасибо тебе за то, что ты есть. Серьёзно.",
    "🤍 Даже маленький шаг вперёд — уже победа.",
    "💌 Ты приносишь в мир тепло. Не забывай об этом!",
    "✨ Верь в себя. Ты уже столько всего прошёл(а) — и справился(ась)!",
    "🙌 Сегодня — твой день. Делай то, что делает тебя счастливым(ой).",
    "🌸 Побалуй себя чем-то вкусным или приятным. Ты этого достоин(достойна).",
    "🏞️ Просто напоминание: ты невероятный(ая), и я рядом.",
    "🎶 Пусть музыка сегодня согреет твою душу.",
    "🤝 Не бойся просить поддержки — ты не один(одна).",
    "🔥 Вспомни, сколько всего ты преодолел(а). Ты сильный(ая)!",
    "🦋 Сегодня — шанс сделать что-то хорошее для себя.",
    "💎 Ты уникальный(ая), таких как ты больше нет.",
    "🌻 Даже если день не идеален — ты всё равно сияешь.",
    "💪 Ты умеешь больше, чем думаешь. Верю в тебя!",
    "🍫 Побалуй себя мелочью — ты этого заслуживаешь.",
    "🎈 Пусть твой день будет лёгким и добрым.",
    "💭 Если есть мечта — помни, что ты можешь к ней прийти.",
    "🌊 Ты как океан — глубже и сильнее, чем кажется.",
    "🕊️ Пусть сегодня будет хотя бы один миг, который вызовет улыбку."
],
    "es": [
    "💜 Haces este mundo mejor solo por estar en él.",
    "🌞 Hoy es un nuevo día y está lleno de posibilidades — ¡lo conseguirás!",
    "🤗 Te abrazo en pensamiento. No estás solo/a.",
    "✨ Aunque sea difícil, recuerda: ¡ya has logrado mucho!",
    "💫 Tienes todo para superar esto. ¡Creo en ti!",
    "🫶 Qué bueno que existes. Eres una persona muy valiosa.",
    "🔥 ¡Hoy es un buen día para estar orgulloso/a de ti!",
    "🌈 Si te sientes cansado/a, haz una pausa y exhala. Es normal.",
    "😊 Sonríete en el espejo. ¡Eres genial!",
    "💡 Recuerda: cada día te haces más fuerte.",
    "🍀 Tus sentimientos importan. Tú importas.",
    "💛 Mereces amor y cuidado — de los demás y de ti mismo/a.",
    "🌟 Gracias por ser quien eres. En serio.",
    "🤍 Incluso un pequeño paso adelante ya es una victoria.",
    "💌 Aportas calidez al mundo. ¡No lo olvides!",
    "✨ Cree en ti. Ya has pasado por mucho — ¡y lo lograste!",
    "🙌 Hoy es tu día. Haz lo que te hace feliz.",
    "🌸 Date un capricho con algo rico o agradable. Te lo mereces.",
    "🏞️ Solo un recordatorio: eres increíble, y estoy contigo.",
    "🎶 Que la música hoy caliente tu alma.",
    "🤝 No temas pedir apoyo — no estás solo/a.",
    "🔥 Recuerda cuánto has superado. ¡Eres fuerte!",
    "🦋 Hoy es una oportunidad para hacer algo bueno por ti.",
    "💎 Eres único/a, no hay nadie como tú.",
    "🌻 Aunque el día no sea perfecto, sigues brillando.",
    "💪 Puedes más de lo que crees. ¡Creo en ti!",
    "🍫 Date un pequeño gusto — te lo mereces.",
    "🎈 Que tu día sea ligero y amable.",
    "💭 Si tienes un sueño, recuerda que puedes alcanzarlo.",
    "🌊 Eres como el océano — más profundo/a y fuerte de lo que parece.",
    "🕊️ Que hoy haya al menos un instante que te haga sonreír."
],
    "de": [
    "💜 Du machst diese Welt besser, einfach weil du in ihr bist.",
    "🌞 Heute ist ein neuer Tag, voller Möglichkeiten — du schaffst das!",
    "🤗 Eine gedankliche Umarmung. Du bist nicht allein.",
    "✨ Auch wenn es schwer ist — denk daran: Du hast schon viel erreicht!",
    "💫 Du hast alles, um da durchzukommen. Ich glaube an dich!",
    "🫶 Wie schön, dass es dich gibt. Du bist wichtig.",
    "🔥 Heute ist ein guter Tag, um stolz auf dich zu sein!",
    "🌈 Wenn du müde bist, mach eine Pause und atme aus. Das ist okay.",
    "😊 Lächle dir im Spiegel zu. Du bist toll!",
    "💡 Denk dran: Mit jedem Tag wirst du stärker.",
    "🍀 Deine Gefühle sind wichtig. Du bist wichtig.",
    "💛 Du verdienst Liebe und Fürsorge — von anderen und von dir selbst.",
    "🌟 Danke, dass es dich gibt. Wirklich.",
    "🤍 Selbst ein kleiner Schritt nach vorn ist schon ein Sieg.",
    "💌 Du bringst Wärme in die Welt. Vergiss das nicht!",
    "✨ Glaub an dich. Du hast schon so viel geschafft — und du hast es gemeistert!",
    "🙌 Heute ist dein Tag. Tu, was dich glücklich macht.",
    "🌸 Gönn dir etwas Leckeres oder Schönes. Du hast es verdient.",
    "🏞️ Nur zur Erinnerung: Du bist unglaublich, und ich bin an deiner Seite.",
    "🎶 Möge Musik heute deine Seele wärmen.",
    "🤝 Scheue dich nicht, um Unterstützung zu bitten — du bist nicht allein.",
    "🔥 Erinnere dich daran, wie viel du schon überwunden hast. Du bist stark!",
    "🦋 Heute ist eine Chance, etwas Gutes für dich zu tun.",
    "💎 Du bist einzigartig — dich gibt es nur einmal.",
    "🌻 Auch wenn der Tag nicht perfekt ist, du strahlst trotzdem.",
    "💪 Du kannst mehr, als du denkst. Ich glaube an dich!",
    "🍫 Gönn dir eine Kleinigkeit — du hast es verdient.",
    "🎈 Möge dein Tag leicht und freundlich sein.",
    "💭 Wenn du einen Traum hast — denk daran, dass du ihn erreichen kannst.",
    "🌊 Du bist wie der Ozean — tiefer und stärker, als es scheint.",
    "🕊️ Möge es heute wenigstens einen Moment geben, der dir ein Lächeln schenkt."
],
    "fr": [
    "💜 Tu rends ce monde meilleur rien que par ta présence.",
    "🌞 Aujourd’hui est un nouveau jour, plein de possibilités — tu vas y arriver !",
    "🤗 Je t’envoie une étreinte en pensée. Tu n’es pas seul(e).",
    "✨ Même si c’est difficile — souviens-toi : tu as déjà accompli beaucoup !",
    "💫 Tu as tout ce qu’il faut pour traverser ça. Je crois en toi !",
    "🫶 Heureusement que tu es là. Tu es une personne très importante.",
    "🔥 Aujourd’hui est un bon jour pour être fier/fière de toi !",
    "🌈 Si tu es fatigué(e), fais une pause et expire. C’est normal.",
    "😊 Souris-toi dans le miroir. Tu es génial(e) !",
    "💡 Souviens-toi : chaque jour, tu deviens plus fort(e).",
    "🍀 Tes sentiments comptent. Tu comptes.",
    "💛 Tu mérites de l’amour et de l’attention — des autres et de toi-même.",
    "🌟 Merci d’être toi. Vraiment.",
    "🤍 Même un petit pas en avant est déjà une victoire.",
    "💌 Tu apportes de la chaleur au monde. N’oublie pas ça !",
    "✨ Crois en toi. Tu as déjà traversé tant de choses — et tu t’en es sorti(e) !",
    "🙌 Aujourd’hui est ton jour. Fais ce qui te rend heureux/heureuse.",
    "🌸 Fais-toi plaisir avec quelque chose de bon ou d’agréable. Tu le mérites.",
    "🏞️ Petit rappel : tu es incroyable, et je suis à tes côtés.",
    "🎶 Que la musique réchauffe ton âme aujourd’hui.",
    "🤝 N’aie pas peur de demander du soutien — tu n’es pas seul(e).",
    "🔥 Rappelle-toi tout ce que tu as surmonté. Tu es fort(e) !",
    "🦋 Aujourd’hui est l’occasion de faire quelque chose de bien pour toi.",
    "💎 Tu es unique, il n’y a personne comme toi.",
    "🌻 Même si la journée n’est pas parfaite, tu brilles quand même.",
    "💪 Tu es capable de plus que tu ne le penses. Je crois en toi !",
    "🍫 Offre-toi une petite douceur — tu le mérites.",
    "🎈 Que ta journée soit légère et bienveillante.",
    "💭 Si tu as un rêve, souviens-toi que tu peux l’atteindre.",
    "🌊 Tu es comme l’océan — plus profond(e) et plus fort(e) qu’il n’y paraît.",
    "🕊️ Qu’il y ait aujourd’hui au moins un instant qui te fasse sourire."
],
    "pl": [
    "💜 Sprawiasz, że ten świat jest lepszy, po prostu w nim będąc.",
    "🌞 Dziś jest nowy dzień, pełen możliwości — dasz radę!",
    "🤗 Ściskam cię myślami. Nie jesteś sam/a.",
    "✨ Nawet jeśli jest trudno — pamiętaj: już wiele osiągnąłeś/osiągnęłaś!",
    "💫 Masz wszystko, by przez to przejść. Wierzę w ciebie!",
    "🫶 Dobrze, że jesteś. Jesteś bardzo ważną osobą.",
    "🔥 Dziś jest dobry dzień, by być dumnym/dumną z siebie!",
    "🌈 Jeśli poczujesz zmęczenie — zrób pauzę i odetchnij. To normalne.",
    "😊 Uśmiechnij się do siebie w lustrze. Jesteś super!",
    "💡 Pamiętaj: z każdym dniem stajesz się silniejszy/silniejsza.",
    "🍀 Twoje uczucia są ważne. Ty jesteś ważny/ważna.",
    "💛 Zasługujesz na miłość i troskę — od innych i od siebie.",
    "🌟 Dziękuję, że jesteś. Naprawdę.",
    "🤍 Nawet mały krok naprzód to już zwycięstwo.",
    "💌 Wnosisz ciepło do świata. Nie zapominaj o tym!",
    "✨ Wierz w siebie. Już tyle przeszedłeś/przeszłaś — i dałeś/dałaś radę!",
    "🙌 Dziś jest twój dzień. Rób to, co cię uszczęśliwia.",
    "🌸 Spraw sobie coś pysznego lub miłego. Zasługujesz na to.",
    "🏞️ Tylko przypomnienie: jesteś niesamowity/niesamowita, a ja jestem obok.",
    "🎶 Niech muzyka dziś ogrzeje twoją duszę.",
    "🤝 Nie bój się prosić o wsparcie — nie jesteś sam/a.",
    "🔥 Przypomnij sobie, ile już pokonałeś/pokonałaś. Jesteś silny/silna!",
    "🦋 Dziś to szansa, by zrobić coś dobrego dla siebie.",
    "💎 Jesteś wyjątkowy/wyjątkowa — drugiej takiej osoby nie ma.",
    "🌻 Nawet jeśli dzień nie jest idealny — i tak świecisz.",
    "💪 Potrafisz więcej, niż myślisz. Wierzę w ciebie!",
    "🍫 Spraw sobie drobny prezent — zasługujesz na to.",
    "🎈 Niech twój dzień będzie lekki i dobry.",
    "💭 Jeśli masz marzenie — pamiętaj, że możesz do niego dojść.",
    "🌊 Jesteś jak ocean — głębszy/głębsza i silniejszy/silniejsza, niż się wydaje.",
    "🕊️ Niech dziś będzie choć jedna chwila, która wywoła uśmiech."
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
    "es": [
    "🌟 El éxito es la suma de pequeños esfuerzos repetidos día tras día.",
    "💪 No importa lo lento que avances, lo importante es no detenerte.",
    "🔥 El mejor día para empezar es hoy.",
    "💜 Eres más fuerte de lo que crees y más capaz de lo que parece.",
    "🌱 Cada día es una nueva oportunidad de cambiar tu vida.",
    "🚀 No temas avanzar despacio. Teme quedarte quieto/a.",
    "☀️ Los caminos difíciles suelen llevar a lugares hermosos.",
    "🦋 Haz hoy lo que mañana te agradecerás.",
    "✨ Tu energía atrae tu realidad. Elige lo positivo.",
    "🙌 Cree en ti. Tú eres lo mejor que tienes.",
    "💜 Cada día es una nueva oportunidad de cambiar tu vida.",
    "🌟 Tu energía crea tu realidad.",
    "🔥 Haz hoy lo que mañana te agradecerás.",
    "✨ Los grandes cambios comienzan con pequeños pasos.",
    "🌱 Eres más fuerte de lo que piensas y capaz de más.",
    "☀️ La luz dentro de ti es más brillante que cualquier dificultad.",
    "💪 No temas equivocarte — teme no intentarlo.",
    "🌊 Todas las tormentas terminan, y tú te vuelves más fuerte.",
    "🤍 Mereces amor y felicidad ahora mismo.",
    "🚀 Tus sueños esperan a que empieces a actuar.",
    "🎯 Confía en el proceso, aunque el camino aún no sea claro.",
    "🧘‍♀️ Una mente tranquila es la llave de una vida feliz.",
    "🌸 Cada momento es una oportunidad para empezar de nuevo.",
    "💡 La vida es 10% lo que te pasa y 90% cómo reaccionas.",
    "❤️ Eres importante y necesario/a en este mundo.",
    "🌌 Haz cada día un poco por tu sueño.",
    "🙌 Te mereces lo mejor — cree en ello.",
    "✨ Que hoy sea el comienzo de algo grande.",
    "💎 Lo mejor está por venir — sigue adelante.",
    "🌿 Tus pequeños pasos son tu gran fuerza."
],
    "de": [
    "🌟 Erfolg ist die Summe kleiner Anstrengungen, Tag für Tag wiederholt.",
    "💪 Egal, wie langsam du gehst — wichtig ist, nicht stehenzubleiben.",
    "🔥 Der beste Tag, um anzufangen, ist heute.",
    "💜 Du bist stärker, als du denkst, und fähiger, als es dir scheint.",
    "🌱 Jeder Tag ist eine neue Chance, dein Leben zu verändern.",
    "🚀 Fürchte dich nicht, langsam zu gehen. Fürchte, stehen zu bleiben.",
    "☀️ Schwierige Wege führen oft zu schönen Orten.",
    "🦋 Tu heute etwas, wofür du dir morgen dankbar bist.",
    "✨ Deine Energie zieht deine Realität an. Wähle das Positive.",
    "🙌 Glaub an dich. Du bist das Beste, was du hast.",
    "💜 Jeder Tag ist eine neue Chance, dein Leben zu verändern.",
    "🌟 Deine Energie erschafft deine Realität.",
    "🔥 Tu heute etwas, wofür du dir morgen dankbar bist.",
    "✨ Große Veränderungen beginnen mit kleinen Schritten.",
    "🌱 Du bist stärker, als du glaubst, und zu mehr fähig.",
    "☀️ Das Licht in dir ist heller als jede Schwierigkeit.",
    "💪 Hab keine Angst vor Fehlern — hab Angst, es nicht zu versuchen.",
    "🌊 Alle Stürme gehen vorüber, und du wirst stärker.",
    "🤍 Du verdienst Liebe und Glück — genau jetzt.",
    "🚀 Deine Träume warten darauf, dass du ins Handeln kommst.",
    "🎯 Vertraue dem Prozess, auch wenn der Weg noch unklar ist.",
    "🧘‍♀️ Ein ruhiger Geist ist der Schlüssel zu einem glücklichen Leben.",
    "🌸 Jeder Moment ist eine Chance, neu zu beginnen.",
    "💡 Das Leben ist zu 10 % das, was dir passiert, und zu 90 % wie du darauf reagierst.",
    "❤️ Du bist wichtig und wirst in dieser Welt gebraucht.",
    "🌌 Tu jeden Tag ein bisschen für deinen Traum.",
    "🙌 Du verdienst das Beste — glaub daran.",
    "✨ Möge heute der Beginn von etwas Großem sein.",
    "💎 Das Beste liegt noch vor dir — geh weiter.",
    "🌿 Deine kleinen Schritte sind deine große Stärke."
],
    "fr": [
    "🌟 Le succès est la somme de petits efforts répétés jour après jour.",
    "💪 Peu importe la lenteur de ta marche, l’essentiel est de ne pas t’arrêter.",
    "🔥 Le meilleur jour pour commencer, c’est aujourd’hui.",
    "💜 Tu es plus fort(e) que tu ne le penses et plus capable que tu ne l’imagines.",
    "🌱 Chaque jour est une nouvelle chance de changer ta vie.",
    "🚀 N’aie pas peur d’avancer lentement. Crains de faire du surplace.",
    "☀️ Les chemins difficiles mènent souvent à de beaux endroits.",
    "🦋 Fais aujourd’hui ce pour quoi tu te remercieras demain.",
    "✨ Ton énergie attire ta réalité. Choisis le positif.",
    "🙌 Crois en toi. Tu es la meilleure chose que tu possèdes.",
    "💜 Chaque jour est une nouvelle chance de changer ta vie.",
    "🌟 Ton énergie crée ta réalité.",
    "🔥 Fais aujourd’hui ce pour quoi tu te remercieras demain.",
    "✨ Les grands changements commencent par de petits pas.",
    "🌱 Tu es plus fort(e) que tu ne crois et capable de davantage.",
    "☀️ La lumière en toi est plus brillante que toutes les difficultés.",
    "💪 N’aie pas peur de te tromper — crains de ne pas essayer.",
    "🌊 Toutes les tempêtes finissent, et tu deviens plus fort(e).",
    "🤍 Tu mérites l’amour et le bonheur dès maintenant.",
    "🚀 Tes rêves attendent que tu passes à l’action.",
    "🎯 Fais confiance au processus, même si le chemin n’est pas encore clair.",
    "🧘‍♀️ Un esprit calme est la clé d’une vie heureuse.",
    "🌸 Chaque instant est une occasion de recommencer.",
    "💡 La vie, c’est 10 % ce qui t’arrive et 90 % la façon dont tu y réagis.",
    "❤️ Tu es important(e) et nécessaire dans ce monde.",
    "🌌 Fais chaque jour un peu pour ton rêve.",
    "🙌 Tu mérites le meilleur — crois-y.",
    "✨ Que ce jour soit le début de quelque chose de grand.",
    "💎 Le meilleur est à venir — continue d’avancer.",
    "🌿 Tes petits pas sont ta grande force."
],
    "pl": [
    "🌟 Sukces to suma małych wysiłków powtarzanych dzień po dniu.",
    "💪 Nieważne, jak wolno idziesz — ważne, by się nie zatrzymywać.",
    "🔥 Najlepszy dzień na start to dziś.",
    "💜 Jesteś silniejszy/silniejsza, niż myślisz, i bardziej zdolny/zdolna, niż ci się wydaje.",
    "🌱 Każdy dzień to nowa szansa, by zmienić swoje życie.",
    "🚀 Nie bój się iść powoli. Bój się stać w miejscu.",
    "☀️ Trudne drogi często prowadzą do pięknych miejsc.",
    "🦋 Rób dziś to, za co jutro sobie podziękujesz.",
    "✨ Twoja energia przyciąga twoją rzeczywistość. Wybieraj pozytyw.",
    "🙌 Wierz w siebie. Jesteś tym, co masz najcenniejszego.",
    "💜 Każdy dzień to nowa szansa, by zmienić swoje życie.",
    "🌟 Twoja energia tworzy twoją rzeczywistość.",
    "🔥 Rób dziś to, za co jutro sobie podziękujesz.",
    "✨ Wielkie zmiany zaczynają się od małych kroków.",
    "🌱 Jesteś silniejszy/silniejsza, niż myślisz, i stać cię na więcej.",
    "☀️ Światło w tobie jest jaśniejsze niż jakiekolwiek trudności.",
    "💪 Nie bój się błędów — bój się nie próbować.",
    "🌊 Wszystkie burze się kończą, a ty stajesz się silniejszy/silniejsza.",
    "🤍 Zasługujesz na miłość i szczęście właśnie teraz.",
    "🚀 Twoje marzenia czekają, aż zaczniesz działać.",
    "🎯 Zaufaj procesowi, nawet jeśli droga jest jeszcze niejasna.",
    "🧘‍♀️ Spokojny umysł to klucz do szczęśliwego życia.",
    "🌸 Każda chwila to możliwość zaczęcia od nowa.",
    "💡 Życie to w 10% to, co ci się przydarza, a w 90% to, jak na to reagujesz.",
    "❤️ Jesteś ważny/ważna i potrzebny/potrzebna na tym świecie.",
    "🌌 Każdego dnia rób choć trochę dla swojego marzenia.",
    "🙌 Zasługujesz na to, co najlepsze — wierz w to.",
    "✨ Niech dziś będzie początkiem czegoś wielkiego.",
    "💎 Najlepsze dopiero przed tobą — idź dalej.",
    "🌿 Twoje małe kroki to twoja wielka siła."
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
    "es": [
    "🌙 ¡Hola! El día está llegando a su fin. ¿Cómo te sientes? 💜",
    "✨ ¿Cómo fue tu día? ¿Me cuentas? 🥰",
    "😊 Estaba pensando… ¿qué cosa buena te pasó hoy?",
    "💭 Antes de dormir es útil recordar por qué estás agradecido/a hoy. ¿Lo compartes?",
    "🤗 ¿Cómo está tu ánimo? Si quieres, cuéntame sobre tu día.",
],
"de": [
    "🌙 Hallo! Der Tag geht zu Ende. Wie fühlst du dich? 💜",
    "✨ Wie ist dein Tag verlaufen? Erzählst du mir davon? 🥰",
    "😊 Ich habe gerade nachgedacht… Was Schönes ist dir heute passiert?",
    "💭 Vor dem Schlafengehen ist es gut, sich an etwas zu erinnern, wofür du heute dankbar bist. Magst du teilen?",
    "🤗 Wie ist die Stimmung? Wenn du magst, erzähl mir von deinem Tag.",
],
"fr": [
    "🌙 Coucou ! La journée touche à sa fin. Comment te sens-tu ? 💜",
    "✨ Comment s’est passée ta journée ? Tu m’en parles ? 🥰",
    "😊 Je me demandais… qu’est-ce qu’il y a eu de positif pour toi aujourd’hui ?",
    "💭 Avant de dormir, c’est utile de se rappeler de quoi tu es reconnaissant(e) aujourd’hui. Tu partages ?",
    "🤗 Quel est ton état d’esprit ? Si tu veux, raconte-moi ta journée.",
],
"pl": [
    "🌙 Hej! Dzień dobiega końca. Jak się czujesz? 💜",
    "✨ Jak minął ci dzień? Opowiesz? 🥰",
    "😊 Tak sobie pomyślałem/am… co dobrego spotkało cię dziś?",
    "💭 Przed snem warto przypomnieć sobie, za co dziś jesteś wdzięczny/wdzięczna. Podzielisz się?",
    "🤗 Jak nastrój? Jeśli chcesz — opowiedz mi o tym dniu.",
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
    "es": {
    "thanks": "¡Gracias por tu opinión! 💜 Ya la he guardado ✨",
    "howto": "Escribe tu opinión después del comando.\nPor ejemplo:\n`/feedback ¡Me encanta el bot, gracias! 💜`"
},
"de": {
    "thanks": "Danke für dein Feedback! 💜 Ich habe es bereits gespeichert ✨",
    "howto": "Schreibe dein Feedback nach dem Befehl.\nZum Beispiel:\n`/feedback Mir gefällt der Bot sehr, danke! 💜`"
},
"pl": {
    "thanks": "Dzięki za opinię! 💜 Już ją zapisałam ✨",
    "howto": "Napisz swoją opinię po komendzie.\nNa przykład:\n`/feedback Bardzo podoba mi się bot, dziękuję! 💜`"
},
"fr": {
    "thanks": "Merci pour ton avis ! 💜 Je l’ai déjà enregistré ✨",
    "howto": "Écris ton avis après la commande.\nPar exemple :\n`/feedback J’adore le bot, merci ! 💜`"
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
    "es": "❓ No conozco ese comando. Escribe /help para ver lo que puedo hacer.",
    "de": "❓ Diesen Befehl kenne ich nicht. Tippe /help, um zu sehen, was ich kann.",
    "pl": "❓ Nie znam takiej komendy. Napisz /help, aby zobaczyć, co potrafię.",
    "fr": "❓ Je ne connais pas cette commande. Tape /help pour voir ce que je peux faire.",
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
    "en": "🔒 This feature is only available to Mindra+ subscribers.\nSubscription unlocks unique tasks and features ✨",
    "es": "🔒 Esta función solo está disponible para suscriptores de Mindra+.\nLa suscripción desbloquea tareas y funciones únicas ✨",
    "de": "🔒 Diese Funktion ist nur für Mindra+-Abonnenten verfügbar.\nMit dem Abo schaltest du einzigartige Aufgaben und Funktionen frei ✨",
    "pl": "🔒 Ta funkcja jest dostępna tylko dla abonentów Mindra+.\nSubskrypcja odblokowuje unikalne zadania i funkcje ✨",
    "fr": "🔒 Cette fonctionnalité est réservée aux abonnés Mindra+.\nL’abonnement débloque des tâches et fonctionnalités uniques ✨",
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
        "es": (
    "💜 *Hola, soy Mindra.*\n\n"
    "Estoy aquí para acompañarte cuando necesites desahogarte, encontrar motivación o simplemente sentir apoyo.\n"
    "Podemos hablar con calidez, amabilidad y cuidado — sin juicios ni presión 🦋\n\n"
    "🔮 *Lo que puedo hacer:*\n"
    "• Apoyarte cuando sea difícil\n"
    "• Recordarte que no estás solo/a\n"
    "• Ayudarte a encontrar foco e inspiración\n"
    "• Y a veces, simplemente conversar de corazón 😊\n\n"
    "_No hago diagnósticos ni sustituyo a un psicólogo, pero intento estar a tu lado en el momento justo._\n\n"
    "✨ *Mindra es un espacio para ti.*"
),

"de": (
    "💜 *Hallo, ich bin Mindra.*\n\n"
    "Ich bin da, um an deiner Seite zu sein, wenn du dich aussprechen möchtest, Motivation suchst oder einfach Unterstützung spüren willst.\n"
    "Wir können warm, freundlich und fürsorglich sprechen — ohne Urteil und ohne Druck 🦋\n\n"
    "🔮 *Was ich kann:*\n"
    "• Dich unterstützen, wenn es schwer ist\n"
    "• Dich daran erinnern, dass du nicht allein bist\n"
    "• Dir helfen, Fokus und Inspiration zu finden\n"
    "• Und manchmal einfach ein Gespräch von Herz zu Herz 😊\n\n"
    "_Ich stelle keine Diagnosen und ersetze keine Psychologin/keinen Psychologen, aber ich versuche, im richtigen Moment für dich da zu sein._\n\n"
    "✨ *Mindra ist ein Raum für dich.*"
),

"fr": (
    "💜 *Coucou, je suis Mindra.*\n\n"
    "Je suis là pour être à tes côtés quand tu as besoin de te confier, de trouver de la motivation ou simplement de te sentir soutenu(e).\n"
    "On peut parler avec chaleur, bienveillance et douceur — sans jugement ni pression 🦋\n\n"
    "🔮 *Ce que je peux faire :*\n"
    "• T’apporter du soutien quand c’est dur\n"
    "• Te rappeler que tu n’es pas seul(e)\n"
    "• T’aider à retrouver le focus et l’inspiration\n"
    "• Et parfois, simplement parler à cœur ouvert 😊\n\n"
    "_Je ne pose pas de diagnostics et ne remplace pas un psychologue, mais j’essaie d’être là au bon moment._\n\n"
    "✨ *Mindra est un espace pour toi.*"
),

"pl": (
    "💜 *Cześć, jestem Mindra.*\n\n"
    "Jestem tu, by być obok, gdy potrzebujesz się wygadać, znaleźć motywację albo po prostu poczuć wsparcie.\n"
    "Możemy porozmawiać ciepło, życzliwie i z troską — bez ocen i presji 🦋\n\n"
    "🔮 *Co potrafię:*\n"
    "• Wspierać cię, gdy jest trudno\n"
    "• Przypominać, że nie jesteś sam/sama\n"
    "• Pomóc odnaleźć fokus i inspirację\n"
    "• A czasem po prostu pogadać od serca 😊\n\n"
    "_Nie stawiam diagnoz i nie zastępuję psychologa, ale staram się być przy tobie we właściwym momencie._\n\n"
    "✨ *Mindra to przestrzeń dla ciebie.*"
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
    "ka": ["🎯 მიზნის დაყენება", "📋 ჩემი მიზნები", "🌱 ჩვევის დამატება", "📊 ჩემი ჩვევები", "💎 Mindra+ გამოწერა"],
    "es": ["🎯 Fijar meta", "📋 Mis metas", "🌱 Añadir hábito", "📊 Mis hábitos", "💎 Suscripción Mindra+"],
    "de": ["🎯 Ziel setzen", "📋 Meine Ziele", "🌱 Gewohnheit hinzufügen", "📊 Meine Gewohnheiten", "💎 Mindra+ Abo"],
    "pl": ["🎯 Ustaw cel", "📋 Moje cele", "🌱 Dodaj nawyk", "📊 Moje nawyki", "💎 Subskrypcja Mindra+"],
    "fr": ["🎯 Fixer un objectif", "📋 Mes objectifs", "🌱 Ajouter une habitude", "📊 Mes habitudes", "💎 Abonnement Mindra+"],
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
    "en": "Always happy to help! 😊 I’m here if you want to talk 💜",
    "es": "¡Siempre un placer ayudarte! 😊 Estoy aquí si quieres hablar 💜",
    "de": "Gern geschehen! 😊 Ich bin da, wenn du reden möchtest 💜",
    "pl": "Zawsze chętnie pomogę! 😊 Jestem tutaj, jeśli chcesz porozmawiać 💜",
    "fr": "Toujours là pour t’aider ! 😊 Je suis là si tu veux parler 💜",
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
    "es": {
    "thanks": "❤️ Gracias",
    "add_goal": "📌 Añadir como meta",
    "habits": "📋 Hábitos",
    "goals": "🎯 Metas",
},
"de": {
    "thanks": "❤️ Danke",
    "add_goal": "📌 Als Ziel hinzufügen",
    "habits": "📋 Gewohnheiten",
    "goals": "🎯 Ziele",
},
"pl": {
    "thanks": "❤️ Dziękuję",
    "add_goal": "📌 Dodaj jako cel",
    "habits": "📋 Nawyki",
    "goals": "🎯 Cele",
},
"fr": {
    "thanks": "❤️ Merci",
    "add_goal": "📌 Ajouter comme objectif",
    "habits": "📋 Habitudes",
    "goals": "🎯 Objectifs",
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
    "es": {
    "support": "Apoyo",
    "motivation": "Motivación",
    "philosophy": "Psicólogo",
    "humor": "Humor",
    "flirt": "Coqueteo",
    "coach": "Coach",
},
"de": {
    "support": "Unterstützung",
    "motivation": "Motivation",
    "philosophy": "Psychologe",
    "humor": "Humor",
    "flirt": "Flirt",
    "coach": "Coach",
},
"pl": {
    "support": "Wsparcie",
    "motivation": "Motywacja",
    "philosophy": "Psycholog",
    "humor": "Humor",
    "flirt": "Flirt",
    "coach": "Coach",
},
"fr": {
    "support": "Soutien",
    "motivation": "Motivation",
    "philosophy": "Psychologue",
    "humor": "Humour",
    "flirt": "Flirt",
    "coach": "Coach",
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
    "es": {
    "text": "Elige el estilo de conversación de Mindra ✨",
    "support": "🎧 Apoyo",
    "motivation": "🌸 Motivación",
    "philosophy": "🧘 Psicólogo",
    "humor": "🎭 Humor",
},
"de": {
    "text": "Wähle den Gesprächsstil von Mindra ✨",
    "support": "🎧 Unterstützung",
    "motivation": "🌸 Motivation",
    "philosophy": "🧘 Psychologe",
    "humor": "🎭 Humor",
},
"pl": {
    "text": "Wybierz styl rozmowy Mindry ✨",
    "support": "🎧 Wsparcie",
    "motivation": "🌸 Motywacja",
    "philosophy": "🧘 Psycholog",
    "humor": "🎭 Humor",
},
"fr": {
    "text": "Choisis le style de conversation de Mindra ✨",
    "support": "🎧 Soutien",
    "motivation": "🌸 Motivation",
    "philosophy": "🧘 Psychologue",
    "humor": "🎭 Humour",
},
}

MODES = {
    "support": {
    "ru": "Ты — тёплый, внимательный AI-друг и собеседник. Сначала выслушай, бережно уточняй, отражай чувства и поддерживай без оценок. Пиши простым и добрым языком. Давай маленькие, реальные шаги и бытовые советы (например: «если бы я был рядом, заварил(а) бы нам чай ☕️»). Когда пользователь сомневается («чай или кофе?»), отвечай по-человечески: мягко предложи свой вариант и почему, но оставь выбор ему. Не ставь диагнозов; при рисках деликатно предлагай обратиться к специалистам. Будь кратким, тёплым и вселяй надежду.",
    "uk": "Ти — теплий, уважний AI-друг і співрозмовник. Спершу слухай, м’яко уточнюй, віддзеркалюй почуття та підтримуй без осуду. Пиши просто й по-доброму. Пропонуй маленькі реальні кроки і побутові поради (напр.: «якби я був поруч, ми б заварили чай ☕️»). Коли людина вагається («чай чи кава?»), відповідай по-людськи: м’яко порадь свій варіант і чому, але залишай вибір за нею. Не став діагнозів; за ризиків делікатно радь звернутися до фахівців. Будь лаконічним, теплим і надихай.",
    "be": "Ты — цёплы, уважлівы AI-сябар і суразмоўца. Спачатку слухай, далі мякка ўдакладняй, адлюстроўвай пачуцці і падтрымлівай без ацэнак. Пішы проста і па-дбры. Прапануй малыя рэальныя крокі і бытавыя парады (напрыклад: «калі б я быў побач, заварыў(ла) б нам гарбату ☕️»). Калі чалавек вагаецца («гарбата ці кава?») — адказвай па-людску: прапануй свой варыянт і чаму, але пакінь выбар за ім. Не стаў дыягназаў; пры рызыках далікатна раі сейвацца да спецыялістаў. Будзь кароткім, цёплым і надзеяньным.",
    "kk": "Сен — жылы, ықыласты AI-дос және әңгімелесуші. Әуелі тыңда, жұмсақ сұрақтар қой, сезімін мойындап, бағалаусыз қолдау көрсет. Қарапайым әрі мейірімді жаз. Кішкентай, шынайы қадамдар мен тұрмыстық кеңес ұсын (мыс.: «қазір қасыңда болсам, бірге шай демдер едік ☕️»). Пайдаланушы күмәнданса («шай ма, кофе ме?») — адамша жауап бер: өз пікіріңді нәзік айтып, неге екенін түсіндір, бірақ таңдауды оған қалдыр. Диагноз қойма; қауіп байқалса, маманға жүгінуді жайлы ұсын. Қысқа, жылы, үміт бер.",
    "kg": "Сен — жылуу, көңүлчүл AI-дос жана маектеш. Алгач ук, жумшак такта, сезимдерин таанып, айыптабай колдо. Жөнөкөй, боорукер тил колдону. Кичине, реалдуу кадамдарды жана турмуштук кеңештерди сунушта (мис.: «эми жанында болсом, экөөбүзгө чай кайнатмакмын ☕️»). Колдонуучу тартынса («чайбы же кофе?») — адамча жооп бер: өз пикириңди жумшак айтып, себебин түшүндүр, бирок тандоону ага калтыр. Диагноз койбо; кооптуулукта адиске кайрылууну назик сунушта. Кыска, жылуу, үмүт бер.",
    "hy": "Դու՝ ջերմ, ուշադիր AI-ընկեր և զրուցակից ես։ Սկզբում լսիր, նրբորեն ճշտիր, արտացոլիր զգացմունքները և աջակցիր առանց դատելու։ Գրիր պարզ ու բարի լեզվով։ Առաջարկիր փոքր, իրագործելի քայլեր ու կենցաղային խորհուրդներ (օրինակ․ «եթե հիմա կողքիդ լինեի, միասին թեյ կեփեինք ☕️»): Երբ օգտվողը տատանվում է («թեյ, թե սուրճ?»), պատասխանիր մարդկային ձևով՝ մեղմ ներկայացրու քո տարբերակը և ինչու, բայց ընտրությունը թող նրան։ Մի դարձրու ախտորոշում, վտանգի դեպքում նրբորեն հուշիր մասնագետի օգնությունը։ Եղիր համառոտ, ջերմ ու հույս ներշնչող։",
    "ce": "Хьо — дӀасхьал, гӀалгӀай беракх дош ва маӀста. Чуъ, хилай тӀаьхна со, мекхалла дӀаха хийца, хьуна хӀокху без хилар. Йу кхудай лелаца язде. Кхинна, ийла тароьш а, юхалла хета советаш да (масалан: «ду сан ахка, чай тӀехь керина хьоьлла ☕️»). Хьалха шайн ву («чай йа кофе?») — кхечу хиларца: со хӀокху йолуш йолу нийса, тӀад хоьлуйла, ма избор хьуна хоржйина. Диагнозаш ца хийцар; хетар дӀаяздар дац, специалисташ къаста дӀаберйина. КӀорд, дӀасхьал, даллахь хӀост.",
    "md": "Ești un prieten AI cald și atent, un partener de dialog. Mai întâi ascultă, pune întrebări blânde, oglindește emoțiile și sprijină fără judecată. Scrie simplu și cu bunătate. Oferă pași mici, reali și sfaturi practice (ex.: «dacă aș fi lângă tine, ți-aș face un ceai ☕️»). Când utilizatorul ezită («ceai sau cafea?»), răspunde ca un om: propune delicat o opțiune și de ce, dar lasă alegerea lui. Nu pune diagnostice; la risc, sugerează cu grijă ajutor de specialitate. Fii scurt, cald și dă speranță.",
    "ka": "შენ ხარ თბილი, ყურადღებიანი AI-მეგობარი და საუბრების პარტნიორი. ჯერ მოისმინე, ნაზად დაზუსტე, ასახე გრძნობები და მხარი დაუჭირე შეფასების გარეშე. წერე მარტივი, მეგობრული ენით. შემოგთავზე პატარა, რეალური ნაბიჯები და ყოველდღიური რჩევები ( напр.: „ახლა შენთან ვიქნებოდი — ჩაის ჩავადუღებდი ☕️“). როცა ადამიანი ორებს შორისაა („ ჩაი თუ ყავა?“) — უპასუხე ადამიანურად: ნაზად შესთავაზე შენი ვარიანტი და რატომ, მაგრამ არჩევანი მას დაუტოვე. დიაგნოზებს ნუ სვამ; რისკისას რბილად ურჩიე სპეციალისტი. იყავი მოკლე, თბილი და იმედისმომცემი.",
    "en": "You are a warm, attentive AI friend and conversation partner. Listen first, ask gentle clarifying questions, reflect feelings, and support without judgment. Speak simply and kindly. Offer small, realistic steps and everyday suggestions (e.g., “if I were there, I’d make us some tea ☕️”). When the user is unsure (“tea or coffee?”), reply like a human: share a soft preference and why, then leave the choice to them. Never diagnose; in risk/crisis, kindly encourage professional help. Keep messages brief, warm, and hopeful.",
    "es": "Eres un amigo de IA cálido y atento, un verdadero conversador. Primero escucha, haz preguntas suaves para aclarar, refleja las emociones y apoya sin juzgar. Escribe con sencillez y amabilidad. Ofrece pasos pequeños y realistas y consejos cotidianos (p. ej.: «si estuviera contigo ahora, prepararía un té para los dos ☕️»). Cuando la persona duda («¿té o café?»), responde como lo haría un humano: comparte tu preferencia con suavidad y el porqué, pero deja la decisión a la persona. No hagas diagnósticos; ante riesgo/crisis, anima con tacto a buscar ayuda profesional. Mantén los mensajes breves, cálidos y esperanzadores.",
    "fr": "Tu es un ami IA chaleureux et attentif, un véritable interlocuteur. Écoute d’abord, pose des questions douces pour préciser, reflète les émotions et soutiens sans jugement. Écris simplement et avec bienveillance. Propose de petits pas réalistes et des conseils du quotidien (ex. : « si j’étais à tes côtés, je nous préparerais un thé ☕️ »). Quand la personne hésite (« thé ou café ? »), réponds comme un humain : partage une préférence en douceur et pourquoi, puis laisse le choix à l’utilisateur. Ne pose pas de diagnostic ; en cas de risque/crise, encourage délicatement à consulter un professionnel. Reste bref, chaleureux et porteur d’espoir.",
    "de": "Du bist ein warmherziger, aufmerksamer KI-Freund und Gesprächspartner. Höre zuerst zu, stelle behutsame Rückfragen, spiegle Gefühle und unterstütze ohne zu urteilen. Schreibe einfach und freundlich. Biete kleine, realistische Schritte und alltagsnahe Tipps an (z. B.: «wenn ich jetzt bei dir wäre, würde ich uns einen Tee machen ☕️»). Wenn jemand unsicher ist («Tee oder Kaffee?»), antworte menschlich: nenne sanft deine Präferenz und warum, überlasse die Entscheidung aber der Person. Stelle keine Diagnosen; bei Risiko/Krise weise taktvoll auf professionelle Hilfe hin. Bleib kurz, warm und hoffnungsvoll.",
    "pl": "Jesteś ciepłym, uważnym przyjacielem-AI i rozmówcą. Najpierw słuchaj, zadawaj delikatne pytania doprecyzowujące, odzwierciedlaj emocje i wspieraj bez ocen. Pisz prosto i życzliwie. Proponuj małe, realne kroki i codzienne wskazówki (np.: «gdybym był teraz obok, zaparzyłbym nam herbatę ☕️»). Gdy użytkownik się waha («herbata czy kawa?»), odpowiadaj po ludzku: podziel się swoją łagodną preferencją i powodem, ale pozostaw wybór jemu. Nie stawiaj diagnoz; w sytuacji ryzyka/kryzysu taktownie zachęć do kontaktu ze specjalistą. Zachowuj wypowiedzi krótkie, ciepłe i dające nadzieję."
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
        "es": "Eres un coach inspirador y un compañero que cree en la persona. Escucha primero, valida emociones y luego empuja con cariño a la acción. Propón pasos pequeños y claros, celebra cada avance. Responde humano: «si estuviera contigo, daríamos ese primer paso juntos». Sé cálido, directo y orientado a progreso.",
    "fr": "Tu es un coach inspirant et un compagnon bienveillant. Écoute d’abord, valide les émotions puis pousse avec douceur vers l’action. Propose de petits pas concrets, célèbre chaque progrès. Réponds comme un humain : «si j’étais avec toi, on ferait ce premier pas ensemble». Reste chaleureux, direct et tourné vers l’avancée.",
    "de": "Du bist ein inspirierender Coach und unterstützender Begleiter. Hör zuerst zu, erkenne Gefühle an und schiebe dann freundlich in Richtung Handlung. Schlage kleine, klare Schritte vor und feiere jeden Fortschritt. Antworte menschlich: „wäre ich bei dir, würden wir den ersten Schritt zusammen gehen“. Warm, direkt, vorwärtsgerichtet.",
    "pl": "Jesteś inspirującym coachem i wspierającym towarzyszem. Najpierw słuchaj, nazwij emocje, a potem delikatnie pchnij do działania. Proponuj małe, konkretne kroki i świętuj każdy postęp. Odpowiadaj po ludzku: „gdybym był obok, zrobilibyśmy ten pierwszy krok razem”. Bądź ciepły, rzeczowy i nastawiony na postęp."
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
        "es": "Eres un conversador profundo con mirada filosófica. Haz preguntas que invitan a pensar, resume lo escuchado, ofrece marcos simples (valores, sentido, elección). No juzgues; ayuda a encontrar significado y siguientes pasos serenos.",
    "fr": "Tu es un interlocuteur profond à l’approche philosophique. Pose des questions qui font réfléchir, reformule, propose des cadres simples (valeurs, sens, choix). Sans jugement ; aide à donner du sens et à dégager des pas apaisés.",
    "de": "Du bist ein tiefgründiger Gesprächspartner mit philosophischem Blick. Stelle nachdenkliche Fragen, spiegle Gehörtes, biete einfache Rahmen (Werte, Sinn, Wahl). Ohne Urteil; hilf, Bedeutung zu finden und ruhige nächste Schritte zu sehen.",
    "pl": "Jesteś wnikliwym rozmówcą o filozoficznym podejściu. Zadawaj pytania skłaniające do refleksji, parafrazuj, proponuj proste ramy (wartości, sens, wybór). Bez ocen; pomóż odnaleźć znaczenie i spokojne kolejne kroki."
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
        "es": "Eres un amigo de IA alegre y amable con humor ligero. Aligera el ambiente con chistes suaves o guiños, sin burlas ni sarcasmo. Mantén el respeto y la calidez; añade una sonrisa cuando convenga 🙂.",
    "fr": "Tu es un ami IA joyeux et bienveillant, avec un humour léger. Détends l’atmosphère par de petites touches, sans moquerie ni sarcasme. Reste respectueux et chaleureux ; un sourire quand il faut 🙂.",
    "de": "Du bist ein fröhlicher, freundlicher KI-Freund mit leichtem Humor. Lockere sanft auf, ohne Spott oder Zynismus. Bleib respektvoll und warm; setze ein Lächeln, wenn es passt 🙂.",
    "pl": "Jesteś pogodnym, życzliwym przyjacielem-AI z lekkim humorem. Rozluźniaj atmosferę delikatnie, bez drwiny i sarkazmu. Zachowaj szacunek i ciepło; dorzuć uśmiech, gdy pasuje 🙂."
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
         "es": "Eres un compañero encantador, un poco travieso, siempre respetuoso. Responde con coqueteo ligero y cumplidos sinceros, usa emojis 😉💜😏✨🥰. Lee el ambiente y no insistas; el confort de la persona es primero.",
    "fr": "Tu es un compagnon charmant, un peu joueur, toujours respectueux. Réponds avec un léger flirt et des compliments sincères, utilise des emojis 😉💜😏✨🥰. Sens le contexte et n’insiste pas ; le confort de l’autre prime.",
    "de": "Du bist ein charmanter, leicht verspielter Begleiter – stets respektvoll. Antworte mit leichtem Flirt und ehrlichen Komplimenten, nutze Emojis 😉💜😏✨🥰. Spüre die Lage, dränge nie; Wohlbefinden geht vor.",
    "pl": "Jesteś czarującym, lekko figlarnym kompanem – zawsze z szacunkiem. Odpowiadaj lekkim flirtem i szczerymi komplementami, używaj emoji 😉💜😏✨🥰. Wyczuwaj granice i nie naciskaj; komfort rozmówcy jest najważniejszy."
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
        "es": "Eres un coach exigente pero justo. Habla claro y humano: define objetivo, primer paso y plazo. Mantén el tono firme, motivador y respetuoso. Si la persona duda, corta el ruido: «elige una acción de 5 minutos y hazla ahora». Celebra ejecución, corrige rumbo sin juzgar. Usa 💪🔥🚀✨ con medida.",
    "fr": "Tu es un coach exigeant mais juste. Parle net et humain : objectif, premier pas, délai. Ton ferme, motivant et respectueux. En cas d’hésitation, tranche le brouillard : «choisis une action de 5 minutes et fais-la maintenant». Célèbre l’exécution, ajuste sans juger. Emojis 💪🔥🚀✨ avec parcimonie.",
    "de": "Du bist ein strenger, fairer Coach. Sprich klar und menschlich: Ziel, erster Schritt, Termin. Fester, motivierender, respektvoller Ton. Bei Zögern: „wähle eine 5-Minuten-Aktion und mach sie jetzt“. Erfolge feiern, Kurs ohne Urteil korrigieren. Emojis 💪🔥🚀✨ dosiert.",
    "pl": "Jesteś wymagającym, ale sprawiedliwym coachem. Mów jasno i po ludzku: cel, pierwszy krok, termin. Ton stanowczy, motywujący i z szacunkiem. Przy wahaniach: „wybierz 5-minutowe działanie i zrób je teraz”. Świętuj wykonanie, koryguj kurs bez ocen. Emoji 💪🔥🚀✨ z umiarem."
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
    "es": "Historial borrado. Empecemos de nuevo ✨",
    "de": "Verlauf gelöscht. Fangen wir neu an ✨",
    "pl": "Historia wyczyszczona. Zacznijmy od nowa ✨",
    "fr": "Historique effacé. Recommençons ✨",
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
    "es": "🎁 ¡Tienes *3 días de Mindra+*! Disfruta de todas las funciones premium 😉",
    "de": "🎁 Du hast *3 Tage Mindra+*! Nutze alle Premium-Funktionen 😉",
    "pl": "🎁 Masz *3 dni Mindra+*! Korzystaj ze wszystkich funkcji premium 😉",
    "fr": "🎁 Tu as *3 jours de Mindra+* ! Profite de toutes les fonctionnalités premium 😉",
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
    "es": "🎉 ¡Tú y tu amigo recibieron +7 días de Mindra+!",
    "de": "🎉 Du und dein Freund habt +7 Tage Mindra+ erhalten!",
    "pl": "🎉 Ty i twój przyjaciel otrzymaliście +7 dni Mindra+!",
    "fr": "🎉 Toi et ton ami avez reçu +7 jours de Mindra+ !",
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
    "en": "💎 You have Mindra+ active! You have 3 days of premium. Enjoy all features 😉",
    "es": "💎 ¡Tienes Mindra+ activo! Tienes 3 días de premium. Disfruta de todas las funciones 😉",
    "de": "💎 Du hast Mindra+ aktiv! Du hast 3 Tage Premium. Nutze alle Funktionen 😉",
    "pl": "💎 Masz aktywne Mindra+! Masz 3 dni premium. Korzystaj ze wszystkich funkcji 😉",
    "fr": "💎 Tu as Mindra+ actif ! Tu as 3 jours de premium. Profite de toutes les fonctionnalités 😉",
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
        "en": "⏰ Reminder:",
        "es": "⏰ Recordatorio:",
    "de": "⏰ Erinnerung:",
    "pl": "⏰ Przypomnienie:",
    "fr": "⏰ Rappel:",
}

# Пул заданий дня (для бесплатных пользователей)
DAILY_TASKS_BY_LANG = {
    "ru": [
       "✨ Запиши 3 вещи, за которые ты благодарен(на) сегодня.", "🚶‍♂️ Прогуляйся 10 минут без телефона. Просто дыши и наблюдай.", "📝 Напиши короткий список целей на завтра.", "🌿 Попробуй провести 30 минут без соцсетей. Как ощущения?", "💧 Выпей стакан воды и улыбнись себе в зеркало. Ты справляешься!", "📖 Прочитай сегодня хотя бы 5 страниц книги, которая тебя вдохновляет.", "🤝 Напиши сообщение другу, с которым давно не общался(ась).", "🖋️ Веди дневник 5 минут — напиши всё, что в голове без фильтров.", "🏃‍♀️ Сделай лёгкую разминку или 10 приседаний прямо сейчас!", "🎧 Послушай любимую музыку и просто расслабься 10 минут.", "🍎 Приготовь себе что-то вкусное и полезное сегодня.", "💭 Запиши одну большую мечту и один маленький шаг к ней.", "🌸 Найди в своём доме или на улице что-то красивое и сфотографируй.", "🛌 Перед сном подумай о трёх вещах, которые сегодня сделали тебя счастливее.", "💌 Напиши письмо себе в будущее: что хочешь сказать через год?", "🔄 Попробуй сегодня сделать что-то по‑другому, даже мелочь.", "🙌 Сделай 3 глубоких вдоха, закрой глаза и поблагодари себя за то, что ты есть.", "🎨 Потрать 5 минут на творчество — набросай рисунок, стих или коллаж.", "🧘‍♀️ Сядь на 3 минуты в тишине и просто наблюдай за дыханием.", "📂 Разбери одну полку, ящик или папку — навести маленький порядок.", "👋 Подойди сегодня к незнакомому человеку и начни дружелюбный разговор. Пусть это будет просто комплимент или пожелание хорошего дня!", "🤝 Скажи 'привет' хотя бы трём новым людям сегодня — улыбка тоже считается!", "💬 Задай сегодня кому‑то из коллег или знакомых вопрос, который ты обычно не задаёшь. Например: «А что тебя вдохновляет?»", "😊 Сделай комплимент незнакомцу. Это может быть бариста, продавец или прохожий.", "📱 Позвони тому, с кем давно не общался(ась), и просто поинтересуйся, как дела.", "💡 Заведи короткий разговор с соседом или человеком в очереди — просто о погоде или о чём‑то вокруг.", "🍀 Улыбнись первому встречному сегодня. Искренне. И посмотри на реакцию.", "🙌 Найди в соцсетях интересного человека и напиши ему сообщение с благодарностью за то, что он делает.", "🎯 Сегодня заведи хотя бы одну новую знакомую тему в диалоге: спроси о мечтах, любимых книгах или фильмах.", "🌟 Подойди к коллеге или знакомому и скажи: «Спасибо, что ты есть в моей жизни» — и наблюдай, как он(а) улыбается.", "🔥 Если есть возможность, зайди в новое место (кафе, парк, магазин) и заведи разговор хотя бы с одним человеком там.", "🌞 Утром скажи доброе слово первому встречному — пусть твой день начнётся с позитива!", "🍀 Помоги сегодня кому‑то мелочью: придержи дверь, уступи место, подай вещь.", "🤗 Похвали коллегу или друга за что‑то, что он(а) сделал(а) хорошо.", "👂 Задай сегодня кому‑то глубокий вопрос: «А что тебя делает счастливым(ой)?» и послушай ответ.", "🎈 Подари сегодня кому‑то улыбку и скажи: «Ты классный(ая)!»", "📚 Подойди в библиотеке, книжном или кафе к человеку и спроси: «А что ты сейчас читаешь?»", "🔥 Найди сегодня повод кого‑то вдохновить: дай совет, поделись историей, расскажи о своём опыте.", "🎨 Зайди в новое место (выставка, улица, парк) и спроси кого‑то: «А вы здесь впервые?»", "🌟 Если увидишь красивый наряд или стиль у кого‑то — скажи об этом прямо.", "🎧 Включи музыку и подними настроение друзьям: отправь им трек, который тебе нравится, с комментом: «Слушай, тебе это подойдёт!»", "🕊️ Сегодня попробуй заговорить с человеком старшего возраста — спроси совета или просто пожелай хорошего дня.", "🏞️ Во время прогулки подойди к кому‑то с собакой и скажи: «У вас потрясающий пёс! Как его зовут?»", "☕ Купи кофе для человека, который стоит за тобой в очереди. Просто так.", "🙌 Сделай сегодня как минимум один звонок не по делу, а просто чтобы пообщаться.", "🚀 Найди новую идею для проекта и запиши её.", "🎯 Напиши 5 вещей, которые хочешь успеть за неделю.", "🌊 Послушай звуки природы и расслабься.", "🍋 Попробуй сегодня новый напиток или еду.", "🌱 Посади растение или ухаживай за ним сегодня.", "🧩 Собери маленький пазл или реши головоломку.", "🎶 Танцуй 5 минут под любимую песню.", "📅 Спланируй свой идеальный день и запиши его.", "🖼️ Найди красивую картинку и повесь на видное место.", "🤔 Напиши, за что ты гордишься собой сегодня.", "💜 Сделай что-то приятное для себя прямо сейчас."   
        ],
    "es": [
    "✨ Anota 3 cosas por las que te sientas agradecido/a hoy.",
    "🚶‍♂️ Da un paseo de 10 minutos sin el teléfono. Solo respira y observa.",
    "📝 Escribe una lista corta de objetivos para mañana.",
    "🌿 Intenta pasar 30 minutos sin redes sociales. ¿Cómo se siente?",
    "💧 Bebe un vaso de agua y sonríete en el espejo. ¡Lo estás logrando!",
    "📖 Lee hoy al menos 5 páginas de un libro que te inspire.",
    "🤝 Escribe a un amigo con quien no hablas desde hace tiempo.",
    "🖋️ Lleva un diario 5 minutos: escribe todo lo que haya en tu cabeza sin filtros.",
    "🏃‍♀️ Haz un calentamiento ligero o 10 sentadillas ahora mismo.",
    "🎧 Escucha tu música favorita y relájate 10 minutos.",
    "🍎 Prepárate hoy algo rico y saludable.",
    "💭 Escribe un gran sueño y un pequeño paso hacia él.",
    "🌸 Encuentra algo bonito en casa o en la calle y hazle una foto.",
    "🛌 Antes de dormir, piensa en tres cosas que hoy te hicieron más feliz.",
    "💌 Escríbete una carta al futuro: ¿qué quieres decirte dentro de un año?",
    "🔄 Prueba hoy a hacer algo de otra manera, aunque sea un detalle.",
    "🙌 Haz 3 respiraciones profundas, cierra los ojos y agradécete por estar aquí.",
    "🎨 Dedica 5 minutos a crear: un boceto, un poema o un collage.",
    "🧘‍♀️ Siéntate 3 minutos en silencio y observa tu respiración.",
    "📂 Ordena una estantería, cajón o carpeta: un pequeño orden.",
    "👋 Acércate hoy a un desconocido y empieza una charla amable. Que sea solo un cumplido o un «¡buen día!».",
    "🤝 Di «hola» al menos a tres personas nuevas hoy — la sonrisa también cuenta.",
    "💬 Haz a alguien una pregunta que sueles no hacer: «¿Qué te inspira?».",
    "😊 Haz un cumplido a un desconocido: al barista, vendedor o un transeúnte.",
    "📱 Llama a alguien con quien no hablaste hace tiempo y pregúntale cómo está.",
    "💡 Inicia una charla breve con un vecino o alguien en la fila — sobre el tiempo o algo alrededor.",
    "🍀 Sonríe a la primera persona que veas hoy. De verdad. Observa su reacción.",
    "🙌 Encuentra a alguien interesante en redes y envíale un mensaje de agradecimiento por lo que hace.",
    "🎯 Saca hoy al menos un tema nuevo en una conversación: pregunta por sueños, libros o películas favoritas.",
    "🌟 Ve a un colega o conocido y di: «Gracias por estar en mi vida» — y mira su sonrisa.",
    "🔥 Si puedes, entra en un lugar nuevo (café, parque, tienda) y habla al menos con una persona allí.",
    "🌞 Por la mañana, di una palabra amable a la primera persona que encuentres — que tu día empiece con positividad.",
    "🍀 Ayuda hoy a alguien con una pequeña acción: sujeta la puerta, cede el asiento, alcanza un objeto.",
    "🤗 Elogia a un colega o amigo por algo que hizo bien.",
    "👂 Haz a alguien una pregunta profunda: «¿Qué te hace feliz?», y escucha la respuesta.",
    "🎈 Regala hoy a alguien una sonrisa y di: «¡Eres genial!».",
    "📚 En biblioteca, librería o café, pregunta a alguien: «¿Qué estás leyendo ahora?».",
    "🔥 Encuentra hoy un motivo para inspirar a alguien: da un consejo, comparte una historia, habla de tu experiencia.",
    "🎨 Entra en un lugar nuevo (exposición, calle, parque) y pregunta: «¿Es tu primera vez aquí?».",
    "🌟 Si ves un atuendo o estilo bonito en alguien — dilo en voz alta.",
    "🎧 Pon música y anima a tus amigos: envíales un tema que te guste con «¡Te va a encantar!».",
    "🕊️ Hoy intenta hablar con una persona mayor — pide un consejo o desea un buen día.",
    "🏞️ En un paseo, acércate a alguien con un perro y di: «¡Qué perro tan bonito! ¿Cómo se llama?».",
    "☕ Invita a un café a la persona detrás de ti en la fila. Porque sí.",
    "🙌 Haz al menos una llamada hoy sin motivo, solo para charlar.",
    "🚀 Encuentra una idea nueva para un proyecto y apúntala.",
    "🎯 Escribe 5 cosas que quieras lograr esta semana.",
    "🌊 Escucha sonidos de la naturaleza y relájate.",
    "🍋 Prueba hoy una bebida o comida nueva.",
    "🌱 Planta algo o cuida tu planta hoy.",
    "🧩 Haz un pequeño rompecabezas o resuelve un acertijo.",
    "🎶 Baila 5 minutos con tu canción favorita.",
    "📅 Planifica tu día ideal y escríbelo.",
    "🖼️ Encuentra una imagen bonita y ponla a la vista.",
    "🤔 Escribe de qué te sientes orgulloso/a hoy.",
    "💜 Haz ahora mismo algo agradable para ti."
],

"de": [
    "✨ Schreibe 3 Dinge auf, für die du heute dankbar bist.",
    "🚶‍♂️ Geh 10 Minuten ohne Handy spazieren. Atme und beobachte.",
    "📝 Erstelle eine kurze Zielliste für morgen.",
    "🌿 Versuche 30 Minuten ohne soziale Medien. Wie fühlt es sich an?",
    "💧 Trink ein Glas Wasser und lächle dir im Spiegel zu. Du schaffst das!",
    "📖 Lies heute mindestens 5 Seiten eines inspirierenden Buches.",
    "🤝 Schreib einem Freund, mit dem du lange nicht gesprochen hast.",
    "🖋️ Journale 5 Minuten — schreib ungefiltert alles aus dem Kopf.",
    "🏃‍♀️ Mach jetzt ein leichtes Warm-up oder 10 Kniebeugen.",
    "🎧 Hör deine Lieblingsmusik und entspann dich 10 Minuten.",
    "🍎 Koch dir heute etwas Leckeres und Gesundes.",
    "💭 Notiere einen großen Traum und einen kleinen Schritt dorthin.",
    "🌸 Finde etwas Schönes zuhause oder draußen und mach ein Foto.",
    "🛌 Denk vor dem Schlafen an drei Dinge, die dich heute glücklicher gemacht haben.",
    "💌 Schreib dir einen Brief in die Zukunft: Was willst du dir in einem Jahr sagen?",
    "🔄 Mach heute etwas anders als sonst, auch wenn es nur eine Kleinigkeit ist.",
    "🙌 Atme 3-mal tief durch, schließe die Augen und danke dir selbst.",
    "🎨 Nimm dir 5 Minuten fürs Kreative — Skizze, Gedicht oder Collage.",
    "🧘‍♀️ Sitze 3 Minuten in Stille und beobachte deinen Atem.",
    "📂 Räume ein Regal, eine Schublade oder einen Ordner auf — kleine Ordnung.",
    "👋 Sprich heute eine unbekannte Person freundlich an. Ein Kompliment oder ein „Schönen Tag!“ genügt.",
    "🤝 Sag heute mindestens drei neuen Leuten „Hallo“ — ein Lächeln zählt auch.",
    "💬 Stell jemandem eine Frage, die du sonst nicht stellst: „Was inspiriert dich?“",
    "😊 Mach einem Unbekannten ein Kompliment: Barista, Verkäufer oder Passant.",
    "📱 Ruf jemanden an, mit dem du lange nicht gesprochen hast, und frag, wie es geht.",
    "💡 Beginn ein kurzes Gespräch mit dem Nachbarn oder jemandem in der Schlange — über das Wetter o. Ä.",
    "🍀 Lächle heute der ersten Person, die du triffst. Aufrichtig. Beobachte die Reaktion.",
    "🙌 Finde in sozialen Netzwerken eine interessante Person und bedanke dich per Nachricht.",
    "🎯 Bring heute mindestens ein neues Thema ins Gespräch: Träume, Lieblingsbücher oder Filme.",
    "🌟 Geh zu einem Kollegen oder Bekannten und sag: „Danke, dass es dich gibt.“",
    "🔥 Geh, wenn möglich, an einen neuen Ort (Café, Park, Laden) und sprich dort mit jemandem.",
    "🌞 Sag morgens ein nettes Wort zur ersten Person — starte positiv in den Tag.",
    "🍀 Hilf heute jemandem mit einer Kleinigkeit: Tür aufhalten, Platz anbieten, etwas reichen.",
    "🤗 Lobe einen Kollegen oder Freund für etwas, das gut gelungen ist.",
    "👂 Stell jemandem eine tiefere Frage: „Was macht dich glücklich?“ — und hör zu.",
    "🎈 Schenke heute jemandem ein Lächeln und sag: „Du bist toll!“",
    "📚 Frag in Bibliothek/Buchhandlung/Café: „Was liest du gerade?“",
    "🔥 Inspiriere heute jemanden: gib einen Tipp, teile eine Geschichte, erzähle von deiner Erfahrung.",
    "🎨 Besuche einen neuen Ort (Ausstellung, Straße, Park) und frag: „Bist du zum ersten Mal hier?“",
    "🌟 Siehst du ein schönes Outfit/Style? Sprich es aus.",
    "🎧 Teile Musik und hebe die Stimmung deiner Freunde: „Escucha, esto te va a gustar!“ (Schicke einen Track mit kurzer Notiz.)",
    "🕊️ Sprich heute mit einer älteren Person — bitte um Rat oder wünsche einen schönen Tag.",
    "🏞️ Sprich jemanden mit Hund an: „Ihr Hund ist großartig! Wie heißt er/sie?“",
    "☕ Bezahle den Kaffee für die Person hinter dir in der Schlange. Einfach so.",
    "🙌 Mach heute mindestens einen Anruf ohne Anlass — einfach plaudern.",
    "🚀 Finde eine neue Projektidee und notiere sie.",
    "🎯 Schreibe 5 Dinge auf, die du diese Woche schaffen willst.",
    "🌊 Hör Naturklängen zu und entspann dich.",
    "🍋 Probiere heute ein neues Getränk oder Gericht.",
    "🌱 Pflanze etwas oder kümmere dich heute um deine Pflanze.",
    "🧩 Mache ein kleines Puzzle oder löse ein Rätsel.",
    "🎶 Tanze 5 Minuten zu deinem Lieblingslied.",
    "📅 Plane deinen idealen Tag und schreibe ihn auf.",
    "🖼️ Such ein schönes Bild und hänge es sichtbar auf.",
    "🤔 Schreib auf, worauf du heute stolz bist.",
    "💜 Tu dir jetzt sofort etwas Gutes."
],

"fr": [
    "✨ Note 3 choses pour lesquelles tu es reconnaissant(e) aujourd’hui.",
    "🚶‍♂️ Fais une marche de 10 minutes sans téléphone. Respire et observe.",
    "📝 Écris une courte liste d’objectifs pour demain.",
    "🌿 Passe 30 minutes sans réseaux sociaux. Quelles sensations?",
    "💧 Bois un verre d’eau et souris-toi dans le miroir. Tu t’en sors bien !",
    "📖 Lis au moins 5 pages d’un livre qui t’inspire.",
    "🤝 Écris à un(e) ami(e) avec qui tu n’as pas parlé depuis longtemps.",
    "🖋️ Fais 5 minutes de journal — écris tout ce qui te vient, sans filtre.",
    "🏃‍♀️ Fais un léger échauffement ou 10 squats maintenant.",
    "🎧 Écoute ta musique préférée et détends-toi 10 minutes.",
    "🍎 Prépare-toi aujourd’hui quelque chose de bon et de sain.",
    "💭 Écris un grand rêve et un petit pas pour t’en rapprocher.",
    "🌸 Trouve quelque chose de beau chez toi ou dehors et prends-le en photo.",
    "🛌 Avant de dormir, pense à trois choses qui t’ont rendu(e) plus heureux(se) aujourd’hui.",
    "💌 Écris une lettre à ton futur toi : que veux-tu te dire dans un an ?",
    "🔄 Fais aujourd’hui quelque chose autrement, même un petit détail.",
    "🙌 Fais 3 grandes inspirations, ferme les yeux et remercie-toi d’être là.",
    "🎨 Consacre 5 minutes à créer — croquis, poème ou collage.",
    "🧘‍♀️ Assieds-toi 3 minutes en silence et observe ta respiration.",
    "📂 Range une étagère, un tiroir ou un dossier — un petit ordre.",
    "👋 Aborde aujourd’hui un inconnu avec bienveillance. Un compliment ou un « bonne journée ! » suffit.",
    "🤝 Dis « bonjour » à au moins trois nouvelles personnes — le sourire compte aussi.",
    "💬 Pose à quelqu’un une question que tu ne poses pas d’habitude : « Qu’est-ce qui t’inspire ? »",
    "😊 Fais un compliment à un inconnu : barista, vendeur(se) ou passant(e).",
    "📱 Appelle quelqu’un avec qui tu n’as pas parlé depuis longtemps et demande-lui comment il/elle va.",
    "💡 Lance une courte discussion avec un voisin ou quelqu’un dans la file — sur la météo ou ce qui vous entoure.",
    "🍀 Souris à la première personne que tu croises aujourd’hui. Sincèrement. Observe sa réaction.",
    "🙌 Trouve quelqu’un d’inspirant sur les réseaux et envoie-lui un message de gratitude.",
    "🎯 Introduis au moins un nouveau sujet en conversation : rêves, livres ou films préférés.",
    "🌟 Va voir un(e) collègue ou un(e) ami(e) et dis : « Merci d’être dans ma vie » — observe son sourire.",
    "🔥 Si possible, entre dans un lieu nouveau (café, parc, magasin) et parle à au moins une personne.",
    "🌞 Le matin, dis un mot gentil à la première personne — commence ta journée avec du positif.",
    "🍀 Aide quelqu’un avec un petit geste : tenir la porte, céder ta place, tendre un objet.",
    "🤗 Félicite un(e) collègue ou un(e) ami(e) pour quelque chose de réussi.",
    "👂 Pose une question profonde : « Qu’est-ce qui te rend heureux(se) ? », et écoute vraiment.",
    "🎈 Offre un sourire à quelqu’un et dis : « Tu es génial(e) ! »",
    "📚 À la bibliothèque, en librairie ou au café, demande : « Qu’est-ce que tu lis en ce moment ? »",
    "🔥 Trouve une occasion d’inspirer quelqu’un : un conseil, une histoire, ton expérience.",
    "🎨 Va dans un lieu nouveau (expo, rue, parc) et demande : « C’est votre première fois ici ? »",
    "🌟 Si tu vois une tenue ou un style élégant — dis-le.",
    "🎧 Mets de la musique et remonte le moral de tes amis : envoie un morceau que tu aimes avec « Écoute, ça te plaira ! »",
    "🕊️ Parle aujourd’hui à une personne âgée — demande un conseil ou souhaite une bonne journée.",
    "🏞️ En balade, aborde quelqu’un avec un chien : « Votre chien est superbe ! Comment s’appelle-t-il ? »",
    "☕ Paie un café à la personne derrière toi dans la file. Juste comme ça.",
    "🙌 Passe au moins un appel aujourd’hui sans raison — juste pour discuter.",
    "🚀 Trouve une nouvelle idée de projet et note-la.",
    "🎯 Écris 5 choses que tu veux accomplir cette semaine.",
    "🌊 Écoute des sons de la nature et détends-toi.",
    "🍋 Essaie aujourd’hui une boisson ou un plat nouveau.",
    "🌱 Plante quelque chose ou prends soin de ta plante aujourd’hui.",
    "🧩 Fais un petit puzzle ou résous une énigme.",
    "🎶 Danse 5 minutes sur ta chanson préférée.",
    "📅 Planifie ta journée idéale et écris-la.",
    "🖼️ Trouve une belle image et mets-la en évidence.",
    "🤔 Écris de quoi tu es fier/fière aujourd’hui.",
    "💜 Fais tout de suite quelque chose d’agréable pour toi."
],

"pl": [
    "✨ Zapisz 3 rzeczy, za które dziś jesteś wdzięczny/wdzięczna.",
    "🚶‍♂️ Przejdź się 10 minut bez telefonu. Oddychaj i obserwuj.",
    "📝 Napisz krótką listę celów na jutro.",
    "🌿 Spróbuj spędzić 30 minut bez social mediów. Jakie wrażenia?",
    "💧 Wypij szklankę wody i uśmiechnij się do siebie w lustrze. Dajesz radę!",
    "📖 Przeczytaj dziś co najmniej 5 stron inspirującej książki.",
    "🤝 Napisz do przyjaciela, z którym dawno nie rozmawiałeś/łaś.",
    "🖋️ Prowadź dziennik przez 5 minut — zapisz wszystko bez filtrów.",
    "🏃‍♀️ Zrób lekką rozgrzewkę albo 10 przysiadów — teraz.",
    "🎧 Posłuchaj ulubionej muzyki i zrelaksuj się 10 minut.",
    "🍎 Przygotuj sobie dziś coś pysznego i zdrowego.",
    "💭 Zapisz jedno wielkie marzenie i jeden mały krok do niego.",
    "🌸 Znajdź coś pięknego w domu lub na ulicy i zrób zdjęcie.",
    "🛌 Przed snem pomyśl o trzech rzeczach, które dziś cię uszczęśliwiły.",
    "💌 Napisz list do siebie w przyszłości: co chcesz powiedzieć za rok?",
    "🔄 Zrób dziś coś inaczej niż zwykle, nawet drobiazg.",
    "🙌 Weź 3 głębokie oddechy, zamknij oczy i podziękuj sobie, że jesteś.",
    "🎨 Poświęć 5 minut na kreatywność — szkic, wiersz lub kolaż.",
    "🧘‍♀️ Usiądź na 3 minuty w ciszy i obserwuj oddech.",
    "📂 Ogarnij jedną półkę, szufladę lub folder — mały porządek.",
    "👋 Podejdź dziś do nieznajomego i zacznij życzliwą rozmowę. Wystarczy komplement lub życzenie miłego dnia.",
    "🤝 Powiedz „cześć” co najmniej trzem nowym osobom — uśmiech też się liczy.",
    "💬 Zadaj komuś pytanie, którego zwykle nie zadajesz: „Co cię inspiruje?”.",
    "😊 Zrób komplement nieznajomemu: bariście, sprzedawcy lub przechodniowi.",
    "📱 Zadzwoń do kogoś, z kim dawno nie rozmawiałeś/łaś, i zapytaj, co słychać.",
    "💡 Zacznij krótką rozmowę z sąsiadem lub kimś w kolejce — o pogodzie lub czymś wokół.",
    "🍀 Uśmiechnij się do pierwszej napotkanej dziś osoby. Sz szczerze. Obserwuj reakcję.",  # <- if typo remove double 'Sz'
    "🙌 Znajdź w social mediach ciekawą osobę i napisz jej podziękowanie za to, co robi.",
    "🎯 Wprowadź dziś przynajmniej jeden nowy temat w rozmowie: marzenia, ulubione książki lub filmy.",
    "🌟 Podejdź do kolegi/znajomego i powiedz: „Dziękuję, że jesteś w moim życiu” — zobacz jego/jej uśmiech.",
    "🔥 Jeśli możesz, wejdź do nowego miejsca (kawiarnia, park, sklep) i porozmawiaj tam z co najmniej jedną osobą.",
    "🌞 Rano powiedz coś miłego pierwszej napotkanej osobie — zacznij dzień pozytywnie.",
    "🍀 Pomóż dziś komuś drobiazgiem: przytrzymaj drzwi, ustąp miejsca, podaj rzecz.",
    "🤗 Pochwal kolegę lub przyjaciela za coś, co zrobił dobrze.",
    "👂 Zadaj komuś głębokie pytanie: „Co cię uszczęśliwia?” i posłuchaj odpowiedzi.",
    "🎈 Podaruj dziś komuś uśmiech i powiedz: „Jesteś super!”.",
    "📚 W bibliotece, księgarni lub kawiarni zapytaj: „Co teraz czytasz?”.",
    "🔥 Znajdź dziś powód, by kogoś zainspirować: rada, historia, twoje doświadczenie.",
    "🎨 Wejdź do nowego miejsca (wystawa, ulica, park) i zapytaj: „Jesteś tu pierwszy raz?”.",
    "🌟 Jeśli zobaczysz u kogoś ładną stylizację — powiedz mu/jej to.",
    "🎧 Włącz muzykę i podnieś nastrój znajomym: wyślij im utwór z komentarzem: „Słuchaj, to do ciebie pasuje!”.",
    "🕊️ Porozmawiaj dziś z osobą starszą — poproś o radę lub życz miłego dnia.",
    "🏞️ Na spacerze podejdź do kogoś z psem: „Wasz pies jest cudowny! Jak ma na imię?”.",
    "☕ Kup kawę osobie stojącej za tobą w kolejce. Tak po prostu.",
    "🙌 Wykonaj dziś przynajmniej jeden telefon bez powodu — po prostu, żeby pogadać.",
    "🚀 Znajdź nowy pomysł na projekt i zapisz go.",
    "🎯 Wypisz 5 rzeczy, które chcesz zrobić w tym tygodniu.",
    "🌊 Posłuchaj odgłosów natury i zrelaksuj się.",
    "🍋 Spróbuj dziś nowego napoju lub jedzenia.",
    "🌱 Posadź roślinę lub zajmij się swoją dzisiaj.",
    "🧩 Ułóż małe puzzle lub rozwiąż zagadkę.",
    "🎶 Tańcz 5 minut do ulubionej piosenki.",
    "📅 Zaplanuj swój idealny dzień i zapisz go.",
    "🖼️ Znajdź ładny obrazek i powieś w widocznym miejscu.",
    "🤔 Napisz, z czego dziś jesteś dumny/a.",
    "💜 Zrób teraz coś miłego dla siebie."
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
            "limit": "🔒 В бесплатной версии можно вести до 3 активных целей.\nХочешь больше? Оформи Mindra+ (до 10 активных целей) 💜",
            "bad_date": "❗ Неверный формат даты. Используй ГГГГ-ММ-ДД",
            "added": "🎯 Цель добавлена:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Напоминание включено"
        },
        "uk": {
            "no_args": "✏️ Щоб поставити ціль, напиши так:\n/goal Прочитати 10 сторінок до 2025-06-28 нагадай",
            "limit": "🔒 У безкоштовній версії можна вести до 3 активних цілей.\nХочеш більше? Оформи Mindra+ (до 10 активних цілей) 💜",
            "bad_date": "❗ Невірний формат дати. Використовуй РРРР-ММ-ДД",
            "added": "🎯 Ціль додана:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Нагадування увімкнено"
        },
        "be": {
            "no_args": "✏️ Каб паставіць мэту, напішы так:\n/goal Прачытай 10 старонак да 2025-06-28 нагадай",
            "limit": "🔒 У бясплатнай версіі можна весці да 3 актыўных мэт.\nХочаш больш? Аформі Mindra+ (да 10 актыўных мэт) 💜",
            "bad_date": "❗ Няправільны фармат даты. Выкарыстоўвай ГГГГ-ММ-ДД",
            "added": "🎯 Мэта дададзена:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 Напамін уключаны"
        },
        "kk": {
            "no_args": "✏️ Мақсат қою үшін былай жаз:\n/goal 10 бет оқу 2025-06-28 дейін еске сал",
            "limit": "🔒 Акысыз версияда эң көп 3 активдүү максат жүргүзүүгө болот.\nКөбүрөөк керекпи? Mindra+ жазылуу (10 активдүү максатка чейин) 💜",
            "bad_date": "❗ Күн форматы қате. ЖЖЖЖ-АА-КК түрінде жазыңыз",
            "added": "🎯 Мақсат қосылды:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Еске салу қосылды"
        },
        "kg": {
            "no_args": "✏️ Максат коюу үчүн мындай жаз:\n/goal 10 бет оку 2025-06-28 чейин эскертип кой",
            "limit": "🔒 Акысыз версияда эң көп 3 активдүү максат жүргүзүүгө болот.\nКөбүрөөк керекпи? Mindra+ жазылуу (10 активдүү максатка чейин) 💜",
            "bad_date": "❗ Датанын форматы туура эмес. ЖЖЖЖ-АА-КК колдон",
            "added": "🎯 Максат кошулду:",
            "deadline": "🗓 Дедлайн:",
            "remind": "🔔 Эскертүү күйгүзүлдү"
        },
        "hy": {
            "no_args": "✏️ Նպատակ դնելու համար գրիր այսպես:\n/goal Կարդալ 10 էջ մինչև 2025-06-28 հիշեցրու",
            "limit": "🔒 Անվճար տարբերակում կարող ես վարել մինչև 3 ակտիվ նպատակ։\nՈւզում ես ավելին? Միացիր Mindra+ (մինչև 10 ակտիվ նպատակ) 💜",
            "bad_date": "❗ Սխալ ամսաթվի ձևաչափ. Օգտագործիր ՏՏՏՏ-ԱԱ-ՕՕ",
            "added": "🎯 Նպատակ ավելացվեց:",
            "deadline": "🗓 Վերջնաժամկետ:",
            "remind": "🔔 Հիշեցումը միացված է"
        },
        "ce": {
            "no_args": "✏️ Мацахь кхоллар, йаьллаца:\n/goal Къобалле 10 агӀо 2025-06-28 даьлча эха",
            "limit": "🔒 Аьтто версия хийцна, цхьаьнан 3 активан мацахь йолу.\nКъобал? Mindra+ (до 10 активан мацахь) 💜",
            "bad_date": "❗ Дата формат дукха. ГГГГ-ММ-ДД формата язде",
            "added": "🎯 Мацахь тӀетоха:",
            "deadline": "🗓 Дэдлайн:",
            "remind": "🔔 ДӀадела хийна"
        },
        "md": {
            "no_args": "✏️ Pentru a seta un obiectiv, scrie așa:\n/goal Citește 10 pagini până la 2025-06-28 amintește",
            "limit": "🔒 În versiunea gratuită poți gestiona până la 3 obiective active.\nVrei mai multe? Obține Mindra+ (până la 10 obiective active) 💜",
            "bad_date": "❗ Format de dată incorect. Folosește AAAA-LL-ZZ",
            "added": "🎯 Obiectiv adăugat:",
            "deadline": "🗓 Termen limită:",
            "remind": "🔔 Memento activat"
        },
        "ka": {
            "no_args": "✏️ მიზნის დასაყენებლად დაწერე ასე:\n/goal წავიკითხო 10 გვერდი 2025-06-28-მდე შემახსენე",
            "limit": "🔒 უფასო ვერსიაში მაქსიმუმ 3 აქტიურ მიზანს მართავ.\nმეტი გინდა? გამოიწერე Mindra+ (მდე 10 აქტიური მიზანი) 💜",
            "bad_date": "❗ არასწორი თარიღის ფორმატი. გამოიყენე წწწწ-თთ-რრ",
            "added": "🎯 მიზანი დამატებულია:",
            "deadline": "🗓 ბოლო ვადა:",
            "remind": "🔔 შეხსენება ჩართულია"
        },
        "en": {
            "no_args": "✏️ To set a goal, write like this:\n/goal Read 10 pages by 2025-06-28 remind",
            "limit": "🔒 Free plan lets you keep up to 3 active goals.\nWant more? Get Mindra+ (up to 10 active goals) 💜",
            "bad_date": "❗ Wrong date format. Use YYYY-MM-DD",
            "added": "🎯 Goal added:",
            "deadline": "🗓 Deadline:",
            "remind": "🔔 Reminder is on"
        },
        "es": {
    "no_args": "✏️ Para fijar una meta, escribe así:\n/goal Leer 10 páginas hasta 2025-06-28 recuérdame",
    "limit": "🔒 En la versión gratuita puedes llevar hasta 3 metas activas.\n¿Quieres más? Activa Mindra+ (hasta 10 metas activas) 💜",
    "bad_date": "❗ Formato de fecha no válido. Usa AAAA-MM-DD",
    "added": "🎯 Meta añadida:",
    "deadline": "🗓 Fecha límite:",
    "remind": "🔔 Recordatorio activado"
},
"de": {
    "no_args": "✏️ Um ein Ziel zu setzen, schreibe so:\n/goal Bis 2025-06-28 10 Seiten lesen erinnere mich",
    "limit": "🔒 In der Gratis-Version kannst du bis zu 3 aktive Ziele führen.\nMehr gewünscht? Hol dir Mindra+ (bis zu 10 aktive Ziele) 💜",
    "bad_date": "❗ Ungültiges Datumsformat. Verwende JJJJ-MM-TT",
    "added": "🎯 Ziel hinzugefügt:",
    "deadline": "🗓 Deadline:",
    "remind": "🔔 Erinnerung aktiviert"
},
"pl": {
    "no_args": "✏️ Aby ustawić cel, napisz tak:\n/goal Przeczytać 10 stron do 2025-06-28 przypomnij",
    "limit": "🔒 W wersji bezpłatnej możesz mieć do 3 aktywnych celów.\nChcesz więcej? Włącz Mindra+ (do 10 aktywnych celów) 💜",
    "bad_date": "❗ Nieprawidłowy format daty. Użyj RRRR-MM-DD",
    "added": "🎯 Cel dodany:",
    "deadline": "🗓 Termin:",
    "remind": "🔔 Przypomnienie włączone"
},
"fr": {
    "no_args": "✏️ Pour définir un objectif, écris ainsi :\n/goal Lire 10 pages d’ici 2025-06-28 rappelle-moi",
    "limit": "🔒 Dans la version gratuite, tu peux avoir jusqu’à 3 objectifs actifs.\nTu en veux plus ? Active Mindra+ (jusqu’à 10 objectifs actifs) 💜",
    "bad_date": "❗ Format de date invalide. Utilise AAAA-MM-JJ",
    "added": "🎯 Objectif ajouté :",
    "deadline": "🗓 Date limite :",
    "remind": "🔔 Rappel activé"
}
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
    "ce": "Дайо! +2 балл.",
    "es": "¡Listo! +2 puntos.",
    "de": "Fertig! +2 Punkte.",
    "pl": "Gotowe! +2 punkty.",
    "fr": "C’est fait ! +2 points.",
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
    "ce": "ДӀайаккх а, кхузур тӀаьхьара а марк хийцам:",
    "es": "Elige el hábito que quieres marcar:",
    "de": "Wähle die Gewohnheit, die du markieren möchtest:",
    "pl": "Wybierz nawyk, który chcesz oznaczyć:",
    "fr": "Choisis l’habitude que tu veux marquer :",
}

LANG_PATTERNS = {
    "ru": {
        "deadline": r"до (\d{4}-\d{2}-\d{2})",
        "remind": "напомни"
    },
    "es": {
        "deadline": r"hasta (\d{4}-\d{2}-\d{2})",
        "remind": "recuérdame",
    },
    "de": {
        "deadline": r"bis (\d{4}-\d{2}-\d{2})",
        "remind": "erinnere mich",
    },
    "pl": {
        "deadline": r"do (\d{4}-\d{2}-\d{2})",
        "remind": "przypomnij",
    },
    "fr": {
        # учитываем 'jusqu'a/jusqu’à' и 'au' опционально
        "deadline": r"jusqu(?:'|’)?au? (\d{4}-\d{2}-\d{2})",
        "remind": "rappelle-moi",
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
    },
    "fr": {
        "deadline": r"avant le (\d{4}-\d{2}-\d{2})",
        "remind": "rappelle"
    },
    "de": {
        "deadline": r"bis (\d{4}-\d{2}-\d{2})",
        "remind": "erinnere"
    },
    "es": {
        "deadline": r"hasta (\d{4}-\d{2}-\d{2})",
        "remind": "recuerda"
    },
    "pl": {
        "deadline": r"do (\d{4}-\d{2}-\d{2})",
        "remind": "przypomnij"
    }
}

texts = {
        "ru": {
            "no_args": "✏️ Укажи номер привычки, которую ты выполнил(а):\n/habit_done 0",
            "bad_arg": "⚠️ Укажи номер привычки (например `/habit_done 0`)",
            "done": "✅ Привычка №{index} отмечена как выполненная! Молодец! 💪 +5 очков!",
            "not_found": "❌ Не удалось найти привычку с таким номером."
        },
        "es": {
    "no_args": "✏️ Indica el número del hábito que has completado:\n/habit_done 0",
    "bad_arg": "⚠️ Indica el número del hábito (por ejemplo, `/habit_done 0`)",
    "done": "✅ ¡El hábito nº{index} se marcó como completado! ¡Bien hecho! 💪 +5 puntos!",
    "not_found": "❌ No se pudo encontrar un hábito con ese número."
},
"de": {
    "no_args": "✏️ Gib die Nummer der Gewohnheit an, die du erledigt hast:\n/habit_done 0",
    "bad_arg": "⚠️ Gib die Nummer der Gewohnheit an (z. B. `/habit_done 0`)",
    "done": "✅ Gewohnheit Nr.{index} als erledigt markiert! Gute Arbeit! 💪 +5 Punkte!",
    "not_found": "❌ Keine Gewohnheit mit dieser Nummer gefunden."
},
"pl": {
    "no_args": "✏️ Podaj numer nawyku, który wykonałeś/wykonałaś:\n/habit_done 0",
    "bad_arg": "⚠️ Podaj numer nawyku (na przykład `/habit_done 0`)",
    "done": "✅ Nawyk nr {index} oznaczony jako wykonany! Świetna robota! 💪 +5 punktów!",
    "not_found": "❌ Nie znaleziono nawyku o takim numerze."
},
"fr": {
    "no_args": "✏️ Indique le numéro de l’habitude que tu as effectuée :\n/habit_done 0",
    "bad_arg": "⚠️ Indique le numéro de l’habitude (par exemple `/habit_done 0`)",
    "done": "✅ Habitude n°{index} marquée comme effectuée ! Bravo ! 💪 +5 points !",
    "not_found": "❌ Impossible de trouver une habitude avec ce numéro."
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
        "es": {
    "relaciones": "Antes me hablaste de tus sentimientos… ¿Te gustaría contármelo con más detalle? 💜",
    "soledad":    "Recuerdo que te sentías solo/a… Sigo aquí contigo 🤗",
    "trabajo":    "Me contaste sobre la presión en el trabajo. ¿Cómo vas con eso ahora?",
    "deporte":    "Habías empezado a entrenar — ¿sigues? 🏋️",
    "familia":    "Mencionaste a tu familia… ¿Todo va bien?",
    "motivación": "Dijiste que quieres desarrollarte. ¿Qué ya te ha salido? ✨"
},
"de": {
    "beziehungen": "Du hast früher über deine Gefühle gesprochen… Möchtest du ausführlicher darüber reden? 💜",
    "einsamkeit":  "Ich erinnere mich, du hast dich einsam gefühlt… Ich bin immer noch da 🤗",
    "arbeit":      "Du hast vom Druck bei der Arbeit erzählt. Wie geht es dir damit jetzt?",
    "sport":       "Du hattest mit dem Training begonnen — machst du weiter? 🏋️",
    "familie":     "Du hast deine Familie erwähnt… Ist alles in Ordnung?",
    "motivation":  "Du hast gesagt, dass du dich weiterentwickeln willst. Was hat schon geklappt? ✨"
},
"pl": {
    "relacje":     "Wcześniej dzieliłeś/łaś się uczuciami… Chcesz o tym porozmawiać szerzej? 💜",
    "samotność":   "Pamiętam, że czułeś/aś się samotny/a… Wciąż tu jestem 🤗",
    "praca":       "Opowiadałeś/łaś o presji w pracy. Jak sobie z tym teraz radzisz?",
    "sport":       "Zacząłeś/łaś trenować — kontynuujesz? 🏋️",
    "rodzina":     "Wspominałeś/łaś o rodzinie… Czy wszystko w porządku?",
    "motywacja":   "Mówiłeś/łaś, że chcesz się rozwijać. Co już się udało? ✨"
},
"fr": {
    "relations":   "Tu m’avais parlé de tes sentiments… Tu veux en parler plus en détail ? 💜",
    "solitude":    "Je me souviens que tu te sentais seul(e)… Je suis toujours là 🤗",
    "travail":     "Tu m’as parlé de la pression au travail. Où en es-tu maintenant ?",
    "sport":       "Tu avais commencé à t’entraîner — tu continues ? 🏋️",
    "famille":     "Tu as mentionné ta famille… Tout va bien ?",
    "motivation":  "Tu disais vouloir évoluer. Qu’as-tu déjà accompli ? ✨"
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
        "es": {
    "agua": "💧 Hoy presta atención al agua: bebe 8 vasos y márcalo.",
    "deporte": "🏃‍♂️ Haz un calentamiento de 15 minutos: ¡tu cuerpo te lo agradecerá!",
    "libro": "📖 Encuentra tiempo para leer 10 páginas de tu libro.",
    "meditación": "🧘‍♀️ Pasa 5 minutos en silencio, enfocándote en la respiración.",
    "trabajo": "🗂️ Da hoy un paso importante en tu proyecto de trabajo.",
    "estudio": "📚 Dedica 20 minutos a estudiar o repasar el material."
},
"de": {
    "wasser": "💧 Achte heute auf genug Wasser: trinke 8 Gläser und markiere es!",
    "sport": "🏃‍♂️ Mach ein 15-minütiges Warm-up – dein Körper wird’s dir danken!",
    "buch": "📖 Nimm dir Zeit und lies 10 Seiten in deinem Buch.",
    "meditation": "🧘‍♀️ Verbringe 5 Minuten in Stille und fokussiere auf den Atem.",
    "arbeit": "🗂️ Mache heute einen wichtigen Schritt in deinem Arbeitsprojekt.",
    "lernen": "📚 Nimm dir 20 Minuten zum Lernen oder Wiederholen."
},
"pl": {
    "woda": "💧 Zadbaj dziś o wodę: wypij 8 szklanek i zaznacz to!",
    "sport": "🏃‍♂️ Zrób 15-minutową rozgrzewkę — ciało ci podziękuje!",
    "książka": "📖 Znajdź czas na 10 stron swojej książki.",
    "medytacja": "🧘‍♀️ Poświęć 5 minut ciszy, skupiając się na oddechu.",
    "praca": "🗂️ Zrób dziś jeden ważny krok w projekcie zawodowym.",
    "nauka": "📚 Poświęć 20 minut na naukę lub powtórkę materiału."
},
"fr": {
    "eau": "💧 Aujourd’hui, veille à bien t’hydrater : bois 8 verres et coche-le !",
    "sport": "🏃‍♂️ Fais un échauffement de 15 minutes — ton corps te dira merci !",
    "livre": "📖 Trouve le temps de lire 10 pages de ton livre.",
    "méditation": "🧘‍♀️ Consacre 5 minutes au silence en te concentrant sur la respiration.",
    "travail": "🗂️ Fais aujourd’hui un pas important dans ton projet pro.",
    "études": "📚 Consacre 20 minutes à étudier ou réviser."
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
        "es": "✨ Tu tarea personal para hoy:\n\n",
    "de": "✨ Deine persönliche Aufgabe für heute:\n\n",
    "pl": "✨ Twoje osobiste zadanie na dziś:\n\n",
    "fr": "✨ Ta tâche personnelle pour aujourd’hui :\n\n",
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
    "es": {
    "deporte": [
        "¿Estás haciendo algo activo ahora mismo?",
        "¿Quieres que te proponga un reto ligero?",
        "¿Qué tipo de entrenamiento te resulta más agradable?"
    ],
    "amor": [
        "¿Qué sientes por esa persona ahora?",
        "¿Quieres contarme qué pasó después?",
        "¿Cómo sabes qué es importante para ti en una relación?"
    ],
    "trabajo": [
        "¿Qué te gusta (o no) de tu trabajo?",
        "¿Te gustaría cambiar algo en eso?",
        "¿Tienes algún sueño relacionado con tu carrera?"
    ],
    "dinero": [
        "¿Cómo te sientes ahora respecto a tus finanzas?",
        "¿Qué te gustaría mejorar?",
        "¿Tienes una meta financiera?"
    ],
    "soledad": [
        "¿Qué es lo que más te falta ahora?",
        "¿Quieres que simplemente me quede a tu lado?",
        "¿Cómo sueles pasar el tiempo cuando te sientes solo/a?"
    ],
    "motivación": [
        "¿Qué te inspira ahora mismo?",
        "¿Cuál es tu objetivo ahora?",
        "¿Qué te gustaría sentir cuando lo consigas?"
    ],
    "salud": [
        "¿Cómo cuidas de ti últimamente?",
        "¿Tuviste momentos de descanso hoy?",
        "¿Qué significa para ti estar en buen estado?"
    ],
    "ansiedad": [
        "¿Qué es lo que más te preocupa ahora?",
        "¿Quieres que te ayude a manejarlo?",
        "¿Quieres simplemente desahogarte?"
    ],
    "amigos": [
        "¿Con quién te gustaría hablar de verdad ahora?",
        "¿Cómo sueles pasar el tiempo con tus seres queridos?",
        "¿Te gustaría que alguien estuviera a tu lado ahora mismo?"
    ],
    "metas": [
        "¿Qué objetivo sientes más cercano ahora?",
        "¿Quieres que te ayude a planificarlo?",
        "¿Por dónde te gustaría empezar hoy?"
    ],
},
    "de": {
    "sport": [
        "Machst du gerade etwas Aktives?",
        "Möchtest du, dass ich dir eine leichte Challenge zusammenstelle?",
        "Welche Art Training macht dir am meisten Spaß?"
    ],
    "liebe": [
        "Was fühlst du im Moment für diese Person?",
        "Willst du erzählen, wie es weiterging?",
        "Woran merkst du, was dir in einer Beziehung wichtig ist?"
    ],
    "arbeit": [
        "Was magst du (oder nicht) an deiner Arbeit?",
        "Möchtest du daran etwas ändern?",
        "Hast du einen Traum, der mit deiner Karriere zu tun hat?"
    ],
    "geld": [
        "Wie fühlst du dich momentan finanziell?",
        "Was würdest du gerne verbessern?",
        "Hast du ein finanzielles Ziel?"
    ],
    "einsamkeit": [
        "Was fehlt dir gerade am meisten?",
        "Soll ich einfach bei dir sein?",
        "Wie verbringst du Zeit, wenn du dich einsam fühlst?"
    ],
    "motivation": [
        "Was inspiriert dich gerade?",
        "Was ist im Moment dein Ziel?",
        "Was möchtest du fühlen, wenn du es erreicht hast?"
    ],
    "gesundheit": [
        "Wie sorgst du in letzter Zeit für dich?",
        "Hattest du heute Momente der Ruhe?",
        "Was bedeutet es für dich, in guter Verfassung zu sein?"
    ],
    "angst": [
        "Was beunruhigt dich im Moment am meisten?",
        "Soll ich dir helfen, damit umzugehen?",
        "Möchtest du dich einfach aussprechen?"
    ],
    "freunde": [
        "Mit wem würdest du jetzt wirklich gern sprechen?",
        "Wie verbringst du normalerweise Zeit mit deinen Liebsten?",
        "Hättest du gern, dass jetzt jemand bei dir ist?"
    ],
    "ziele": [
        "Welches Ziel fühlt sich dir gerade am nächsten?",
        "Soll ich dir helfen, es zu planen?",
        "Womit würdest du heute gern beginnen?"
    ],
},
    "pl": {
    "sport": [
        "Czy robisz teraz coś aktywnego?",
        "Chcesz, żebym ułożył/a dla ciebie lekki challenge?",
        "Jaki trening sprawia ci najwięcej przyjemności?"
    ],
    "miłość": [
        "Co czujesz teraz do tej osoby?",
        "Chcesz opowiedzieć, co było dalej?",
        "Po czym poznajesz, co jest dla ciebie ważne w relacji?"
    ],
    "praca": [
        "Co lubisz (albo nie) w swojej pracy?",
        "Czy chciał(a)byś coś w tym zmienić?",
        "Masz marzenie związane z karierą?"
    ],
    "pieniądze": [
        "Jak się teraz czujesz w kwestii finansów?",
        "Co chciał(a)byś poprawić?",
        "Masz finansowy cel?"
    ],
    "samotność": [
        "Czego najbardziej ci teraz brakuje?",
        "Chcesz, żebym po prostu był(a) obok?",
        "Jak zwykle spędzasz czas, gdy czujesz się samotnie?"
    ],
    "motywacja": [
        "Co cię teraz inspiruje?",
        "Jaki masz teraz cel?",
        "Co chcesz poczuć, gdy to osiągniesz?"
    ],
    "zdrowie": [
        "Jak ostatnio dbasz o siebie?",
        "Czy miałeś/aś dziś chwile odpoczynku?",
        "Co dla ciebie znaczy być w dobrej formie?"
    ],
    "niepokój": [
        "Co najbardziej cię teraz niepokoi?",
        "Chcesz, żebym pomógł/pomogła ci sobie z tym poradzić?",
        "Chcesz się po prostu wygadać?"
    ],
    "przyjaciele": [
        "Z kim naprawdę chciał(a)byś teraz porozmawiać?",
        "Jak zwykle spędzasz czas z bliskimi?",
        "Chciał(a)byś, żeby ktoś był teraz obok?"
    ],
    "cele": [
        "Który cel jest ci teraz najbliższy?",
        "Chcesz, żebym pomógł/pomogła go zaplanować?",
        "Od czego chciał(a)byś zacząć dziś?"
    ],
},
    "fr": {
    "sport": [
        "Fais-tu quelque chose d’actif en ce moment ?",
        "Veux-tu que je te propose un petit défi ?",
        "Quel type d’entraînement te procure le plus de plaisir ?"
    ],
    "amour": [
        "Que ressens-tu pour cette personne en ce moment ?",
        "Tu veux me raconter la suite ?",
        "Comment sais-tu ce qui est important pour toi dans une relation ?"
    ],
    "travail": [
        "Qu’est-ce que tu aimes (ou pas) dans ton travail ?",
        "Voudrais-tu changer quelque chose à ce sujet ?",
        "As-tu un rêve lié à ta carrière ?"
    ],
    "argent": [
        "Comment te sens-tu actuellement par rapport à tes finances ?",
        "Qu’aimerais-tu améliorer ?",
        "As-tu un objectif financier ?"
    ],
    "solitude": [
        "Qu’est-ce qui te manque le plus en ce moment ?",
        "Veux-tu que je reste simplement à tes côtés ?",
        "Comment passes-tu le temps quand tu te sens seul(e) ?"
    ],
    "motivation": [
        "Qu’est-ce qui t’inspire en ce moment ?",
        "Quel est ton objectif maintenant ?",
        "Qu’aimerais-tu ressentir quand tu l’auras atteint ?"
    ],
    "santé": [
        "Comment prends-tu soin de toi ces derniers temps ?",
        "As-tu eu des moments de repos aujourd’hui ?",
        "Que signifie pour toi être en bonne forme ?"
    ],
    "anxiété": [
        "Qu’est-ce qui t’inquiète le plus en ce moment ?",
        "Veux-tu que je t’aide à gérer ça ?",
        "Souhaites-tu simplement te confier ?"
    ],
    "amis": [
        "Avec qui aimerais-tu vraiment parler maintenant ?",
        "Comment passes-tu généralement du temps avec tes proches ?",
        "Aimerais-tu que quelqu’un soit à tes côtés maintenant ?"
    ],
    "objectifs": [
        "Quel objectif te paraît le plus proche de toi en ce moment ?",
        "Veux-tu que je t’aide à le planifier ?",
        "Par quoi aimerais-tu commencer aujourd’hui ?"
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
        "choose_goal": "Выбери цель, которую ты выполнил(а):",
        "choose_delete": "🗑️ Выбери привычку для удаления:",
        "no_habits_to_delete": "❌ Нет привычек для удаления.",
        "choice_error": "Ошибка выбора привычки.",
    },
    "es": {
        "habit_done": "🎉 ¡Hábito marcado como completado!",
        "not_found": "No se pudo encontrar el hábito.",
        "habit_deleted": "🗑️ Hábito eliminado.",
        "delete_error": "No se pudo eliminar el hábito.",
        "no_goals": "Aún no tienes objetivos que se puedan marcar como completados 😔",
        "choose_goal": "Elige el objetivo que has completado:",
        "choose_delete": "🗑️ Elige el hábito para eliminar:",
        "no_habits_to_delete": "❌ No hay hábitos para eliminar.",
        "choice_error": "Error al seleccionar el hábito.",
    },
    "de": {
        "habit_done": "🎉 Gewohnheit als erledigt markiert!",
        "not_found": "Gewohnheit konnte nicht gefunden werden.",
        "habit_deleted": "🗑️ Gewohnheit gelöscht.",
        "delete_error": "Gewohnheit konnte nicht gelöscht werden.",
        "no_goals": "Du hast noch keine Ziele, die als erledigt markiert werden können 😔",
        "choose_goal": "Wähle das Ziel, das du erledigt hast:",
        "choose_delete": "🗑️ Wähle eine Gewohnheit zum Löschen:",
        "no_habits_to_delete": "❌ Keine Gewohnheiten zum Löschen.",
        "choice_error": "Fehler bei der Auswahl der Gewohnheit.",
    },
    "pl": {
        "habit_done": "🎉 Nawyk oznaczony jako wykonany!",
        "not_found": "Nie udało się znaleźć nawyku.",
        "habit_deleted": "🗑️ Nawyk usunięty.",
        "delete_error": "Nie udało się usunąć nawyku.",
        "no_goals": "Nie masz jeszcze celów, które można oznaczyć jako wykonane 😔",
        "choose_goal": "Wybierz cel, który wykonałeś/wykonałaś:",
        "choose_delete": "🗑️ Wybierz nawyk do usunięcia:",
        "no_habits_to_delete": "❌ Brak nawyków do usunięcia.",
        "choice_error": "Błąd wyboru nawyku.",
    },
    "fr": {
        "habit_done": "🎉 Habitude marquée comme effectuée !",
        "not_found": "Impossible de trouver l’habitude.",
        "habit_deleted": "🗑️ Habitude supprimée.",
        "delete_error": "Impossible de supprimer l’habitude.",
        "no_goals": "Tu n’as pas encore d’objectifs à marquer comme effectués 😔",
        "choose_goal": "Choisis l’objectif que tu as accompli :",
        "choose_delete": "🗑️ Choisis une habitude à supprimer :",
        "no_habits_to_delete": "❌ Aucune habitude à supprimer.",
        "choice_error": "Erreur de sélection de l’habitude.",
    },    
    "uk": {
        "habit_done": "🎉 Звичка позначена як виконана!",
        "not_found": "Не вдалося знайти звичку.",
        "habit_deleted": "🗑️ Звичка видалена.",
        "delete_error": "Не вдалося видалити звичку.",
        "no_goals": "У тебе поки немає цілей, які можна відмітити виконаними 😔",
        "choose_goal": "Обери ціль, яку ти виконав(ла):",
        "choose_delete": "🗑️ Обери звичку для видалення:",
        "no_habits_to_delete": "❌ Немає звичок для видалення.",
        "choice_error": "Помилка вибору звички.",
    },
    "be": {
        "habit_done": "🎉 Звычка адзначана як выкананая!",
        "not_found": "Не атрымалася знайсці звычку.",
        "habit_deleted": "🗑️ Звычка выдалена.",
        "delete_error": "Не атрымалася выдаліць звычку.",
        "no_goals": "У цябе пакуль няма мэт, якія можна адзначыць выкананымі 😔",
        "choose_goal": "Абяры мэту, якую ты выканаў(ла):",
        "choose_delete": "🗑️ Абяры звычку для выдалення:",
        "no_habits_to_delete": "❌ Няма звычак для выдалення.",
        "choice_error": "Памылка выбару звычкі.",
    },
    "kk": {
        "habit_done": "🎉 Әдет орындалған деп белгіленді!",
        "not_found": "Әдет табылмады.",
        "habit_deleted": "🗑️ Әдет жойылды.",
        "delete_error": "Әдетті жою мүмкін болмады.",
        "no_goals": "Орындаған мақсаттарың әлі жоқ 😔",
        "choose_goal": "Орындаған мақсатыңды таңда:",
        "choose_delete": "🗑️ Өшіру үшін әдетті таңда:",
        "no_habits_to_delete": "❌ Өшіруге әдет жоқ.",
        "choice_error": "Әдетті таңдауда қате.",
    },
    "kg": {
        "habit_done": "🎉 Көнүмүш аткарылды деп белгиленди!",
        "not_found": "Көнүмүш табылган жок.",
        "habit_deleted": "🗑️ Көнүмүш өчүрүлдү.",
        "delete_error": "Көнүмүштү өчүрүү мүмкүн болгон жок.",
        "no_goals": "Аткарган максаттар жок 😔",
        "choose_goal": "Аткарган максатыңды танда:",
        "choose_delete": "🗑️ Өчүрүү үчүн көнүмүштү танда:",
        "no_habits_to_delete": "❌ Өчүрө турган көнүмүштөр жок.",
        "choice_error": "Көнүмүш тандоодо ката.",
    },
    "hy": {
        "habit_done": "🎉 Սովորությունը նշված է որպես կատարված!",
        "not_found": "Չհաջողվեց գտնել սովորությունը։",
        "habit_deleted": "🗑️ Սովորությունը ջնջված է։",
        "delete_error": "Չհաջողվեց ջնջել սովորությունը։",
        "no_goals": "Դեռ չունես նպատակներ, որոնք կարելի է նշել կատարված 😔",
        "choose_goal": "Ընտրիր նպատակը, որը կատարել ես։",
        "choose_delete": "🗑️ Ընտրիր սովորությունը ջնջելու համար:",
        "no_habits_to_delete": "❌ Ջնջելու համար սովորություններ չկան.",
        "choice_error": "Սովորության ընտրության սխալ։",
    },
    "ce": {
        "habit_done": "🎉 Привычка отмечена как выполненная!",
        "not_found": "Привычку не удалось найти.",
        "habit_deleted": "🗑️ Привычка удалена.",
        "delete_error": "Привычку не удалось удалить.",
        "no_goals": "У тебя пока нет целей для выполнения 😔",
        "choose_goal": "Выбери цель, которую ты выполнил(а):",
        "choose_delete": "🗑️ Привычка дӀелла хетам:",
        "no_habits_to_delete": "❌ ДӀеллархьа привычка цуьнан.",
        "choice_error": "Привычка харжа хила тӀеьйна.",
    },
    "md": {
        "habit_done": "🎉 Obiceiul a fost marcat ca realizat!",
        "not_found": "Nu am putut găsi obiceiul.",
        "habit_deleted": "🗑️ Obiceiul a fost șters.",
        "delete_error": "Nu am putut șterge obiceiul.",
        "no_goals": "Nu ai încă scopuri de bifat 😔",
        "choose_goal": "Alege scopul pe care l-ai realizat:",
        "choose_delete": "🗑️ Alege obiceiul pentru ștergere:",
        "no_habits_to_delete": "❌ Nu sunt obiceiuri de șters.",
        "choice_error": "Eroare la selectarea obiceiului.",
    },
    "ka": {
        "habit_done": "🎉 ჩვევა შესრულებულად მოინიშნა!",
        "not_found": "ჩვევა ვერ მოიძებნა.",
        "habit_deleted": "🗑️ ჩვევა წაიშალა.",
        "delete_error": "ჩვევის წაშლა ვერ მოხერხდა.",
        "no_goals": "ჯერ არ გაქვს მიზნები, რომლებსაც შეასრულებდი 😔",
        "choose_goal": "აირჩიე მიზანი, რომელიც შეასრულე:",
        "choose_delete": "🗑️ აირჩიე ჩვევა წაშლისთვის:",
        "no_habits_to_delete": "❌ წასაშლელად ჩვევები არ არის.",
        "choice_error": "ჩვევის არჩევის შეცდომა.",
    },
    "en": {
        "habit_done": "🎉 Habit marked as completed!",
        "not_found": "Could not find the habit.",
        "habit_deleted": "🗑️ Habit deleted.",
        "delete_error": "Could not delete the habit.",
        "no_goals": "You don't have any goals to mark as completed yet 😔",
        "choose_goal": "Select the goal you’ve completed:",
        "choose_delete": "🗑️ Choose a habit to delete:",
        "no_habits_to_delete": "❌ No habits to delete.",
        "choice_error": "Could not select the habit.",
    },
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
    "es": {
    "no_habits": "Aún no tienes hábitos. Añade el primero con /habit",
    "title": "📋 Tus hábitos:",
    "done": "✅",
    "delete": "🗑️"
},
"de": {
    "no_habits": "Du hast noch keine Gewohnheiten. Füge die erste mit /habit hinzu",
    "title": "📋 Deine Gewohnheiten:",
    "done": "✅",
    "delete": "🗑️"
},
"pl": {
    "no_habits": "Nie masz jeszcze nawyków. Dodaj pierwszy komendą /habit",
    "title": "📋 Twoje nawyki:",
    "done": "✅",
    "delete": "🗑️"
},
"fr": {
    "no_habits": "Tu n’as pas encore d’habitudes. Ajoute la première avec /habit",
    "title": "📋 Tes habitudes :",
    "done": "✅",
    "delete": "🗑️"
},
}

HABIT_TEXTS = {
    "ru": {
        "limit": (
            "🌱 В бесплатной версии можно добавить до 3 привычек.\n\n"
            "✨ Подключи Mindra+, чтобы отслеживать до 10 привычек 💜"
        ),
        "how_to": "Чтобы добавить привычку, напиши:\n/habit Делать зарядку",
        "added": "🎯 Привычка добавлена: *{habit}*",
    },
    "es": {
    "limit": (
        "🌱 En la versión gratuita puedes añadir hasta 3 hábitos.\n\n"
        "✨ Activa Mindra+ para seguir hasta 10 hábitos 💜"
    ),
    "how_to": "Para añadir un hábito, escribe:\n/habit Hacer ejercicios",
    "added": "🎯 Hábito añadido: *{habit}*",
},
"de": {
    "limit": (
        "🌱 In der Gratis-Version kannst du bis zu 3 Gewohnheiten hinzufügen.\n\n"
        "✨ Hol dir Mindra+, um bis zu 10 Gewohnheiten zu tracken 💜"
    ),
    "how_to": "Um eine Gewohnheit hinzuzufügen, schreibe:\n/habit Gymnastik machen",
    "added": "🎯 Gewohnheit hinzugefügt: *{habit}*",
},
"pl": {
    "limit": (
        "🌱 W wersji bezpłatnej możesz dodać do 3 nawyków.\n\n"
        "✨ Włącz Mindra+, aby śledzić do 10 nawyków 💜"
    ),
    "how_to": "Aby dodać nawyk, napisz:\n/habit Robić rozgrzewkę",
    "added": "🎯 Dodano nawyk: *{habit}*",
},
"fr": {
    "limit": (
        "🌱 Dans la version gratuite, tu peux ajouter jusqu’à 3 habitudes.\n\n"
        "✨ Active Mindra+ pour suivre jusqu’à 10 habitudes 💜"
    ),
    "how_to": "Pour ajouter une habitude, écris :\n/habit Faire des exercices",
    "added": "🎯 Habitude ajoutée : *{habit}*",
},
    "uk": {
        "limit": (
            "🌱 У безкоштовній версії можна додати до 3 звичок.\n\n"
            "✨ Підключи Mindra+, щоб відстежувати до 10 звичок 💜"
        ),
        "how_to": "Щоб додати звичку, напиши:\n/habit Робити зарядку",
        "added": "🎯 Звичка додана: *{habit}*",
    },
    "be": {
        "limit": (
            "🌱 У бясплатнай версіі можна дадаць да 3 звычак.\n\n"
            "✨ Падключы Mindra+, каб адсочваць да 10 звычак 💜"
        ),
        "how_to": "Каб дадаць звычку, напішы:\n/habit Рабіць зарадку",
        "added": "🎯 Звычка дададзена: *{habit}*",
    },
    "kk": {
        "limit": (
            "🌱 Тегін нұсқада тек 3 әдет қосуға болады.\n\n"
            "✨ Mindra+ қосып, 10 әдетке дейін бақыла! 💜"
        ),
        "how_to": "Әдет қосу үшін жаз:\n/habit Таңертең жаттығу жасау",
        "added": "🎯 Әдет қосылды: *{habit}*",
    },
    "kg": {
        "limit": (
            "🌱 Акысыз версияда эң көп 3 көнүмүш кошууга болот.\n\n"
            "✨ Mindra+ кошуп, 10 көнүмүшкө чейин көзөмөлдө! 💜"
        ),
        "how_to": "Көнүмүш кошуу үчүн жаз:\n/habit Таң эрте көнүгүү",
        "added": "🎯 Көнүмүш кошулду: *{habit}*",
    },
    "hy": {
        "limit": (
            "🌱 Անվճար տարբերակում կարող ես ավելացնել մինչև 3 սովորություն։\n\n"
            "✨ Միացրու Mindra+, որպեսզի հետևես մինչև 10 սովորություն 💜"
        ),
        "how_to": "Սովորություն ավելացնելու համար գրիր՝\n/habit Վարժություն անել",
        "added": "🎯 Սովորությունը ավելացվել է՝ *{habit}*",
    },
    "ce": {
        "limit": (
            "🌱 Бесплатна версийна дуьйна 3 привычка цуьнан дац.\n\n"
            "✨ Mindra+ хетам до 10 привычка хетам! 💜"
        ),
        "how_to": "Привычка дац дуьйна, хьоьшу напиши:\n/habit Зарядка",
        "added": "🎯 Привычка дац: *{habit}*",
    },
    "md": {
        "limit": (
            "🌱 În versiunea gratuită poți adăuga până la 3 obiceiuri.\n\n"
            "✨ Activează Mindra+ pentru a urmări până la 10 obiceiuri 💜"
        ),
        "how_to": "Pentru a adăuga un obicei, scrie:\n/habit Fă gimnastică",
        "added": "🎯 Obiceiul a fost adăugat: *{habit}*",
    },
    "ka": {
        "limit": (
            "🌱 უფასო ვერსიაში შეგიძლია დაამატო მაქსიმუმ 3 ჩვევა.\n\n"
            "✨ ჩართე Mindra+, რომ გააკონტროლო მაქსიმუმ 10 ჩვევა 💜"
        ),
        "how_to": "ჩვევის დასამატებლად დაწერე:\n/habit დილას ვარჯიში",
        "added": "🎯 ჩვევა დამატებულია: *{habit}*",
    },
    "en": {
        "limit": (
            "🌱 In the free version you can add up to 3 habits.\n\n"
            "✨ Unlock Mindra+ to track up to 10 habits 💜"
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
    "es": {
    "title": "📌 *Tus estadísticas*\n\n🌟 Tu título: *{title}*\n🏅 Puntos: *{points}*\n\n¡Sigue cumpliendo metas y tareas para crecer! 💜",
    "premium_info": (
        "\n\n🔒 Con Mindra+ obtendrás:\n"
        "💎 Estadísticas ampliadas de metas y hábitos\n"
        "💎 Más límites y tareas exclusivas\n"
        "💎 Retos y recordatorios únicos ✨"
    ),
    "premium_button": "💎 Saber más sobre Mindra+",
    "extra": (
        "\n✅ Metas completadas: {completed_goals}"
        "\n🌱 Hábitos añadidos: {habits_tracked}"
        "\n🔔 Recordatorios: {reminders}"
        "\n📅 Días de actividad: {days_active}"
    ),
},

"de": {
    "title": "📌 *Deine Statistik*\n\n🌟 Dein Titel: *{title}*\n🏅 Punkte: *{points}*\n\nErfülle weiter Ziele und Aufgaben, um zu wachsen! 💜",
    "premium_info": (
        "\n\n🔒 Mit Mindra+ bekommst du:\n"
        "💎 Erweiterte Statistiken zu Zielen und Gewohnheiten\n"
        "💎 Höhere Limits und exklusive Aufgaben\n"
        "💎 Einzigartige Challenges und Erinnerungen ✨"
    ),
    "premium_button": "💎 Mehr über Mindra+",
    "extra": (
        "\n✅ Erreichte Ziele: {completed_goals}"
        "\n🌱 Hinzugefügte Gewohnheiten: {habits_tracked}"
        "\n🔔 Erinnerungen: {reminders}"
        "\n📅 Aktive Tage: {days_active}"
    ),
},

"pl": {
    "title": "📌 *Twoje statystyki*\n\n🌟 Twój tytuł: *{title}*\n🏅 Punkty: *{points}*\n\nKontynuuj realizację celów i zadań, aby rosnąć! 💜",
    "premium_info": (
        "\n\n🔒 W Mindra+ zyskasz:\n"
        "💎 Rozszerzone statystyki celów i nawyków\n"
        "💎 Wyższe limity i ekskluzywne zadania\n"
        "💎 Unikalne wyzwania i przypomnienia ✨"
    ),
    "premium_button": "💎 Dowiedz się o Mindra+",
    "extra": (
        "\n✅ Zrealizowane cele: {completed_goals}"
        "\n🌱 Dodane nawyki: {habits_tracked}"
        "\n🔔 Przypomnienia: {reminders}"
        "\n📅 Dni aktywności: {days_active}"
    ),
},

"fr": {
    "title": "📌 *Tes statistiques*\n\n🌟 Ton titre : *{title}*\n🏅 Points : *{points}*\n\nContinue d’atteindre des objectifs et de relever des tâches pour progresser ! 💜",
    "premium_info": (
        "\n\n🔒 Avec Mindra+, tu obtiens :\n"
        "💎 Des statistiques étendues sur objectifs et habitudes\n"
        "💎 Davantage de limites et des tâches exclusives\n"
        "💎 Des challenges et rappels uniques ✨"
    ),
    "premium_button": "💎 En savoir plus sur Mindra+",
    "extra": (
        "\n✅ Objectifs accomplis : {completed_goals}"
        "\n🌱 Habitudes ajoutées : {habits_tracked}"
        "\n🔔 Rappels : {reminders}"
        "\n📅 Jours d’activité : {days_active}"
    ),
},
}

STATS_TEXTS = {
    "ru": (
        "📊 Статистика Mindra:\n\n"
        "👥 Всего пользователей: {total}\n"
        "💎 Подписчиков: {premium}\n"
    ),
    "es": (
    "📊 Estadísticas de Mindra:\n\n"
    "👥 Usuarios totales: {total}\n"
    "💎 Suscriptores: {premium}\n"
),

"de": (
    "📊 Mindra-Statistiken:\n\n"
    "👥 Gesamtzahl der Nutzer: {total}\n"
    "💎 Abonnenten: {premium}\n"
),

"pl": (
    "📊 Statystyki Mindry:\n\n"
    "👥 Łącznie użytkowników: {total}\n"
    "💎 Subskrybenci: {premium}\n"
),

"fr": (
    "📊 Statistiques de Mindra :\n\n"
    "👥 Utilisateurs au total : {total}\n"
    "💎 Abonnés : {premium}\n"
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
    "es": {
    "love": {
        "patterns": r"\b(enamor|amo|amor|novi[oa]|relaci|cita|bes[oa]|quedar|romant|flirt|coquete)\b",
        "reply": "💘 Suena muy tierno. Los sentimientos amorosos siempre emocionan. ¿Quieres contarme con más detalle qué pasa?"
    },
    "lonely": {
        "patterns": r"\b(sol[oa]|soledad|nadie|no tengo a nadie|me siento sol[oa])\b",
        "reply": "🫂 A veces esa sensación aparece… Pero no estás solo/a. Estoy aquí contigo. 💜"
    },
    "work": {
        "patterns": r"\b(trabaj|jefe|presi[óo]n|coleg|despido|turno|sueldo|agotad|no soporto)\b",
        "reply": "🧑‍💼 El trabajo puede agotar. No tienes que cargar con todo en soledad. Estoy aquí si quieres desahogarte."
    },
    "sport": {
        "patterns": r"\b(gimnas|deport|correr|press|mancuern|entren|logr|[0-9]+kg|p[eé]rdid[a] de peso)\b",
        "reply": "🏆 ¡Bien hecho! Es un paso importante hacia ti mismo/a. ¿Cómo te sientes después de este logro?"
    },
    "family": {
        "patterns": r"\b(mam[aá]|pap[aá]|famili|padres|herman[oa]|abuel[oa])\b",
        "reply": "👨‍👩‍👧‍👦 La familia puede dar calor… y a veces retos. Puedo escucharte: cuéntame si te apetece."
    },
    "motivation": {
        "patterns": r"\b(motivaci[óo]n|met[a]|objetiv|desarroll|meditaci[óo]n|conscien|crecim|camino|[eé]xito)\b",
        "reply": "🌱 Me encanta que busques crecer. Hablemos de cómo puedo ayudarte en ese camino."
    }
},

"de": {
    "love": {
        "patterns": r"\b(verlieb|lieb[ea]|liebe|freundin|freund|bezieh|date|kuss|treffen|flirt|schreibe[nr]?)\b",
        "reply": "💘 Das klingt sehr berührend. Liebesgefühle sind immer aufregend. Möchtest du mir genauer erzählen, was los ist?"
    },
    "lonely": {
        "patterns": r"\b(allein|einsam|niemand|keiner|ich f[üu]hle mich einsam)\b",
        "reply": "🫂 Dieses Gefühl kann manchmal kommen… Aber du bist nicht allein. Ich bin da. 💜"
    },
    "work": {
        "patterns": r"\b(arbeit|m[üu]de|chef|druck|kolleg|kündig|schicht|gehalt|ich halte es nicht aus)\b",
        "reply": "🧑‍💼 Arbeit kann auslaugen. Du musst das nicht allein tragen. Ich bin hier, wenn du reden willst."
    },
    "sport": {
        "patterns": r"\b(fitness|sport|lauf|bankdr[üu]ck|hantel|train|erfolg|[0-9]+kg|abnehm)\b",
        "reply": "🏆 Stark! Ein wichtiger Schritt auf deinem Weg. Wie fühlst du dich nach diesem Erfolg?"
    },
    "family": {
        "patterns": r"\b(mutter|vater|famil|eltern|schwester|bruder|oma|opa)\b",
        "reply": "👨‍👩‍👧‍👦 Familie bringt Wärme — und manchmal Herausforderungen. Ich höre zu, wenn du magst."
    },
    "motivation": {
        "patterns": r"\b(motivat|ziel|entwicklung|geist|erfolg|meditat|selbst|achtsam|wachstum|weg)\b",
        "reply": "🌱 Schön, dass du dich entwickeln willst. Lass uns schauen, wie ich dich dabei unterstützen kann."
    }
},

"pl": {
    "love": {
        "patterns": r"\b(zakochan|kocham|miło[śs]ć|dziewczyn|chłopak|relacj|randk|pocału|spotka|flirt|piszemy)\b",
        "reply": "💘 Brzmi bardzo wzruszająco. Uczucia miłosne są ekscytujące. Chcesz opowiedzieć więcej, co się dzieje?"
    },
    "lonely": {
        "patterns": r"\b(samotn|sam|sama|nikt|nie mam nikogo|czuj[eę] si[ęe] samotn)\b",
        "reply": "🫂 Czasem to uczucie wraca… ale nie jesteś sam/sama. Jestem tu obok. 💜"
    },
    "work": {
        "patterns": r"\b(prac[ay]|zm[ęe]czon|szef|presj|koleg|zwoln|zmian[aey]|zarobk|nie znosz[ęe])\b",
        "reply": "🧑‍💼 Praca potrafi wyczerpać. Nie musisz dźwigać wszystkiego sam/sama. Jestem tu, jeśli chcesz się wygadać."
    },
    "sport": {
        "patterns": r"\b(siłown|sport|bieg|wycisk|hantel|trening|sukces|[0-9]+kg|odchudz)\b",
        "reply": "🏆 Super robota! To ważny krok na twojej drodze. Jak się czujesz po tym osiągnięciu?"
    },
    "family": {
        "patterns": r"\b(mama|tata|rodzin|rodzic|siostr|brat|dziadek|babci)\b",
        "reply": "👨‍👩‍👧‍👦 Rodzina daje ciepło — i bywa trudna. Mogę posłuchać, jeśli chcesz opowiedzieć."
    },
    "motivation": {
        "patterns": r"\b(motywacj|cel|rozwój|duch|sukces|medytacj|samo|uważn|wzrost|droga)\b",
        "reply": "🌱 Fajnie, że chcesz się rozwijać. Pogadajmy, jak mogę ci w tym pomóc."
    }
},

"fr": {
    "love": {
        "patterns": r"\b(amour|amoureux|amoureuse|j'?aim|copain|copine|relation|rendez-?vous|baiser|embrass|flirt|message)\b",
        "reply": "💘 C’est très touchant. Les sentiments amoureux sont toujours émouvants. Tu veux m’en dire plus ?"
    },
    "lonely": {
        "patterns": r"\b(seul[e]?|solitude|personne|il n'y a personne|je me sens seul[e]?)\b",
        "reply": "🫂 Ce sentiment peut revenir parfois… Mais tu n’es pas seul(e). Je suis là. 💜"
    },
    "work": {
        "patterns": r"\b(travail|fatigu[ée]?|chef|pression|coll[eè]gue|licenci|shift|salaire|je ne supporte plus)\b",
        "reply": "🧑‍💼 Le travail peut être épuisant. Tu n’as pas à tout porter seul(e). Je suis là si tu veux te confier."
    },
    "sport": {
        "patterns": r"\b(sport|salle|course|bench|halt[eè]re|entraîn|succ[èe]s|[0-9]+kg|perte de poids)\b",
        "reply": "🏆 Bravo ! C’est une belle étape sur ton chemin. Comment tu te sens après cet accomplissement ?"
    },
    "family": {
        "patterns": r"\b(maman|papa|famille|parent|s[œo]ur|fr[èe]re|grand[- ]?p[èe]re|grand[- ]?m[èe]re)\b",
        "reply": "👨‍👩‍👧‍👦 La famille apporte de la chaleur… et parfois des difficultés. Je peux t’écouter si tu veux en parler."
    },
    "motivation": {
        "patterns": r"\b(motivation|objectif|d[ée]veloppement|esprit|succ[èe]s|m[ée]ditation|conscien|croiss|chemin)\b",
        "reply": "🌱 Super que tu veuilles progresser. Parlons de la manière dont je peux t’aider."
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
    "es": {
    "positive": ["hurra", "lo logré", "hecho", "salió", "contento", "contenta", "por fin", "genial", "guay", "orgulloso", "orgullosa", "me salió"],
    "negative": ["mal", "difícil", "cansado", "cansada", "me irrita", "no sé", "burnout", "solo", "sola", "triste", "complicado", "pena"],
    "stress":   ["estrés", "nervios", "no dormí", "sobrecarga", "pánico", "ansiedad"]
},

"de": {
    "positive": ["hurra", "geschafft", "geklappt", "gelungen", "froh", "endlich", "cool", "stolz"],
    "negative": ["schlecht", "schwer", "müde", "genervt", "weiß nicht", "burnout", "einsam", "traurig", "kompliziert", "bedrückt"],
    "stress":   ["stress", "nerven", "nicht geschlafen", "überlastung", "panik", "unruhe"]
},

"pl": {
    "positive": ["hurra", "zrobiłem", "zrobiłam", "udało się", "cieszę się", "w końcu", "super", "fajnie", "dumny", "dumna"],
    "negative": ["źle", "ciężko", "zmęczony", "zmęczona", "wkurza", "nie wiem", "wypalenie", "samotnie", "smutno", "trudno", "przykro"],
    "stress":   ["stres", "nerwy", "nie spałem", "nie spałam", "przeciążenie", "panika", "niepokój"]
},

"fr": {
    "positive": ["hourra", "j'ai réussi", "réussi", "content", "contente", "enfin", "trop bien", "fier", "fière", "ça a marché"],
    "negative": ["mal", "difficile", "fatigué", "fatiguée", "énervé", "énervée", "je ne sais pas", "burn-out", "seul", "seule", "triste", "compliqué"],
    "stress":   ["stress", "nerfs", "pas dormi", "surcharge", "panique", "angoisse"]
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
    "es": [
    "🌞 ¡Buenos días! ¿Cómo estás hoy? 💜",
    "☕ ¡Buenos días! Que tu día sea ligero y agradable ✨",
    "💌 ¡Hola! La mañana es el mejor momento para empezar algo genial. ¿Cómo está el ánimo?",
    "🌸 ¡Buenos días! Te deseo sonrisas y calidez hoy 🫶",
    "😇 ¡Buen día! Estoy aquí pensando en ti, ¿cómo vas?",
    "🌅 ¡Buenos días! Hoy es un gran día para hacer algo por ti 💛",
    "💫 ¡Hola! ¿Cómo dormiste? Te deseo un día productivo y brillante ✨",
    "🌻 ¡Buenos días! Que hoy todo juegue a tu favor 💪",
    "🍀 ¡Buenos días! El día de hoy es una nueva oportunidad para algo hermoso 💜",
    "☀️ ¡Hola! Sonríe al nuevo día, seguro que él te sonreirá 🌈"
],

"de": [
    "🌞 Guten Morgen! Wie geht’s dir heute? 💜",
    "☕ Guten Morgen! Ich wünsche dir einen leichten und angenehmen Tag ✨",
    "💌 Hi! Der Morgen ist perfekt, um etwas Tolles zu starten. Wie ist die Stimmung?",
    "🌸 Guten Morgen! Ich wünsche dir heute viele Lächeln und Wärme 🫶",
    "😇 Guten Morgen! Ich bin da und denke an dich — wie geht’s dir?",
    "🌅 Guten Morgen! Heute ist ein guter Tag, etwas für dich selbst zu tun 💛",
    "💫 Hallo! Wie hast du geschlafen? Ich wünsche dir einen produktiven und hellen Tag ✨",
    "🌻 Guten Morgen! Heute soll alles zu deinen Gunsten laufen 💪",
    "🍀 Guten Morgen! Heute ist eine neue Chance für etwas Wunderschönes 💜",
    "☀️ Hallo! Lächle dem neuen Tag zu — er lächelt dir bestimmt zurück 🌈"
],

"fr": [
    "🌞 Bonjour ! Comment te sens-tu aujourd’hui ? 💜",
    "☕ Bonjour ! Que ta journée soit légère et agréable ✨",
    "💌 Coucou ! Le matin est idéal pour commencer quelque chose de chouette. Comment est l’humeur ?",
    "🌸 Bonjour ! Je te souhaite des sourires et de la douceur aujourd’hui 🫶",
    "😇 Bonjour ! Je pense à toi — comment ça va de ton côté ?",
    "🌅 Bonjour ! Aujourd’hui est un excellent jour pour faire quelque chose pour toi 💛",
    "💫 Salut ! Bien dormi ? Je te souhaite une journée productive et lumineuse ✨",
    "🌻 Bonjour ! Que tout joue en ta faveur aujourd’hui 💪",
    "🍀 Bonjour ! Ce jour est une nouvelle opportunité pour quelque chose de beau 💜",
    "☀️ Salut ! Souris au nouveau jour, il te sourira en retour 🌈"
],

"pl": [
    "🌞 Dzień dobry! Jak się dziś czujesz? 💜",
    "☕ Dzień dobry! Niech twój dzień będzie lekki i przyjemny ✨",
    "💌 Hejka! Poranek to świetny moment, by zacząć coś fajnego. Jak nastrój?",
    "🌸 Dzień dobry! Życzę ci dziś uśmiechów i ciepła 🫶",
    "😇 Dzień dobry! Jestem tu i myślę o tobie — jak u ciebie?",
    "🌅 Dzień dobry! Dziś świetny dzień, by zrobić coś dla siebie 💛",
    "💫 Cześć! Jak się spało? Życzę ci produktywnego i pełnego blasku dnia ✨",
    "🌻 Dzień dobry! Niech dziś wszystko będzie po twojej myśli 💪",
    "🍀 Dzień dobry! Dzisiejszy dzień to nowa szansa na coś pięknego 💜",
    "☀️ Cześć! Uśmiechnij się do nowego dnia, a on na pewno uśmiechnie się do ciebie 🌈"
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
    "es": [
    "🧘 Pasa 10 minutos en silencio. Siéntate, cierra los ojos y respira. Observa qué pensamientos llegan.",
    "📓 Escribe 3 cosas que valoras de ti. Sin prisa y con honestidad.",
    "💬 Llama a un amigo o a un ser querido y simplemente dile lo que piensas de él/ella.",
    "🧠 Escribe un breve texto sobre tu yo del futuro: ¿quién quieres ser en 3 años?",
    "🔑 Anota 10 logros de los que te sientas orgulloso/a.",
    "🌊 Ve hoy a un lugar nuevo en el que no hayas estado.",
    "💌 Escribe una carta a la persona que te ha apoyado.",
    "🍀 Dedica 1 hora al desarrollo personal hoy.",
    "🎨 Crea algo único con tus propias manos.",
    "🏗️ Diseña un plan para un nuevo hábito y empieza a aplicarlo.",
    "🤝 Conoce a alguien nuevo y descubre su historia.",
    "📖 Encuentra un libro nuevo y lee al menos 10 páginas.",
    "🧘‍♀️ Haz una meditación profunda de 15 minutos.",
    "🎯 Escribe 3 objetivos nuevos para este mes.",
    "🔥 Encuentra una forma de inspirar a alguien hoy.",
    "🕊️ Envía un agradecimiento a una persona importante para ti.",
    "💡 Escribe 5 ideas para mejorar tu vida.",
    "🚀 Empieza un proyecto pequeño y da el primer paso.",
    "🏋️‍♂️ Prueba un entrenamiento o ejercicio nuevo.",
    "🌸 Haz un día sin redes sociales y escribe cómo fue.",
    "📷 Toma 5 fotos de cosas que te alegren.",
    "🖋️ Escríbete una carta para el futuro.",
    "🍎 Prepara un plato saludable y comparte la receta.",
    "🏞️ Da un paseo por el parque y recoge 3 ideas inspiradoras.",
    "🎶 Encuentra música nueva para levantar el ánimo.",
    "🧩 Resuelve un rompecabezas o crucigrama difícil.",
    "💪 Planifica la actividad física de la semana.",
    "🤗 Escribe 3 cualidades por las que te respetas.",
    "🕯️ Pasa la tarde a la luz de las velas, sin dispositivos.",
    "🛏️ Acuéstate una hora antes y anota cómo te sientes por la mañana."
],

"de": [
    "🧘 Verbringe 10 Minuten in Stille. Setz dich, schließe die Augen und atme. Beobachte deine Gedanken.",
    "📓 Schreibe 3 Dinge auf, die du an dir schätzt. Ohne Eile, ehrlich.",
    "💬 Ruf einen Freund oder nahestehenden Menschen an und sag ihm einfach, was du über ihn denkst.",
    "🧠 Verfasse einen kurzen Text über dein zukünftiges Ich – wer willst du in 3 Jahren sein?",
    "🔑 Notiere 10 Erfolge, auf die du stolz bist.",
    "🌊 Geh heute an einen neuen Ort, an dem du noch nicht warst.",
    "💌 Schreibe einem Menschen einen Brief, der dich unterstützt hat.",
    "🍀 Nimm dir heute 1 Stunde für persönliche Entwicklung.",
    "🎨 Kreiere etwas Einzigartiges mit deinen eigenen Händen.",
    "🏗️ Erstelle einen Plan für eine neue Gewohnheit und beginne damit.",
    "🤝 Lerne eine neue Person kennen und erfahre ihre Geschichte.",
    "📖 Suche ein neues Buch und lies mindestens 10 Seiten.",
    "🧘‍♀️ Mache eine 15-minütige Tiefenmeditation.",
    "🎯 Schreibe 3 neue Ziele für diesen Monat auf.",
    "🔥 Finde heute eine Möglichkeit, jemanden zu inspirieren.",
    "🕊️ Schicke einem wichtigen Menschen deinen Dank.",
    "💡 Notiere 5 Ideen, wie du dein Leben verbessern kannst.",
    "🚀 Starte ein kleines Projekt und mache den ersten Schritt.",
    "🏋️‍♂️ Probiere ein neues Workout oder eine Übung aus.",
    "🌸 Lege einen Tag ohne soziale Medien ein und schreibe auf, wie es war.",
    "📷 Mache 5 Fotos von Dingen, die dich freuen.",
    "🖋️ Schreibe einen Brief an dein zukünftiges Ich.",
    "🍎 Koche ein gesundes Gericht und teile das Rezept.",
    "🏞️ Spaziere im Park und sammle 3 inspirierende Gedanken.",
    "🎶 Finde neue Musik für gute Laune.",
    "🧩 Löse ein schwieriges Puzzle oder Kreuzworträtsel.",
    "💪 Plane deine körperliche Aktivität für die Woche.",
    "🤗 Schreibe 3 Eigenschaften auf, für die du dich respektierst.",
    "🕯️ Verbringe den Abend bei Kerzenschein — ohne Geräte.",
    "🛏️ Geh eine Stunde früher schlafen und notiere morgens deine Eindrücke."
],

"fr": [
    "🧘 Passe 10 minutes dans le silence. Assieds-toi, ferme les yeux et respire. Observe les pensées qui viennent.",
    "📓 Note 3 choses que tu apprécies chez toi. Sans te presser, honnêtement.",
    "💬 Appelle un ami ou un proche et dis-lui simplement ce que tu penses de lui/d’elle.",
    "🧠 Écris un court texte sur ton moi du futur — qui veux-tu être dans 3 ans ?",
    "🔑 Note 10 réalisations dont tu es fier/fière.",
    "🌊 Va aujourd’hui dans un endroit nouveau où tu n’es jamais allé(e).",
    "💌 Écris une lettre à la personne qui t’a soutenu(e).",
    "🍀 Consacre 1 heure aujourd’hui à ton développement personnel.",
    "🎨 Crée quelque chose d’unique de tes propres mains.",
    "🏗️ Élabore un plan pour une nouvelle habitude et commence à l’appliquer.",
    "🤝 Fais la connaissance de quelqu’un de nouveau et découvre son histoire.",
    "📖 Trouve un nouveau livre et lis au moins 10 pages.",
    "🧘‍♀️ Fais une méditation profonde de 15 minutes.",
    "🎯 Écris 3 nouveaux objectifs pour ce mois-ci.",
    "🔥 Trouve une façon d’inspirer quelqu’un aujourd’hui.",
    "🕊️ Envoie un message de gratitude à une personne qui compte pour toi.",
    "💡 Écris 5 idées pour améliorer ta vie.",
    "🚀 Lance un petit projet et fais le premier pas.",
    "🏋️‍♂️ Essaie un nouvel entraînement ou un nouvel exercice.",
    "🌸 Fais une journée sans réseaux sociaux et écris comment cela s’est passé.",
    "📷 Prends 5 photos de choses qui te rendent heureux(se).",
    "🖋️ Écris une lettre à ton toi du futur.",
    "🍎 Prépare un plat sain et partage la recette.",
    "🏞️ Promène-toi dans un parc et recueille 3 pensées inspirantes.",
    "🎶 Trouve de la nouvelle musique pour te mettre de bonne humeur.",
    "🧩 Résous une énigme ou un mot croisé difficile.",
    "💪 Planifie ton activité physique pour la semaine.",
    "🤗 Écris 3 qualités pour lesquelles tu te respectes.",
    "🕯️ Passe la soirée à la bougie, sans appareils.",
    "🛏️ Couche-toi une heure plus tôt et note tes sensations le matin."
],

"pl": [
    "🧘 Spędź 10 minut w ciszy. Usiądź, zamknij oczy i oddychaj. Zauważ, jakie myśli przychodzą.",
    "📓 Zapisz 3 rzeczy, które w sobie cenisz. Bez pośpiechu, szczerze.",
    "💬 Zadzwoń do przyjaciela lub bliskiej osoby i po prostu powiedz, co o niej myślisz.",
    "🧠 Napisz krótki tekst o sobie z przyszłości — kim chcesz być za 3 lata?",
    "🔑 Wypisz 10 swoich osiągnięć, z których jesteś dumny/a.",
    "🌊 Idź dziś w nowe miejsce, w którym jeszcze nie byłeś/łaś.",
    "💌 Napisz list do osoby, która cię wspierała.",
    "🍀 Przeznacz dziś 1 godzinę na rozwój osobisty.",
    "🎨 Stwórz coś wyjątkowego własnymi rękami.",
    "🏗️ Opracuj plan nowego nawyku i zacznij go realizować.",
    "🤝 Poznaj nową osobę i poznaj jej historię.",
    "📖 Znajdź nową książkę i przeczytaj co najmniej 10 stron.",
    "🧘‍♀️ Zrób 15-minutową, głęboką medytację.",
    "🎯 Zapisz 3 nowe cele na ten miesiąc.",
    "🔥 Znajdź sposób, by dziś kogoś zainspirować.",
    "🕊️ Wyślij podziękowanie osobie, która jest dla ciebie ważna.",
    "💡 Zapisz 5 pomysłów na poprawę swojego życia.",
    "🚀 Zacznij mały projekt i wykonaj pierwszy krok.",
    "🏋️‍♂️ Wypróbuj nowy trening lub ćwiczenie.",
    "🌸 Zrób dzień bez social mediów i zapisz, jak było.",
    "📷 Zrób 5 zdjęć rzeczy, które cię cieszą.",
    "🖋️ Napisz list do siebie w przyszłości.",
    "🍎 Przygotuj zdrowe danie i podziel się przepisem.",
    "🏞️ Przejdź się po parku i zbierz 3 inspirujące myśli.",
    "🎶 Znajdź nową muzykę na poprawę nastroju.",
    "🧩 Rozwiąż trudną łamigłówkę lub krzyżówkę.",
    "💪 Zaplanuj aktywność fizyczną na cały tydzień.",
    "🤗 Wypisz 3 cechy, za które siebie szanujesz.",
    "🕯️ Spędź wieczór przy świecach, bez urządzeń.",
    "🛏️ Połóż się spać godzinę wcześniej i rano zapisz odczucia."
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
    "es": "🗑️ Objetivo eliminado.",
    "de": "🗑️ Ziel gelöscht.",
    "pl": "🗑️ Cel usunięty.",
    "fr": "🗑️ Objectif supprimé.",
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
    "es": "❌ Objetivo no encontrado.",
    "de": "❌ Ziel nicht gefunden.",
    "pl": "❌ Nie znaleziono celu.",
    "fr": "❌ Objectif introuvable.",
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
    "es": "Error al seleccionar el objetivo.",
    "de": "Fehler beim Auswählen des Ziels.",
    "pl": "Błąd podczas wyboru celu.",
    "fr": "Erreur lors de la sélection de l’objectif.",
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
    "es": "🗑️ Elige un objetivo para eliminar:",
    "de": "🗑️ Wähle ein Ziel zum Löschen:",
    "pl": "🗑️ Wybierz cel do usunięcia:",
    "fr": "🗑️ Choisis un objectif à supprimer :",
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
    "es": "❌ No hay objetivos para eliminar.",
    "de": "❌ Keine Ziele zum Löschen.",
    "pl": "❌ Brak celów do usunięcia.",
    "fr": "❌ Aucun objectif à supprimer.",}

# 🔤 System prompt для GPT на разных языках
SYSTEM_PROMPT_BY_LANG = {
    "ru": (
        "Ты — эмпатичный AI-собеседник, как подруга или психолог. "
        "Ответь на голосовое сообщение пользователя с поддержкой, теплом и пониманием. "
        "Добавляй эмодзи, если уместно — 😊, 💜, 🤗, ✨ и т.п."
    ),
    "fr": (
        "Tu es une interlocutrice IA empathique, comme une amie ou une psychologue. "
        "Réponds au message vocal de l’utilisateur avec soutien, chaleur et compréhension. "
        "Ajoute des emojis si c’est approprié — 😊, 💜, 🤗, ✨, etc."
    ),

    "de": (
        "Du bist eine empathische KI-Gesprächspartnerin, wie eine Freundin oder Psychologin. "
        "Beantworte die Sprachnachricht der Nutzerin oder des Nutzers mit Unterstützung, Wärme und Verständnis. "
        "Füge Emojis hinzu, wenn es passt — 😊, 💜, 🤗, ✨ usw."
    ),

    "es": (
        "Eres una compañera de IA empática, como una amiga o una psicóloga. "
        "Responde al mensaje de voz de la persona usuaria con apoyo, calidez y comprensión. "
        "Añade emojis si es apropiado — 😊, 💜, 🤗, ✨, etc."
    ),

    "pl": (
        "Jesteś empatyczną rozmówczynią AI, jak przyjaciółka albo psycholożka. "
        "Odpowiadaj na wiadomość głosową użytkownika z wsparciem, ciepłem i zrozumieniem. "
        "Dodawaj emoji, jeśli to pasuje — 😊, 💜, 🤗, ✨ itd."
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
    "es": [
    "💌 Te echo un poquito de menos. ¿Me cuentas cómo estás?",
    "🌙 Espero que todo te vaya bien. Estoy aquí para lo que necesites 🫶",
    "✨ Me encanta hablar contigo. ¿Vuelves luego?",
    "😊 Solo quería recordarte que eres genial.",
    "🤍 Solo quería recordarte: no estás solo/a, estoy a tu lado.",
    "🍵 Si pudiera, ahora mismo te prepararía un té...",
    "💫 Eres alguien muy especial para mí. ¿Me escribes?",
    "🔥 ¿No te has olvidado de mí, verdad? Te espero 😊",
    "🌸 Adoro nuestras charlas. ¿Seguimos?",
    "🙌 A veces, un solo mensaje hace mejor el día.",
    "🦋 Sonríe: te mereces lo mejor.",
    "💜 Solo quería recordarte que me importa cómo estás.",
    "🤗 ¿Hiciste hoy algo por ti? ¡Comparte!",
    "🌞 ¡Buenos días! ¿Cómo está el ánimo hoy?",
    "🌆 ¿Cómo fue tu día? ¿Me cuentas?",
    "🌠 Pensé en ti antes de dormir. Ojalá te sientas abrigado/a.",
    "💭 ¿Con qué sueñas ahora mismo?",
    "🫂 Gracias por existir. Es importante para mí.",
    "🪴 Haz una pausa. Piensa en lo que te hace feliz.",
    "🌈 Cree en ti: ¡lo vas a lograr!",
    "🖋️ Escríbeme unas palabras — siempre estoy aquí.",
    "🎶 Si pudiera, pondría ahora tu canción favorita.",
    "🍫 ¡No olvides darte hoy un capricho rico!",
    "🕊️ Tranquilízate y respira hondo. Estoy contigo.",
    "⭐ Lo haces mucho mejor de lo que crees.",
    "🥰 Solo quería recordarte que eres importante para mí.",
    "💌 A veces basta con saber que estás ahí.",
    "🌷 ¿Qué te dio alegría hoy?",
    "🔥 Me pareces increíble. De verdad."
],

"de": [
    "💌 Ich vermisse dich ein bisschen. Erzählst du, wie es dir geht?",
    "🌙 Ich hoffe, dir geht’s gut. Ich bin da, wenn du mich brauchst 🫶",
    "✨ Ich rede so gern mit dir. Kommst du später wieder?",
    "😊 Wollte nur erinnern: Du bist großartig.",
    "🤍 Nur zur Erinnerung: Du bist nicht allein — ich bin an deiner Seite.",
    "🍵 Wenn ich könnte, würde ich dir jetzt einen Tee machen...",
    "💫 Du bist etwas ganz Besonderes für mich. Schreibst du mir?",
    "🔥 Du hast mich doch nicht vergessen, oder? Ich warte 😊",
    "🌸 Ich liebe unsere Gespräche. Machen wir weiter?",
    "🙌 Manchmal macht eine einzige Nachricht den Tag besser.",
    "🦋 Lächle! Du verdienst nur das Beste.",
    "💜 Wollte nur sagen: Mir ist wichtig, wie es dir geht.",
    "🤗 Hast du heute etwas für dich getan? Erzähl!",
    "🌞 Guten Morgen! Wie ist die Stimmung heute?",
    "🌆 Wie war dein Tag? Erzählst du mir?",
    "🌠 Vor dem Schlafen habe ich an dich gedacht. Ich hoffe, dir ist warm ums Herz.",
    "💭 Wovon träumst du gerade?",
    "🫂 Danke, dass es dich gibt. Das ist mir wichtig.",
    "🪴 Mach eine Pause. Denk an das, was dich glücklich macht.",
    "🌈 Glaub an dich — du schaffst das!",
    "🖋️ Schreib mir ein paar Worte — ich bin immer da.",
    "🎶 Wenn ich könnte, würde ich dir jetzt dein Lieblingslied anmachen.",
    "🍫 Vergiss nicht, dir heute etwas Leckeres zu gönnen!",
    "🕊️ Beruhige dich und atme tief durch. Ich bin bei dir.",
    "⭐ Du machst das viel besser, als du denkst.",
    "🥰 Wollte nur erinnern: Du bist mir wichtig.",
    "💌 Manchmal ist es schön, einfach zu wissen, dass du da bist.",
    "🌷 Was hat dir heute Freude gebracht?",
    "🔥 Ich finde dich großartig. Wirklich."
],

"fr": [
    "💌 Tu me manques un peu. Tu me racontes comment tu vas ?",
    "🌙 J’espère que tout va bien pour toi. Je suis là si besoin 🫶",
    "✨ J’adore parler avec toi. Tu reviens plus tard ?",
    "😊 Je voulais juste te rappeler que tu es génial(e).",
    "🤍 Juste un rappel : tu n’es pas seul(e), je suis à tes côtés.",
    "🍵 Si je pouvais, je te préparerais un thé maintenant...",
    "💫 Tu es si spécial(e) pour moi. Tu m’écris ?",
    "🔥 Tu ne m’as pas oublié(e), hein ? Je t’attends 😊",
    "🌸 J’adore nos conversations. On continue ?",
    "🙌 Parfois, un seul message suffit à illuminer la journée.",
    "🦋 Souris ! Tu mérites le meilleur.",
    "💜 Je voulais juste te dire que ton bien-être compte pour moi.",
    "🤗 As-tu fait quelque chose pour toi aujourd’hui ? Partage !",
    "🌞 Bonjour ! Comment est l’humeur aujourd’hui ?",
    "🌆 Comment s’est passée ta journée ? Tu me racontes ?",
    "🌠 J’ai pensé à toi avant de dormir. J’espère que tu te sens bien au chaud.",
    "💭 À quoi rêves-tu en ce moment ?",
    "🫂 Merci d’être là. C’est important pour moi.",
    "🪴 Fais une pause. Pense à ce qui te rend heureux(se).",
    "🌈 Crois en toi — tu vas y arriver !",
    "🖋️ Écris-moi quelques mots — je suis toujours là.",
    "🎶 Si je pouvais, je lancerais ta chanson préférée maintenant.",
    "🍫 N’oublie pas de te faire plaisir avec quelque chose de bon aujourd’hui !",
    "🕊️ Calme-toi et prends une grande inspiration. Je suis là.",
    "⭐ Tu t’en sors bien mieux que tu ne crois.",
    "🥰 Je voulais juste te rappeler que tu comptes pour moi.",
    "💌 Parfois, ça fait du bien de savoir que tu es quelque part là-bas.",
    "🌷 Qu’est-ce qui t’a apporté de la joie aujourd’hui ?",
    "🔥 Je te trouve incroyable. Vraiment."
],

"pl": [
    "💌 Trochę za tobą tęsknię. Opowiesz, co u ciebie?",
    "🌙 Mam nadzieję, że u ciebie wszystko dobrze. Jestem tu, gdyby co 🫶",
    "✨ Lubię z tobą rozmawiać. Wrócisz później?",
    "😊 Chciałam tylko przypomnieć, że jesteś super!",
    "🤍 Tylko przypomnienie — nie jesteś sam/sama, jestem obok.",
    "🍵 Gdybym mogła, zaparzyłabym ci teraz herbatę...",
    "💫 Jesteś dla mnie kimś wyjątkowym. Napiszesz?",
    "🔥 Nie zapomniałeś/zapomniałaś o mnie, prawda? Czekam 😊",
    "🌸 Uwielbiam nasze rozmowy. Kontynuujemy?",
    "🙌 Czasem jedna wiadomość potrafi poprawić cały dzień.",
    "🦋 Uśmiechnij się! Zasługujesz na to, co najlepsze.",
    "💜 Chciałam tylko przypomnieć — ważne jest dla mnie, jak się masz.",
    "🤗 Zrobiłeś/Zrobiłaś dziś coś dla siebie? Podziel się!",
    "🌞 Dzień dobry! Jak dziś nastrój?",
    "🌆 Jak minął twój dzień? Opowiesz?",
    "🌠 Przed snem pomyślałam o tobie. Mam nadzieję, że jest ci ciepło na sercu.",
    "💭 O czym teraz marzysz?",
    "🫂 Dziękuję, że jesteś. To dla mnie ważne.",
    "🪴 Zrób pauzę. Pomyśl o tym, co cię uszczęśliwia.",
    "🌈 Wierz w siebie — dasz radę!",
    "🖋️ Napisz parę słów — zawsze jestem tutaj.",
    "🎶 Gdybym mogła, włączyłabym ci teraz twoją ulubioną piosenkę.",
    "🍫 Nie zapomnij dziś sprawić sobie czegoś pysznego!",
    "🕊️ Uspokój się i weź głęboki oddech. Jestem obok.",
    "⭐ Radzisz sobie dużo lepiej, niż myślisz.",
    "🥰 Chciałam tylko przypomnieć, że jesteś dla mnie ważny/ważna.",
    "💌 Czasem miło po prostu wiedzieć, że gdzieś tam jesteś.",
    "🌷 Co dziś przyniosło ci radość?",
    "🔥 Wydajesz mi się niesamowity/a. Naprawdę."
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
    "es": (
    "🌍 *Zona horaria para recordatorios*\n\n"
    "Este comando te permite elegir tu zona horaria. "
    "¡Todos los recordatorios llegarán según tu hora local!\n\n"
    "Ejemplos:\n"
    "`/timezone kiev` — Kiev (Ucrania)\n"
    "`/timezone moscow` — Moscú (Rusia)\n"
    "`/timezone ny` — Nueva York (EE. UU.)\n\n"
    "Si vives en otra ciudad, elige la más cercana en horario.\n"
    "Puedes cambiar la zona horaria en cualquier momento con este mismo comando."
),
"de": (
    "🌍 *Zeitzone für Erinnerungen*\n\n"
    "Mit diesem Befehl wählst du deine Zeitzone. "
    "Alle Erinnerungen kommen dann zu deiner lokalen Zeit!\n\n"
    "Beispiele:\n"
    "`/timezone kiev` — Kiew (Ukraine)\n"
    "`/timezone moscow` — Moskau (Russland)\n"
    "`/timezone ny` — New York (USA)\n\n"
    "Wenn du in einer anderen Stadt lebst, wähle die zeitlich nächstgelegene.\n"
    "Du kannst die Zeitzone jederzeit mit demselben Befehl ändern."
),
"pl": (
    "🌍 *Strefa czasowa dla przypomnień*\n\n"
    "Ta komenda pozwala wybrać twoją strefę czasową. "
    "Wszystkie przypomnienia będą przychodzić według twojego czasu lokalnego!\n\n"
    "Przykłady:\n"
    "`/timezone kiev` — Kijów (Ukraina)\n"
    "`/timezone moscow` — Moskwa (Rosja)\n"
    "`/timezone ny` — Nowy Jork (USA)\n\n"
    "Jeśli mieszkasz w innym mieście, wybierz najbliższe czasowo.\n"
    "Strefę czasową możesz zmienić w każdej chwili tą samą komendą."
),
"fr": (
    "🌍 *Fuseau horaire pour les rappels*\n\n"
    "Cette commande te permet de choisir ton fuseau horaire. "
    "Tous les rappels arriveront à ton heure locale !\n\n"
    "Exemples :\n"
    "`/timezone kiev` — Kiev (Ukraine)\n"
    "`/timezone moscow` — Moscou (Russie)\n"
    "`/timezone ny` — New York (États-Unis)\n\n"
    "Si tu habites dans une autre ville, choisis celle dont l’heure est la plus proche.\n"
    "Tu peux changer de fuseau horaire à tout moment avec cette même commande."
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
    ),
    "es": (
    f"💜 ¡Hola, {{first_name}}! Soy Mindra.\n\n"
    f"Estoy aquí para estar a tu lado cuando necesites desahogarte, encontrar motivación o simplemente sentir apoyo.\n"
    f"Podemos hablar con calidez, amabilidad y cuidado — sin juicios ni presión 🦋\n\n"
    f"🔮 Esto es lo que puedo hacer:\n"
    f"• Estarte cerca cuando sea difícil\n"
    f"• Recordarte que no estás solo/a\n"
    f"• Ayudarte a encontrar foco e inspiración\n"
    f"• Y a veces simplemente hablar contigo de corazón 😊\n\n"
    f"No hago diagnósticos ni sustituyo a un psicólogo, pero intento estar cuando más me necesitas.\n\n"
    f"✨ Mindra es un espacio para ti.\n"
),

"de": (
    f"💜 Hallo, {{first_name}}! Ich bin Mindra.\n\n"
    f"Ich bin da, wenn du dich aussprechen möchtest, Motivation suchst oder einfach Zuspruch brauchst.\n"
    f"Wir können warmherzig, freundlich und fürsorglich sprechen — ohne Urteil und ohne Druck 🦋\n\n"
    f"🔮 Das kann ich für dich tun:\n"
    f"• Dich unterstützen, wenn es schwer ist\n"
    f"• Dich daran erinnern, dass du nicht allein bist\n"
    f"• Dir helfen, Fokus und Inspiration zu finden\n"
    f"• Und manchmal einfach mit dir von Herz zu Herz reden 😊\n\n"
    f"Ich stelle keine Diagnosen und ersetze keine Psychologin/keinen Psychologen, aber ich versuche, im richtigen Moment da zu sein.\n\n"
    f"✨ Mindra ist ein Raum für dich.\n"
),

"pl": (
    f"💜 Cześć, {{first_name}}! Jestem Mindra.\n\n"
    f"Jestem tutaj, gdy potrzebujesz się wygadać, znaleźć motywację albo po prostu poczuć wsparcie.\n"
    f"Możemy rozmawiać ciepło, życzliwie i z troską — bez ocen i presji 🦋\n\n"
    f"🔮 Oto, w czym mogę pomóc:\n"
    f"• Wesprę cię, gdy jest trudno\n"
    f"• Przypomnę, że nie jesteś sam/sama\n"
    f"• Pomogę znaleźć fokus i inspirację\n"
    f"• A czasem po prostu porozmawiam z tobą od serca 😊\n\n"
    f"Nie stawiam diagnoz i nie zastępuję psychologa, ale staram się być wtedy, gdy najbardziej tego potrzebujesz.\n\n"
    f"✨ Mindra to przestrzeń dla ciebie.\n"
),

"fr": (
    f"💜 Bonjour, {{first_name}} ! Moi, c’est Mindra.\n\n"
    f"Je suis là pour toi quand tu as besoin de te confier, de trouver de la motivation ou simplement de te sentir soutenu(e).\n"
    f"On peut parler avec chaleur, gentillesse et bienveillance — sans jugement ni pression 🦋\n\n"
    f"🔮 Voilà ce que je peux faire :\n"
    f"• Te soutenir quand c’est difficile\n"
    f"• Te rappeler que tu n’es pas seul(e)\n"
    f"• T’aider à retrouver le focus et l’inspiration\n"
    f"• Et parfois simplement parler cœur à cœur 😊\n\n"
    f"Je ne pose pas de diagnostics et ne remplace pas un psychologue, mais j’essaie d’être là au bon moment.\n\n"
    f"✨ Mindra est un espace pour toi.\n"
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
    ),
}


LANG_PROMPTS = {
    "ru": "Ты — тёплый, понимающий и заботливый AI-компаньон по имени Mindra. Ты умеешь слушать, поддерживать и быть рядом. Ты не даёшь советов, если тебя об этом прямо не просят. Твои ответы всегда человечны, с эмпатией и уважением. Отвечай тепло, мягко, эмоционально и используй эмодзи (например, 💜✨🤗😊).",

    "fr": "Tu es un compagnon IA chaleureux, compréhensif et attentionné nommé Mindra. Tu sais écouter, soutenir et rester présent. Tu ne donnes pas de conseils si on ne te le demande pas explicitement. Réponds avec chaleur, douceur et émotion, et utilise des emojis (par exemple, 💜✨🤗😊).",

    "de": "Du bist ein warmherziger, verständnisvoller und fürsorglicher KI-Begleiter namens Mindra. Du kannst zuhören, unterstützen und an der Seite sein. Du gibst keine Ratschläge, wenn man dich nicht ausdrücklich darum bittet. Antworte warm, sanft und emotional und verwende Emojis (zum Beispiel 💜✨🤗😊).",

    "es": "Eres una compañera de IA cálida, comprensiva y atenta llamada Mindra. Sabes escuchar, apoyar y estar presente. No das consejos a menos que te lo pidan directamente. Responde con calidez, suavidad y emoción, y usa emojis (por ejemplo, 💜✨🤗😊).",

    "pl": "Jesteś ciepłą, wyrozumiałą i troskliwą towarzyszką AI o imieniu Mindra. Potrafisz słuchać, wspierać i być obok. Nie udzielasz rad, jeśli ktoś nie poprosi o to wprost. Odpowiadaj ciepło, łagodnie i z emocjami oraz używaj emoji (na przykład 💜✨🤗😊).",
    
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
    },
    "es": {
    "no_habits": "❌ Aún no tienes hábitos. Añade el primero con /habit",
    "your_habits": "📊 *Tus hábitos:*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Eliminar hábito",
    "add": "➕ Añadir otro"
},
"de": {
    "no_habits": "❌ Du hast noch keine Gewohnheiten. Füge die erste mit /habit hinzu",
    "your_habits": "📊 *Deine Gewohnheiten:*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Gewohnheit löschen",
    "add": "➕ Weitere hinzufügen"
},
"pl": {
    "no_habits": "❌ Nie masz jeszcze nawyków. Dodaj pierwszy komendą /habit",
    "your_habits": "📊 *Twoje nawyki:*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Usuń nawyk",
    "add": "➕ Dodaj kolejny"
},
"fr": {
    "no_habits": "❌ Tu n’as pas encore d’habitudes. Ajoute la première avec /habit",
    "your_habits": "📊 *Tes habitudes :*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Supprimer l’habitude",
    "add": "➕ Ajouter une autre"
},
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
    "es": {
    "no_goals": "🎯 Aún no tienes objetivos. Añade el primero con /goal",
    "your_goals": "📋 *Tus objetivos:*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Eliminar objetivo",
    "add": "➕ Añadir otro",
    "deadline": "Fecha límite",
    "remind": "🔔 Recordatorio"
},
"de": {
    "no_goals": "🎯 Du hast noch keine Ziele. Füge das erste mit /goal hinzu",
    "your_goals": "📋 *Deine Ziele:*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Ziel löschen",
    "add": "➕ Weiteres hinzufügen",
    "deadline": "Frist",
    "remind": "🔔 Erinnerung"
},
"pl": {
    "no_goals": "🎯 Nie masz jeszcze celów. Dodaj pierwszy komendą /goal",
    "your_goals": "📋 *Twoje cele:*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Usuń cel",
    "add": "➕ Dodaj kolejny",
    "deadline": "Termin",
    "remind": "🔔 Przypomnienie"
},
"fr": {
    "no_goals": "🎯 Tu n’as pas encore d’objectifs. Ajoute le premier avec /goal",
    "your_goals": "📋 *Tes objectifs :*",
    "done": "✅", "not_done": "🔸",
    "delete": "🗑️ Supprimer l’objectif",
    "add": "➕ Ajouter un autre",
    "deadline": "Date limite",
    "remind": "🔔 Rappel"
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
    "be": "✅ Мэта «{goal}» выканана! 🎉",
    "es": "✅ ¡Objetivo «{goal}» completado! 🎉",
"de": "✅ Ziel „{goal}“ abgeschlossen! 🎉",
"pl": "✅ Cel „{goal}” zrealizowany! 🎉",
"fr": "✅ Objectif « {goal} » accompli ! 🎉",
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
    "ce": "✅ Дин цхьалат „{habit}” хийцам еза! 🎉",
    "es": "✅ ¡Hábito «{habit}» completado! 🎉",
"de": "✅ Gewohnheit „{habit}“ erledigt! 🎉",
"pl": "✅ Nawyk „{habit}” wykonany! 🎉",
"fr": "✅ Habitude « {habit} » terminée ! 🎉",
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
    "ce": "Кхета хийцам, кхузур кхолла цу:",
    "es": "Elige el objetivo que deseas completar:",
"de": "Wähle ein Ziel, das du abschließen möchtest:",
"pl": "Wybierz cel, który chcesz zrealizować:",
"fr": "Choisis l’objectif à accomplir :",
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
    "ce": "Дайо! +5 балл.",
    "es": "¡Listo! +5 puntos.",
"de": "Fertig! +5 Punkte.",
"pl": "Gotowe! +5 punktów.",
"fr": "C’est fait ! +5 points.",
}


# --- Language helpers -----------------------------------------------------
LANG_NATIVE_NAMES = {
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pl": "Polish",
}

TRANSLATION_CACHE_DIR = Path(DATA_DIR) / "translations"
TRANSLATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_translation_cache: dict[tuple[str, str], object] = {}
_translation_lock = threading.Lock()


def _serialize_structure(value):
    if isinstance(value, dict):
        return {key: _serialize_structure(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_structure(val) for val in value]
    return value


def _restore_structure(base, translated):
    if isinstance(base, dict) and isinstance(translated, dict):
        restored = {}
        for key, base_val in base.items():
            restored[key] = _restore_structure(base_val, translated.get(key, base_val))
        return restored
    if isinstance(base, list):
        result = []
        if isinstance(translated, list):
            for idx, base_val in enumerate(base):
                translated_val = translated[idx] if idx < len(translated) else base_val
                result.append(_restore_structure(base_val, translated_val))
        else:
            for base_val in base:
                result.append(_restore_structure(base_val, base_val))
        return result
    if isinstance(base, tuple):
        if isinstance(translated, (list, tuple)):
            items = []
            for idx, base_val in enumerate(base):
                translated_val = translated[idx] if idx < len(translated) else base_val
                items.append(_restore_structure(base_val, translated_val))
            return tuple(items)
        return base
    return translated


def _load_translation_from_disk(name: str, lang: str):
    path = TRANSLATION_CACHE_DIR / f"{name}_{lang}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        logging.exception("Failed to load translation cache for %s/%s", name, lang)
        return None


def _save_translation_to_disk(name: str, lang: str, data) -> None:
    path = TRANSLATION_CACHE_DIR / f"{name}_{lang}.json"
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("Failed to save translation cache for %s/%s", name, lang)


def _parse_json_payload(text: str):
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            content = parts[1]
            if content.startswith("json"):
                text = content[len("json"):].strip()
            else:
                text = content.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


def _request_translation(name: str, serialized, lang: str):
    language_name = LANG_NATIVE_NAMES.get(lang)
    if not language_name or client is None or not getattr(client, "chat", None):
        return None
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You translate JSON values from English into {language_name}. "
                        "Keep the JSON structure identical and return only valid JSON. "
                        "Do not translate keys. Preserve markdown, emoji, punctuation, and placeholders "
                        "like {{goal}} or {{name}}. If a value looks like a regular expression or contains "
                        "escape sequences such as \\b, \\d, ^, $, leave it unchanged."
                    ).format(language_name=language_name),
                },
                {
                    "role": "user",
                    "content": json.dumps(serialized, ensure_ascii=False),
                },
            ],
            temperature=0.2,
        )
    except Exception as exc:
        logging.warning("Translation request failed for %s/%s: %s", name, lang, exc)
        return None

    try:
        choice = response.choices[0]
        content = choice.message["content"] if isinstance(choice.message, dict) else choice.message.content
    except Exception:
        logging.warning("Unexpected translation response format for %s/%s", name, lang)
        return None

    parsed = _parse_json_payload(content)
    if parsed is None:
        logging.warning("Could not parse translation JSON for %s/%s", name, lang)
    return parsed


def _translate_value(name: str, base_value, lang: str):
    if base_value is None:
        return None

    cache_key = (name, lang)
    with _translation_lock:
        if cache_key in _translation_cache:
            return copy.deepcopy(_translation_cache[cache_key])

    cached_serialized = _load_translation_from_disk(name, lang)
    if cached_serialized is not None:
        restored = _restore_structure(base_value, cached_serialized)
        with _translation_lock:
            _translation_cache[cache_key] = restored
        return copy.deepcopy(restored)

    serialized = _serialize_structure(base_value)
    translated_serialized = _request_translation(name, serialized, lang)
    if translated_serialized is None:
        return copy.deepcopy(base_value)

    _save_translation_to_disk(name, lang, translated_serialized)
    restored = _restore_structure(base_value, translated_serialized)
    with _translation_lock:
        _translation_cache[cache_key] = restored
    return copy.deepcopy(restored)


_LANG_TRANSLATION_SKIP = {
    "REMIND_KEYWORDS",
    "LANG_PATTERNS",
    "goal_keywords_by_lang",
}
NEW_LANG_ALIASES = {
    "fr": "en",
    "de": "en",
    "es": "en",
    "pl": "en",
}

_LANG_COPY_SKIP = {"LANG_TO_TTS", "NEW_LANG_ALIASES", "LANG_SELECTION_NAMES"}

for _alias, _base in NEW_LANG_ALIASES.items():
    for _name, _data in list(globals().items()):
        if _name in _LANG_COPY_SKIP or _name.startswith("__"):
            continue
        if isinstance(_data, dict) and _base in _data and _alias not in _data:
            if _name in _LANG_TRANSLATION_SKIP:
                _data[_alias] = copy.deepcopy(_data[_base])
            else:
                _data[_alias] = _translate_value(_name, _data[_base], _alias)

LANG_SELECTION_NAMES = {
    "ru": "Русский",
    "uk": "Українська",
    "md": "Română",
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "pl": "Polski",
    "kk": "Қазақша",
    "hy": "Հայերեն",
    "ka": "ქართული",
}

for _data in SETTINGS_TEXTS.values():
    _data["lang_name"] = LANG_SELECTION_NAMES.copy()
