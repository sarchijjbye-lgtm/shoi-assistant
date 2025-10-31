import os
TOKEN = os.getenv("TOKEN")
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "SHOI Assistant is alive 💧"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set. Please add your Telegram bot token from BotFather.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="Начать подбор масла")]
    ])
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
        "flax": {
            "name": "💧 Льняное масло SHOI",
            "why": "Поддерживает сердце, сосуды и мозг. Источник Омега-3 и антиоксидантов.",
            "how": "Принимайте по 1 ч.л. утром натощак или добавляйте в салаты."
        },
        "hemp": {
            "name": "🌿 Конопляное масло SHOI",
            "why": "Баланс Омега-3 и Омега-6, помогает при стрессе, тревоге и воспалениях.",
            "how": "1 ч.л. утром, курсом 1–2 месяца."
        },
        "pumpkin": {
            "name": "🎃 Тыквенное масло SHOI",
            "why": "Поддерживает печень, ЖКТ и мужское здоровье, богато цинком и магнием.",
            "how": "1 ч.л. 2 раза в день до еды."
        },
        "blackseed": {
            "name": "🌑 Масло чёрного тмина SHOI",
            "why": "Укрепляет иммунитет, снижает воспаления, помогает при простудах и аллергии.",
            "how": "0.5–1 ч.л. после еды, курсом 30 дней."
        },
        "coconut": {
            "name": "🥥 Кокосовое масло SHOI",
            "why": "Источник быстрой энергии, улучшает иммунитет и состояние кожи и волос.",
            "how": "Можно добавлять в кашу, кофе или использовать наружно."
        },
        "sunflower": {
            "name": "🌻 Подсолнечное масло SHOI",
            "why": "Богато витамином E, улучшает кожу и обмен веществ.",
            "how": "1 ч.л. в день в составе салатов."
        },
        "walnut": {
            "name": "🌰 Масло грецкого ореха SHOI",
            "why": "Поддерживает концентрацию, память и работу сердца.",
            "how": "1 ч.л. утром перед едой."
        }
    }
    
    score = {k: 0 for k in oils.keys()}

    if "иммун" in answers:
        score["blackseed"] += 3
    if "жкт" in answers or "печен" in answers or "пищеварен" in answers:
        score["pumpkin"] += 3
    if "кожа" in answers or "волос" in answers or "сухая" in answers:
        score["sunflower"] += 3
        score["coconut"] += 1
    if "стресс" in answers or "тревож" in answers:
        score["hemp"] += 3
    if "мозг" in answers or "концентра" in answers:
        score["walnut"] += 3
    if "сердце" in answers or "сосуд" in answers:
        score["flax"] += 3
    if "энерг" in answers or "актив" in answers:
        score["coconut"] += 3
    if "гормональн" in answers:
        score["pumpkin"] += 2
        score["hemp"] += 2
    if "устаю" in answers or "усталь" in answers:
        score["coconut"] += 2
        score["walnut"] += 1
    if "болею" in answers:
        score["blackseed"] += 3
    if "сидяч" in answers:
        score["flax"] += 2
        score["walnut"] += 1
    if "спокойн" in answers:
        score["sunflower"] += 1
        score["walnut"] += 1
    if "нейтральн" in answers:
        score["sunflower"] += 1
        score["coconut"] += 1
    if "орехов" in answers:
        score["walnut"] += 2
    if "пряный" in answers:
        score["blackseed"] += 1
        score["pumpkin"] += 1
    if "универсальн" in answers:
        score["coconut"] += 2
    if "мясо" in answers or "рыба" in answers:
        score["flax"] += 1
    if "овощи" in answers or "крупы" in answers:
        score["sunflower"] += 1
    if "фастфуд" in answers or "сладкое" in answers:
        score["pumpkin"] += 2
        score["hemp"] += 1
    if "почти не ем" in answers or "животные продукты" in answers:
        score["flax"] += 2
        score["walnut"] += 1

    best = max(score, key=lambda k: score[k])
    rec = oils[best]

    restart_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🔄 Пройти опрос заново")]
    ])
    
    await message.answer(
        f"✨ Мы подобрали масло именно для вас!\n\n"
        f"<b>{rec['name']}</b>\n\n"
        f"🔹 Почему оно вам подходит: {rec['why']}\n"
        f"💡 Как принимать: {rec['how']}\n\n"
        f"📊 9 из 10 клиентов SHOI отмечают улучшение самочувствия уже через 7 дней.\n\n"
        f"💬 Хотите заказать или получить персональную консультацию?\n"
        f"<a href='https://wa.me/message/3NNTHAAA6GFMH1'>Напишите в WhatsApp — помогу оформить заказ прямо сейчас.</a>\n\n"
        f"💡 <i>Хотите подобрать другое масло? Нажмите кнопку ниже.</i>",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=restart_kb
    )

async def main():
    print("🤖 SHOI-ассистент запущен и готов к работе!")
    print("💬 Отправьте /start боту в Telegram для начала работы")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
