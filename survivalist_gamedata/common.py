import logging
import re
from pathlib import Path
from typing import Any

from .config import conf

log = logging.getLogger(__name__)


class ExtractsError(Exception):
    """General error class for Survivalist Extracts script."""


def load_game_version() -> str:
    version_path = Path(conf.version_file)

    with version_path.open() as version_file:
        version = version_file.readline().strip()

    log.info('Game version found: %s', version)

    return version


def unique(seq: list) -> list:
    seen: set = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def expand_names(text: Any) -> Any:  # noqa: ANN401
    if isinstance(text, str):
        text = re.sub(r'[a-z][A-Z]', lambda x: x.group(0)[0] + ' ' + x.group(0)[1], text)
        text = re.sub(r'_([a-zA-Z0-9 ]+)', lambda x: f' ({x.group(1)})', text)
        for orig, repl in conf.replacements.items():
            text = text.replace(orig, repl)

    return text
