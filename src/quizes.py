# -*- coding: UTF-8 -*-
"""
    Unit Test Lab
    2025-04-07
    Description:
    
"""

import abc
import random

import num2words

class Quiz(abc.ABC):

    def __init__(self, storage):
        self.storage = storage
        self._current_answer = dict()
        self._current_quiz = dict()
        self._user_stats = dict()
        self._user_level = dict()

    async def register_user(self, user_id: int):
        if not await self.storage.is_user_exists(user_id):
            await self.storage.insert_user(user_id)

    async def load_user_level(self, user_id: int):
        user_level = await self.storage.get_user_level(user_id)
        if user_level is None:
            await self.storage.insert_user(user_id)
            self._user_level[user_id] = 0
        else:
            self._user_level[user_id] = user_level
        return self._user_level[user_id]

    async def clear_user_stats(self, user_id: int):
        await self.storage.clear_user_stats(user_id)

    def create_quiz_stats(self, user_id: int):
        self._user_stats[user_id] = {
            'correct': 0,
            'wrong': 0,
        }

    def update_quiz_stats(self, user_id: int, correct: bool):
        if user_id not in self._user_stats.keys():
            self._user_stats[user_id] = {
                'correct': 0,
                'wrong': 0,
            }
        if correct:
            self._user_stats[user_id]['correct'] += 1
        else:
            self._user_stats[user_id]['wrong'] += 1

    async def get_user_stats(self, user_id: int) -> dict:
        db_stats = await self.storage.get_user_stats(user_id)
        stats = {
            'level': 0,
            'correct': 0,
            'wrong': 0,
            'percent': 0,
        }
        if db_stats is not None:
            stats['level'] = db_stats['level']
            stats['correct'] = db_stats['correct']
            stats['wrong'] = db_stats['wrong']
        stats['percent'] = (stats['correct'] / (stats['correct'] + stats['wrong'])) * 100 if (stats['correct'] + stats['wrong']) > 0 else 0
        return stats

    async def get_quiz_stats(self, user_id: int) -> dict:
        cached_stats = self._user_stats.get(user_id, {'correct': 0, 'wrong': 0})
        stats = {'level': self._user_level.get(user_id, 0), 'correct': cached_stats['correct'], 'wrong': cached_stats['wrong'],'percent': 0}
        stats['percent'] = (stats['correct'] / (stats['correct'] + stats['wrong'])) * 100 if (stats['correct'] + stats['wrong']) > 0 else 0
        return stats

    @abc.abstractmethod
    async def start_quiz(self, user_id: int) -> dict:
        pass

    @abc.abstractmethod
    async def stop_quiz(self, user_id: int):
        pass

    @abc.abstractmethod
    async def process_quiz(self, user_id: int, answer: str) -> dict:
        pass

# Quiz for dates in Spanish
class DateQuiz(Quiz):
    __MONTHS = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ]

    __WEEK_DAYS = [
        'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'
    ]

    __WEEK_DAYS_RU = [
        'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'
    ]

    __MONTHS_LENGTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def __init__(self, storage):
        super().__init__(storage)

    async def start_quiz(self, user_id: int) -> dict:
        user_level = await self.load_user_level(user_id)
        self._current_quiz[user_id] = 1
        self.create_quiz_stats(user_id)
        return {'mode': 1, 'question': self._create_question(user_id, 1), 'level': user_level}

    async def stop_quiz(self, user_id: int):
        # do nothing
        pass

    async def process_quiz(self, user_id: int, answer: str) -> dict:
        # check answer
        res, right_answer = self._check_answer(user_id, answer)
        if res:
            self.update_quiz_stats(user_id, True)
        else:
            self.update_quiz_stats(user_id, False)
        # increase quiz number
        self._current_quiz[user_id] += 1
        if self._current_quiz[user_id] > 5: # max 5 questions for date quiz
            # finish quiz
            await self._finish_quiz(user_id)
            return {'mode': 0, 'result': res, 'correct_answer': right_answer, 'question': None}
        # get new question
        question = self._create_question(user_id, 1)
        return {'mode': 1, 'result': res, 'correct_answer': right_answer, 'question': question}

    def _new_date(self):
        week_day = random.randint(0, 6)
        month = random.randint(0, 11)
        day = random.randint(1, self.__MONTHS_LENGTH[month])
        return week_day, day, month

    def _create_question(self, user_id: int, mode: int = 1) -> str | tuple | None:
        week_day, day, month = self._new_date()
        string_day = 'primero' if day == 1 else num2words.num2words(day, lang='es')
        self._current_answer[user_id] = f"{self.__WEEK_DAYS[week_day]}, {string_day} de {self.__MONTHS[month]}"
        # add leading zero to day and month for quiz
        day = str(day).zfill(2)
        month = str(month + 1).zfill(2)
        quiz_date = f"{self.__WEEK_DAYS_RU[week_day]}, {day}.{month}"
        return quiz_date

    def _check_answer(self, user_id: int, answer: str) -> tuple[bool, str]:
        quiz_answer = self._current_answer.get(user_id, "")
        answer = answer.lower().strip().replace(' ', '').replace(',', '')
        if answer == quiz_answer.replace(' ', '').replace(',', ''):
            return True, quiz_answer
        return False, quiz_answer

    async def _finish_quiz(self, user_id: int):
        # date quiz finish, not update stats or user level
        # do nothing
        pass

