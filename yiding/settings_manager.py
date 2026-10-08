# ------------------------------------------------------------------------------------------
# settings_manager
# ------------------------------------------------------------------------------------------

from pathlib import Path
from shutil import copy2

from platformdirs import user_config_dir

import tomlkit

APP_NAME = "Yiding"


def get_settings_path():

    config_dir = Path(
        user_config_dir(
            APP_NAME,
            appauthor=False,
            roaming=True
        )
    )

    config_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return config_dir / "settings.toml"


def get_default_settings_path():

    return Path(__file__).with_name(
        "settings.toml"
    )


def ensure_settings_file():

    settings_path = get_settings_path()

    if not settings_path.exists():

        copy2(
            get_default_settings_path(),
            settings_path
        )

    return settings_path

def load_settings():

    settings_path = ensure_settings_file()

    with open(
        settings_path,
        "r",
        encoding="utf-8"
    ) as file:

        return tomlkit.load(file)


def save_settings(settings):

    settings_path = ensure_settings_file()

    with open(
        settings_path,
        "w",
        encoding="utf-8"
    ) as file:

        tomlkit.dump(
            settings,
            file
        )
        
if __name__ == "__main__":

    print(
        ensure_settings_file()
    )
    
