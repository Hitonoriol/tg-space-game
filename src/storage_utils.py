import threading
import pickle
import globals
import utils

print("* Loading player data...")
player_file = 'players.dat'

if utils.file_size(player_file) > 10:
    globals.player_storage = pickle.load(open(player_file, "rb"))


def load_player(uid):
    if str(uid) in globals.player_storage:
        return globals.player_storage[str(uid)]
    else:
        return None


def save_player(player):
    globals.storage_changed = True
    globals.player_storage[str(player.id)] = player


def write_all():
    if not globals.storage_changed:
        return

    utils.out("Writing memory storage to disk...")
    pickle.dump(globals.player_storage, open(player_file, 'wb'))
    globals.storage_changed = False


# Recurring tasks

# Save everything to disk
backup_daemon: threading.Timer
timed_task_daemon: threading.Timer


def perform_backup():
    global backup_daemon
    write_all()
    backup_daemon = threading.Timer(60, perform_backup)
    backup_daemon.start()


# Timed tasks (for players)
def perform_timed_tasks():
    global timed_task_daemon

    for uid in globals.pending_players[:]:
        player = load_player(int(uid))
        player.check_pending_actions()
        if not player.has_more_pending_actions():
            globals.pending_players.remove(uid)

    timed_task_daemon = threading.Timer(1, perform_timed_tasks)
    timed_task_daemon.start()


perform_backup()
perform_timed_tasks()
