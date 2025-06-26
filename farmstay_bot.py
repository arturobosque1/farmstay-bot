
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import sqlite3
from datetime import datetime

API_ID = 123456  # <-- Замени на свой
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

app = Client("farmstay_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# База данных
conn = sqlite3.connect("bookings.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    region TEXT,
    house TEXT,
    date TEXT,
    services TEXT,
    created_at TEXT
)""")
conn.commit()

# Память пользователей
user_data = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏞️ Карпаты", callback_data="region_karpaty")],
        [InlineKeyboardButton("🌳 Подмосковье", callback_data="region_podmoskovie")],
        [InlineKeyboardButton("🌾 Кубань", callback_data="region_kuban")]
    ])

    await message.reply_text(
    "👋 Привет! Добро пожаловать в эко-сервис 🏕️ *FarmStay*.\n\n"
    "Выбери регион, где ты хочешь остановиться:",
    reply_markup=keyboard,
    parse_mode="Markdown"
)

@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data.startswith("region_"):
        region = data.split("_")[1]
        user_data[user_id]["region"] = region

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏡 Лесная сказка", callback_data="house_forest")],
            [InlineKeyboardButton("🌄 Вид на горы", callback_data="house_mountain")]
        ])

        await callback_query.message.edit_text(
            f"📍 Регион выбран: *{region.title()}*

Выбери домик:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data.startswith("house_"):
        house = data.split("_")[1]
        user_data[user_id]["house"] = house

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 12–14 июля", callback_data="date_12_14")],
            [InlineKeyboardButton("📅 20–22 июля", callback_data="date_20_22")]
        ])

        await callback_query.message.edit_text(
            f"🏡 Домик выбран: *{house.replace('forest', 'Лесная сказка').replace('mountain', 'Вид на горы')}*

Выбери даты:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data.startswith("date_"):
        date = data.split("_", 1)[1].replace("_", "–")
        user_data[user_id]["date"] = date

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚲 Велосипед", callback_data="service_bike")],
            [InlineKeyboardButton("🍳 Завтрак", callback_data="service_breakfast")],
            [InlineKeyboardButton("🐐 Экскурсия", callback_data="service_tour")],
            [InlineKeyboardButton("✅ Завершить", callback_data="done")]
        ])

        user_data[user_id]["services"] = []
        await callback_query.message.edit_text(
            f"📅 Даты брони: *{date}*

Выбери доп.услуги (можно несколько):",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif data.startswith("service_"):
        service = data.split("_")[1]
        if service not in user_data[user_id]["services"]:
            user_data[user_id]["services"].append(service)
        await callback_query.answer("Услуга добавлена ✔")

    elif data == "done":
        region = user_data[user_id].get("region", "—")
        house = user_data[user_id].get("house", "—")
        date = user_data[user_id].get("date", "—")
        services = user_data[user_id].get("services", [])
        service_text = ", ".join(services) or "—"

        cursor.execute(
            "INSERT INTO bookings (user_id, region, house, date, services, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, region, house, date, service_text, datetime.now().isoformat())
        )
        conn.commit()

        await callback_query.message.edit_text(
            f"🎉 *Бронирование подтверждено!*

"
            f"📍 Регион: *{region.title()}*
"
            f"🏡 Домик: *{house}*
"
            f"📅 Даты: *{date}*
"
            f"🧺 Услуги: {service_text}

"
            f"Спасибо за выбор *FarmStay*! 🌿",
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    app.run()
