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
                                     'star-rating': (0.0, 9999.9),
                                     'sub-only': False,
                                     'channel-points-only': False,
                                     'excluded-users': '',
                                     'listen-to-self-message': False,
                                     'username': '',
                                     'tmi-token': '',
                                     'command-prefix': '!',
                                     'client-secret': ''}

            self.config['OSU'] = {'api-key': '',
                                  'username': '',
                                  'irc-password': ''}

            self.save()

    def save(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def load(self):
        self.config.read(self.config_file)
