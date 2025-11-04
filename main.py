import os
import asyncio
import threading
import datetime
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from oils_data import OILS
from google_sheets import connect_to_sheet, add_order, get_orders
from config import BOT_TOKEN, ADMIN_CHAT_ID, GROUP_CHAT_ID

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__)

BOT_URL = os.getenv("BOT_URL", "https://hion-shop-bot.onrender.com")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = f"{BOT_URL}{WEBHOOK_PATH}"

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("🌿 Каталог"),
    KeyboardButton("🧩 Подбор масла"),
    KeyboardButton("🛒 Корзина")
)

# Данные
user_carts = {}
pending_address = {}
pending_phone = {}
user_profiles = {}
user_quiz = {}
sheet = connect_to_sheet()

# === Универсальная функция генерации кода ===
def get_oil_code(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum() or ch == "_")

# === Webhook ===
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/')
def home():
    return "✅ HION Bot is running with oil assistant."

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = types.Update(**update_data)

        async def process_update():
            from aiogram import Bot
            Bot.set_current(bot)
            await dp.process_update(update)

        asyncio.run_coroutine_threadsafe(process_update(), loop)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
    return "OK", 200


# === Напоминания ===
@app.route('/remind')
def remind_users():
    try:
        orders = get_orders(sheet)
        today = datetime.datetime.now().date()
        for order in orders:
            if "@" not in order["Клиент"]:
                continue
            date_str = order["Время"].split(" ")[0]
            order_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            if (today - order_date).days == 30:
                asyncio.run_coroutine_threadsafe(
                    bot.send_message(order["Клиент"], "🌿 Как вам масло? Пора обновить курс 💛"),
                    loop
                )
        return "Reminders sent", 200
    except Exception as e:
        print(f"❌ Reminder error: {e}")
        return str(e), 500


# === /start ===
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать в HION 🌿\n"
        "Натуральные масла холодного отжима — прямо от производителя.\n\n"
        "👇 Выберите действие:",
        reply_markup=main_menu
    )


# === Каталог ===
@dp.message_handler(lambda m: m.text and "каталог" in m.text.lower())
async def open_catalog(message: types.Message):
    markup = InlineKeyboardMarkup()
    for name in OILS.keys():
        code = get_oil_code(name)
        markup.add(InlineKeyboardButton(name, callback_data=f"oil|{code}"))
    await message.answer("🌿 Выберите продукт:", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith("oil|"))
async def oil_info(callback: types.CallbackQuery):
    code = callback.data.split("|")[1]
    oil_name = next((n for n in OILS if get_oil_code(n) == code), None)
    if not oil_name:
        await callback.answer("Ошибка: продукт не найден.")
        return

    oil = OILS[oil_name]
    text = f"*{oil_name}*\n\n{oil['desc']}"
    markup = InlineKeyboardMarkup()
    for vol, price in oil['prices'].items():
        markup.add(InlineKeyboardButton(f"{vol} — {price}₽", callback_data=f"add|{code}|{vol}|{price}"))
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="back_to_catalog"))
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery):
    markup = InlineKeyboardMarkup()
    for name in OILS.keys():
        code = get_oil_code(name)
        markup.add(InlineKeyboardButton(name, callback_data=f"oil|{code}"))
    await callback.message.edit_text("🌿 Выберите продукт:", reply_markup=markup)


# === Добавление в корзину ===
@dp.callback_query_handler(lambda c: c.data.startswith("add|"))
async def add_item(callback: types.CallbackQuery):
    _, code, vol, price = callback.data.split("|")
    user_id = callback.from_user.id
    oil_name = next((n for n in OILS if get_oil_code(n) == code), code)
    user_carts.setdefault(user_id, []).append((oil_name, vol, int(price)))
    await callback.answer("✅ Товар добавлен в корзину")
    await callback.message.answer(
        "🛒 Товар добавлен в корзину!\nОткройте её для оформления 💛",
        reply_markup=main_menu
    )


# === Корзина ===
async def send_cart(user_id, message_obj):
    cart = user_carts.get(user_id, [])
    if not cart:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🌿 Вернуться в каталог", callback_data="back_to_catalog"))
        await message_obj.answer("🧺 Корзина пуста", reply_markup=markup)
        return
    total = sum(p for _, _, p in cart)
    text = "\n".join([f"{i+1}. {n} {v} — {p}₽" for i, (n, v, p) in enumerate(cart)])
    text += f"\n\n💰 Итого: {total}₽"
    markup = InlineKeyboardMarkup()
    for i in range(len(cart)):
        markup.add(InlineKeyboardButton(f"❌ Удалить {i+1}", callback_data=f"remove|{i}"))
    markup.add(
        InlineKeyboardButton("📦 Оформить заказ", callback_data="checkout"),
        InlineKeyboardButton("🗑 Очистить корзину", callback_data="clear_cart")
    )
    await message_obj.answer(text, reply_markup=markup)


