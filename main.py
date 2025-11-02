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

# === Инициализация ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# Главный event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

user_data = {}

# === Flask ===
@app.route("/")
def home():
    return "💧 SHOI Assistant is alive and mindful."

@app.route(WEBHOOK_PATH, methods=["POST"])
def receive_update():
    update = types.Update(**request.json)
    asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
    return {"ok": True}


# === ТЕКСТЫ И ВОПРОСЫ ===

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="🌿 Начать подбор масла")]])
    await message.answer(
        "💧 Здравствуйте!\n\n"
        "Я SHOI-ассистент — ваш личный гид по маслам холодного отжима.\n"
        "Давайте мягко подберём масло, которое поддержит именно ваш ритм, тело и настроение 🌿\n\n"
        "Нажмите «Начать подбор масла».",
        reply_markup=kb
    )


@dp.message(lambda m: m.text in ["🌿 Начать подбор масла", "🔄 Пройти опрос заново"])
async def question_1(message: types.Message):
    user_data[message.from_user.id] = {}
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="💪 Энергия и бодрость")],
        [KeyboardButton(text="🧘 Спокойствие и устойчивость")],
        [KeyboardButton(text="🫀 Сердце и сосуды")],
        [KeyboardButton(text="💆 Кожа и волосы")],
        [KeyboardButton(text="🧠 Концентрация и память")],
        [KeyboardButton(text="🌸 Гормональный баланс")]
    ])
    await message.answer(
        "Если бы вы могли улучшить одно состояние прямо сейчас — что бы это было? 💭",
        reply_markup=kb
    )


@dp.message(lambda m: m.text in [
    "💪 Энергия и бодрость", "🧘 Спокойствие и устойчивость", "🫀 Сердце и сосуды",
    "💆 Кожа и волосы", "🧠 Концентрация и память", "🌸 Гормональный баланс"
])
async def question_2(message: types.Message):
    user_data[message.from_user.id]["q1"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="😊 Всё стабильно")],
        [KeyboardButton(text="😴 Часто устаю")],
        [KeyboardButton(text="🥴 Есть тревожность или стресс")],
        [KeyboardButton(text="🤧 Бывают простуды")],
        [KeyboardButton(text="🤕 Есть проблемы с пищеварением")]
    ])
    await message.answer(
        "Как вы чувствуете себя в последние недели? 🌿",
        reply_markup=kb
    )


@dp.message(lambda m: m.text in [
    "😊 Всё стабильно", "😴 Часто устаю", "🥴 Есть тревожность или стресс",
    "🤧 Бывают простуды", "🤕 Есть проблемы с пищеварением"
])
async def question_3(message: types.Message):
    user_data[message.from_user.id]["q2"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🏃 Очень активный")],
        [KeyboardButton(text="💻 Сидячая работа")],
        [KeyboardButton(text="😌 Спокойный ритм")],
        [KeyboardButton(text="🔥 Много стресса")]
    ])
    await message.answer("Какой у вас сейчас ритм жизни? ☀️", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "🏃 Очень активный", "💻 Сидячая работа", "😌 Спокойный ритм", "🔥 Много стресса"
])
async def question_4(message: types.Message):
    user_data[message.from_user.id]["q3"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🍗 Мясо, рыба, яйца")],
        [KeyboardButton(text="🥦 Овощи, крупы, бобовые")],
        [KeyboardButton(text="🍕 Фастфуд или сладкое")],
        [KeyboardButton(text="🌿 В основном растительное питание")]
    ])
    await message.answer("Какие продукты чаще всего на вашем столе? 🥣", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "🍗 Мясо, рыба, яйца", "🥦 Овощи, крупы, бобовые",
    "🍕 Фастфуд или сладкое", "🌿 В основном растительное питание"
])
async def question_5(message: types.Message):
    user_data[message.from_user.id]["q4"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="💆 Да, часто")],
        [KeyboardButton(text="💅 Иногда")],
        [KeyboardButton(text="🚫 Нет, только внутрь")]
    ])
    await message.answer("Используете ли вы масла для ухода за кожей или волосами? 💧", reply_markup=kb)


