import csv
import itertools
import logging
from collections import OrderedDict
from pathlib import Path

import xmltodict

from .common import ExtractsError, expand_names
from .config import conf

log = logging.getLogger(__name__)


def item_cmp(x: dict) -> tuple:
    """Sort items."""
    name = x['NativeName']
    cat = x['Category']
    bp = float(x.get('BasePrice', '-1').split('/')[0])
    dmg = x.get('Damage', '')

    if cat.startswith('2:Weapons/Melee'):
        return (cat, dmg, name)

    return (cat, bp, name)


def lootloc_str(equip: dict) -> str:
    if 'LootableFromLocations' not in equip or 'Scarcity' not in equip:
        return ''

    things: dict = {}
    if isinstance(equip['LootableFromLocations']['LootableFrom'], dict):
        equip['LootableFromLocations']['LootableFrom'] = [
            equip['LootableFromLocations']['LootableFrom'],
        ]

    for loot_from in equip['LootableFromLocations']['LootableFrom']:
        loot_sc = equip['Scarcity']
        if 'OverrideScarcity' in loot_from:
            loot_sc = loot_from['OverrideScarcity']

        if loot_sc not in things:
            things[loot_sc] = []
        things[loot_sc].append(loot_from['Name'])

    things_strs = [f"{k} at {', '.join(v)}" for k, v in things.items()]
    return '\n'.join(things_strs)


def load_items() -> list[OrderedDict]:
    items = []

    xml_files = itertools.chain(
        *(Path(conf.base_dir, p, 'Equipment').glob('*.xml') for p in conf.gamedata_dirs),
        *(Path(conf.base_dir, p, 'Liquid').glob('*.xml') for p in conf.gamedata_dirs))
    for xml_file in xml_files:
        if xml_file.name in conf.game_items.skip_files:
            log.debug('Skipping %s', xml_file.name)
            continue

        log.debug('Loading gameitem from %s', xml_file)
        item = xmltodict.parse(xml_file.open('rb'))
        item['xml_file_name'] = xml_file.name
        items.append(item)

    log.info('Found %s items', len(items))

    return items


def process_items(items: list[OrderedDict]) -> list[OrderedDict]:
    clean_items = []
    for xml in items:
        # identify type
        if 'EquipmentPrototype' in xml:
            item = xml['EquipmentPrototype']
        elif 'LiquidPrototype' in xml:
            item = xml['LiquidPrototype']
        else:
            msg = 'Not a EquipmentPrototype or LiquidPrototype'
            raise ExtractsError(msg)

        # NativeName fix for Kerosene.xml
        if 'NativeName' not in item:
            log.warning('Adding property NativeName to %s', xml['xml_file_name'])
            item['NativeName'] = xml['xml_file_name']

        # re-organise some categories
        if item['Category'] == '5:Food/Seeds':
            item['Category'] = '5:Seeds'
        elif item['Category'] == '4:Clothing/Backpacks':
            item['Category'] = '4:Backpacks'

        # relocate some items to another category
        if item['NativeName'] in 'Sugar':
            item['Category'] = '5:Food/Dishes'
        elif item['NativeName'] in 'Urine':
            item['Category'] = '5:Food/Drink'

        # make friendly loot location strings
        item['LootLocations'] = lootloc_str(item)

        # flatten some lists
        if 'GiftFor' in item and item['GiftFor']:
            if isinstance(item['GiftFor']['string'], list):
                item['GiftFor'] = ', '.join(item['GiftFor']['string'])
            else:
                item['GiftFor'] = item['GiftFor']['string']
        if 'BadGiftFor' in item and item['BadGiftFor']:
            if isinstance(item['BadGiftFor']['string'], list):
                item['BadGiftFor'] = ', '.join(item['BadGiftFor']['string'])
            else:
                item['BadGiftFor'] = item['BadGiftFor']['string']
        if 'FoodForAnimal' in item and item['FoodForAnimal']:
            if isinstance(item['FoodForAnimal']['BaseObjectType'], list):
                item['FoodForAnimal'] = ', '.join(item['FoodForAnimal']['BaseObjectType'])
            else:
                item['FoodForAnimal'] = item['FoodForAnimal']['BaseObjectType']
        if 'AmmoTypes' in item and item['AmmoTypes']:
            if isinstance(item['AmmoTypes']['string'], list):
                item['AmmoTypes'] = ', '.join(item['AmmoTypes']['string'])
            else:
                item['AmmoTypes'] = item['AmmoTypes']['string']

        # make friendly skill bonus strings
        if 'SkillBonus' in item:
            item['SkillBonus'] = item['SkillBonus'] + ' ' + item['SkillBonusType']

        # add property at level 5 skill level strings
        if 'DamageBonusPerSkillLevel' in item:
            dmg_l5 = float(item['Damage']) + 5 * float(item['DamageBonusPerSkillLevel'])
            item['Damage'] = f'{float(item["Damage"]):.2f} / {dmg_l5:.2f}'
        if 'RangeBonusPerSkillLevel' in item:
            rg_l5 = float(item['Range']) + 5 * float(item['RangeBonusPerSkillLevel'])
            item['Range'] = f'{item["Range"]} / {rg_l5:.0f}'
        if 'AccurateRangeBonusPerSkillLevel' in item:
            rg_l5 = float(item['AccurateRange']) + 5 * float(
                item['AccurateRangeBonusPerSkillLevel'])
            item['AccurateRange'] = f'{item["AccurateRange"]} / {rg_l5:.0f}'
        if 'CarryWeightBonusPerSkillLevel' in item:
            rg_l5 = float(
                item['CarryWeight']) + 5 * float(item['CarryWeightBonusPerSkillLevel'])
            item['CarryWeight'] = f'{item["CarryWeight"]} / {rg_l5:.0f}'

        # merge /item and /floz columns
        if 'BasePricePerFlOz' in item:
            item['BasePrice'] = item['BasePricePerFlOz'] + ' / FlOz'
        if 'NutritionPerFlOz' in item:
            item['Nutrition'] = item['NutritionPerFlOz'] + ' / FlOz'
        if 'SkillOnConsumptionProgression' in item:
            item['SkillOnConsumption'] = (item['SkillOnConsumptionProgression'] + ' ' +
                                          item['SkillOnConsumptionType'])
        elif 'SkillOnConsumptionProgressionPerFlOz' in item:
            item['SkillOnConsumption'] = (item['SkillOnConsumptionProgressionPerFlOz'] +
                                          ' ' + item['SkillOnConsumptionType'] +
                                          ' / FlOz')

        clean_items.append(item)

    return clean_items


