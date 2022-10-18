import os
from dotenv import load_dotenv
import requests

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv('.env')
TG_API_TOKEN = os.getenv('TG_API_TOKEN')
OWM_API_TOKEN = os.getenv('OWM_API_TOKEN')

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def create_keyboard() -> InlineKeyboardMarkup:
    """Creates inline keyboard markup"""
    keyboard = [
        [
            InlineKeyboardButton('Find city', callback_data='find'),
        ],
        [
            InlineKeyboardButton('Help', callback_data='help'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with bot menu."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please choose:",
        reply_markup=create_keyboard()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery."""
    query = update.callback_query

    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")
    if query.data == 'help':
        await help_command(update, context)
    elif query.data == 'find':
        await find_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    message_text = "Use /start to view a menu of this bot." \
                   "Use /help to get help for using this bot."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text)


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to find a city for weather forecast"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Input the name of the city:")


def kelv_to_cels(kelv: float) -> float:
    return kelv - 273


async def find_weather_for_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Finds a weather forecast for user-specified city"""
    city_name = update.message.text
    url_city = f'http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={OWM_API_TOKEN}'
    r_city = requests.get(url_city)
    try:
        city_dict = r_city.json()[0]
    except IndexError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Can't find this city.")
        return

    lat = city_dict['lat']
    lon = city_dict['lon']

    url_weather = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_TOKEN}'
    r_weather = requests.get(url_weather)
    weather_dict = r_weather.json()

    description = weather_dict['weather'][0]['description']
    temp_kelv = float(weather_dict['main']['temp'])
    temp_cels = kelv_to_cels(temp_kelv)

    message = f'Temparature: {temp_cels:.2f} °C. {description.capitalize()}'

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    await start_command(update, context)


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TG_API_TOKEN).build()

    start_handler = CommandHandler('start', start_command)
    help_handler = CommandHandler('help', help_command)
    city_handler = MessageHandler(filters.TEXT, find_weather_for_city)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(city_handler)
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == "__main__":
    main()
