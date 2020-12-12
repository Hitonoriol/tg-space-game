import random
import string
import calendar
import time
import datetime
from pathlib import Path


def rand_str(length=4):
    letters_and_digits = string.ascii_letters + string.digits + " "
    return ''.join((random.choice(letters_and_digits) for i in range(length)))


def file_size(file):
    return Path(file).stat().st_size


def now():
    return calendar.timegm(time.gmtime())


def out(msg):
    print("[" + time.strftime("%H:%M:%S", time.localtime()) + "] " + msg)


def time_str(sec):
    return str(datetime.timedelta(seconds=sec))
