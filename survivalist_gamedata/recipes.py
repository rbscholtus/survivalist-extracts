import csv
import logging
from pathlib import Path

import xmltodict

from .common import ExtractsError, expand_names
from .config import conf

log = logging.getLogger(__name__)


def recipes_cmp(rec: dict) -> tuple:
    return tuple(rec.get(col, '') for col in conf.recipes.order_by)


def load_recipes() -> list[dict]:
    recipes = []

    xml_files = [Path(conf.base_dir, p, 'Recipes.xml') for p in conf.gamedata_dirs]
    for xml_file in xml_files:
        if xml_file.exists():
            log.debug('Loading recipes from %s', xml_file)
            recipes_dict = xmltodict.parse(xml_file.open('rb'))
            if isinstance(recipes_dict['RecipeList']['Recipes']['Recipe'], list):
                recipes.extend(recipes_dict['RecipeList']['Recipes']['Recipe'])
            else:
                recipes.append(recipes_dict['RecipeList']['Recipes']['Recipe'])

    log.info('Found %s recipes', len(recipes))

    return recipes


def stringify_ingredients(rec: dict) -> str:
    ingr_list = []
    if ('Ingredients' in rec and rec['Ingredients'] and
            'Ingredient' in rec['Ingredients']):
        # Ensure it's a list, not a single item
        if isinstance(rec['Ingredients']['Ingredient'], dict):
            rec['Ingredients']['Ingredient'] = [rec['Ingredients']['Ingredient']]

        for ingr in rec['Ingredients']['Ingredient']:
            if 'PrototypeNames' in ingr:
                new_ingr = f"{ingr['PrototypeNames']['string']} ({ingr['Amount']})"
                ingr_list.append(new_ingr)
            elif 'LiquidTypeNames' in ingr:
                new_ingr = (
                    f"{ingr['LiquidTypeNames']['string']} ({ingr['LiquidAmount']} FlOz)")
                ingr_list.append(new_ingr)
            else:
                msg = f'Unexpected ingredient: {ingr}'
                raise ExtractsError(msg)

    ingr_str = '\n'.join(ingr_list)

    return ingr_str.replace("'", '')


def process_recipes(recipes: list[dict]) -> list[dict]:
    for rec in recipes:
        # Make product name field consistent
        if 'ProductPrototypeName' not in rec and 'ProductType' in rec:
            rec['ProductPrototypeName'] = rec['ProductType']
        elif 'ProductPrototypeName' not in rec and 'ProductLiquidPrototypeName' in rec:
            rec['ProductPrototypeName'] = rec['ProductLiquidPrototypeName']

        # Missing ProductPrototypeName fix for Infect AntiqueKatana
        if 'ProductPrototypeName' not in rec:
            log.warning('Adding property ProductPrototypeName to %s', rec['UniqueID'])
            rec['ProductPrototypeName'] = 'Product?'

        # Make product amount field consistent
        if 'ProductAmount' not in rec and 'ProductLiquidAmount' in rec:
            rec['ProductAmount'] = rec['ProductLiquidAmount'] + ' FlOz'

        rec['Product'] = rec['ProductPrototypeName']
        if 'ProductAmount' in rec and rec['ProductAmount']:
            rec['Product'] += f" ({rec['ProductAmount']})"

        # Stringify ingredients list
        rec['Ingredients'] = stringify_ingredients(rec)

        # Ensure RecipeType and SkillLevel are set
        if 'RecipeType' not in rec or not rec['RecipeType']:
            rec['RecipeType'] = 'Inventory'
        if 'SkillLevel' not in rec or not rec['SkillLevel']:
            rec['SkillLevel'] = '0'

        # Simplify RecipeType in some cases
        if rec['RecipeType'].startswith('Campfire_SpitRoast'):
            rec['RecipeType'] = 'Campfire'

    return recipes


def save_recipes_as_csv(recipes: list[dict], filename: str) -> None:
    csv_path = Path(filename)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    log.info('Writing CSV to %s', csv_path.name)

    with csv_path.open('w', newline='\n') as csv_file:
        writer = csv.DictWriter(csv_file,
                                fieldnames=conf.recipes.csv_fields,
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(recipes)


def save_recipes_as_steamml(recipes: list[dict], filename: str) -> int:
    cnt_added = 0
    cnt_depr = 0

    markup_path = Path(filename)
    markup_path.parent.mkdir(parents=True, exist_ok=True)
    log.info('Writing Steam markup to %s', markup_path.name)

    with markup_path.open('w') as markup_buff:
        for table in conf.recipes.steam_tables.tables:
            table_id = f'{table.SkillType}/{table.RecipeType}'
            log.debug('Making table %s', table_id)
            cols = (table.columns
                    if table.columns else conf.recipes.steam_tables.default_columns)

            # table start and header row
            markup_buff.write('[table]\n')
            markup_buff.write(' [tr]\n')
            for val in cols.values():
                markup_buff.write(f'  [th]{val}[/th]\n')
            markup_buff.write(' [/tr]\n')

            for rec in recipes:
                # add recipe to the right table
                if table.SkillType == rec['SkillType'] and (table.RecipeType
                                                            in ('*', rec['RecipeType'])):
                    # skip deprecated recipes
                    if conf.recipes.skip_deprecated and 'Deprecated' in rec and (
                            rec['Deprecated'] == 'true'):
                        cnt_depr += 1
                        log.debug('Skipping deprecated recipe %s', rec['UniqueID'])
                        continue

                    log.debug('%s goes in %s', rec['UniqueID'], table_id)
                    cnt_added += 1
                    markup_buff.write(' [tr]\n')
                    for col in cols:
                        val = expand_names(rec.get(col, ''))
                        markup_buff.write(f'  [td]{val}[/td]\n')
                    markup_buff.write(' [/tr]\n')

            markup_buff.write('[/table]\n\n')

    log.info('Matched %s recipes with a table, %s deprecated recipes were skipped',
             cnt_added, cnt_depr)

    return cnt_added + cnt_depr


def extract_recipes(version: str) -> None:
    recipes = load_recipes()
    rcps_proc = process_recipes(recipes)
    rcps_proc.sort(key=recipes_cmp)
    save_recipes_as_csv(rcps_proc, conf.recipes.csv_file.format(version=version))
    found_cnt = save_recipes_as_steamml(rcps_proc,
                                        conf.recipes.steam_file.format(version=version))
    if len(recipes) != found_cnt:
        log.warning(
            'Only %s out of %s recipes have been saved/skipped. '
            'Are there new SkillTypes or RecipeTypes?', found_cnt, len(recipes))
