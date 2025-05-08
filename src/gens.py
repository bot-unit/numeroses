# -*- coding: UTF-8 -*-
"""
    Unit Test Lab
    2025-05-08
    Description:
    
"""

import random

def get_quiz_mode(user_level: int, quiz_number: int):
    """
    Modes:
    0 -- finish
    1 -- words to number, choose 1 from 4
    2 -- number to words, choose 1 from 4
    3 -- words to number, write
    4 -- number to words, write
    5 -- ordinal words to number, choose 1 from 3
    6 -- ordinal number to words, choose 1 from 3
    7 -- ordinal words to number, write
    8 -- ordinal number to words, write
    9 -- audio to number, write
    """
    # for begginers
    if user_level == 0:
        if quiz_number <= 4:
            return 1
        elif quiz_number <= 8:
            return 2
        return 0  # finish
    elif user_level <= 2:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        return 0  # finish
    elif user_level <= 4:
        if quiz_number <= 10:
            return 1
        elif quiz_number <= 20:
            return 2
        return 0  # finish
    elif user_level <= 6:
        if quiz_number <= 6:
            return 1
        elif quiz_number <= 12:
            return 2
        elif quiz_number <= 18:
            return 3
        elif quiz_number <= 24:
            return 4
        elif quiz_number <= 25:
            return 5
        return 0  # finish
    elif user_level <= 8:
        if quiz_number <= 7:
            return 1
        elif quiz_number <= 14:
            return 2
        elif quiz_number <= 21:
            return 3
        elif quiz_number <= 28:
            return 4
        elif quiz_number <= 29:
            return 5
        elif quiz_number <= 30:
            return 6
        return 0  # finish
    elif user_level <= 10:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        elif quiz_number <= 24:
            return 3
        elif quiz_number <= 32:
            return 4
        elif quiz_number <= 34:
            return 5
        return 0  # finish
    elif user_level <= 12:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        elif quiz_number <= 24:
            return 3
        elif quiz_number <= 32:
            return 4
        elif quiz_number <= 33:
            return 5
        elif quiz_number <= 34:
            return 6
        return 0 # finish
    elif user_level <= 14:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        elif quiz_number <= 24:
            return 3
        elif quiz_number <= 32:
            return 4
        elif quiz_number <= 34:
            return 5
        return 0 # finish
    elif user_level <= 16:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        elif quiz_number <= 24:
            return 3
        elif quiz_number <= 32:
            return 4
        elif quiz_number <= 33:
            return 5
        elif quiz_number <= 34:
            return 6
        return 0 # finish
    elif user_level <= 18:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        elif quiz_number <= 24:
            return 3
        elif quiz_number <= 32:
            return 4
        elif quiz_number <= 33:
            return 5
        elif quiz_number <= 34:
            return 6
        elif quiz_number <= 35:
            return 7
        elif quiz_number <= 36:
            return 8
        return 0 # finish
    elif user_level <= 20:
        if quiz_number <= 8:
            return 1
        elif quiz_number <= 16:
            return 2
        elif quiz_number <= 24:
            return 3
        elif quiz_number <= 32:
            return 4
        elif quiz_number <= 34:
            return 5
        elif quiz_number <= 36:
            return 6
        elif quiz_number <= 38:
            return 7
        elif quiz_number <= 40:
            return 8
        return 0 # finish
    else:
        x = user_level - 20
        if quiz_number <= x + 16:
            return 3
        elif quiz_number <= 2 * x + 32:
            return 4
        elif quiz_number <= 2 * x + 32 + 4:
            return 7
        elif quiz_number <= 2 * x + 32 + 8:
            return 8
    return 0 # all finish

def get_quiz_numbers(user_level: int, mode: int) -> int | list| None:
    if mode <= 2:
        if user_level <= 0:
            return random.sample([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4)
        elif user_level <= 2:
            return random.sample([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], 4)
        elif user_level <= 8:
            x = random.randint(10, 95)
            return [x, x + 1, x + 3, x + 5]
        elif user_level <= 12:
            x = random.randint(100, 950)
            return [x, x + 10, x + 30, x + 50]
        x = random.randint(1000, 9500)
        return [x, x + 100, x + 300, x + 500]
    elif mode <= 4:
        if user_level <= 0:
            return random.randint(1, 10)
        elif user_level <= 2:
            return random.randint(1, 20)
        elif user_level <= 8:
            return random.randint(10, 100)
        elif user_level <= 12:
            return random.randint(100, 1000)
        return random.randint(1000, 9999)
    elif mode <= 6:
        if user_level <= 8:
            return random.sample([1, 2, 3, 4, 5], 3)
        elif user_level <= 12:
            return random.sample([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3)
        elif user_level <= 18:
            return random.sample([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], 3)
        return random.sample([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25], 3)
    elif mode <= 8:
        if user_level <= 8:
            return random.randint(1, 5)
        elif user_level <= 12:
            return random.randint(1, 10)
        elif user_level <= 18:
            return random.randint(1, 20)
        return random.randint(1, 25)
    elif mode <= 9:
        return random.randint(1, 100)
    return None
