import datetime
from abc import ABC
from threading import Thread
from typing import AnyStr, Tuple, Union

from twitchio import Message, Chatter
from twitchio.ext import commands

from ronnia.bots.irc_bot import IrcBot
from ronnia.helpers.beatmap_link_parser import parse_beatmap_link, convert_seconds_to_readable
from ronnia.helpers.logger import RonniaLogger
from ronnia.helpers.osu_api import OsuApi
from ronnia.helpers.settings import Settings

logger = RonniaLogger(__name__)


class TwitchBot(commands.Bot, ABC):
    PER_REQUEST_COOLDOWN = 30  # each request has 30 seconds cooldown
    BEATMAP_STATUS_DICT = {"0": 'Pending',
                           "1": 'Ranked',
                           "2": 'Approved',
                           "3": 'Qualified',
                           "4": 'Loved',
                           "-1": 'WIP',
                           "-2": 'Graveyard'}

    def __init__(self):
        self.main_prefix = None
        self.settings = Settings()
        self.osu_api = OsuApi(self.settings.osu_api_key)

        args = {
            'token': self.settings.twitch_tmi_token,
            'client_secret': self.settings.twitch_client_secret,
            'prefix': self.settings.twitch_command_prefix,
            'initial_channels': [self.settings.twitch_username]
        }
        logger.debug(f'Sending args to super().__init__: {args}')
        super().__init__(**args)

        self.irc_bot = IrcBot(self.settings.osu_username, "irc.ppy.sh",
                              password=self.settings.osu_irc_password)
        self.irc_bot_thread = Thread(target=self.irc_bot.start)

        self.prefix = None
        self.user_last_request = {}

    def run(self):
        self.irc_bot_thread.start()
        super().run()

    async def event_message(self, message: Message):
        if message.author is None:
            return

        await self.handle_commands(message)
        await self.handle_request(message)

    async def handle_request(self, message: Message):
        logger.debug(f"{message.channel.name} - {message.author.name}: {message.content}")
        given_mods, api_params = self._check_message_contains_beatmap_link(message)
        if given_mods is not None:
            await self._check_user_cooldown(message.author)
            beatmap_info = await self.osu_api.get_beatmap_info(api_params)
            if beatmap_info:
                await self.check_request_criteria(message, beatmap_info)
                # If user has enabled echo setting, send twitch chat a message
                if self.settings.feedback:
                    await self._send_twitch_message(message, beatmap_info)

                await self._send_beatmap_to_irc(message, beatmap_info, given_mods)

    async def check_beatmap_star_rating(self, message: Message, beatmap_info):
        requester_name = message.author.name
        diff_rating = float(beatmap_info['difficultyrating'])
        range_low, range_high = self.settings.star_rating

        if range_low == -1 or range_high == -1:
            return

        assert range_low < diff_rating < range_high, \
            f'@{requester_name} Streamer is accepting requests between {range_low:.1f}-{range_high:.1f}* difficulty.' \
            f' Your map is {diff_rating:.1f}*.'

        return

    async def check_request_criteria(self, message: Message, beatmap_info: dict):
        await self.check_sub_only_mode(message)
        await self.check_channel_points_only_mode(message)
        await self.check_user_excluded(message)
        await self.check_if_author_is_broadcaster(message)

        try:
            await self.check_beatmap_star_rating(message, beatmap_info)
        except AssertionError as e:
            await message.channel.send(str(e))
            raise AssertionError

    async def check_user_excluded(self, message: Message):
        assert message.author.name.lower() not in self.settings.excluded_users, f'{message.author.name} is excluded'

    async def check_sub_only_mode(self, message: Message):
        is_sub_only = self.settings.sub_only
        if is_sub_only:
            assert message.author.is_mod or message.author.is_subscriber != '0' or 'vip' in message.author.badges, \
                'Subscriber only request mode is active.'

    async def check_channel_points_only_mode(self, message):
        channel_points_only = self.settings.channel_points_only
        if channel_points_only:
            assert 'custom-reward-id' in message.tags, 'Channel Points only mode is active.'
        return

    async def event_command_error(self, ctx, error):
        logger.error(error)
        pass

    async def check_if_author_is_broadcaster(self, message: Message):

        if not self.settings.listen_to_self_message:
            assert message.author.name != message.channel.name, 'Author is broadcaster and not in test mode.'

        return

    async def _check_user_cooldown(self, author: Chatter):
        """
        Check if user is on cooldown, raise an exception if the user is on request cooldown.
        :param author: Twitch user object
        :return: Exception if user has requested a beatmap before TwitchBot.PER_REQUEST_COOLDOWN seconds passed.
        """
        author_id = author.id
        time_right_now = datetime.datetime.now()

        await self._prune_cooldowns(time_right_now)

        if author_id not in self.user_last_request:
            self.user_last_request[author_id] = time_right_now
        else:
            last_message_time = self.user_last_request[author_id]
            seconds_since_last_request = (time_right_now - last_message_time).total_seconds()
            assert seconds_since_last_request >= TwitchBot.PER_REQUEST_COOLDOWN, \
                f'{author.name} is on cooldown.'
            self.user_last_request[author_id] = time_right_now

        return

    async def _prune_cooldowns(self, time_right_now: datetime.datetime):
        """
        Prunes users on that are on cooldown list so it doesn't get too cluttered.
        :param time_right_now:
        :return:
        """
        pop_list = []
        for user_id, last_message_time in self.user_last_request.items():
            seconds_since_last_request = (time_right_now - last_message_time).total_seconds()
            if seconds_since_last_request >= TwitchBot.PER_REQUEST_COOLDOWN:
                pop_list.append(user_id)

        for user in pop_list:
            self.user_last_request.pop(user)

        return

    async def _send_beatmap_to_irc(self, message: Message, beatmap_info: dict, given_mods: str):
        """
        Sends the beatmap request message to osu!irc bot
        :param message: Twitch Message object
        :param beatmap_info: Dictionary containing beatmap information from osu! api
        :param given_mods: String of mods if they are requested, empty string instead
        :return:
        """
        irc_message = await self._prepare_irc_message(message, beatmap_info, given_mods)
        await self._send_irc_message(irc_message, self.settings.osu_username)

        return

    async def _send_irc_message(self, irc_message: str, irc_target_channel):
        self.irc_bot.send_message(irc_target_channel, irc_message)

    @staticmethod
    async def _send_twitch_message(message: Message, beatmap_info: dict):
        """
        Sends twitch feedback message
        :param message: Twitch Message object
        :param beatmap_info: Dictionary containing beatmap information from osu! api
        :return:
        """
        artist = beatmap_info['artist']
        title = beatmap_info['title']
        version = beatmap_info['version']
        bmap_info_text = f"{artist} - {title} [{version}]"
        await message.channel.send(f"{bmap_info_text} - Request sent!")
        return

    @staticmethod
    def _check_message_contains_beatmap_link(message: Message) -> Tuple[Union[AnyStr, None], Union[dict, None]]:
        """
        Splits message by space character and checks for possible beatmap links
        :param message: Twitch Message object
        :return:
        """
        logger.debug("Checking if message contains beatmap link")
        content = message.content

        for candidate_link in content.split(' '):
            result, mods = parse_beatmap_link(candidate_link, content)
            if result:
                logger.debug(f"Found beatmap id: {result}")
                return mods, result
        else:
            logger.debug("Couldn't find beatmap in message")
            return None, None

    async def _prepare_irc_message(self, message: Message, beatmap_info: dict, given_mods: str):
        """
        Prepare beatmap request message to send to osu!irc.
        :param message: Twitch message
        :param beatmap_info: Beatmap info taken from osu!api as dictionary
        :param given_mods: Mods as string
        :return:
        """
        artist = beatmap_info['artist']
        title = beatmap_info['title']
        version = beatmap_info['version']
        bpm = beatmap_info['bpm']
        beatmap_status = self.BEATMAP_STATUS_DICT[beatmap_info['approved']]
        difficultyrating = float(beatmap_info['difficultyrating'])
        beatmap_id = beatmap_info['beatmap_id']
        beatmap_length = convert_seconds_to_readable(beatmap_info['hit_length'])
        beatmap_info = f"[https://osu.ppy.sh/b/{beatmap_id} {artist} - {title} [{version}]] " \
                       f"({bpm} BPM, {difficultyrating:.2f}*, {beatmap_length}) {given_mods}"
        extra_postfix = ""
        extra_prefix = ""

        badges = message.author.badges

        if message.author.is_mod:
            extra_prefix += "[MOD] "
        elif message.author.is_subscriber:
            extra_prefix += "[SUB] "
        elif 'vip' in badges:
            extra_prefix += "[VIP] "

        if 'custom-reward-id' in message.tags:
            extra_postfix += "+ USED POINTS"

        return f"{extra_prefix}{message.author.name} -> [{beatmap_status}] {beatmap_info} {extra_postfix}"

    async def event_ready(self):

        self.main_prefix = self._prefix

        initial_extensions = ['cogs.request_cog']
        for extension in initial_extensions:
            self.load_module(extension)
            logger.debug(f'Successfully loaded: {extension}')

        logger.info(f'Started the request bot as: {self.nick}')
