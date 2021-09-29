#!venv/bin/python
import json
import urllib.request
import logging
import aiohttp
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import deep_linking, exceptions
from random import choice
import string

import pickle

from poll import Poll

bot = Bot(token="248190991:AAFYN8IC-4-Zb6nXzMeBkPvM5YCxst094mw")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

CHATS_CACHE = 'chats'
POLL_CACHE = 'poll'
ADMIN_CACHE = 'admin'
API_CACHE = 'api'


def loadCache(cache_name, val):
    try:
        with open(cache_name, 'rb') as fp:
            return pickle.load(fp)
    except:
        return val


def saveCache(cache_name, val):
    with open(cache_name, 'wb') as fp:
        pickle.dump(val, fp)


poll_active = loadCache(POLL_CACHE, None)
chats_send = loadCache(CHATS_CACHE, {})
admins = loadCache(ADMIN_CACHE, [])
api_url = loadCache(
    API_CACHE, "http://46.17.97.44:5003/potter/?text=%D1%82%D0%B5%D0%BA%D1%81%D1%82&temp=1")

secret_key = ''.join(choice(
    string.ascii_uppercase + string.digits) for _ in range(8))


def check(chat_id):  # surely there is a smarter way around it but i am too lazy to google
    if not chat_id in chats_send:
        chats_send[chat_id] = True
        saveCache(CHATS_CACHE, chats_send)


@dp.poll_answer_handler()
async def handle_poll_answer(answer: types.PollAnswer):
    global poll_active
    if not poll_active:
        await message.answer("Опрос не найден")
        return
    poll_active.change_answer(
        answer.poll_id, answer.user.id, answer.option_ids)
    saveCache(POLL_CACHE, poll_active)


@dp.message_handler(commands=["switch"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    chats_send[message.chat.id] = not chats_send[message.chat.id]
    saveCache(CHATS_CACHE, chats_send)
    if (chats_send[message.chat.id]):
        await message.answer("Baм буду приходить активные опросы")
    else:
        await message.answer("Опросы будут игнорироваться")


@dp.message_handler(commands=["poll"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    if not message.from_user.id in admins:
        await message.answer("Нет доступа")
        return
    if message.chat.type == types.ChatType.PRIVATE:

        poll = Poll(message.chat.id)

        words = message.text.split()
        if len(words) == 1 or not words[1].isdigit():
            amount = 2
        else:
            amount = int(words[1])
        waiting = await message.answer(text="generating 0%")
        for i in range(amount):
            async with aiohttp.ClientSession() as session:
                # poll.add_option("somewjafjkljsal jfjasojfiasjfiojasfoi")
                # continue

                async with session.get(api_url) as resp:
                    data = await resp.json()
                    poll.add_option(data["text"])
                    await waiting.edit_text(
                        text=f"generating {round((i + 1)/amount * 100)}%")
    await waiting.delete()
    try:
        await poll.send_options(bot, message.chat.id)
    except exceptions.CantParseEntities as e:
        await message.answer(text=f"bad entity")
        return
    global poll_active
    poll_active = poll

    keyboard_conformation = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_conformation.add(types.KeyboardButton(text="Ок"))
    keyboard_conformation.add(types.KeyboardButton(text="Отмена"))

    suffix = ""

    count = 0
    countAll = len(chats_send)
    for chat_id in chats_send:
        if chats_send[chat_id]:
            count += 1
    if count > 5:
        suffix = "ов"
    elif count > 2:
        suffix = "а"

    off = ""
    if countAll - count > 0:
        off = f" (отключено: {countAll - count})"

    await message.answer(f"Отправляем в {count} чат{suffix}?{off}", reply_markup=keyboard_conformation)


@dp.message_handler(commands=["finish"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    if not message.from_user.id in admins:
        await message.answer("Нет доступа")
        return
    global poll_active
    if not poll_active:
        await message.answer("Опрос не найден")
        return

    ans = await poll_active.finish(bot, message.chat.id)
    poll_active = None
    os.remove(POLL_CACHE)
    await message.answer(ans)


@dp.message_handler(commands=["admin"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    words = message.text.split()
    ans = "Используйте /admin <secret key>"
    if message.from_user.id in admins:
        ans = "Вы уже админ"
    elif len(admins) == 0:
        admins.append(message.from_user.id)
        saveCache(ADMIN_CACHE, admins)
        ans = "Поздравляю вы первый админ"
    elif len(words) == 2 and words[1] == secret_key:
        admins.append(message.from_user.id)
        saveCache(ADMIN_CACHE, admins)
        ans = "Поздравляю вы админ"

    await message.answer(ans)


@dp.message_handler(commands=["stats"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    if not poll_active:
        await message.answer("Опрос не найден")
        return
    await poll_active.send_results(bot, message.chat.id)


@dp.message_handler(commands=["api"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    if not message.from_user.id in admins:
        await message.answer("Нет доступа")
        return

    words = message.text.split()

    global api_url
    ans = "Текущий"
    if len(words) == 2:
        api_url = words[1]
        ans = "Новый"
        saveCache(API_CACHE, api_url)

    await message.answer(ans + f" <a href='{api_url}'>api</a>", parse_mode="HTML")


@dp.message_handler(commands=["key"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    if not message.from_user.id in admins:
        await message.answer("Нет доступа")
        return
    await message.answer(f"`{secret_key}`", parse_mode="Markdown")

remove_keyboard = types.ReplyKeyboardRemove()
@dp.message_handler(lambda message: message.text == "Отмена")
async def action_cancel(message: types.Message):
    check(message.chat.id)

    global poll_active
    if not poll_active:
        await message.answer("Опрос не найден")
        return

    if poll_active.send_out:
        await message.answer("Aктивный опрос уже отправлен")
        return

    poll_active = None
    await message.answer("Введите /poll, чтобы начать заново", reply_markup=remove_keyboard)


@dp.message_handler(lambda message: message.text == "Ок")
async def action_cancel(message: types.Message):
    check(message.chat.id)
    global poll_active
    if not poll_active:
        await message.answer("Опрос не найден")
        return

    ans = await poll_active.send(bot, chats_send)
    saveCache(POLL_CACHE, poll_active)
    await message.answer(ans, reply_markup=remove_keyboard)


@dp.message_handler()
async def just_check(message: types.Message):
    check(message.chat.id)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
