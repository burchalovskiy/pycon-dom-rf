import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.executor import start_webhook

from constants import HELLO_MESSAGE, MORTGAGE_INIT_PAYMENT_ERROR_MESSAGE, SUCCESS_MESSAGE, RESPONSE_MESSAGE, \
    MORTGAGE_AMOUNT_REQUEST_MESSAGE, MORTGAGE_INIT_PAYMENT_MESSAGE, COMMAND_ERROR

logger = logging.getLogger()

API_TOKEN = os.getenv("API_TOKEN")
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
WEBAPP_PORT = os.getenv('PORT', default=8000)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


class Form(StatesGroup):
    amount = State()
    init_payment = State()


async def on_startup(dp):
    logging.warning('Starting bot...')
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dp):
    logging.warning('Shutdown bot...')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await Form.amount.set()
    await message.reply(HELLO_MESSAGE.format(message.from_user.username))
    await message.answer(MORTGAGE_AMOUNT_REQUEST_MESSAGE)


@dp.message_handler(lambda message: not message.text.isdigit(), state='*')
async def check_type(message: types.Message, state: FSMContext):
    await message.reply(COMMAND_ERROR)


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.amount)
async def process_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = float(message.text)
        await message.reply(f'Принял {data["amount"]}')

    await Form.init_payment.set()
    await message.answer(MORTGAGE_INIT_PAYMENT_MESSAGE)


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.init_payment)
async def process_init_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['init_payment'] = float(message.text)
        await message.reply(f'Принял {data["init_payment"]}')

        if data['init_payment'] < (data['amount'] * 0.15):
            await message.answer(MORTGAGE_INIT_PAYMENT_ERROR_MESSAGE)
            await Form.init_payment.set()
        else:
            await message.answer(SUCCESS_MESSAGE)
            await message.answer(RESPONSE_MESSAGE)
            await state.finish()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host='0.0.0.0',
        port=WEBAPP_PORT,
    )
