"""Dostring."""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import confuse  # type: ignore  # noqa: PGH003
import toml

log = logging.getLogger(__name__)


def path2str(data: Any) -> Any:  # noqa: ANN401
    if isinstance(data, dict):
        return {key: path2str(value) for key, value in data.items()}
    elif isinstance(data, list):  # noqa: RET505
        return [path2str(item) for item in data]
    elif isinstance(data, Path):
        return str(data)
    else:
        return data


_template = {
    'dump_config': bool,
    'base_dir': confuse.Path(cwd=Path.cwd()),
    'version_file': confuse.Path(relative_to='base_dir'),
    'gamedata_dirs': confuse.StrSeq(split=False),
    'replacements': confuse.Optional(confuse.MappingValues(str)),
    'recipes': {
        'skip_deprecated': bool,
        'order_by': confuse.StrSeq(split=True),
        'csv_file': str,
        'csv_fields': confuse.StrSeq(split=False),
        'steam_file': str,
        'steam_tables': {
            'default_columns':
                confuse.MappingValues(str),
            'tables':
                confuse.Sequence({
                    'SkillType': str,
                    'RecipeType': confuse.Optional(str, default='*'),
                    'columns': confuse.Optional(confuse.MappingValues(str)),
                }),
        },
    },
    'game_items': {
        'skip_files': confuse.StrSeq(split=False),
        'csv_file': str,
        'remove_keys': confuse.StrSeq(split=False),
        'steam_file': str,
        'steam_tables': {
            'default_columns':
                confuse.MappingValues(str),
            'tables':
                confuse.Sequence({
                    'Category': str,
                    'columns': confuse.Optional(confuse.MappingValues(str)),
                }),
        },
    },
}


def _init_conf() -> confuse.templates.AttrDict:
    """Read the config file."""
    here = Path(__file__).parent
    pyprj = toml.load(here.parent / 'pyproject.toml')
    version = pyprj['tool']['poetry']['version']
    desc = pyprj['tool']['poetry']['description']

    # Get arguments from the command line.
    argp = argparse.ArgumentParser(description=(f'Survivalist Gamedata - {desc}'))
    argp.add_argument('--version',
                      action='version',
                      version=f'Survivalist Gamedata {version}')
    argp.add_argument(
        '--dump-config',
        dest='dump_config',
        action='store_true',
        help='Dump config and exit',
    )
    args = argp.parse_args()

    # make confuse understand where config.yaml is
    os.environ['CONFDIR'] = str(Path().absolute())

    # ensure there is a config.yaml file
    configfile = Path() / 'config.yaml'
    if not configfile.exists():
        configfile.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(__file__).parent / 'config_default.yaml', configfile)
        log.warning('Default config.yaml created in %s', os.environ['CONFDIR'])

    # get all config
    config = confuse.Configuration('CONF', __name__)
    config.set_args(args, dots=True)

    return config.get(_template)


conf: confuse.templates.AttrDict = _init_conf()

# Dump config
if conf.dump_config:
    log.warning(json.dumps(path2str(conf), indent=4))
    sys.exit()
