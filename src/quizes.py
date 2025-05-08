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
        answer = answer.lower().strip().replace(' ', '').replace(',', '').replace('el', '')
        if answer == quiz_answer.replace(' ', '').replace(',', ''):
            return True, quiz_answer
        return False, quiz_answer

    async def _finish_quiz(self, user_id: int):
        # date quiz finish, not update stats or user level
        # do nothing
        pass

# Quiz for time in Spanish
class TimeQuiz(Quiz):

    ALL_MINUTES = ('00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55')
    WITH_MENOS = ('35', '40', '45', '50', '55')

    __TIMES_PUNTO = {
        '00': 'Es medianoche',
        '12': 'Es mediodía',
    }

    __MINUTES = {
        '00': 'en punto',
        '05': 'y cinco',
        '10': 'y diez',
        '15': 'y cuarto',
        '20': 'y veinte',
        '25': 'y veinticinco',
        '30': 'y media',
        '35': 'menos veinticinco',
        '40': 'menos veinte',
        '45': 'menos cuarto',
        '50': 'menos diez',
        '55': 'menos cinco'
    }

    __TIMES_OF_DAY = {
        '00': 'de la madrugada',
        '01': 'de la madrugada',
        '02': 'de la madrugada',
        '03': 'de la madrugada',
        '04': 'de la mañana',
        '05': 'de la mañana',
        '06': 'de la mañana',
        '07': 'de la mañana',
        '08': 'de la mañana',
        '09': 'de la mañana',
        '10': 'de la mañana',
        '11': 'de la mañana',
        '12': 'de la tarde',
        '13': 'de la tarde',
        '14': 'de la tarde',
        '15': 'de la tarde',
        '16': 'de la tarde',
        '17': 'de la tarde',
        '18': 'de la tarde',
        '19': 'de la noche',
        '20': 'de la noche',
        '21': 'de la noche',
        '22': 'de la noche',
        '23': 'de la noche'
    }

    __TIMES_OF_DAY_M = {
        '00': 'de la noche',
        '01': 'de la madrugada',
        '02': 'de la madrugada',
        '03': 'de la madrugada',
        '04': 'de la mañana',
        '05': 'de la mañana',
        '06': 'de la mañana',
        '07': 'de la mañana',
        '08': 'de la mañana',
        '09': 'de la mañana',
        '10': 'de la mañana',
        '11': 'de la mañana',
        '12': 'de la mañana',
        '13': 'de la tarde',
        '14': 'de la tarde',
        '15': 'de la tarde',
        '16': 'de la tarde',
        '17': 'de la tarde',
        '18': 'de la tarde',
        '19': 'de la tarde',
        '20': 'de la noche',
        '21': 'de la noche',
        '22': 'de la noche',
        '23': 'de la noche'
    }

    __HOURS = {
        '00': 'Son las doce',
        '01': 'Es la una',
        '02': 'Son las dos',
        '03': 'Son las tres',
        '04': 'Son las cuatro',
        '05': 'Son las cinco',
        '06': 'Son las seis',
        '07': 'Son las siete',
        '08': 'Son las ocho',
        '09': 'Son las nueve',
        '10': 'Son las diez',
        '11': 'Son las once',
        '12': 'Son las doce',
        '13': 'Es la una',
        '14': 'Son las dos',
        '15': 'Son las tres',
        '16': 'Son las cuatro',
        '17': 'Son las cinco',
        '18': 'Son las seis',
        '19': 'Son las siete',
        '20': 'Son las ocho',
        '21': 'Son las nueve',
        '22': 'Son las diez',
        '23': 'Son las once'
    }

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
        if self._current_quiz[user_id] > 10:  # max 10 questions for time quiz
            # finish quiz
            await self._finish_quiz(user_id)
            return {'mode': 0, 'result': res, 'correct_answer': right_answer, 'question': None}
        # get new question
        question = self._create_question(user_id, 1)
        return {'mode': 1, 'result': res, 'correct_answer': right_answer, 'question': question}

    def _generate_times(self):
        hour_a = random.randint(0, 11)
        hour_b = hour_a + 12
        minutes = random.sample(self.ALL_MINUTES, 3)
        return [
            (hour_a, minutes[0]), (hour_a, minutes[1]), (hour_a, minutes[2]),
            (hour_b, minutes[0]), (hour_b, minutes[1]), (hour_b, minutes[2])]

    def _create_question(self, user_id: int, mode: int = 1) -> tuple:
        times = self._generate_times()
        # choose random correct answer
        correct_answer = random.choice(times)
        # convert times to strings
        answers = [str(x[0]).zfill(2) + ':' + x[1] for x in times]
        # convert correct answer to string
        correct_answer_str = str(correct_answer[0]).zfill(2) + ':' + correct_answer[1]
        # save correct answer
        self._current_answer[user_id] = correct_answer_str
        # create question string
        # check if correct answer is 00:00 or 12:00
        if correct_answer[0] == 0 and correct_answer[1] == '00':
            question = self.__TIMES_PUNTO['00']
        elif correct_answer[0] == 12 and correct_answer[1] == '00':
            question = self.__TIMES_PUNTO['12']
        else:
            minutes = correct_answer[1]
            # check if minute is in WITH_MENOS
            if minutes in self.WITH_MENOS:
                # add one our
                hour = correct_answer[0] + 1 if correct_answer[0] < 23 else 0
                # convert hour to string with leading zero
                hour = str(hour).zfill(2)
                # create question string
                question = f"{self.__HOURS[hour]} {self.__MINUTES[minutes]} {self.__TIMES_OF_DAY_M[hour]}"
            else:
                # convert hour to string with leading zero
                hour = str(correct_answer[0]).zfill(2)
                # create question string
                question = f"{self.__HOURS[hour]} {self.__MINUTES[minutes]} {self.__TIMES_OF_DAY[hour]}"
        return question, answers

    def _check_answer(self, user_id: int, answer: str) -> tuple[bool, str]:
        quiz_answer = self._current_answer.get(user_id, "")
        answer = answer.lower().strip()
        if answer == quiz_answer:
            return True, quiz_answer
        return False, quiz_answer

    async def _finish_quiz(self, user_id: int):
        # time quiz finish, not update stats or user level
        # do nothing
        pass

