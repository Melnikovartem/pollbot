#!venv/bin/python
import json
import urllib.request
import logging
import aiohttp
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import deep_linking, exceptions

import pickle

from poll import Poll

bot = Bot(token="248190991:AAFYN8IC-4-Zb6nXzMeBkPvM5YCxst094mw")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

CHATS_CAHCE = 'chats'
POLL_CHACHE = 'poll'

poll_active = None
try:
    with open(POLL_CHACHE, 'rb') as fp:
        poll_active = pickle.load(fp)
except:
    pass

chats_send = {}
try:
    with open(CHATS_CAHCE, 'rb') as fp:
        chats_send = pickle.load(fp)
except:
    pass


def check(chat_id):  # surely there is a smarter way around it but i am too lazy to google
    if not chat_id in chats_send:
        chats_send[chat_id] = True
    with open(CHATS_CAHCE, 'wb') as fp:
        pickle.dump(chats_send, fp)


@dp.poll_answer_handler()
async def handle_poll_answer(answer: types.PollAnswer):
    global poll_active
    if poll_active:
        poll_active.change_answer(
            answer.poll_id, answer.user.id, answer.option_ids)
        with open(POLL_CHACHE, 'wb') as fp:
            pickle.dump(poll_active, fp)


@dp.message_handler(commands=["switch"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
    chats_send[message.chat.id] = not chats_send[message.chat.id]
    with open(CHATS_CAHCE, 'wb') as fp:
        pickle.dump(chats_send, fp)
    if (chats_send[message.chat.id]):
        await message.answer("Baм буду приходить активные опросы")
    else:
        await message.answer("Опросы будут игнорироваться")


@dp.message_handler(commands=["poll"])
async def cmd_start(message: types.Message):
    check(message.chat.id)
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

                url = "http://46.17.97.44:5001/stih/?name=%D1%81%D0%BE%D1%81%D0%B8&temp=1.0&length=100"
                async with session.get(url) as resp:
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
    if message.chat.type == types.ChatType.PRIVATE:
        global poll_active
        ans = "Опрос не найден"
        if poll_active:
            ans = await poll_active.finish(bot, message.chat.id)
            poll_active = None
            os.remove(POLL_CHACHE)
        await message.answer(ans)

remove_keyboard = types.ReplyKeyboardRemove()
@dp.message_handler(lambda message: message.text == "Отмена")
async def action_cancel(message: types.Message):
    check(message.chat.id)
    global poll_active
    if poll_active and not poll_active.send_out:
        poll_active = None
    await message.answer("Введите /poll, чтобы начать заново", reply_markup=remove_keyboard)


@dp.message_handler(lambda message: message.text == "Ок")
async def action_cancel(message: types.Message):
    check(message.chat.id)
    global poll_active
    ans = "Опрос не найден"
    if poll_active:
        ans = await poll_active.send(bot, chats_send)
        with open(POLL_CHACHE, 'wb') as fp:
            pickle.dump(poll_active, fp)
    await message.answer(ans, reply_markup=remove_keyboard)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