def save_items_as_csv(items: list[OrderedDict], filename: str) -> None:
    """Write data to CSV file."""
    csv_path = Path(filename)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    log.info('Writing CSV to %s', csv_path.name)

    with csv_path.open('w', newline='\n') as csv_file:
        all_keys = set().union(*(d.keys() for d in items))
        export_keys = all_keys - set(conf.game_items.remove_keys)

        writer = csv.DictWriter(csv_file, fieldnames=export_keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(items)


def save_items_as_steamml(items: list[OrderedDict], filename: str) -> int:
    cnt_added = 0

    markup_path = Path(filename)
    markup_path.parent.mkdir(parents=True, exist_ok=True)
    log.info('Writing Steam markup to %s', markup_path.name)

    with markup_path.open('w') as markup_buff:
        for table in conf.game_items.steam_tables.tables:
            log.debug('Making table %s', table.Category)
            cols = (table.columns
                    if table.columns else conf.game_items.steam_tables.default_columns)

            # table start and header row
            markup_buff.write('[table]\n')
            markup_buff.write(' [tr]\n')
            for val in cols.values():
                markup_buff.write(f'  [th]{val}[/th]\n')
            markup_buff.write(' [/tr]\n')

            for item in items:
                # add item to the right table
                if item['Category'].startswith(table.Category):
                    log.debug('%s goes in %s', item['NativeName'], table.Category)
                    cnt_added += 1
                    markup_buff.write(' [tr]\n')
                    for col in cols:
                        val = expand_names(item.get(col, ''))
                        markup_buff.write(f'  [td]{val}[/td]\n')
                    markup_buff.write(' [/tr]\n')

            markup_buff.write('[/table]\n\n')

    log.info('Matched %s items with a table', cnt_added)

    return cnt_added


def extract_items(version: str) -> None:
    items = load_items()
    items_proc = process_items(items)
    items_proc.sort(key=item_cmp)
    save_items_as_csv(items_proc, conf.game_items.csv_file.format(version=version))
    found_cnt = save_items_as_steamml(items_proc,
                                      conf.game_items.steam_file.format(version=version))
    if len(items) != found_cnt:
        log.warning(
            'Only %s out of %s items have been saved/skipped. '
            'Are there new Categories?', found_cnt, len(items))
