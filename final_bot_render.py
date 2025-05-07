
import logging
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_URL = 'https://best-form.website/data.json'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def fetch_data():
    response = requests.get(DATA_URL, headers=HEADERS)
    return response.json()

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Общая статистика", callback_data='stat')],
        [InlineKeyboardButton("💰 Общая сумма остатков", callback_data='sum')],
        [InlineKeyboardButton("📋 Список товаров", callback_data='list')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите действие:", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = fetch_data()

    if query.data == 'stat':
        message = "<b>📊 Общая статистика:</b>\n\n"
        for item in data:
            total = item.get('quantity', 0) + item.get('received', 0) - item.get('sold', 0)
            value = total * item.get('price', 0)
            message += (
                f"🆔 <code>{item.get('id')}</code> | <b>{item.get('name')}</b>\n"
                f"   Остаток: <b>{total}</b> | Сумма: <b>{value:.2f}</b>\n\n"
            )
        message += f"🕓 Обновлено: <code>{data[0].get('updated')}</code>"
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data='back')]]
        await query.edit_message_text(text=message, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'sum':
        total_sum = sum(
            (item.get('quantity', 0) + item.get('received', 0) - item.get('sold', 0)) * item.get('price', 0)
            for item in data
        )
        msg = f"💰 Общая сумма остатков: <b>{total_sum:.2f}</b>\n🕓 {data[0].get('updated')}"
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data='back')]]
        await query.edit_message_text(text=msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'list':
        keyboard = [[InlineKeyboardButton("🔎 Поиск по названию или ID", callback_data='prompt_search')]]
        for item in data:
            label = f"{item.get('id')} | {item.get('name')}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"item_{item.get('id')}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data='back')])
        await query.edit_message_text("Выберите товар или используйте поиск:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'prompt_search':
        await query.edit_message_text("Введите название товара или ID для поиска:")

    elif query.data == 'back':
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())

    elif query.data.startswith("item_"):
        item_id = int(query.data.split("_")[1])
        item = next((i for i in data if i.get('id') == item_id), None)
        if item:
            total = item.get('quantity', 0) + item.get('received', 0) - item.get('sold', 0)
            value = total * item.get('price', 0)
            msg = (
                f"<b>{item.get('name')}</b> (ID: <code>{item.get('id')}</code>)\n"
                f"📦 Остаток: <b>{total}</b>\n"
                f"💰 Сумма остатка: <b>{value:.2f}</b>\n"
                f"🕓 {item.get('updated')}"
            )
            keyboard = [[InlineKeyboardButton("🔙 Назад к списку", callback_data='list')]]
            await query.edit_message_text(text=msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    data = fetch_data()
    matches = [item for item in data if text in str(item.get('id')).lower() or text in item.get('name', '').lower()]

    if not matches:
        await update.message.reply_text("❌ Товар не найден.")
        return

    keyboard = [[InlineKeyboardButton(f"{item.get('id')} | {item.get('name')}", callback_data=f"item_{item.get('id')}")] for item in matches]
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data='back')])
    await update.message.reply_text("🔍 Найденные товары:", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == '__main__':
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("menu", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search))
        print("✅ Бот запущен. Ожидаю команды...")
        app.run_polling()
    except Exception as e:
        print("❌ Ошибка запуска:", e)
        input("Нажмите Enter для выхода...")
