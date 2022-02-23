import attr
import irc.bot
from irc.client import Event, ServerConnection

from ronnia.helpers.logger import RonniaLogger

logger = RonniaLogger(__name__)


@attr.s
class RangeInput(object):
    range_low = attr.ib(converter=float)
    range_high = attr.ib(converter=float)


class IrcBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, server, port=6667, password=None):
        reconnect_strategy = irc.bot.ExponentialBackoff(min_interval=5, max_interval=30)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname,
                                            recon=reconnect_strategy)
        self.connection.set_rate_limit(1)

    def on_welcome(self, c: ServerConnection, e: Event):
        logger.info(f"Successfully connected to osu! irc as: {self._nickname}")

    def send_message(self, target: str, cmd: str):
        target = target.replace(" ", "_")
        logger.info(f"Sending request in-game to {target}: {cmd}")
        self.connection.privmsg(target, cmd)