# Quiz for numbers in Spanish
class NumeroQuiz(Quiz):

    def __init__(self, storage):
        super().__init__(storage)
        from src.gens import get_quiz_numbers, get_quiz_mode
        self._new_quiz_number = get_quiz_numbers
        self._get_quiz_mode = get_quiz_mode

    async def start_quiz(self, user_id: int) -> dict:
        user_level = await self.load_user_level(user_id)
        self.create_quiz_stats(user_id)
        self._current_quiz[user_id] = 1
        mode, *question = self._create_question(user_id)
        if question is None or mode == 0:
            return {'mode': 0, 'result': 0, 'correct_answer': 0, 'question': None}
        return {'mode': mode, 'question': question, 'level': user_level}

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
        # get new question
        mode, *question = self._create_question(user_id)
        if question is None or mode == 0:
            # finish quiz
            await self._finish_quiz(user_id)
            return {'mode': 0, 'result': res, 'correct_answer': right_answer, 'question': None}
        return {'mode': mode, 'result': res, 'correct_answer': right_answer, 'question': question}

    def _create_question(self, user_id: int) -> tuple:
        """
        Modes:
        1 -- words to number, choose mode
        2 -- number to words, choose mode
        3 -- words to number, write mode
        4 -- number to words, write mode
        5 -- ordinal words to ru number, choose mode
        6 -- ordinal ru number to words, choose mode
        7 -- ordinal words to ru number, write mode
        8 -- ordinal ru number to words, write mode
        """
        user_level = self._user_level.get(user_id, 0)
        current_quiz = self._current_quiz.get(user_id, 0)
        mode = self._get_quiz_mode(self._user_level[user_id], current_quiz)
        qn = self._new_quiz_number(user_level, mode)
        if qn is None:
            return 0, None
        if mode == 1:
            if not isinstance(qn, list):
                return 0, None
            x = random.choice(qn)
            self._current_answer[user_id] = x
            question = num2words.num2words(x, lang='es')
            return 1, question, [str(y) for y in qn]
        elif mode == 2:
            if not isinstance(qn, list):
                return 0, None
            x = random.choice(qn)
            self._current_answer[user_id] = x
            question = str(x)
            return 2, question, [num2words.num2words(y, lang='es') for y in qn]
        elif mode == 3:
            self._current_answer[user_id] = qn
            return 3, num2words.num2words(qn, lang='es')
        elif mode == 4:
            self._current_answer[user_id] = qn
            return 4, str(qn)
        elif mode == 5:
            if not isinstance(qn, list):
                return 0, None
            x = random.choice(qn)
            self._current_answer[user_id] = x
            question = num2words.num2words(x, lang='es', to='ordinal')
            return 5, question, [num2words.num2words(y, lang='ru', to='ordinal') for y in qn]
        elif mode == 6:
            if not isinstance(qn, list):
                return 0, None
            x = random.choice(qn)
            self._current_answer[user_id] = x
            question = num2words.num2words(x, lang='ru', to='ordinal')
            return 6, question, [num2words.num2words(y, lang='es', to='ordinal') for y in qn]
        elif mode == 7:
            self._current_answer[user_id] = qn
            return 7, num2words.num2words(qn, lang='es', to='ordinal')
        elif mode == 8:
            self._current_answer[user_id] = qn
            return 8, num2words.num2words(qn, lang='ru', to='ordinal')
        elif mode == 9:
            self._current_answer[user_id] = qn
            return 9, qn  # change this when audio is implemented
        return 0, None

    def _check_answer(self, user_id: int, answer: str) -> tuple[bool, str]:
        question_number = self._current_quiz.get(user_id, 0)
        user_level = self._user_level.get(user_id, 0)
        current_mode = self._get_quiz_mode(user_level, question_number)
        if current_mode == 1 or current_mode == 3 or current_mode == 7 or current_mode == 9:
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
        elif current_mode == 5:
            current_answer = num2words.num2words(self._current_answer.get(user_id, 0), lang='ru', to='ordinal')
            if answer == current_answer:
                return True, current_answer
            return False, current_answer
        elif current_mode == 6 or current_mode == 8:
            current_answer = num2words.num2words(self._current_answer.get(user_id, 0), lang='es', to='ordinal')
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
