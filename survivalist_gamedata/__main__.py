"""Make the package runnable."""

from .common import load_game_version
from .items import extract_items
from .recipes import extract_recipes


def run() -> None:
    version = load_game_version()
    extract_recipes(version)
    extract_items(version)


if __name__ == '__main__':
    run()