@dp.message(lambda m: m.text in ["💆 Да, часто", "💅 Иногда", "🚫 Нет, только внутрь"])
async def question_6(message: types.Message):
    user_data[message.from_user.id]["q5"] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🌰 Ореховый вкус")],
        [KeyboardButton(text="💧 Нейтральный, лёгкий")],
        [KeyboardButton(text="🌶 Пряный и характерный")],
        [KeyboardButton(text="✨ Универсальное — и внутрь, и наружно")]
    ])
    await message.answer("Какое масло вы бы выбрали по ощущениям? 🌸", reply_markup=kb)


@dp.message(lambda m: m.text in [
    "🌰 Ореховый вкус", "💧 Нейтральный, лёгкий",
    "🌶 Пряный и характерный", "✨ Универсальное — и внутрь, и наружно"
])
async def show_result(message: types.Message):
    user_data[message.from_user.id]["q6"] = message.text
    answers = " ".join(user_data[message.from_user.id].values()).lower()

    oils = {
        "flax": {"name": "💧 Льняное масло SHOI", "why": "Поддерживает сердце, сосуды и мозг. Источник Омега-3 и природных антиоксидантов.", "how": "По 1 ч.л. утром натощак или добавляйте в салаты."},
        "hemp": {"name": "🌿 Конопляное масло SHOI", "why": "Баланс Омега-3 и Омега-6, мягко снижает стресс и воспаления.", "how": "1 ч.л. утром курсом 1–2 месяца."},
        "pumpkin": {"name": "🎃 Тыквенное масло SHOI", "why": "Поддерживает печень и ЖКТ, богато цинком и магнием.", "how": "1 ч.л. 2 раза в день до еды."},
        "blackseed": {"name": "🌑 Масло чёрного тмина SHOI", "why": "Укрепляет иммунитет, помогает при простудах и аллергиях.", "how": "0.5–1 ч.л. после еды курсом 30 дней."},
        "coconut": {"name": "🥥 Кокосовое масло SHOI", "why": "Источник быстрой энергии, улучшает кожу и волосы.", "how": "Добавляйте в кашу, кофе или используйте наружно."},
        "sunflower": {"name": "🌻 Подсолнечное масло SHOI", "why": "Богато витамином E, улучшает состояние кожи и обмен веществ.", "how": "1 ч.л. в день в составе салатов."},
        "walnut": {"name": "🌰 Масло грецкого ореха SHOI", "why": "Поддерживает концентрацию, память и работу сердца.", "how": "1 ч.л. утром перед едой."}
    }

    score = {k: 0 for k in oils.keys()}
    if "иммун" in answers or "простуд" in answers: score["blackseed"] += 3
    if "жкт" in answers or "печен" in answers or "пищевар" in answers: score["pumpkin"] += 3
    if "кожа" in answers or "волос" in answers: score["sunflower"] += 3; score["coconut"] += 1
    if "стресс" in answers or "тревож" in answers: score["hemp"] += 3
    if "мозг" in answers or "память" in answers: score["walnut"] += 3
    if "сердце" in answers or "сосуд" in answers: score["flax"] += 3
    if "энерг" in answers or "устал" in answers: score["coconut"] += 3
    if "гормон" in answers: score["hemp"] += 2; score["pumpkin"] += 2

    best = max(score, key=lambda k: score[k])
    rec = oils[best]
    restart_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="🔄 Пройти опрос заново")]])

    await message.answer(
        f"✨ Мы нашли масло, которое мягко откликается на ваши ответы.\n\n"
        f"<b>{rec['name']}</b>\n\n"
        f"🔹 Почему оно вам подходит: {rec['why']}\n"
        f"💡 Как принимать: {rec['how']}\n\n"
        f"💬 Хотите оформить заказ или узнать, как сочетать масла между собой?\n"
        f"<a href='https://wa.me/message/3NNTHAAA6GFMH1'>Написать в WhatsApp</a>\n\n"
        f"🌿 <i>Чтобы попробовать заново — нажмите «Пройти опрос заново».</i>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=restart_kb
    )


# === Запуск webhook и Flask ===
async def on_startup():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    print("💧 SHOI Assistant webhook установлен успешно!")

def start_bot():
    loop.run_until_complete(on_startup())
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=start_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