# Quiz for numbers in Spanish
class NumeroQuiz(Quiz):

    def __init__(self, storage):
        super().__init__(storage)

    async def start_quiz(self, user_id: int) -> dict:
        user_level = await self.load_user_level(user_id)
        self._current_quiz[user_id] = 1
        self.create_quiz_stats(user_id)
        return {'mode': 1, 'question': self._create_question(user_id, 1), 'level': user_level}

    async def stop_quiz(self, user_id: int):
        # stop quiz, decrease level because interrupted
        await self.storage.decrease_user_level(user_id)

    async def process_quiz(self, user_id: int, answer: str) -> dict:
        # check answer
        res, right_answer = self._check_answer(user_id, answer)
        if res:
            self.update_quiz_stats(user_id, True)
        else:
            self.update_quiz_stats(user_id, False)
        # increase quiz number
        self._current_quiz[user_id] += 1
        # get new current mode
        mode = self._get_quiz_mode(self._user_level[user_id], self._current_quiz[user_id])
        if mode == 0:
            # finish quiz
            await self._finish_quiz(user_id)
            return {'mode': 0, 'result': res, 'correct_answer': right_answer, 'question': None}
        # get new question
        question = self._create_question(user_id, mode)
        return {'mode': mode, 'result': res, 'correct_answer': right_answer, 'question': question}

    @staticmethod
    def _get_quiz_mode(user_level: int = 0, quiz_number: int = 1):
        """
        Modes:
        0 -- finish
        1 -- words to number, choose mode
        2 -- number to words, choose mode
        3 -- words to number, write mode
        4 -- number to words, write mode
        """
        # for begginers
        if user_level <= 4:
            if quiz_number <= (user_level + 1):
                return 1
            elif quiz_number <= (user_level + 1) * 2:
                return 2
            elif quiz_number <= (user_level + 1) * 3:
                return 3
            elif quiz_number <= (user_level + 1) * 4:
                return 4
            return 0  # finish
        # for level 5, 6, 7
        elif user_level <= 7:
            if quiz_number <= 5:
                return 1
            elif quiz_number <= 10:
                return 2
            elif quiz_number <= 15:
                return 3
            elif quiz_number <= 20:
                return 4
            return 0  # finish
        # for level 8, 9, 10
        elif user_level <= 10:
            if quiz_number <= 10:
                return 3
            elif quiz_number <= 20:
                return 4
            return 0  # finish
        # for level 11 and above
        if quiz_number <= user_level:
            return 3
        elif quiz_number <= user_level * 2:
            return 4
        return 0  # finish

    @staticmethod
    def _new_quiz_number(user_level: int = 0):
        if user_level <= 1:
            return random.randint(1, 20)
        elif user_level <= 4:
            return random.randint(1, 100)
        elif user_level <= 7:
            return random.randint(1, 1000)
        return random.randint(1001, 9999)

    def _create_question(self, user_id: int, mode: int = 1) -> str | tuple | None:
        """
        Modes:
        1 -- words to number, choose mode
        2 -- number to words, choose mode
        3 -- words to number, write mode
        4 -- number to words, write mode
        """
        user_level = self._user_level.get(user_id, 0)
        number = self._new_quiz_number(user_level)
        self._current_answer[user_id] = number
        if mode == 1:
            question = num2words.num2words(number, lang='es')
            n1 = number
            n2 = number + 1
            if number == 1:
                n3 = number + 3
            else:
                n3 = number - 1
            n4 = number + random.randint(2, 5)
            if number > 100:
                n2 = number - random.randint(1, 3)
                n3 = number + random.randint(10, 20)
                n4 = number + random.randint(1, 10)
            return question, str(n1), str(n2), str(n3), str(n4)
        elif mode == 2:
            n1 = num2words.num2words(number, lang='es')
            n2 = num2words.num2words(number + 1, lang='es')
            if number == 1:
                n3 = num2words.num2words(number + 3, lang='es')
            else:
                n3 = num2words.num2words(number - 1, lang='es')
            n4 = num2words.num2words(number + 2, lang='es')
            if number > 100:
                n2 = num2words.num2words(number - random.randint(100, 200), lang='es')
                n3 = num2words.num2words(number + random.randint(10, 50), lang='es')
                n4 = num2words.num2words(number + random.randint(50, 150), lang='es')
            return number, n1, n2, n3, n4
        elif mode == 3:
            return num2words.num2words(number, lang='es')
        elif mode == 4:
            return str(number)
        return None

    def _check_answer(self, user_id: int, answer: str) -> tuple[bool, str]:
        question_number = self._current_quiz.get(user_id, 0)
        user_level = self._user_level.get(user_id, 0)
        current_mode = self._get_quiz_mode(user_level, question_number)
        if current_mode == 1 or current_mode == 3:
            current_answer = self._current_answer.get(user_id, 0)
            try:
                answer = int(answer)
                if answer == current_answer:
                    return True, str(current_answer)
            except ValueError:
                pass
            return False, str(current_answer)
        elif current_mode == 2 or current_mode == 4:
            current_answer = num2words.num2words(self._current_answer.get(user_id, 0), lang='es')
            if answer == current_answer:
                return True, current_answer
            return False, current_answer
        return False, ""

    async def _finish_quiz(self, user_id: int):
        correct = self._user_stats[user_id]['correct']
        wrong = self._user_stats[user_id]['wrong']
        if wrong == 0:
            await self.storage.increase_user_level(user_id)
            self._user_level[user_id] += 1
        elif wrong >= correct:
            await self.storage.decrease_user_level(user_id)
            self._user_level[user_id] -= 1 if self._user_level[user_id] > 0 else 0
        await self.storage.update_user_stats(user_id, correct, wrong)
