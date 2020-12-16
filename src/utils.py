import random
import string
import calendar
import time
import datetime
from pathlib import Path


def rand_str(length=4) -> str:
    letters_and_digits = string.ascii_letters + string.digits + " "
    return ''.join((random.choice(letters_and_digits) for i in range(length)))


def file_size(file) -> int:
    return Path(file).stat().st_size


def now() -> int:
    return calendar.timegm(time.gmtime())


def out(msg):
    print("[" + time.strftime("%H:%M:%S", time.localtime()) + "] " + msg)


def time_str(sec) -> str:
    return str(datetime.timedelta(seconds=sec))


def round_str(num) -> str:
    return str(round(num, 2))


def roll_result(roll: float, percent: float) -> bool:
    return roll < percent


def rand_percent() -> float:
    return random.uniform(0, 100)


def percent_roll(percent: float) -> bool:
    return roll_result(rand_percent(), percent)
