import player as plr
import storage_utils
import globals as game
import utils
from resource import Resource

admin_ids = [46010798]

player: plr.Player


def handle_admin_command(command):
    if command == "restart":
        restart()
    if command == "stop":
        stop()


def handle_arg_command(command, args):
    global player

    if command == "sell":
        player.sell_resource(Resource[args[0]], int(args[1]))


def handle_command(command):
    global player

    if player.id in admin_ids:
        handle_admin_command(command)

    if command == "profile":
        player.show_profile()

    elif command == "find_planet":
        player.start_timed_action(plr.Action.PLANET_SEARCH)

    elif command == "check_progress":
        player.check_progress(True)

    elif command == "show_cargo":
        player.show_cargo()

    else:
        tokens = command.split("_")
        handle_arg_command(tokens[0], tokens[1:])

    storage_utils.save_player(player)


@game.bot.message_handler(func=lambda m: True)
def handle_input(message):
    global player
    user_data = message.from_user
    init_context(user_data.id, user_data.username)

    if "/" in message.text:
        handle_command(message.text[1:])
        return

    game.bot.send_message(player.id, "Unknown command")


def init_context(uid, player_name):
    global player
    player = storage_utils.load_player(uid)

    if player is None:
        player = plr.Player(uid, player_name)


def shutdown():
    storage_utils.backup_daemon.cancel()
    storage_utils.timed_task_daemon.cancel()
    storage_utils.write_all()


def restart():
    shutdown()
    game.bot.send_message(player.id, "We do be restarting tha bot...")
    raise Exception("restart")


def stop():
    shutdown()
    game.bot.send_message(player.id, "Stopping... Good night!")
    raise Exception("stop")


for id in admin_ids:
    game.bot.send_message(id, "bot started!")

utils.out("Running & listening for updates...")

game.bot.polling()