@dp.message_handler(lambda m: "корзин" in m.text.lower())
async def view_cart(message: types.Message):
    await send_cart(message.from_user.id, message)


@dp.callback_query_handler(lambda c: c.data.startswith("remove|"))
async def remove_item(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("|")[1])
    if user_id in user_carts and 0 <= index < len(user_carts[user_id]):
        user_carts[user_id].pop(index)
    await callback.message.delete()
    await send_cart(user_id, callback.message)


@dp.callback_query_handler(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_carts[callback.from_user.id] = []
    await callback.message.edit_text("🗑 Корзина очищена.",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Назад в каталог", callback_data="back_to_catalog"))
    )


# === Оформление заказа ===
@dp.callback_query_handler(lambda c: c.data == "checkout")
async def checkout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    if not cart:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🌿 Вернуться в каталог", callback_data="back_to_catalog"))
        await callback.message.edit_text("🧺 Корзина пуста.", reply_markup=markup)
        return

    text = (
        "🚚 <b>Как удобнее получить заказ?</b>\n\n"
        "💛 Стоимость доставки и адрес самовывоза "
        "согласовываются с менеджером после оформления.\n\n"
        "Выберите удобный способ ниже 👇"
    )
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🚗 Доставка", callback_data="delivery"),
        InlineKeyboardButton("🏠 Самовывоз", callback_data="pickup")
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data in ["delivery", "pickup"])
async def choose_delivery(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "pickup":
        await ask_phone(callback.message, "Самовывоз — ул. Гостиева, 8")
    else:
        pending_address[user_id] = True
        await callback.message.edit_text("📍 Напишите адрес доставки (улица, дом, квартира) 💌:")


async def ask_phone(message, address):
    user_id = message.from_user.id
    pending_phone[user_id] = address
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📞 Отправить номер", request_contact=True))
    await message.answer("📞 Укажите номер телефона для связи:", reply_markup=kb)


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    address = pending_phone.pop(user_id, "—")
    await finalize_order(message, address, phone)


async def finalize_order(message, address, phone):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    total = sum(p for _, _, p in cart)
    items = "; ".join([f"{n} {v} — {p}₽" for n, v, p in cart])
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    add_order(sheet, username, items, address, total, phone)
    user_profiles[user_id] = {"address": address, "phone": phone}
    order_text = f"🛍 Новый заказ:\n{items}\n\n💰 {total}₽\n📍 {address}\n📞 {phone}\n👤 {username}"
    await bot.send_message(ADMIN_CHAT_ID, order_text)
    if GROUP_CHAT_ID:
        await bot.send_message(GROUP_CHAT_ID, order_text)
    user_carts[user_id] = []
    await message.answer(
        "Спасибо! Ваш заказ зарегистрирован 💛\n"
        "Менеджер свяжется с вами в течение дня для уточнения деталей ✨",
        reply_markup=main_menu
    )


# === ПОДБОР МАСЛА ===
QUIZ_QUESTIONS = {
    1: ("Если бы вы могли улучшить одно состояние прямо сейчас — что бы это было?",
        ["💪 Энергия и бодрость", "🧘 Спокойствие и устойчивость", "🫀 Сердце и сосуды",
         "💆 Кожа и волосы", "🧠 Концентрация и память", "🌸 Гормональный баланс"]),
    2: ("Как вы чувствуете себя в последние недели?",
        ["😊 Всё стабильно", "😴 Часто устаю", "🥴 Есть тревожность или стресс", "🤧 Бывают простуды", "🤕 Есть проблемы с пищеварением"]),
    3: ("Какой у вас ритм жизни?",
        ["🏃 Очень активный", "💻 Сидячая работа", "😌 Спокойный ритм", "🔥 Много стресса"]),
    4: ("Какие продукты чаще всего на вашем столе?",
        ["🍗 Мясо, рыба, яйца", "🥦 Овощи, крупы, бобовые", "🍕 Фастфуд или сладкое", "🌿 В основном растительное питание"]),
    5: ("Какое масло вы бы хотели — по ощущениям?",
        ["🌰 С насыщенным ореховым вкусом", "💧 Нейтральное, лёгкое", "🌶 Пряное и характерное", "✨ Универсальное — и внутрь, и наружно"]),
    6: ("Используете ли вы масла для ухода за кожей или волосами?",
        ["💆 Да, часто", "💅 Иногда", "🚫 Нет, только внутрь"]),
    7: ("Какую цель хотите достичь быстрее всего?",
        ["🌿 Улучшить самочувствие", "💆 Улучшить внешний вид", "🔥 Повысить энергию", "🧘 Снизить стресс"])
}

OIL_CODES = {
    "flax": "Масло семян льна",
    "hemp": "Масло семян конопли",
    "pumpkin": "Масло семян тыквы",
    "blackseed": "Масло семян чёрного тмина",
    "sunflower": "Масло семян подсолнечника",
    "walnut": "Масло грецкого ореха",
    "coconut": "Масло кокосовое (200 мл)"
}


async def start_quiz(message: types.Message):
    user_quiz[message.from_user.id] = {"step": 1, "answers": {}}
    await send_quiz_question(message, 1)


async def send_quiz_question(message, step):
    q_text, q_options = QUIZ_QUESTIONS[step]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for opt in q_options:
        kb.add(opt)
    nav = []
    if step > 1:
        nav.append("🔙 Назад")
    nav.append("❌ Выйти")
    kb.add(*nav)
    await message.answer(q_text, reply_markup=kb)


@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = (message.text or "").lower()

    # запуск квиза
    if "подбор" in text:
        await start_quiz(message)
        return

    # выход из квиза
    if text.startswith("❌") or "выйти" in text:
        user_quiz.pop(user_id, None)
        await message.answer("Вы вышли из подбора масел 🌿", reply_markup=main_menu)
        return

    # назад
    if text.startswith("🔙") or "назад" in text:
        if user_id in user_quiz:
            step = user_quiz[user_id]["step"]
            if step > 1:
                user_quiz[user_id]["step"] -= 1
                await send_quiz_question(message, user_quiz[user_id]["step"])
            else:
                await message.answer("Это первый вопрос 🌿", reply_markup=main_menu)
        return

    # обработка ответов квиза
    if user_id in user_quiz:
        await handle_quiz_answer(message)
        return

    # ввод адреса при доставке
    if user_id in pending_address:
        address = message.text.strip()
        pending_address.pop(user_id, None)
        await ask_phone(message, address)
        return


async def handle_quiz_answer(message: types.Message):
    uid = message.from_user.id
    data = user_quiz.get(uid, {"step": 1, "answers": {}})
    step = data["step"]
    data["answers"][f"q{step}"] = message.text
    next_step = step + 1
    if next_step in QUIZ_QUESTIONS:
        user_quiz[uid]["step"] = next_step
        await send_quiz_question(message, next_step)
    else:
        await recommend_oil(message, data["answers"])
        user_quiz.pop(uid, None)


async def recommend_oil(message: types.Message, answers):
    joined = " ".join(answers.values()).lower()
    score = {k: 0 for k in OIL_CODES}
    if "устал" in joined or "энерг" in joined: score["coconut"] += 3
    if "стресс" in joined or "тревож" in joined: score["hemp"] += 3
    if "кожа" in joined or "волос" in joined: score["sunflower"] += 3
    if "память" in joined or "мозг" in joined: score["walnut"] += 3
    if "сердце" in joined or "сосуд" in joined: score["flax"] += 3
    if "иммун" in joined or "простуд" in joined: score["blackseed"] += 3
    if "печен" in joined or "жкт" in joined: score["pumpkin"] += 3
    if "гормон" in joined: score["hemp"] += 2; score["pumpkin"] += 2
    best = max(score, key=score.get)

    oil_display = {
        "flax": "💧 Масло семян льна",
        "hemp": "🌿 Масло семян конопли",
        "pumpkin": "🎃 Масло семян тыквы",
        "blackseed": "🌑 Масло семян чёрного тмина",
        "sunflower": "🌻 Масло семян подсолнечника",
        "walnut": "🌰 Масло грецкого ореха",
        "coconut": "🥥 Масло кокосовое"
    }[best]

    code = get_oil_code(OIL_CODES[best])
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"oil|{code}"))
    markup.add(InlineKeyboardButton("🌿 Каталог", callback_data="back_to_catalog"))

    await message.answer(
        f"✨ Мы нашли масло, которое подходит именно вам.\n\n"
        f"<b>{oil_display}</b>\n\n"
        f"🌿 Рекомендуем начать с 1 ч.л. утром курсом 1–2 месяца.\n"
        f"💛 Вы можете добавить его в корзину или открыть каталог.",
        parse_mode="HTML",
        reply_markup=markup
    )


# === Webhook setup ===
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook установлен: {WEBHOOK_URL}")


if __name__ == "__main__":
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    threading.Thread(target=run_loop, daemon=True).start()
    asyncio.run_coroutine_threadsafe(on_startup(), loop)
    print("🚀 Bot is running with persistent event loop")
    app.run(host="0.0.0.0", port=8080)
