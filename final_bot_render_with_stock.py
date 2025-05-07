
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_URL = "https://best-form.website/data.json"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

logging.basicConfig(level=logging.INFO)

def fetch_data():
    response = requests.get(DATA_URL, headers=HEADERS)
    return response.json()

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Общая статистика", callback_data='stat')],
        [InlineKeyboardButton("💰 Общая сумма остатков", callback_data='sum')],
        [InlineKeyboardButton("📋 Список товаров", callback_data='list')]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите действие:", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = fetch_data()

    if query.data == 'stat':
        message = "<b>📊 Общая статистика:</b>\n\n"
        for item in data:
            total = item['quantity']
            value = total * item['price']
            message += (
                f"🆔 <code>{item['id']}</code> | <b>{item['name']}</b>\n"
                f"   Остаток: <b>{total}</b> | Сумма: <b>{value:.2f}</b>\n\n"
            )
        message += f"🕓 Обновлено: <code>{data[0].get('updated')}</code>"
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data='back')]]
        await query.edit_message_text(text=message, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'sum':
        total_sum = sum(item['quantity'] * item['price'] for item in data)
        msg = f"💰 Общая сумма остатков: <b>{total_sum:.2f}</b>\n🕓 {data[0].get('updated')}"
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data='back')]]
        await query.edit_message_text(text=msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'list':
        keyboard = [[InlineKeyboardButton("🔎 Поиск по названию или ID", callback_data='prompt_search')]]
        for item in data:
            label = f"{item['id']} | {item['name']} (📦 {item['quantity']})"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"item_{item['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data='back')])
        await query.edit_message_text("Выберите товар или используйте поиск:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'prompt_search':
        await query.edit_message_text("Введите название товара или ID для поиска:")

    elif query.data == 'back':
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())

    elif query.data.startswith("item_"):
        item_id = int(query.data.split("_")[1])
        item = next((i for i in data if i['id'] == item_id), None)
        if item:
            total = item['quantity']
            value = total * item['price']
            msg = (
                f"<b>{item['name']}</b> (ID: <code>{item['id']}</code>)\n"
                f"📦 Остаток: <b>{total}</b>\n"
                f"💰 Сумма остатка: <b>{value:.2f}</b>\n"
                f"🕓 {item['updated']}"
            )
            keyboard = [[InlineKeyboardButton("🔙 Назад к списку", callback_data='list')]]
            await query.edit_message_text(text=msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    data = fetch_data()
    matches = [item for item in data if text in str(item['id']).lower() or text in item['name'].lower()]

    if not matches:
        await update.message.reply_text("❌ Товар не найден.")
        return

    keyboard = [[InlineKeyboardButton(f"{item['id']} | {item['name']} (📦 {item['quantity']})", callback_data=f"item_{item['id']}")] for item in matches]
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data='back')])
    await update.message.reply_text("🔍 Найденные товары:", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search))
    print("✅ Бот запущен. Ожидаю команды...")
    app.run_polling()
