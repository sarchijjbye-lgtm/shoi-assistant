import os
import asyncio
import threading
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# === Конфигурация ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = "https://shoi-assistant.onrender.com"  # URL Render
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

# === Инициализация бота и Flask ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# Главный event loop для aiogram
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

user_data = {}

@app.route("/")
def home():
    return "💧 SHOI Assistant is alive and running."

@app.route(WEBHOOK_PATH, methods=["POST"])
def receive_update():
    """
    Flask вызывает этот endpoint при каждом новом апдейте Telegram.
    Мы просто отправляем update в event loop aiogram.
    """
    update = types.Update(**request.json)
    asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
    return {"ok": True}


# === Логика бота ===
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Начать подбор масла")]])
    await message.answer(
        "Здравствуйте! 💧\nЯ SHOI-ассистент.\n"
        "Помогу подобрать масло холодного отжима, которое лучше всего подойдёт именно вам.\n\n"
        "Нажмите «Начать подбор масла».",
        reply_markup=kb
    )


@dp.message(lambda m: m.text in ["Начать подбор масла", "🔄 Пройти опрос заново"])
async def question_1(message: types.Message):
    user_data[message.from_user.id] = {}
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Иммунитет и защита")],
        [KeyboardButton(text="ЖКТ и печень")],
        [KeyboardButton(text="Кожа и волосы")],
        [KeyboardButton(text="Концентрация и мозг")],
        [KeyboardButton(text="Стресс и настроение")],
        [KeyboardButton(text="Сердце и сосуды")],
        [KeyboardButton(text="Гормональный баланс")]
    ])
    await message.answer("1️⃣ Что для вас сейчас важнее всего?", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "Иммунитет и защита", "ЖКТ и печень", "Кожа и волосы",
    "Концентрация и мозг", "Стресс и настроение", "Сердце и сосуды", "Гормональный баланс"
])
async def question_2(message: types.Message):
    user_data[message.from_user.id]["q1"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Часто устаю")],
        [KeyboardButton(text="Есть проблемы с пищеварением")],
        [KeyboardButton(text="Сухая кожа")],
        [KeyboardButton(text="Тревожность и стресс")],
        [KeyboardButton(text="Часто болею")],
        [KeyboardButton(text="Хочу больше энергии")]
    ])
    await message.answer("2️⃣ Что вы чаще всего чувствуете?", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "Часто устаю", "Есть проблемы с пищеварением", "Сухая кожа",
    "Тревожность и стресс", "Часто болею", "Хочу больше энергии"
])
async def question_3(message: types.Message):
    user_data[message.from_user.id]["q2"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Мясо, рыба, яйца")],
        [KeyboardButton(text="Овощи и крупы")],
        [KeyboardButton(text="Фастфуд и сладкое")],
        [KeyboardButton(text="Почти не ем животные продукты")]
    ])
    await message.answer("3️⃣ Как вы питаетесь чаще всего?", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "Мясо, рыба, яйца", "Овощи и крупы", "Фастфуд и сладкое", "Почти не ем животные продукты"
])
async def question_4(message: types.Message):
    user_data[message.from_user.id]["q3"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Активный образ жизни")],
        [KeyboardButton(text="Сидячая работа")],
        [KeyboardButton(text="Постоянный стресс")],
        [KeyboardButton(text="Спокойный ритм")]
    ])
    await message.answer("4️⃣ Какой у вас образ жизни?", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "Активный образ жизни", "Сидячая работа", "Постоянный стресс", "Спокойный ритм"
])
async def question_5(message: types.Message):
    user_data[message.from_user.id]["q4"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Нейтральный вкус")],
        [KeyboardButton(text="Ореховый вкус")],
        [KeyboardButton(text="Пряный вкус")],
        [KeyboardButton(text="Универсальность — внутрь и для ухода")]
    ])
    await message.answer("5️⃣ Что вам важнее в вкусе и применении масла?", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "Нейтральный вкус", "Ореховый вкус", "Пряный вкус", "Универсальность — внутрь и для ухода"
])
async def show_result(message: types.Message):
    user_data[message.from_user.id]["q5"] = message.text
    answers = " ".join(user_data[message.from_user.id].values()).lower()

    oils = {
        "flax": {"name": "💧 Льняное масло SHOI", "why": "Поддерживает сердце, сосуды и мозг. Источник Омега-3.", "how": "1 ч.л. утром натощак."},
        "hemp": {"name": "🌿 Конопляное масло SHOI", "why": "Баланс Омега-3 и Омега-6, помогает при стрессе.", "how": "1 ч.л. утром курсом 1–2 месяца."},
        "pumpkin": {"name": "🎃 Тыквенное масло SHOI", "why": "Поддерживает печень и ЖКТ, богато цинком.", "how": "1 ч.л. 2 раза в день до еды."},
        "blackseed": {"name": "🌑 Масло чёрного тмина SHOI", "why": "Укрепляет иммунитет, снижает воспаления.", "how": "0.5–1 ч.л. после еды курсом 30 дней."},
        "coconut": {"name": "🥥 Кокосовое масло SHOI", "why": "Источник энергии, улучшает кожу и волосы.", "how": "Добавляйте в кашу или кофе, можно наружно."},
        "sunflower": {"name": "🌻 Подсолнечное масло SHOI", "why": "Богато витамином E, улучшает кожу.", "how": "1 ч.л. в день в составе салатов."},
        "walnut": {"name": "🌰 Масло грецкого ореха SHOI", "why": "Поддерживает концентрацию и память.", "how": "1 ч.л. утром перед едой."}
    }

    score = {k: 0 for k in oils.keys()}
    if "иммун" in answers: score["blackseed"] += 3
    if "жкт" in answers or "печен" in answers: score["pumpkin"] += 3
    if "кожа" in answers: score["sunflower"] += 3
    if "стресс" in answers: score["hemp"] += 3
    if "мозг" in answers: score["walnut"] += 3
    if "сердце" in answers: score["flax"] += 3
    if "энерг" in answers: score["coconut"] += 3

    best = max(score, key=lambda k: score[k])
    rec = oils[best]
    restart_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="🔄 Пройти опрос заново")]])

    await message.answer(
        f"✨ Мы подобрали масло именно для вас!\n\n"
        f"<b>{rec['name']}</b>\n\n"
        f"🔹 Почему оно вам подходит: {rec['why']}\n"
        f"💡 Как принимать: {rec['how']}\n\n"
        f"<a href='https://wa.me/message/3NNTHAAA6GFMH1'>Написать в WhatsApp для заказа</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=restart_kb
    )


# === Инициализация webhook и фонового потока ===
async def on_startup():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    print("💧 SHOI Assistant webhook установлен успешно!")

def start_bot():
    loop.run_until_complete(on_startup())
    loop.run_forever()

if __name__ == "__main__":
    # Запускаем бота в фоне
    threading.Thread(target=start_bot, daemon=True).start()
    # Запускаем Flask-сервер
    app.run(host="0.0.0.0", port=8080)
