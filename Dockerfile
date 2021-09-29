FROM python:3.7
ADD src /
ADD tg_key /
RUN pip install aiogram aiohttp
CMD [ "python", "bot.py" ]
