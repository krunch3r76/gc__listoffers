# modified source: get_datadir() originally written/shared by Honest Abe
# https://www.py4u.net/discuss/161917

import sys
import pathlib

def get_datadir() -> pathlib.Path:

    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"

# create your program's directory

my_datadir = get_datadir() / "program-name"

try:
    my_datadir.mkdir(parents=True)
except FileExistsError:
    pass
