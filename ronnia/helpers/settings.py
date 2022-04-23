import configparser
import os.path


class Settings:
    def __init__(self):
        self.config_file = 'config.ini'
        self.config = configparser.ConfigParser()

        if os.path.exists(self.config_file):
            self.load()
        else:
            self.config['TWITCH'] = {'feedback': True,
                                     'sub-only': False,
                                     'channel-points-only': False,
                                     'listen-to-self-message': False,
                                     'min-stars': 0.0,
                                     'max-stars': 9999.9,
                                     'excluded-users': '',
                                     'username': '',
                                     'tmi-token': '',
                                     'command-prefix': '!',
                                     'client-secret': ''}

            self.config['OSU'] = {'api-key': '',
                                  'username': '',
                                  'irc-password': '',
                                  'irc-server-address': 'irc.ppy.sh'}

            self.save()

            raise Exception('Template config file created. Please update the fields.')

        self.feedback = self.config.getboolean('TWITCH', 'feedback')
        self.channel_points_only = self.config.getboolean('TWITCH', 'channel-points-only')
        self.sub_only = self.config.getboolean('TWITCH', 'sub-only')
        self.listen_to_self_message = self.config.getboolean('TWITCH', 'listen-to-self-message')

        self.star_rating = self.config.getfloat('TWITCH', 'min-stars'), self.config.getfloat('TWITCH', 'max-stars')
        self.excluded_users = [user.strip() for user in self.config.get('TWITCH', 'excluded-users').split(',')]

        self.twitch_username = self.config.get('TWITCH', 'username')
        self.twitch_tmi_token = self.config.get('TWITCH', 'tmi-token')
        self.twitch_command_prefix = self.config.get('TWITCH', 'command-prefix')
        self.twitch_client_secret = self.config.get('TWITCH', 'client-secret')

        self.osu_api_key = self.config.get('OSU', 'api-key')
        self.osu_username = self.config.get('OSU', 'username')
        self.osu_irc_password = self.config.get('OSU', 'irc-password')
        self.osu_irc_server_address\
            = self.config.get('OSU', 'irc-server-address')

    def save(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def load(self):
        self.config.read(self.config_file)
