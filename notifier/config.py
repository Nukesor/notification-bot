"""Config values for pollbot."""
import os
import sys
import tomllib

import tomli_w

default_config = {
    "telegram": {
        "bot_name": "your_bot_@_username",
        "api_key": "your_telegram_api_key",
        "target_channel": "your_chat_id",
    },
    "logging": {
        "debug": False,
    },
}

config_path = os.path.expanduser("~/.config/telegram_notifier.toml")

if not os.path.exists(config_path):
    with open(config_path, "wb") as file_descriptor:
        tomli_w.dump(default_config, file_descriptor)
    print("Please adjust the configuration file at '~/.config/kleinanzeigen.toml'")
    sys.exit(1)
else:
    with open(config_path, "rb") as file_descriptor:
        config = tomllib.load(file_descriptor)

    # Set default values for any missing keys in the loaded config
    for key, category in default_config.items():
        for option, value in category.items():
            if option not in config[key]:
                config[key][option] = value
