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
from .quizes import NumeroQuiz, DateQuiz, TimeQuiz


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

MESSAGE_DATE_EXAMPLE = """
    Напишите дату согласно примерам:
    Вопрос: <b>Понедельник, 01.01</b>
    Ответ: <b>lunes, primero de enero</b>
    Вопрос: <b>Вторник, 11.02</b>
    Ответ: <b>martes, once de febrero</b>
    Не забудьте ударение где нужно!
    """

MESSAGE_DATE_QUESTION = """
    Напишите дату: <b>{0}</b>
    """

MESSAGE_TIME_QUESTION = """
    Выбирите правильное время:
    <b>{0}</b>
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

MESSAGE_HELP = """
    <b>Испанские числительные</b>
    Бот позволяет вам тренировать испанские числительные.
    Выполняя задания, следуйте указаниям бота.
    
    <b>Доступные команды:</b>
    /help - Справка
    /numeros - Тренировка чисел
    /dates - Тренировка дат
    /times - Тренировка времени
    /stop - Остановить тест
    /stats - Ваша статистика
    /clear - Сбросить прогресс
    
    Вопросы и предложения по улучшению бота можно отправлять в Сообщество Estudiamos или Вашему куратору.
    """

class TgBot:
    """
    Quizes:
    0 - не в тесте
    1 - в тесте Numero
    2 - в тесте Date
    3 - в тесте Time
    """
    def __init__(self, token: str, host: str, port: int, user: str, password: str, database: str):
        self._storage = Storage(host, port, user, password, database)
        self._bot = Bot(token=token, default=DefaultBotProperties())
        self._dp = Dispatcher(bot=self._bot)
        self._numeros = NumeroQuiz(self._storage)
        self._dates =DateQuiz(self._storage)
        self._times = TimeQuiz(self._storage)
        self._in_quiz = dict()

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
        # user commands
        router.message.register(self.handler_numeros_command, Command(commands=['numeros']))
        router.message.register(self.handler_dates_command, Command(commands=['dates']))
        router.message.register(self.handler_times_command, Command(commands=['times']))
        router.message.register(self.handler_help_command, Command(commands=['help']))
        router.message.register(self.handler_stats_command, Command(commands=['stats']))
        router.message.register(self.handler_clear_command, Command(commands=['clear']))
        router.message.register(self.handler_stop_command, Command(commands=['stop']))
        # all messages
        router.message.register(self.handler_all_messages)
        return router

    async def start_handler(self, message: Message, command: CommandObject):
        if not self._check_chat_is_private(message):
            return
        await self._numeros.register_user(message.from_user.id)
        await self._send_help(message)

    async def handler_help_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        await self._send_help(message)

    async def handler_stats_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        quiz_mode = self._in_quiz.get(message.from_user.id, 0)
        if quiz_mode == 1:
            stats = await self._numeros.get_quiz_stats(message.from_user.id)
            await self._send_current_stats(message, stats['level'], stats['correct'], stats['wrong'], stats['percent'])
        elif quiz_mode == 2:
            stats = await self._dates.get_quiz_stats(message.from_user.id)
            await self._send_current_stats(message, stats['level'], stats['correct'], stats['wrong'], stats['percent'])
        elif quiz_mode == 3:
            stats = await self._times.get_quiz_stats(message.from_user.id)
            await self._send_current_stats(message, stats['level'], stats['correct'], stats['wrong'], stats['percent'])
        else:
            stats = await self._numeros.get_user_stats(message.from_user.id)
            await self._send_stats(message, stats['level'], stats['correct'], stats['wrong'], stats['percent'])

    async def handler_clear_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        user_mode = self._in_quiz.get(message.from_user.id, 0)
        if user_mode != 0:
            await message.answer("Чтобы очистить статистику, сначала завершите тест.")
            return
        await self._numeros.clear_user_stats(message.from_user.id)
        await message.answer("Статистика очищена.", reply_markup=ReplyKeyboardRemove())

    async def handler_stop_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        user_mode = self._in_quiz.get(message.from_user.id, 0)
        if user_mode == 0:
            return
        elif user_mode == 1:
            await self._numeros.stop_quiz(message.from_user.id)
        elif user_mode == 2:
            await self._dates.stop_quiz(message.from_user.id)
        elif user_mode == 3:
            await self._times.stop_quiz(message.from_user.id)
        self._in_quiz[message.from_user.id] = 0
        await message.answer("Тест остановлен.", reply_markup=ReplyKeyboardRemove())

    async def handler_numeros_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        user_mode = self._in_quiz.get(message.from_user.id, 0)
        if user_mode != 0:
            await message.answer("Сначала завершите текущий тест.")
            return
        self._in_quiz[message.from_user.id] = 1
        quiz = await self._numeros.start_quiz(message.from_user.id)
        await self._numeros_send_first_question(message, quiz['mode'], quiz['question'], quiz['level'])

    async def handler_dates_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        user_mode = self._in_quiz.get(message.from_user.id, 0)
        if user_mode != 0:
            await message.answer("Сначала завершите текущий тест.")
            return
        self._in_quiz[message.from_user.id] = 2
        quiz = await self._dates.start_quiz(message.from_user.id)
        await self._dates_send_first_question(message, quiz['question'])

    async def handler_times_command(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        user_mode = self._in_quiz.get(message.from_user.id, 0)
        if user_mode != 0:
            await message.answer("Сначала завершите текущий тест.")
            return
        self._in_quiz[message.from_user.id] = 3
        quiz = await self._times.start_quiz(message.from_user.id)
        await self._times_send_first_question(message, quiz['question'])

    async def handler_all_messages(self, message: Message):
        if not self._check_chat_is_private(message):
            return
        quiz_mode = self._in_quiz.get(message.from_user.id, 0)
        if quiz_mode == 0:
            return
        answer = message.text.strip().lower()
        if len(answer) == 0:
            return
        if quiz_mode == 1:
            quiz = await self._numeros.process_quiz(message.from_user.id, answer)
            if quiz['mode'] == 0:
                self._in_quiz[message.from_user.id] = 0
                stats = await self._numeros.get_quiz_stats(message.from_user.id)
                await self._send_finish_result(
                    message, quiz['result'], quiz['correct_answer'],
                    stats['level'], stats['correct'], stats['wrong'], stats['percent'])
            else:
                await self._numeros_send_question(
                    message, quiz['result'], quiz['correct_answer'], quiz['mode'], quiz['question'])
        elif quiz_mode == 2:
            quiz = await self._dates.process_quiz(message.from_user.id, answer)
            if quiz['mode'] == 0:
                self._in_quiz[message.from_user.id] = 0
                stats = await self._dates.get_quiz_stats(message.from_user.id)
                await self._send_finish_result(
                    message, quiz['result'], quiz['correct_answer'],
                    stats['level'], stats['correct'], stats['wrong'], stats['percent'])
            else:
                await self._dates_send_question(
                    message, quiz['result'], quiz['correct_answer'], quiz['mode'], quiz['question'])
        elif quiz_mode == 3:
            quiz = await self._times.process_quiz(message.from_user.id, answer)
            if quiz['mode'] == 0:
                self._in_quiz[message.from_user.id] = 0
                stats = await self._times.get_quiz_stats(message.from_user.id)
                await self._send_finish_result(
                    message, quiz['result'], quiz['correct_answer'],
                    stats['level'], stats['correct'], stats['wrong'], stats['percent'])
            else:
                await self._times_send_question(
                    message, quiz['result'], quiz['correct_answer'], quiz['question'])
        pass

    @staticmethod
    async def _set_main_menu(bot: Bot):
        main_menu_commands = [
            BotCommand(command='/numeros',
                       description='Тренировка чисел'),
            BotCommand(command='/dates',
                          description='Тренировка дат'),
            BotCommand(command='/times',
                            description='Тренировка времени'),
            BotCommand(command='/stop',
                       description='Остановить тест'),
            BotCommand(command='/stats',
                       description='Ваша статистика'),
            BotCommand(command='/clear',
                       description='Сбросить прогресс'),
            BotCommand(command='/help',
                       description='Справка по работе бота'),
        ]
        await bot.set_my_commands(main_menu_commands)

    @staticmethod
    async def _send_help(message: Message):
        await message.answer(MESSAGE_HELP, parse_mode=ParseMode.HTML)

    @staticmethod
    async def _numeros_send_first_question(message: Message, mode: int, question: str | tuple, level: int):
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
    async def _numeros_send_question(message: Message, result: bool, answer: str, mode: int, question: str | tuple):
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
    async def _dates_send_first_question(message: Message, question: str):
        await message.answer(MESSAGE_DATE_EXAMPLE, parse_mode=ParseMode.HTML)
        await message.answer(MESSAGE_DATE_QUESTION.format(question), parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())

    @staticmethod
    async def _dates_send_question(message: Message, result: bool, answer: str, mode: int, question: str):
        if result:
            msg = MESSAGE_CORRECT
        else:
            msg = MESSAGE_INCORRECT.format(answer)
        await message.answer(msg + MESSAGE_DATE_QUESTION.format(question), parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())

    @staticmethod
    async def _times_send_first_question(message: Message, question: tuple):
        variants = question[1]
        random.shuffle(variants)
        kb = [
            [
                KeyboardButton(text=variants[0]),
                KeyboardButton(text=variants[1]),
                KeyboardButton(text=variants[2]),
            ],
            [
                KeyboardButton(text=variants[3]),
                KeyboardButton(text=variants[4]),
                KeyboardButton(text=variants[5]),
            ]
        ]
        keyword = ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
        )
        await message.answer(MESSAGE_TIME_QUESTION.format(question[0]), parse_mode=ParseMode.HTML, reply_markup=keyword)

    @staticmethod
    async def _times_send_question(message: Message, result: bool, answer: str, question: tuple):
        if result:
            msg = MESSAGE_CORRECT
        else:
            msg = MESSAGE_INCORRECT.format(answer)
        variants = question[1]
        random.shuffle(variants)
        kb = [
            [
                KeyboardButton(text=variants[0]),
                KeyboardButton(text=variants[1]),
                KeyboardButton(text=variants[2]),
            ],
            [
                KeyboardButton(text=variants[3]),
                KeyboardButton(text=variants[4]),
                KeyboardButton(text=variants[5]),
            ]
        ]
        keyword = ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
        )
        await message.answer(msg + MESSAGE_TIME_QUESTION.format(question[0]), parse_mode=ParseMode.HTML, reply_markup=keyword)

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
