<div align="center">

# Ronnia - A Beatmap Request Bot

</div>

Ronnia is a Twitch/osu! bot that sends beatmap requests from Twitch chat to the streamer's in-game messages.

# Usage

Update the config.ini file with your settings.

```ini
[TWITCH]
# Change to False if you don't want the request acknowledgment message on Twitch chat.
feedback = True
min-stars = 0.0
max-stars = 9999.9
# Change to True if you want only subscribers to request
sub-only = False
# Change to True want requests to be through channel points only
channel-points-only = False
# Add twitch usernames comma-separated, lowercase. Ex: "user1,user2,user3"
excluded-users = 
# Change listen-to-self-message to True if you want to test it yourself
listen-to-self-message = False
# Put your twitch username here
username = 
# Get your tmi-token from here: https://twitchapps.com/tmi/
tmi-token = 
command-prefix = !
# Get your client-secret by creating an application from here: https://dev.twitch.tv/console
client-secret =

[OSU]
# Get your api-key and irc-password from https://osu.ppy.sh/home/account/edit at the bottom
api-key = 
username = 
irc-password = 
irc-server-address = irc.ppy.sh
```

## Windows

[Download the latest Windows release from here.](https://github.com/aticie/ronnia-selfhost/releases)

**If Windows Defender gives a VIRUS warning, click "Allow on device"**

If you think this software is a virus, you can literally look at the source code.

## Python

- Clone this repository `git clone https://github.com/aticie/ronnia-selfhost.git`
- Install requirements: `pip install -r requirements.txt`
- Fill in the `config.ini` file with your settings.
- Run the bot: `python ronnia/main.py`
