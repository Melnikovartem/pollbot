from math import floor


class Poll:
    def __init__(self, innit_id):
        # Используем подсказки типов, чтобы было проще ориентироваться.
        self.innit_id = innit_id
        self.polls_ids = {}
        self.send_out = False
        self.question = "Какая версия лучше?"
        self.refs = []
        self.answer_ids = {}
        self.texts = {}

    async def send(self, bot, chats_send):
        if self.send_out:
            return "Эта версия уже была отправлена"

        for chat_id in chats_send:
            if not chats_send[chat_id]:
                continue
            await self.send_options(bot, chat_id)

        options = map(lambda x: self.texts[x], self.refs)
        for chat_id in chats_send:
            if not chats_send[chat_id]:
                continue
            msg = await bot.send_poll(chat_id=chat_id, question=self.question,
                                      is_anonymous=False, options=self.refs)
            self.polls_ids[chat_id] = msg.message_id
            self.answer_ids[msg.poll.id] = {}
        self.send_out = True
        return "Отправлено"

    def add_option(self, text):
        ref = "v" + str(len(self.refs) + 1)
        self.refs.append(ref)
        self.texts[ref] = text

    async def send_options(self, bot, chat_id):
        for ref in self.refs:
            await bot.send_message(chat_id=chat_id, text=f"***{ref}***\n" + self.texts[ref], parse_mode="Markdown")

    async def finish(self, bot, close_id):
        if not self.send_out:
            return "Опрос не был отправлен"
        for chat_id in self.polls_ids:
            await bot.stop_poll(chat_id, self.polls_ids[chat_id])

        await self.send_results(bot, close_id)
        if close_id != self.innit_id:
            await self.send_results(bot, self.innit_id)
        return "Опросы остановлены"

    async def send_results(self, bot, chat_id):
        results = {}
        for ref in self.refs:
            results[ref] = 0
        sum = 0
        for poll_id in self.answer_ids:
            for userd_id in self.answer_ids[poll_id]:
                for id in self.answer_ids[poll_id][userd_id]:
                    results[self.refs[id]] += 1
                    sum += 1

        stats = ""
        for ref in self.refs:
            bar = ""
            if sum > 0:
                bar = "=" * floor(25 * results[ref] / sum)
            stats += f"***{ref}*** : {results[ref]}\n{bar}\n\n"
        await bot.send_message(chat_id=chat_id, text=stats, parse_mode="Markdown")

    def change_answer(self, poll_id, user_id, ans_ids):
        if not poll_id in self.answer_ids:
            return  # add to logger ?
        self.answer_ids[poll_id][user_id] = ans_ids
