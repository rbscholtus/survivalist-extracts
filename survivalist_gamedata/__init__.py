"""Initialise the package."""

import logging.config
from pathlib import Path

import yaml


def _init_logging() -> None:
    # Load yaml file
    logconf_path = Path(__file__).parent / 'logging.yaml'
    with logconf_path.open() as y:
        c = yaml.safe_load(y)

    # create directories for file-based log handlers
    if 'handlers' in c:
        for handler in c['handlers']:
            if 'filename' in c['handlers'][handler]:
                logdir = Path(c['handlers'][handler]['filename']).parent
                logdir.mkdir(parents=True, exist_ok=True)

    # Initialise the logging system
    logging.config.dictConfig(c)


_init_logging()
