import telebot

version = "v0.1"
bot = telebot.TeleBot("1250437591:AAH6edw9aDKW8S8MKKxtj5hdf0OGNn3fCY4", parse_mode=None)

player_storage = {}
pending_players = []

storage_changed = False
