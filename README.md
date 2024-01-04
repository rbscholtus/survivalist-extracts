# survivalist-gamedata

## Description

This is a utility for extracting information about the game Survivalist: Invisible Strain from the game's XML files. The information comprises the game's crafting recipes and items (equipment and liquids). The utility saves the extracted data in CSV format, as well as table format using the markup language used for writing Steam Community guides.

The utility is useful for fans and modders who want to generate up-to-date references for the game's crafting recipes and items.

The output of the utility is used for the [Crafting Reference Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2987340791) and the [Item Reference Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2987756847) for the game on steamcommunity.com.

## Getting Started

### Installing

The usual:

```pip install survivalist-gamedata```

Or an appropriate command for the virtual environment manager you use.

The installation will install the `survivalist-gamedata` console script.

### Usage

The game needs to be installed to run this.

Run the utility on the command-line:

```survivalist-gamedata```

Or as a package:

```python -m survivalist_gamedata```

Get help:

```survivalist-gamedata --help```

The first time the utility is run, it will create a `config.yaml` file in your current working directory. You may configure this file to customise the utility's behavior if needed.

The utility will find the version of the game that is installed on your system, and creates a subdirectory in `data/` for the output files for the detected version.

The utility will print essential messages to the console, and debugging messages to `debug.log`.

### Configuration

The `config.yaml` file in your current working directory contains the utility's configuration directives.

* The `base_dir` is by default set to the game's installation directory assuming you installed the game using Steam on Windows. Change this directive if your game is installed somewhere else.

* `version_file` and `gamedata_dirs` tell the utility where the game files are. The utility will search for crafting recipes by looking for Recipes.xml in each directory. It will search for items by searching for XML files in Equipment/ and Liquid/ subdirectories in each directory.

* String replacements are configured in `replacements`. Replacements are applied when outputting the game's data in Steam Community markup format.

* The `recipes` section configures the output of the game's craftig recipes.

  * `csv_fields` configures which columns are exported to the CSV file.

  * The `steam_tables` > `table` directive configures the tables that are generated in Steam Community markup language. For each table, `SkillType` and optionally `RecipeType` must be specified to let the generator know what subset of the full recipes list you want to include in the table. Any recipe for which SkillType and RecipeType matches your configuration will be included. Optionally, `columns` can be specified to change the columns for specific tables, if different from `default_columns`.

* The `game_items` section configures the output of the game's equipment and liquids.

  * `skip_files` specifies XML files that need to be excluded from the output, for example if they contain duplicated information.

  * `remove_keys` configures which columns are not exported to the CSV file.

  * The `steam_tables` > `table` directive configures the tables that are generated in Steam Community markup language. For each table, `Category` must be specified to let the generator know what subset of the full items list you want to include in the table. Any item for which the Category starts with your configuration will be included. Optionally, `columns` can be specified to change the columns for specific tables, if different from `default_columns`.

## Version History

* 1.0
    * Initial Release. Supports recipes, equipment and liquids.

## Future development

As of January 2024, the utility works properly with Survivalist: Invisible Strain, public beta v196. In the future, more recipe files and gamedata directories may be added to the game. These may require tweaks to the utility's configuration and/or code.

## Authors

* [Barend Scholtus](https://github.com/rbscholtus)

## License

This project is licensed under the Apache License Version 2.0 - see the LICENSE.txt file for details.

## Acknowledgments

A shout-out to Bob The PR Bot - the sole developer of Survivalist: Invisible Strain!
