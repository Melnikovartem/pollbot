#!venv/bin/python
import logging
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import deep_linking, exceptions

import urllib.request
import json

bot = Bot(token="248190991:AAFYN8IC-4-Zb6nXzMeBkPvM5YCxst094mw")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

poll_active = None


class Poll:
    def __init__(self, innit_id):
        # Используем подсказки типов, чтобы было проще ориентироваться.
        self.innit_id = innit_id
        self.chat_ids = [innit_id]
        self.polls_ids = {}
        self.send_out = False
        self.question = "Какая версия лучше?"
        self.refs = []
        self.answers = {}
        self.texts = {}

    async def send(self):
        if self.send_out:
            return "Эта версия уже была отправлена"

        for chat_id in self.chat_ids:
            await self.send_options(chat_id)

        options = map(lambda x: self.texts[x], self.refs)
        for chat_id in self.chat_ids:
            msg = await bot.send_poll(chat_id=chat_id, question=self.question,
                                      is_anonymous=False, options=self.refs)
            self.polls_ids[chat_id] = msg.message_id
        self.send_out = True
        return "Отправлено"

    def add_option(self, text):
        ref = "v" + str(len(self.refs) + 1)
        self.refs.append(ref)
        self.texts[ref] = text

    async def send_options(self, chat_id):
        for ref in self.refs:
            await bot.send_message(chat_id=chat_id, text=f"***{ref}***\n" + self.texts[ref], parse_mode="Markdown")

    async def finish(self, close_id):
        if not self.send_out:
            return "Опрос не был отправлен"
        for chat_id in self.polls_ids:
            await bot.stop_poll(chat_id, self.polls_ids[chat_id])
        await self.send_results(close_id)
        if close_id != self.innit_id:
            await self.send_results(self.innit_id)
        return "Опросы остановлены"

    async def send_results(self, chat_id):
        return

    async def change_answer(self, chat_id, user_id, ans_ids):
        if not user_id in self.answers:
            self.answers[user_id] = {}
        self.answers[user_id][chat_id] = ans_ids


@dp.poll_answer_handler()
async def handle_poll_answer(quiz_answer: types.PollAnswer):
    """
    Это хендлер на новые ответы в опросах (Poll) и викторинах (Quiz)
    Реагирует на изменение голоса. В случае отзыва голоса тоже срабатывает!
    Чтобы не было путаницы:
    * quiz_answer - ответ на активную викторину
    * saved_quiz - викторина, находящаяся в нашем "хранилище" в памяти
    :param quiz_answer: объект PollAnswer с информацией о голосующем
    """
    global poll_active
    if poll_active:
        await bot.stop_poll(saved_quiz.chat_id, saved_quiz.message_id)


@dp.poll_handler(lambda active_quiz: active_quiz.is_closed is True)
async def just_poll_answer(active_quiz: types.Poll):
    """
    Реагирует на закрытие опроса/викторины. Если убрать проверку на poll.is_closed == True,
    то этот хэндлер будет срабатывать при каждом взаимодействии с опросом/викториной, наравне
    с poll_answer_handler
    Чтобы не было путаницы:
    * active_quiz - викторина, в которой кто-то выбрал ответ
    * saved_quiz - викторина, находящаяся в нашем "хранилище" в памяти
    Этот хэндлер частично повторяет тот, что выше, в части, касающейся поиска нужного опроса в нашем "хранилище".
    :param active_quiz: объект Poll
    """
    quiz_owner = polls_owners.get(active_quiz.id)
    if not quiz_owner:
        logging.error(
            f"Не могу найти автора викторины с active_quiz.id = {active_quiz.id}")
        return
    for num, saved_quiz in enumerate(polls_database[quiz_owner]):
        if saved_quiz.quiz_id == active_quiz.id:
            # Удаляем викторину из обоих наших "хранилищ"
            del polls_owners[active_quiz.id]
            del polls_database[quiz_owner][num]


@dp.message_handler(commands=["poll"])
async def cmd_start(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:

        poll = Poll(message.chat.id)
        amount = 2
        waiting = await message.answer(text="generating 0%")
        for i in range(amount):
            async with aiohttp.ClientSession() as session:
                poll.add_option("somewjafjkljsal jfjasojfiasjfiojasfoi")
                continue

                url = "http://46.17.97.44:5001/stih/?name=%D1%81%D0%BE%D1%81%D0%B8&temp=1.0&length=100"
                async with session.get(url) as resp:
                    data = await resp.json()
                    poll.add_option(data["text"])
                    await waiting.edit_text(
                        text=f"generating {round((i + 1)/amount * 100)}%")

        try:
            await poll.send_options(message.chat.id)
            await waiting.delete()
        except exceptions.CantParseEntities as e:
            await waiting.edit_text(
                text=f"bad entity")
            return
        global poll_active
        poll_active = poll

        keyboard_conformation = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard_conformation.add(types.KeyboardButton(text="Ок"))
        keyboard_conformation.add(types.KeyboardButton(text="Отмена"))

        suffix = ""
        if len(poll_active.chat_ids) > 5:
            suffix = "ов"
        elif len(poll_active.chat_ids) > 2:
            suffix = "а"
        await message.answer(f"Отправляем в {len(poll_active.chat_ids)} чат{suffix}?", reply_markup=keyboard_conformation)


remove_keyboard = types.ReplyKeyboardRemove()
@dp.message_handler(commands=["finish"])
async def cmd_start(message: types.Message):
    if message.chat.type == types.ChatType.PRIVATE:
        global poll_active
        ans = "Опрос не найден"
        if poll_active:
            ans = await poll_active.finish(message.chat.id)
        await message.answer(ans, reply_markup=remove_keyboard)


@dp.message_handler(lambda message: message.text == "Отмена")
async def action_cancel(message: types.Message):
    remove_keyboard = types.ReplyKeyboardRemove()
    global poll_active
    if poll_active and not poll_active.send_out:
        poll_active = None
    await message.answer("Введите /poll, чтобы начать заново", reply_markup=remove_keyboard)


@dp.message_handler(lambda message: message.text == "Ок")
async def action_cancel(message: types.Message):
    remove_keyboard = types.ReplyKeyboardRemove()
    global poll_active
    ans = "Опрос не найден"
    if poll_active:
        ans = await poll_active.send()
    await message.answer(ans, reply_markup=remove_keyboard)


@dp.inline_handler()  # Обработчик любых инлайн-запросов
async def inline_query(query: types.InlineQuery):
    results = []
    user_quizzes = polls_database.get(str(query.from_user.id))
    if user_quizzes:
        for quiz in user_quizzes:
            keyboard = types.InlineKeyboardMarkup()
            start_quiz_button = types.InlineKeyboardButton(
                text="Отправить в группу",
                url=await deep_linking.get_startgroup_link(quiz.quiz_id)
            )
            keyboard.add(start_quiz_button)
            results.append(types.InlineQueryResultArticle(
                id=quiz.quiz_id,
                title=quiz.question,
                input_message_content=types.InputTextMessageContent(
                    message_text="Нажмите кнопку ниже, чтобы отправить викторину в группу."),
                reply_markup=keyboard
            ))
    await query.answer(switch_pm_text="Создать викторину", switch_pm_parameter="_",
                       results=results, cache_time=120, is_personal=True)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
