# -*- coding: UTF-8 -*-
"""
    Unit Test Lab
    2025-04-04
    Description:
    
"""

import asyncio
import random


from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatType
from aiogram.types import Message, BotCommand, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart, CommandObject

from .storage import Storage
from .quizes import Quizes


MESSAGE_LEVEL = """
    Ваш уровень: <i>{0}</i>
    """

MESSAGE_QUESTION_1 = """
    Выберите, какое число написано: <b>{0}</b>
    """

MESSAGE_QUESTION_2 = """
    Выберите правильное число: <b>{0}</b>
    """

MESSAGE_QUESTION_3 = """
    Напишите заданное число цифрами: <b>{0}</b>
    """

MESSAGE_QUESTION_4 = """
    Напишите заданное число прописью: <b>{0}</b>
    """

MESSAGE_CORRECT = """
    Правильно!
    """

MESSAGE_INCORRECT = """
    ❌ Правильный ответ: <i>{0}</i>
    """

MESSAGE_STATS = """
    <b>Ваша суммарная статистика</b>
    Текущий уровень: <i>{0}</i>
    Правильных ответов: <i>{1}</i>
    Неправильных ответов: <i>{2}</i>
    Процент правильных ответов: <i>{3:.2f}%</i>
    """

MESSAGE_STATS_CURRENT = """
    <b>Ваша последняя статистика</b>
    Новый уровень: <i>{0}</i>
    Правильных ответов: <i>{1}</i>
    Неправильных ответов: <i>{2}</i>
    Процент правильных ответов: <i>{3:.2f}%</i>
    """

