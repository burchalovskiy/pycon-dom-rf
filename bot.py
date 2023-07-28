import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook

from constants import HELLO_MESSAGE

logger = logging.getLogger()

API_TOKEN = os.getenv("API_TOKEN")
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
WEBAPP_PORT = os.getenv('PORT', default=8000)

bot = Bot(token=API_TOKEN)
dispatcher = Dispatcher(bot)


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


@dispatcher.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(HELLO_MESSAGE)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    start_webhook(
        dispatcher=dispatcher,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host='0.0.0.0',
        port=WEBAPP_PORT,
    )
