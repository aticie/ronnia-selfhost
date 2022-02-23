import sys
import traceback

from ronnia.bots.twitch_bot import TwitchBot

if __name__ == '__main__':
    try:
        bot = TwitchBot()
        bot.run()
    except:
        print("Unexpected error:", traceback.format_exc())
        input("Press Enter to continue...")
        sys.exit(1)
