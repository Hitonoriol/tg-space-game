import sys
import traceback
import utils

error_interval = 5  # seconds
errors_max = 4

last_error = 0  # timestamp of last error
errors = 0  # error count in the last <error_interval> seconds

while True:
    try:
        utils.out("Starting the bot...")
        exec(open('main.py').read())
        utils.out("Stopped.")
    except Exception as e:
        if (utils.now() - last_error) > error_interval:
            errors = 0

        last_error = utils.now()
        errors += 1

        if str(e) == "stop":
            sys.exit()

        if errors > errors_max:
            utils.out("Too many errors!")
            sys.exit()

        traceback.print_exc()
        utils.out("Restarting...")
