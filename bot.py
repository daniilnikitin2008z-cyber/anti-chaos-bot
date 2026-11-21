"""
Система Анти-Хаос — Telegram бот
Запуск: python bot.py
Токен берется из .env или переменной BOT_TOKEN
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- КОНФИГ ---
# Замени на свои ссылки оплаты (Boosty / Tribute / Gumroad / Stripe)
PAYMENT_BASE = os.getenv("PAYMENT_BASE", "https://boosty.to/your_page")  # 4 900₽
PAYMENT_PRO = os.getenv("PAYMENT_PRO", "https://boosty.to/your_page_pro")  # 9 900₽
PAYMENT_SALE = os.getenv("PAYMENT_SALE", "https://boosty.to/your_page_sale")  # 7 900₽ для 31-50
CONTACT_USERNAME = os.getenv("CONTACT_USERNAME", "@your_username")  # твой контакт для разбора
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 25 ВОПРОСОВ (5 блоков) ---
QUESTIONS = [
    # Блок 1
    ("Блок 1/5: ГОЛОВА И ФОКУС", "Держу >20 задач в голове, боюсь что-то забыть"),
    ("Блок 1/5: ГОЛОВА И ФОКУС", "Прокрастинирую, т.к. не понимаю за что хвататься первым"),
    ("Блок 1/5: ГОЛОВА И ФОКУС", "Прыгаю между задачами, ничего не довожу до конца"),
    ("Блок 1/5: ГОЛОВА И ФОКУС", "Вечером чувство вины: день прошел, а результата нет"),
    ("Блок 1/5: ГОЛОВА И ФОКУС", "Идеи раскиданы по 5+ местам: чаты, заметки, листы"),
    # Блок 2
    ("Блок 2/5: ПРОЕКТЫ И ДЕДЛАЙНЫ", "Срываю или сдаю проекты в последний момент"),
    ("Блок 2/5: ПРОЕКТЫ И ДЕДЛАЙНЫ", "Забываю про договоренности с клиентом"),
    ("Блок 2/5: ПРОЕКТЫ И ДЕДЛАЙНЫ", "Нет единого списка всех проектов и статусов"),
    ("Блок 2/5: ПРОЕКТЫ И ДЕДЛАЙНЫ", "Беру больше чем могу, потом выгораю"),
    ("Блок 2/5: ПРОЕКТЫ И ДЕДЛАЙНЫ", "Клиент пишет «где результат?», а я ищу файл"),
    # Блок 3
    ("Блок 3/5: ДЕНЬГИ И ТРЕВОГА", "Не знаю сколько точно заработал в прошлом месяце"),
    ("Блок 3/5: ДЕНЬГИ И ТРЕВОГА", "Не веду учет долгов клиентов (кто сколько должен)"),
    ("Блок 3/5: ДЕНЬГИ И ТРЕВОГА", "Трачу время на дешевые заказы, нет плана дохода"),
    ("Блок 3/5: ДЕНЬГИ И ТРЕВОГА", "К концу месяца тревога: хватит ли на аренду?"),
    ("Блок 3/5: ДЕНЬГИ И ТРЕВОГА", "Не знаю цену своего часа, занижаю чек"),
    # Блок 4
    ("Блок 4/5: СИСТЕМА И РИТМ", "Нет плана на неделю, живу «как пойдет»"),
    ("Блок 4/5: СИСТЕМА И РИТМ", "Нет ритуала закрытия недели / планирования"),
    ("Блок 4/5: СИСТЕМА И РИТМ", "Пробовал Notion/трекер — бросил через 3 дня"),
    ("Блок 4/5: СИСТЕМА И РИТМ", "Выходные трачу на доделку хвостов"),
    ("Блок 4/5: СИСТЕМА И РИТМ", "Кажется что система — «слишком сложно для меня»"),
    # Блок 5
    ("Блок 5/5: ЭНЕРГИЯ И ВЫГОРАНИЕ", "Выгорание: работаю много, а радости нет"),
    ("Блок 5/5: ЭНЕРГИЯ И ВЫГОРАНИЕ", "Плохо сплю из-за мыслей о незакрытых делах"),
    ("Блок 5/5: ЭНЕРГИЯ И ВЫГОРАНИЕ", "Откладываю личные дела из-за работы"),
    ("Блок 5/5: ЭНЕРГИЯ И ВЫГОРАНИЕ", "Сравниваю: «у них порядок, а у меня бардак»"),
    ("Блок 5/5: ЭНЕРГИЯ И ВЫГОРАНИЕ", "Хочу порядок, но руки опускаются как начать"),
]

def get_result(score: int):
    if score <= 15:
        return (
            "0–15 баллов — Лёгкий хаос",
            "У тебя уже есть зачатки системы. Нужна шлифовка: собрать всё в одном месте. Тебе хватит Базового тарифа.",
            PAYMENT_BASE,
            "Базовый — 4 900₽ / 49€"
        )
    elif score <= 30:
        return (
            "16–30 баллов — Хронический хаос",
            "Ты теряешь 5–10 часов и ~20% дохода в месяц просто из-за отсутствия системы. Рекомендую тариф с разбором — я посмотрю твою систему и дам план.",
            PAYMENT_PRO,
            "🔥 С разбором — 9 900₽ / 99€ (хит)"
        )
    else:
        return (
            "31–50 баллов — Тотальный хаос → риск выгорания",
            "Срочно нужна внешняя система! Твоя голова не справляется — и это нормально. Даю спец-условие на 24 часа.",
            PAYMENT_SALE,
            "🚨 Спец-цена — 7 900₽ / 79€ (24 часа)"
        )

# --- Клавиатуры ---

def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Скачать гайд «Дамп мозга»", callback_data="guide")],
        [InlineKeyboardButton("🔍 Пройти Аудит Хаоса (2 мин)", callback_data="audit_start")],
        [InlineKeyboardButton("💬 Задать вопрос автору", url=f"https://t.me/{CONTACT_USERNAME.replace('@','')}" if CONTACT_USERNAME.startswith("@") else CONTACT_USERNAME)],
    ])

def audit_keyboard(q_index: int):
    prefix = f"ans_{q_index}_"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("0 — Нет", callback_data=prefix+"0"),
            InlineKeyboardButton("1 — Иногда", callback_data=prefix+"1"),
            InlineKeyboardButton("2 — Да", callback_data=prefix+"2"),
        ]
    ])

def after_audit_keyboard(score: int):
    title, desc, link, label = get_result(score)
    # показываем оба тарифа, но подсвечиваем нужный
    if score <= 15:
        buttons = [
            [InlineKeyboardButton("📦 Базовый — 4 900₽ / 49€", url=PAYMENT_BASE)],
            [InlineKeyboardButton("💬 Хочу с разбором — 9 900₽", url=PAYMENT_PRO)],
            [InlineKeyboardButton("🔄 Пройти заново", callback_data="audit_start")],
        ]
    elif score <= 30:
        buttons = [
            [InlineKeyboardButton("🔥 С разбором — 9 900₽ / 99€", url=PAYMENT_PRO)],
            [InlineKeyboardButton("📦 Только базу — 4 900₽", url=PAYMENT_BASE)],
            [InlineKeyboardButton("💬 Написать автору", url=f"https://t.me/{CONTACT_USERNAME.replace('@','')}")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton("🚨 Забрать за 7 900₽ (24ч)", url=PAYMENT_SALE)],
            [InlineKeyboardButton("📦 Базовый — 4 900₽", url=PAYMENT_BASE)],
            [InlineKeyboardButton("💬 Нужна помощь — написать", url=f"https://t.me/{CONTACT_USERNAME.replace('@','')}")],
        ]
    return InlineKeyboardMarkup(buttons)

# --- Хендлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args  # для deep link t.me/bot?start=chaos
    logger.info(f"/start from {user.id} @{user.username} args={args}")

    text = (
        f"Привет, {user.first_name}! Я — твой Анти-Хаос 👋\n\n"
        "Ты пришёл по слову <b>ХАОС</b> — значит голова пухнет от задач, а деньги утекают.\n\n"
        "🎁 <b>Забирай подарок:</b> гайд «Дамп мозга за 30 минут» — как выгрузить 100 мыслей из головы и перестать тревожиться.\n\n"
        "А хочешь точно понять, насколько у тебя всё запущено — пройди аудит на 25 вопросов. Это 2 минуты и честный диагноз.\n\n"
        "👇 Выбирай:"
    )
    # deep link приветствие
    if args and "chaos" in args[0].lower():
        text = (
            f"Вижу твой коммент <b>ХАОС</b> 🔥 Спасибо!\n\n"
            + text
        )

    await update.message.reply_text(text, reply_markup=start_keyboard(), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "guide":
        await query.message.reply_text(
            "📄 <b>Гайд «Дамп мозга за 30 минут»</b>\n\n"
            "1. Поставь таймер на 25 мин\n"
            "2. Выпиши ВСЁ что в голове в лист «ДАМП МОЗГА» (из трекеров)\n"
            "3. Пометь каждую строку: <i>Быстрое &lt;2м / Задача / Идея</i>\n"
            "4. Разнеси в Проекты / Финансы / Контент\n\n"
            "Голова пустеет на глазах. Это первый шаг из Системы.\n\n"
            "Файл трекеров + PDF чек-лист уже ждут тебя в продукте. А пока — пройди аудит, чтобы понять с чего начать:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Пройти аудит — 2 мин", callback_data="audit_start")]]),
            parse_mode="HTML"
        )
        # Попробуй отправить PDF если он рядом (опционально)
        # await query.message.reply_document(document=open("../Audit-Chaosa-Checklist.pdf","rb"), caption="Твой чек-лист аудита")

    elif data == "audit_start":
        context.user_data["score"] = 0
        context.user_data["q"] = 0
        await send_question(query, context, 0)

    elif data.startswith("ans_"):
        # формат ans_7_2
        try:
            _, q_idx, val = data.split("_")
            q_idx = int(q_idx)
            val = int(val)
        except:
            return
        # защита от двойного клика не на тот вопрос
        if context.user_data.get("q", 0) != q_idx:
            await query.answer("Уже отвечено, жми дальше 👇", show_alert=False)
            return

        context.user_data["score"] = context.user_data.get("score", 0) + val
        next_q = q_idx + 1
        context.user_data["q"] = next_q

        # Удаляем кнопки у старого вопроса (чтобы не кликали снова)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except:
            pass

        if next_q < len(QUESTIONS):
            await send_question(query, context, next_q)
        else:
            await send_result(query, context)
    elif data == "offer_base":
        await query.message.reply_text(f"Отлично! База — {PAYMENT_BASE}")
    elif data == "offer_pro":
        await query.message.reply_text(f"Супер, с разбором — {PAYMENT_PRO}")

async def send_question(query, context, idx):
    block, question = QUESTIONS[idx]
    total = len(QUESTIONS)
    progress = f"{idx+1}/{total}"
    bar_len = 20
    filled = int((idx+1)/total * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    text = (
        f"<b>{block}</b>\n"
        f"<i>Вопрос {progress}</i>  {bar}  {int((idx+1)/total*100)}%\n\n"
        f"<b>{question}</b>\n\n"
        f"Отвечай честно: 0 — нет, 1 — иногда, 2 — да, постоянно"
    )
    # Отправляем новый месседж, а не редактируем, чтобы история сохранялась (удобнее)
    await query.message.reply_text(text, reply_markup=audit_keyboard(idx), parse_mode="HTML")

async def send_result(query, context):
    score = context.user_data.get("score", 0)
    title, desc, link, label = get_result(score)

    text = (
        f"✅ <b>Готово! Твой результат:</b>\n\n"
        f"📊 <b>{title}</b> — <b>{score}/50 баллов</b>\n\n"
        f"{desc}\n\n"
        f"👇 <b>Рекомендую тебе:</b>\n"
        f"— Внутри: Notion-шаблон 1-клик + Excel-трекеры (6 листов) + 4 видео по 18 мин\n"
        f"— Установка 15 мин, результат за выходные\n"
        f"— Гарантия 7 дней, возврат без вопросов\n\n"
        f"Выбирай тариф:"
    )
    # Если тотальный хаос — добавляем дедлайн
    if score > 30:
        text += "\n\n⏳ <b>Спец-цена 7 900₽ действует 24 часа с момента прохождения аудита!</b>"

    await query.message.reply_text(text, reply_markup=after_audit_keyboard(score), parse_mode="HTML")

    # Дополнительно: предлагаем написать
    await query.message.reply_text(
        "💡 <i>Сомневаешься? Напиши мне — подскажу с какого модуля начать именно тебе.</i>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Написать автору", url=f"https://t.me/{CONTACT_USERNAME.replace('@','')}")]]),
        parse_mode="HTML"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start — начать заново\n"
        "/audit — пройти аудит\n"
        "/help — помощь\n\n"
        f"Связь: {CONTACT_USERNAME}"
    )

async def audit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["score"] = 0
    context.user_data["q"] = 0
    # создаем фейковый query объект — проще отправить первый вопрос как сообщение
    total = len(QUESTIONS)
    block, q = QUESTIONS[0]
    text = f"<b>{block}</b>\n<i>Вопрос 1/{total}</i>\n\n<b>{q}</b>\n\n0 — нет, 1 — иногда, 2 — да"
    await update.message.reply_text(text, reply_markup=audit_keyboard(0), parse_mode="HTML")

def main():
    if BOT_TOKEN == "PASTE_YOUR_TOKEN_HERE" or not BOT_TOKEN:
        print("❌ ОШИБКА: Не указан BOT_TOKEN!")
        print("1. Иди в @BotFather в Telegram -> /newbot -> скопируй токен")
        print("2. Создай файл .env рядом с bot.py и вставь: BOT_TOKEN=твой_токен")
        print("3. Или экспортируй: export BOT_TOKEN=твой_токен && python bot.py")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("audit", audit_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот запущен! Нажми Ctrl+C для остановки.")
    print(f"   Оплата Base: {PAYMENT_BASE}")
    print(f"   Оплата Pro: {PAYMENT_PRO}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