class TgBot:

    __ADMIN_ID = 129507956

    def __init__(self, token: str, host: str, port: int, user: str, password: str, database: str):
        self._storage = Storage(host, port, user, password, database)
        self._bot = Bot(token=token, default=DefaultBotProperties())
        self._dp = Dispatcher(bot=self._bot)
        self._quiz = Quizes(self._storage)
        self._in_quiz = set()

    @staticmethod
    def _check_chat_is_private(message: Message):
        return (
                message.chat.type == ChatType.PRIVATE and message.chat.id == message.from_user.id
        )

    async def on_shutdown(self, dispatcher: Dispatcher, bot: Bot) -> None:
        await bot.delete_webhook()
        await bot.session.close()
        await self._storage.disconnect()

    async def on_startup(self, dispatcher: Dispatcher, bot: Bot) -> None:
        loop = asyncio.get_event_loop()
        # set main menu
        await self._set_main_menu(bot)
        pass

    async def run(self) -> None:
        # connect to the database
        await self._storage.connect()
        # register handlers
        self._dp.startup.register(self.on_startup)
        self._dp.shutdown.register(self.on_shutdown)
        # create router and register handlers
        router = self.register_router()
        self._dp.include_router(router)
        # start polling
        await self._bot.delete_webhook()
        await self._dp.start_polling(self._bot, allowed_updates=self._dp.resolve_used_update_types(), skip_updates=True)

    def register_router(self):
        router = Router()
        router.message.register(self.start_handler, CommandStart())
        router.message.register(self.handler_id, Command(commands=['id']))
        # user commands
        router.message.register(self.handler_go_command, Command(commands=['go']))
        router.message.register(self.handler_help_command, Command(commands=['help']))
        router.message.register(self.handler_stats_command, Command(commands=['stats']))
        router.message.register(self.handler_clear_command, Command(commands=['clear']))
        router.message.register(self.handler_stop_command, Command(commands=['stop']))
        # admin commands
        router.message.register(self.handler_users_command, Command(commands=['users']))
        # all messages
        router.message.register(self.handler_all_messages)
        return router

    async def start_handler(self, message: Message, command: CommandObject):
        if not self._check_chat_is_private(message):
            return
        await self._quiz.register_user(message.from_user.id)
        await self._send_help(message)

    async def handler_help_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        await self._send_help(message)

    async def handler_users_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        if message.from_user.id != self.__ADMIN_ID:
            await message.answer("У вас нет прав на выполнение этой команды.")
            return
        users_count = await self._storage.get_users_count()
        await message.answer(f"Количество пользователей: {users_count}")

    async def handler_go_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        if message.from_user.id in self._in_quiz:
            await message.answer("Вы уже находитесь в тесте.")
            return
        self._in_quiz.add(message.from_user.id)
        quiz = await self._quiz.start_quiz(message.from_user.id)
        await self._send_first_question(message, quiz['mode'], quiz['question'], quiz['level'])

    async def handler_stats_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        if message.from_user.id not in self._in_quiz:
            stats = await self._quiz.get_user_stats(message.from_user.id)
            await self._send_stats(message, stats['level'], stats['correct'], stats['wrong'], stats['percent'])
        else:
            stats = await self._quiz.get_current_user_stats(message.from_user.id)
            await self._send_current_stats(message, stats['level'], stats['correct'], stats['wrong'], stats['percent'])

    async def handler_clear_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        if message.from_user.id in self._in_quiz:
            await message.answer("Вы находитесь в тесте. Чтобы очистить статистику, сначала завершите тест.")
            return
        await self._quiz.clear_user_stats(message.from_user.id)
        await message.answer("Статистика очищена. Чтобы начать заново, введите /go", reply_markup=ReplyKeyboardRemove())

    async def handler_stop_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        if message.from_user.id not in self._in_quiz:
            return
        await self._quiz.stop_quiz(message.from_user.id)
        self._in_quiz.remove(message.from_user.id)
        await message.answer("Тест остановлен. Чтобы начать заново, введите /go", reply_markup=ReplyKeyboardRemove())

    async def handler_all_messages(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        if message.from_user.id not in self._in_quiz:
            return
        answer = message.text.strip().lower()
        if len(answer) == 0:
            return
        quiz = await self._quiz.process_answer(message.from_user.id, answer)
        if quiz['mode'] == 0:
            self._in_quiz.remove(message.from_user.id)
            stats = await self._quiz.get_current_user_stats(message.from_user.id)
            await self._send_finish_result(message, quiz['result'], quiz['correct_answer'], stats['level'], stats['correct'], stats['wrong'], stats['percent'])
        else:
            await self._send_question(message, quiz['result'], quiz['correct_answer'], quiz['mode'], quiz['question'])

    async def handler_id(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        await message.answer(f"Ваш ID: {message.from_user.id}")

    @staticmethod
    async def _set_main_menu(bot: Bot):
        main_menu_commands = [
            BotCommand(command='/go',
                       description='Запуск теста'),
            BotCommand(command='/stats',
                       description='Ваша статистика'),
            BotCommand(command='/clear',
                       description='Сбросить прогресс'),
            BotCommand(command='/stop',
                       description='Остановить тест'),
            BotCommand(command='/help',
                       description='Справка по работе бота'),
        ]
        await bot.set_my_commands(main_menu_commands)

    @staticmethod
    async def _send_help(message: Message):
        msg_help = """
        <b>Испанские числительные</b>
        Бот позволяет вам изучать испанские числительные.
        Выполняя задания, следуйте указаниям бота.
        <b>Доступные команды:</b>
        /help - Справка
        /go - Запуск теста
        /stats - Ваша статистика
        /clear - Сбросить прогресс
        /stop - Остановить тест
        """
        await message.answer(msg_help, parse_mode=ParseMode.HTML)

    @staticmethod
    async def _send_first_question(message: Message, mode: int, question: str | tuple, level: int):
        msg = MESSAGE_LEVEL.format(level)
        if mode == 1:
            variants = list(question[1:])
            random.shuffle(variants)
            kb = [
                [
                    KeyboardButton(text=variants[0]),
                    KeyboardButton(text=variants[1]),
                ],
                [
                    KeyboardButton(text=variants[2]),
                    KeyboardButton(text=variants[3]),
                ]
            ]
            keyboard = ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
            )
            await message.answer(msg + MESSAGE_QUESTION_1.format(question[0]), parse_mode=ParseMode.HTML, reply_markup=keyboard)
        elif mode == 2:
            variants = list(question[1:])
            random.shuffle(variants)
            kb = [
                [
                    KeyboardButton(text=variants[0])
                ],
                [
                    KeyboardButton(text=variants[1]),
                ],
                [
                    KeyboardButton(text=variants[2]),
                ],
                [
                    KeyboardButton(text=variants[3]),
                ]
            ]
            keyboard = ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
            )
            await message.answer(msg + MESSAGE_QUESTION_2.format(question[0]), parse_mode=ParseMode.HTML, reply_markup=keyboard)
        elif mode == 3:
            await message.answer(msg + MESSAGE_QUESTION_3.format(question), parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        elif mode == 4:
            await message.answer(msg + MESSAGE_QUESTION_4.format(question), parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        pass

    @staticmethod
    async def _send_question(message: Message, result: bool, answer: str, mode: int, question: str | tuple):
        if result:
            msg = MESSAGE_CORRECT
        else:
            msg = MESSAGE_INCORRECT.format(answer)
        if mode == 1:
            variants = list(question[1:])
            random.shuffle(variants)
            kb = [
                [
                    KeyboardButton(text=variants[0]),
                    KeyboardButton(text=variants[1]),
                ],
                [
                    KeyboardButton(text=variants[2]),
                    KeyboardButton(text=variants[3]),
                ]
            ]
            keyboard = ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
            )
            await message.answer(msg + MESSAGE_QUESTION_1.format(question[0]), parse_mode=ParseMode.HTML, reply_markup=keyboard)
        elif mode == 2:
            variants = list(question[1:])
            random.shuffle(variants)
            kb = [
                [
                    KeyboardButton(text=variants[0])
                ],
                [
                    KeyboardButton(text=variants[1]),
                ],
                [
                    KeyboardButton(text=variants[2]),
                ],
                [
                    KeyboardButton(text=variants[3]),
                ]
            ]
            keyboard = ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
            )
            await message.answer(msg + MESSAGE_QUESTION_2.format(question[0]), parse_mode=ParseMode.HTML, reply_markup=keyboard)
        elif mode == 3:
            await message.answer(msg + MESSAGE_QUESTION_3.format(question), parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        elif mode == 4:
            await message.answer(msg + MESSAGE_QUESTION_4.format(question), parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        pass

    @staticmethod
    async def _send_finish_result(message: Message, result: bool, answer: str, level, correct, wrong, percent):
        if result:
            msg = MESSAGE_CORRECT
        else:
            msg = MESSAGE_INCORRECT.format(answer)
        msg += MESSAGE_STATS_CURRENT.format(level, correct, wrong, percent)
        await message.answer(msg, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())

    @staticmethod
    async def _send_stats(message: Message, level, correct, wrong, percent):
        await message.answer(MESSAGE_STATS.format(level, correct, wrong, percent), parse_mode=ParseMode.HTML)

    @staticmethod
    async def _send_current_stats(message: Message, level, correct, wrong, percent):
        await message.answer(MESSAGE_STATS_CURRENT.format(level, correct, wrong, percent), parse_mode=ParseMode.HTML)
