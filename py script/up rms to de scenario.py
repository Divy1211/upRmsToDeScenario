from AoE2ScenarioParser.aoe2_scenario import AoE2Scenario
from AoE2ScenarioParser.datasets.buildings import Building
from AoE2ScenarioParser.datasets.conditions import Condition
from AoE2ScenarioParser.datasets.effects import Effect
from AoE2ScenarioParser.datasets.heroes import Hero
from AoE2ScenarioParser.datasets.players import Player
from AoE2ScenarioParser.datasets.techs import Tech
from AoE2ScenarioParser.datasets.trigger_lists import ObjectAttribute, Operation, Attribute, ButtonLocation, \
    DiplomacyState, Comparison, PanelLocation
from AoE2ScenarioParser.datasets.units import Unit, GaiaUnit
import re as regex
import json

map_name = input("Enter map name:").replace(".rms", "")

# load all dependencies
with open("../json data/wk tech data.json") as file:
    techs = json.load(file)
with open("../json data/wk unit data.json") as file:
    units = json.load(file)
with open("../json data/wk to de tech id map.json") as file:
    tech_map = json.load(file)
with open("../json data/wk to de unit id map.json") as file:
    unit_map = json.load(file)
with open("../json data/UP to DE map.json") as file:
    trigger_map = json.load(file)
with open(f"../{map_name}.rms") as file:
    rms = file.read()

def extract_constants(rms):
    constants = {}
    consts = regex.findall("#const\s+\w+\s+\d+", rms)
    for const in consts:
        const = const.replace("#const ", "")
        const = regex.findall("\w+", const)
        constants[const[0]] = const[1]
    return constants
def extract_effect_amount_commands(rms):
    effect_amount_commands = []
    eft_amt_cmds = regex.findall("effect_amount\s+\w+\s+\w+\s+\w+\s+-*\d+", rms)
    for cmd in eft_amt_cmds:
        cmd = cmd.replace("effect_amount ", "")
        cmd = regex.findall("\w+", cmd)
        effect_amount_commands.append({
            "effect" : cmd[0],
            "target_object" : cmd[1],
            "attribute_or_operation" : cmd[2],
            "value" : cmd[3]
        })
    return effect_amount_commands
def extract_effect_percent_commands(rms):
    effect_percent_commands = []
    eft_per_cmds = regex.findall("effect_percent\s+\w+\s+\w+\s+\w+\s+-*\d+", rms)
    for cmd in eft_per_cmds:
        cmd = cmd.replace("effect_percent ", "")
        cmd = regex.findall("\w+", cmd)
        effect_percent_commands.append({
            "effect" : cmd[0],
            "target_object" : cmd[1],
            "attribute_or_operation" : cmd[2],
            "value" : cmd[3]
        })
    return effect_percent_commands
def extract_guard_state_commands(rms):
    effect_percent_commands = []
    eft_per_cmds = regex.findall("guard_state\s+\w+\s+\w+\s+-*\d+\s+-*\d+", rms)
    for cmd in eft_per_cmds:
        cmd = cmd.replace("guard_state ", "")
        cmd = regex.findall("\w+", cmd)
        effect_percent_commands.append({
            "unit_or_class" : cmd[0],
            "resource" : cmd[1],
            "resource_delta" : cmd[2],
            "guard_flags" : cmd[3]
        })
    return effect_percent_commands

# extract information needed from RMS file
constants = extract_constants(rms)
effect_amount_commands = extract_effect_amount_commands(rms)
effect_percent_commands = extract_effect_percent_commands(rms)
guard_state_commands = extract_guard_state_commands(rms)

def operate(operation, value, og_value):
    if operation == Operation.SET:
        return value
    elif operation == Operation.ADD:
        return og_value+value
    elif operation == Operation.MULTIPLY:
        return  og_value*value

def modify_attribute(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "SET" in effect:
        effect_operation = Operation.SET
    elif "ADD" in effect:
        effect_operation = Operation.ADD
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    object_id = -10
    unit_class = -10
    if target_object in constants:
        temp_id = int(constants[target_object])
        if 900 < temp_id < 1000:
            unit_class = temp_id - 900
        else:
            object_id = unit_map[str(temp_id)]
        if unit_class < 0 and object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        object_id = unit_map[str(trigger_map['object'][target_object])]
        if object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['class']:
        unit_class = trigger_map['class'][target_object] - 900
    else:
        print(f"Error: Object or Unit Class '{target_object}' not found")
        exit()

    effect_attribute = -10
    if attribute_or_operation in constants:
        effect_attribute = int(constants[attribute_or_operation])
        for attribute in trigger_map['attribute']:
            temp_id = trigger_map['attribute'][attribute]
            if temp_id < 0 and abs(temp_id) == effect_attribute:
                print(f"ThxDE: Attribute '{abs(temp_id)}' is not supported on DE")
                exit()
            if (attribute == "ATTR_PROJECTILE_ID" or \
                attribute == "ATTR_TRAIN_LOCATION" or \
                attribute == "ATTR_DEAD_ID") and temp_id == effect_attribute:
                if unit_map[value] < 0:
                    print(f"ThxDE: An Equivalent for Object '{value}' on WK does not exist on DE")
                    exit()
                else:
                    value = unit_map[value]
    elif attribute_or_operation in trigger_map['attribute']:
        if trigger_map['attribute'][attribute_or_operation] >= 0:
            if attribute_or_operation == "ATTR_PROJECTILE_ID" or \
                    attribute_or_operation == "ATTR_TRAIN_LOCATION" or \
                    attribute_or_operation == "ATTR_DEAD_ID":
                if unit_map[value] < 0:
                    print(f"ThxDE: An Equivalent for Object '{value}' on WK does not exist on DE")
                    exit()
                else:
                    value = unit_map[value]
            effect_attribute = trigger_map['attribute'][attribute_or_operation]
        else:
            print(f"ThxDE: Attribute '{attribute_or_operation}' is not supported on DE")
            exit()
    else:
        print(f"Error: Attribute '{attribute_or_operation}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation} {value}")
    if "GAIA" in effect:
        if unit_class >= 0:
            for unit in units:
                if int(units[unit]['class']) == unit_class:
                    if unit_map[unit] >= 0:
                        trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                           quantity=int(value),
                                           object_list_unit_id=unit_map[unit],
                                           source_player=Player.GAIA,
                                           item_id=unit_map[unit],
                                           operation=effect_operation,
                                           object_attributes=effect_attribute)
                    else:
                        print(f"Warning, ThxDE: Unit ID '{unit}' of class '{unit_class}' " +
                              f"on WK does not exist on DE, skipping unit!")
        else:
            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                               quantity=int(value),
                               object_list_unit_id=object_id,
                               source_player=Player.GAIA,
                               item_id=object_id,
                               operation=effect_operation,
                               object_attributes=effect_attribute)
    else:
        if unit_class >= 0:
            for unit in units:
                if int(units[unit]['class']) == unit_class:
                    if unit_map[unit] >= 0:
                        for player in range(1, number_of_players + 1):
                            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                               quantity=int(value),
                                               object_list_unit_id=unit_map[unit],
                                               source_player=player,
                                               item_id=unit_map[unit],
                                               operation=effect_operation,
                                               object_attributes=effect_attribute)
                    else:
                        print(f"Warning, ThxDE: Unit ID '{unit}' of class '{unit_class}' " +
                              f"on WK does not exist on DE, skipping unit!")
        else:
            for player in range(1, number_of_players + 1):
                trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                   quantity=int(value),
                                   object_list_unit_id=object_id,
                                   source_player=player,
                                   item_id=object_id,
                                   operation=effect_operation,
                                   object_attributes=effect_attribute)
def modify_resource(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "MOD" in effect:
        if attribute_or_operation in constants:
            effect_operation = int(constants[attribute_or_operation])
            if effect_operation == 0:
                effect_operation = 1
            elif effect_operation == 1:
                effect_operation = 2
            else:
                print(f"Error: Operation '{attribute_or_operation}' not found")
                exit()
        elif attribute_or_operation in trigger_map['operation']:
            effect_operation = trigger_map['operation'][attribute_or_operation]
        else:
            print(f"Error: Operation '{attribute_or_operation}' not found")
            exit()
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    effect_resource = -10
    if target_object in constants:
        effect_resource = int(constants[target_object])
        if effect_resource == 211:
            print(f"Warning, ThxDE: Resource '{target_object}' with id 211 has been changed on DE!")
    elif target_object in trigger_map['resource']:
        effect_resource = trigger_map['resource'][target_object]
        if effect_resource == 211:
            print(f"Warning, ThxDE: Resource '{target_object}' with id 211 has been changed on DE!")
    else:
        print(f"Error: Resource '{target_object}' not found")
        exit()

    trigger = trigger_manager.add_trigger(
        f"effect_amount {effect} {target_object} {attribute_or_operation} {value}")
    if "GAIA" in effect:
        trigger.add_effect(Effect.MODIFY_RESOURCE,
                           quantity=int(value),
                           tribute_list=effect_resource,
                           source_player=Player.GAIA,
                           operation=effect_operation)
    else:
        for player in range(1, number_of_players + 1):
            trigger.add_effect(Effect.MODIFY_RESOURCE,
                               quantity=int(value),
                               tribute_list=effect_resource,
                               source_player=player,
                               operation=effect_operation)
def change_tech_cost(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "SET" in effect:
        effect_operation = Operation.SET
    elif "ADD" in effect:
        effect_operation = Operation.ADD
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    tech_id = -10
    wk_tech_id = -10
    if target_object in constants:
        wk_tech_id = constants[target_object]
        tech_id = tech_map[constants[target_object]]
        if tech_id < 0:
            print(f"ThxDE: Tech '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        wk_tech_id = str(trigger_map['object'][target_object])
        tech_id = tech_map[str(trigger_map['object'][target_object])]
        if tech_id < 0:
            print(f"ThxDE: Tech '{target_object}' on WK does not exist on DE")
            exit()
    else:
        print(f"Error: Tech '{target_object}' not found")
        exit()

    effect_resource = -10
    if "GAIA" in effect and wk_tech_id in gaia_tech_cost_mods:
        food_cost = gaia_tech_cost_mods[wk_tech_id].food
        wood_cost = gaia_tech_cost_mods[wk_tech_id].wood
        stone_cost = gaia_tech_cost_mods[wk_tech_id].stone
        gold_cost = gaia_tech_cost_mods[wk_tech_id].gold
    elif "GAIA" not in effect and wk_tech_id in tech_cost_mods:
        food_cost = tech_cost_mods[wk_tech_id][0].food
        wood_cost = tech_cost_mods[wk_tech_id][0].wood
        stone_cost = tech_cost_mods[wk_tech_id][0].stone
        gold_cost = tech_cost_mods[wk_tech_id][0].gold
    else:
        food_cost = int(techs[wk_tech_id]['food_cost'])
        wood_cost = int(techs[wk_tech_id]['wood_cost'])
        stone_cost = int(techs[wk_tech_id]['stone_cost'])
        gold_cost = int(techs[wk_tech_id]['gold_cost'])
    if attribute_or_operation in constants:
        effect_resource = int(constants[attribute_or_operation])
        if effect_resource == 0:
            food_cost = operate(effect_operation, int(value), food_cost)
        elif effect_resource == 1:
            wood_cost = operate(effect_operation, int(value), wood_cost)
        elif effect_resource == 2:
            stone_cost = operate(effect_operation, int(value), stone_cost)
        elif effect_resource == 3:
            gold_cost = operate(effect_operation, int(value), gold_cost)
        else:
            print("ThxDE: Costs of resources other than food, wood, stone and gold cannot be changed")
            exit()

    elif attribute_or_operation in trigger_map['resource']:
        effect_resource = trigger_map['resource'][attribute_or_operation]
        if effect_resource == 0:
            food_cost = operate(effect_operation, int(value), food_cost)
        elif effect_resource == 1:
            wood_cost = operate(effect_operation, int(value), wood_cost)
        elif effect_resource == 2:
            stone_cost = operate(effect_operation, int(value), stone_cost)
        elif effect_resource == 3:
            gold_cost = operate(effect_operation, int(value), gold_cost)
        else:
            print("ThxDE: Costs of resources other than food, wood, stone and gold cannot be changed")
            exit()
    else:
        print(f"Error: Resource '{attribute_or_operation}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation}")
    if "GAIA" in effect:
        if wk_tech_id not in gaia_tech_cost_mods:
            teffect = trigger.add_effect(Effect.CHANGE_TECHNOLOGY_COST)
            gaia_tech_cost_mods[wk_tech_id] = teffect
            teffect.technology = tech_id
            teffect.source_player = Player.GAIA
            teffect.food = max(food_cost, 0)
            teffect.wood = max(wood_cost, 0)
            teffect.stone = max(stone_cost, 0)
            teffect.gold = max(gold_cost, 0)
        else:
            gaia_tech_cost_mods[wk_tech_id].food = max(food_cost, 0)
            gaia_tech_cost_mods[wk_tech_id].wood = max(wood_cost, 0)
            gaia_tech_cost_mods[wk_tech_id].stone = max(stone_cost, 0)
            gaia_tech_cost_mods[wk_tech_id].gold = max(gold_cost, 0)
    else:
        tech_cost_mods[wk_tech_id] = []
        if wk_tech_id not in tech_cost_mods:
            for player in range(1, number_of_players + 1):
                teffect = trigger.add_effect(Effect.CHANGE_TECHNOLOGY_COST)
                tech_cost_mods[wk_tech_id].append(teffect)
                teffect.technology = tech_id
                teffect.source_player = player
                teffect.food = max(food_cost, 0)
                teffect.wood = max(wood_cost, 0)
                teffect.stone = max(stone_cost, 0)
                teffect.gold = max(gold_cost, 0)
        else:
            for player in range(1, number_of_players + 1):
                tech_cost_mods[wk_tech_id][player-1].food = max(food_cost, 0)
                tech_cost_mods[wk_tech_id][player-1].wood = max(wood_cost, 0)
                tech_cost_mods[wk_tech_id][player-1].stone = max(stone_cost, 0)
                tech_cost_mods[wk_tech_id][player-1].gold = max(gold_cost, 0)
def change_unit_cost(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "SET" in effect:
        effect_operation = Operation.SET
    elif "ADD" in effect:
        effect_operation = Operation.ADD
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    object_id = -10
    unit_class = -10
    wk_object_id = -10
    if target_object in constants:
        temp_id = int(constants[target_object])
        wk_object_id = str(temp_id)
        if 900 < temp_id < 1000:
            unit_class = temp_id - 900
        else:
            object_id = unit_map[str(temp_id)]
        if unit_class < 0 and object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        object_id = unit_map[str(trigger_map['object'][target_object])]
        wk_object_id = str(trigger_map['object'][target_object])
        if object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['class']:
        unit_class = trigger_map['class'][target_object] - 900
        wk_object_id = str(unit_class+900)
    else:
        print(f"Error: Object or Unit Class '{target_object}' not found")
        exit()

    effect_resource = -10
    if "GAIA" in effect and wk_object_id in gaia_unit_cost_mods:
        if 900 < int(wk_object_id) < 1000:
            food_cost = gaia_unit_cost_mods[wk_object_id][0].food
            wood_cost = gaia_unit_cost_mods[wk_object_id][0].wood
            stone_cost = gaia_unit_cost_mods[wk_object_id][0].stone
            gold_cost = gaia_unit_cost_mods[wk_object_id][0].gold
        else:
            food_cost = gaia_unit_cost_mods[wk_object_id].food
            wood_cost = gaia_unit_cost_mods[wk_object_id].wood
            stone_cost = gaia_unit_cost_mods[wk_object_id].stone
            gold_cost = gaia_unit_cost_mods[wk_object_id].gold
    elif "GAIA" not in effect and wk_object_id in unit_cost_mods:
        if 900 < int(wk_object_id) < 1000:
            food_cost = unit_cost_mods[wk_object_id][0][0].food
            wood_cost = unit_cost_mods[wk_object_id][0][0].wood
            stone_cost = unit_cost_mods[wk_object_id][0][0].stone
            gold_cost = unit_cost_mods[wk_object_id][0][0].gold
        else:
            food_cost = unit_cost_mods[wk_object_id][0].food
            wood_cost = unit_cost_mods[wk_object_id][0].wood
            stone_cost = unit_cost_mods[wk_object_id][0].stone
            gold_cost = unit_cost_mods[wk_object_id][0].gold
    else:
        food_cost = int(units[wk_object_id]['food_cost'])
        wood_cost = int(units[wk_object_id]['wood_cost'])
        stone_cost = int(units[wk_object_id]['stone_cost'])
        gold_cost = int(units[wk_object_id]['gold_cost'])
    if attribute_or_operation in constants:
        effect_resource = int(constants[attribute_or_operation])
        if effect_resource == 103:
            food_cost = operate(effect_operation, int(value), food_cost)
        elif effect_resource == 104:
            wood_cost = operate(effect_operation, int(value), wood_cost)
        elif effect_resource == 106:
            stone_cost = operate(effect_operation, int(value), stone_cost)
        elif effect_resource == 105:
            gold_cost = operate(effect_operation, int(value), gold_cost)
        else:
            print("ThxDE: Costs of resources other than food, wood, stone and gold cannot be changed")
            exit()

    elif attribute_or_operation in trigger_map['attribute']:
        effect_resource = trigger_map['attribute'][attribute_or_operation]
        if effect_resource == 103:
            food_cost = operate(effect_operation, int(value), food_cost)
        elif effect_resource == 104:
            wood_cost = operate(effect_operation, int(value), wood_cost)
        elif effect_resource == 106:
            stone_cost = operate(effect_operation, int(value), stone_cost)
        elif effect_resource == 105:
            gold_cost = operate(effect_operation, int(value), gold_cost)
        else:
            print("ThxDE: Costs of resources other than food, wood, stone and gold cannot be changed")
            exit()
    else:
        print(f"Error: Resource '{attribute_or_operation}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation}")
    if "GAIA" in effect:
        if wk_object_id not in gaia_unit_cost_mods:
            if unit_class >= 0:
                gaia_unit_cost_mods[wk_object_id] = []
                for unit in units:
                    if int(units[unit]['class']) == unit_class:
                        teffect = trigger.add_effect(Effect.CHANGE_OBJECT_COST)
                        gaia_unit_cost_mods[wk_object_id].append(teffect)
                        teffect.object_list_unit_id = unit_map[unit]
                        teffect.source_player = Player.GAIA
                        teffect.food = max(food_cost, 0)
                        teffect.wood = max(wood_cost, 0)
                        teffect.stone = max(stone_cost, 0)
                        teffect.gold = max(gold_cost, 0)
            elif object_id >= 0:
                teffect = trigger.add_effect(Effect.CHANGE_OBJECT_COST)
                gaia_unit_cost_mods[wk_object_id] = teffect
                teffect.object_list_unit_id = object_id
                teffect.source_player = Player.GAIA
                teffect.food = max(food_cost, 0)
                teffect.wood = max(wood_cost, 0)
                teffect.stone = max(stone_cost, 0)
                teffect.gold = max(gold_cost, 0)
            else:
                print(f"Error: Object or Unit Class '{target_object}' not found")
                exit()
        else:
            if unit_class >= 0:
                for teffect in gaia_unit_cost_mods[wk_object_id]:
                    teffect.food = max(food_cost, 0)
                    teffect.wood = max(wood_cost, 0)
                    teffect.stone = max(stone_cost, 0)
                    teffect.gold = max(gold_cost, 0)
            elif object_id >= 0:
                gaia_unit_cost_mods[wk_object_id].food = max(food_cost, 0)
                gaia_unit_cost_mods[wk_object_id].wood = max(wood_cost, 0)
                gaia_unit_cost_mods[wk_object_id].stone = max(stone_cost, 0)
                gaia_unit_cost_mods[wk_object_id].gold = max(gold_cost, 0)
            else:
                print(f"Error: Object or Unit Class '{target_object}' not found")
                exit()
    else:
        if wk_object_id not in unit_cost_mods:
            unit_cost_mods[wk_object_id] = []
            if unit_class >= 0:
                for player in range(1, number_of_players + 1):
                    unit_cost_mods[wk_object_id].append([])
                    for unit in units:
                        if int(units[unit]['class']) == unit_class:
                            teffect = trigger.add_effect(Effect.CHANGE_OBJECT_COST)
                            gaia_unit_cost_mods[wk_object_id][player-1].append(teffect)
                            teffect.object_list_unit_id = unit_map[int(unit)]
                            teffect.source_player = player
                            teffect.food = max(food_cost, 0)
                            teffect.wood = max(wood_cost, 0)
                            teffect.stone = max(stone_cost, 0)
                            teffect.gold = max(gold_cost, 0)
            elif object_id >= 0:
                for player in range(1, number_of_players + 1):
                    teffect = trigger.add_effect(Effect.CHANGE_OBJECT_COST)
                    unit_cost_mods[wk_object_id].append(teffect)
                    teffect.object_list_unit_id = object_id
                    teffect.source_player = player
                    teffect.food = max(food_cost, 0)
                    teffect.wood = max(wood_cost, 0)
                    teffect.stone = max(stone_cost, 0)
                    teffect.gold = max(gold_cost, 0)
            else:
                print(f"Error: Object or Unit Class '{target_object}' not found")
                exit()
        else:
            if unit_class >= 0:
                for player in range(1, number_of_players + 1):
                    for teffect in gaia_unit_cost_mods[wk_object_id][player-1]:
                        teffect.food = max(food_cost, 0)
                        teffect.wood = max(wood_cost, 0)
                        teffect.stone = max(stone_cost, 0)
                        teffect.gold = max(gold_cost, 0)
            elif object_id >= 0:
                for player in range(1, number_of_players + 1):
                    unit_cost_mods[wk_object_id][player-1].food = max(food_cost, 0)
                    unit_cost_mods[wk_object_id][player-1].wood = max(wood_cost, 0)
                    unit_cost_mods[wk_object_id][player-1].stone = max(stone_cost, 0)
                    unit_cost_mods[wk_object_id][player-1].gold = max(gold_cost, 0)
            else:
                print(f"Error: Object or Unit Class '{target_object}' not found")
                exit()
def change_tech_time(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "MOD" in effect:
        if attribute_or_operation in constants:
            effect_operation = int(constants[attribute_or_operation])
            if effect_operation == 0:
                effect_operation = 1
            elif effect_operation == 1:
                effect_operation = 2
            else:
                print(f"Error: Operation '{attribute_or_operation}' not found")
                exit()
        elif attribute_or_operation in trigger_map['operation']:
            effect_operation = trigger_map['operation'][attribute_or_operation]
        else:
            print(f"Error: Operation '{attribute_or_operation}' not found")
            exit()
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    tech_id = -10
    wk_tech_id = -10
    if target_object in constants:
        wk_tech_id = constants[target_object]
        tech_id = tech_map[constants[target_object]]
        if tech_id < 0:
            print(f"ThxDE: Tech '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        wk_tech_id = str(trigger_map['object'][target_object])
        tech_id = tech_map[str(trigger_map['object'][target_object])]
        if tech_id < 0:
            print(f"ThxDE: Tech '{target_object}' on WK does not exist on DE")
            exit()
    else:
        print(f"Error: Tech '{target_object}' not found")
        exit()

    if "GAIA" in effect and wk_tech_id in gaia_tech_time_mods:
        tech_time = gaia_tech_time_mods[wk_tech_id].quantity
    elif "GAIA" not in effect and wk_tech_id in tech_time_mods:
        tech_time = tech_time_mods[wk_tech_id][0].quantity
    else:
        tech_time = int(techs[wk_tech_id]['train_time'])

    tech_time = operate(effect_operation, int(value), tech_time)

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation}")
    if "GAIA" in effect:
        if wk_tech_id not in gaia_tech_time_mods:
            teffect = trigger.add_effect(Effect.CHANGE_TECHNOLOGY_RESEARCH_TIME)
            gaia_tech_time_mods[wk_tech_id] = teffect
            teffect.technology = tech_id
            teffect.source_player = Player.GAIA
            teffect.quantity = max(tech_time, 0)
        else:
            gaia_tech_time_mods[wk_tech_id].quantity = max(tech_time, 0)
    else:
        tech_time_mods[wk_tech_id] = []
        if wk_tech_id not in tech_time_mods:
            for player in range(1, number_of_players + 1):
                teffect = trigger.add_effect(Effect.CHANGE_TECHNOLOGY_RESEARCH_TIME)
                tech_time_mods[wk_tech_id].append(teffect)
                teffect.technology = tech_id
                teffect.source_player = player
                teffect.quantity = max(tech_time, 0)
        else:
            for player in range(1, number_of_players + 1):
                tech_time_mods[wk_tech_id][player-1].quantity = max(tech_time, 0)
def enable_object(effect, target_object, attribute_or_operation):
    effect_enable = -10
    if attribute_or_operation in constants:
        effect_enable = int(constants[attribute_or_operation])
        if not (effect_enable == 1 or effect_enable == 0):
            print(f"Error: Operation '{attribute_or_operation}' of id '{effect_enable}' is not supported in '{effect}'")
            exit()
    elif attribute_or_operation in trigger_map['operation']:
        effect_enable = int(trigger_map['operation'][attribute_or_operation])
        if not (effect_enable == 1 or effect_enable == 0):
            print(f"Error: Operation '{attribute_or_operation}' of id '{effect_enable}' is not supported in '{effect}'")
            exit()
    else:
        print(f"Error: Operation '{attribute_or_operation}' not found")
        exit()
    object_id = -10
    unit_class = -10
    if target_object in constants:
        temp_id = int(constants[target_object])
        if 900 < temp_id < 1000:
            unit_class = temp_id - 900
        else:
            object_id = unit_map[str(temp_id)]
        if unit_class < 0 and object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        object_id = unit_map[str(trigger_map['object'][target_object])]
        if object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['class']:
        unit_class = trigger_map['class'][target_object] - 900
    else:
        print(f"Error: Object or Unit Class '{target_object}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation}")
    if "GAIA" in effect:
        if unit_class >= 0:
            for unit in units:
                if units[unit]['class'] == unit_class:
                    teffect = trigger.add_effect(Effect.ENABLE_DISABLE_OBJECT)
                    teffect.object_list_unit_id = unit_map[unit]
                    teffect.item_id = unit_map[unit]
                    teffect.source_player = Player.GAIA
                    teffect.enabled_or_victory = effect_enable
        elif object_id >= 0:
            teffect = trigger.add_effect(Effect.ENABLE_DISABLE_OBJECT)
            teffect.object_list_unit_id = object_id
            teffect.item_id = object_id
            teffect.source_player = Player.GAIA
            teffect.enabled_or_victory = effect_enable
        else:
            print(f"Error: Object or Unit Class '{target_object}' not found")
            exit()
    else:
        if unit_class >= 0:
            for unit in units:
                if units[unit]['class'] == unit_class:
                    for player in range(1, number_of_players+1):
                        teffect = trigger.add_effect(Effect.ENABLE_DISABLE_OBJECT)
                        teffect.object_list_unit_id = unit_map[unit]
                        teffect.item_id = unit_map[unit]
                        teffect.source_player = player
                        teffect.enabled_or_victory = effect_enable
        elif object_id >= 0:
            for player in range(1, number_of_players + 1):
                teffect = trigger.add_effect(Effect.ENABLE_DISABLE_OBJECT)
                teffect.object_list_unit_id = object_id
                teffect.item_id = object_id
                teffect.source_player = player
                teffect.enabled_or_victory = effect_enable
        else:
            print(f"Error: Object or Unit Class '{target_object}' not found")
            exit()
def replace_object(effect, target_object, attribute_or_operation):
    object_id = -10
    unit_class = -10
    if target_object in constants:
        temp_id = int(constants[target_object])
        if 900 < temp_id < 1000:
            unit_class = temp_id - 900
        else:
            object_id = unit_map[str(temp_id)]
        if unit_class < 0 and object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        object_id = unit_map[str(trigger_map['object'][target_object])]
        if object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['class']:
        unit_class = trigger_map['class'][target_object] - 900
    else:
        print(f"Error: Object or Unit Class '{target_object}' not found")
        exit()

    replace_object_id = -10
    if attribute_or_operation in constants:
        temp_id = int(constants[attribute_or_operation])
        if 900 < temp_id < 1000:
            print(f"Error: You cannot upgrade unit to a class '{attribute_or_operation}'")
            exit()
        else:
            replace_object_id = unit_map[str(temp_id)]
        if replace_object_id < 0:
            print(f"ThxDE: Object '{attribute_or_operation}' on WK does not exist on DE")
            exit()
    elif attribute_or_operation in trigger_map['object']:
        replace_object_id = unit_map[str(trigger_map['object'][attribute_or_operation])]
        if replace_object_id < 0:
            print(f"ThxDE: Object '{attribute_or_operation}' on WK does not exist on DE")
            exit()
    elif attribute_or_operation in trigger_map['class']:
        print(f"Error: You cannot upgrade unit to a class '{attribute_or_operation}'")
        exit()
    else:
        print(f"Error: Object or Unit Class '{attribute_or_operation}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation}")
    if "GAIA" in effect:
        if unit_class >= 0:
            for unit in units:
                if units[unit]['class'] == unit_class:
                    teffect = trigger.add_effect(Effect.REPLACE_OBJECT)
                    teffect.object_list_unit_id = unit_map[unit]
                    teffect.object_list_unit_id_2 = replace_object_id
                    teffect.source_player = Player.GAIA
                    teffect.target_player = Player.GAIA
        elif object_id >= 0:
            teffect = trigger.add_effect(Effect.REPLACE_OBJECT)
            teffect.object_list_unit_id = object_id
            teffect.object_list_unit_id_2 = replace_object_id
            teffect.source_player = Player.GAIA
            teffect.target_player = Player.GAIA
        else:
            print(f"Error: Object or Unit Class '{target_object}' not found")
            exit()
    else:
        if unit_class >= 0:
            for unit in units:
                if units[unit]['class'] == unit_class:
                    for player in range(1, number_of_players+1):
                        teffect = trigger.add_effect(Effect.REPLACE_OBJECT)
                        teffect.object_list_unit_id = unit_map[unit]
                        teffect.object_list_unit_id_2 = replace_object_id
                        teffect.source_player = player
                        teffect.target_player = player
        elif object_id >= 0:
            for player in range(1, number_of_players + 1):
                teffect = trigger.add_effect(Effect.REPLACE_OBJECT)
                teffect.object_list_unit_id = object_id
                teffect.object_list_unit_id_2 = replace_object_id
                teffect.source_player = player
                teffect.target_player = player
        else:
            print(f"Error: Object or Unit Class '{target_object}' not found")
            exit()
def disable_enable_tech(effect, target_object, attribute_or_operation):
    effect_enable = -10
    if attribute_or_operation in constants:
        effect_enable = int(constants[attribute_or_operation])
        if not (effect_enable == 1 or effect_enable == 0):
            if effect_enable == 2:
                print("Error: The functionality of ATTR_FORCE is unknown, you can help to make this tool better by"+
                      " notifying me at Alian713#0069 on discord, thank you!")
                exit()
            print(f"Error: Operation '{attribute_or_operation}' of id '{effect_enable}' is not supported in '{effect}'")
            exit()
    elif attribute_or_operation in trigger_map['operation']:
        effect_enable = int(trigger_map['operation'][attribute_or_operation])
        if not (effect_enable == 1 or effect_enable == 0):
            if effect_enable == 2:
                print("Error: The functionality of ATTR_FORCE is unknown, you can help to make this tool better by"+
                      " notifying me at Alian713#0069 on discord, thank you!")
                exit()
            print(f"Error: Operation '{attribute_or_operation}' of id '{effect_enable}' is not supported in '{effect}'")
            exit()
    else:
        print(f"Error: Operation '{attribute_or_operation}' not found")
        exit()
    tech_id = -10
    if target_object in constants:
        tech_id = tech_map[constants[target_object]]
        if tech_id < 0:
            print(f"ThxDE: Tech '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        tech_id = tech_map[str(trigger_map['object'][target_object])]
        if tech_id < 0:
            print(f"ThxDE: Tech '{target_object}' on WK does not exist on DE")
            exit()
    else:
        print(f"Error: Tech '{target_object}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation}")
    if "GAIA" in effect:
        teffect = trigger.add_effect(Effect.ENABLE_DISABLE_TECHNOLOGY)
        teffect.technology = tech_id
        teffect.item_id = tech_id
        teffect.source_player = Player.GAIA
        teffect.enabled_or_victory = effect_enable
    else:
        for player in range(1, number_of_players+1):
            teffect = trigger.add_effect(Effect.ENABLE_DISABLE_TECHNOLOGY)
            teffect.technology = tech_id
            teffect.item_id = tech_id
            teffect.source_player = player
            teffect.enabled_or_victory = effect_enable

def ep_modify_attribute(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "SET" in effect:
        effect_operation = Operation.SET
    elif "ADD" in effect:
        effect_operation = Operation.ADD
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    object_id = -10
    unit_class = -10
    if target_object in constants:
        temp_id = int(constants[target_object])
        if 900 < temp_id < 1000:
            unit_class = temp_id - 900
        else:
            object_id = unit_map[str(temp_id)]
        if unit_class < 0 and object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['object']:
        object_id = unit_map[str(trigger_map['object'][target_object])]
        if object_id < 0:
            print(f"ThxDE: Object '{target_object}' on WK does not exist on DE")
            exit()
    elif target_object in trigger_map['class']:
        unit_class = trigger_map['class'][target_object] - 900
    else:
        print(f"Error: Object or Unit Class '{target_object}' not found")
        exit()

    effect_attribute = -10
    if attribute_or_operation in constants:
        effect_attribute = int(constants[attribute_or_operation])
        for attribute in trigger_map['attribute']:
            temp_id = trigger_map['attribute'][attribute]
            if temp_id < 0 and abs(temp_id) == effect_attribute:
                print(f"ThxDE: Attribute '{abs(temp_id)}' is not supported on DE")
                exit()
            if (attribute == "ATTR_PROJECTILE_ID" or \
                attribute == "ATTR_TRAIN_LOCATION" or \
                attribute == "ATTR_DEAD_ID") and temp_id == effect_attribute:
                if unit_map[value] < 0:
                    print(f"ThxDE: An Equivalent for Object '{value}' on WK does not exist on DE")
                    exit()
                else:
                    value = unit_map[value]
    elif attribute_or_operation in trigger_map['attribute']:
        if trigger_map['attribute'][attribute_or_operation] >= 0:
            if attribute_or_operation == "ATTR_PROJECTILE_ID" or \
                    attribute_or_operation == "ATTR_TRAIN_LOCATION" or \
                    attribute_or_operation == "ATTR_DEAD_ID":
                if unit_map[value] < 0:
                    print(f"ThxDE: An Equivalent for Object '{value}' on WK does not exist on DE")
                    exit()
                else:
                    value = unit_map[value]
            effect_attribute = trigger_map['attribute'][attribute_or_operation]
        else:
            print(f"ThxDE: Attribute '{attribute_or_operation}' is not supported on DE")
            exit()
    else:
        print(f"Error: Attribute '{attribute_or_operation}' not found")
        exit()

    trigger = trigger_manager.add_trigger(f"effect_amount {effect} {target_object} {attribute_or_operation} {value}")
    if "GAIA" in effect:
        if unit_class >= 0:
            for unit in units:
                if int(units[unit]['class']) == unit_class:
                    if unit_map[unit] >= 0:
                        if effect_operation == Operation.ADD:
                            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                               quantity=100,
                                               object_list_unit_id=unit_map[unit],
                                               source_player=Player.GAIA,
                                               item_id=unit_map[unit],
                                               operation=Operation.MULTIPLY,
                                               object_attributes=effect_attribute)

                        trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                           quantity=int(value),
                                           object_list_unit_id=unit_map[unit],
                                           source_player=Player.GAIA,
                                           item_id=unit_map[unit],
                                           operation=effect_operation,
                                           object_attributes=effect_attribute)

                        trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                           quantity=100,
                                           object_list_unit_id=unit_map[unit],
                                           source_player=Player.GAIA,
                                           item_id=unit_map[unit],
                                           operation=Operation.DIVIDE,
                                           object_attributes=effect_attribute)
                    else:
                        print(f"Warning, ThxDE: Unit ID '{unit}' of class '{unit_class}' " +
                              f"on WK does not exist on DE, skipping unit!")
        else:
            if effect_operation == Operation.ADD:
                trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                   quantity=int(value),
                                   object_list_unit_id=object_id,
                                   source_player=Player.GAIA,
                                   item_id=object_id,
                                   operation=effect_operation,
                                   object_attributes=effect_attribute)

            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                               quantity=int(value),
                               object_list_unit_id=object_id,
                               source_player=Player.GAIA,
                               item_id=object_id,
                               operation=effect_operation,
                               object_attributes=effect_attribute)

            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                               quantity=100,
                               object_list_unit_id=object_id,
                               source_player=Player.GAIA,
                               item_id=object_id,
                               operation=Operation.DIVIDE,
                               object_attributes=effect_attribute)
    else:
        if unit_class >= 0:
            for unit in units:
                if int(units[unit]['class']) == unit_class:
                    if unit_map[unit] >= 0:
                        for player in range(1, number_of_players + 1):
                            if effect_operation == Operation.ADD:
                                trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                                   quantity=100,
                                                   object_list_unit_id=unit_map[unit],
                                                   source_player=player,
                                                   item_id=unit_map[unit],
                                                   operation=Operation.MULTIPLY,
                                                   object_attributes=effect_attribute)

                            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                               quantity=int(value),
                                               object_list_unit_id=unit_map[unit],
                                               source_player=player,
                                               item_id=unit_map[unit],
                                               operation=effect_operation,
                                               object_attributes=effect_attribute)

                            trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                               quantity=100,
                                               object_list_unit_id=unit_map[unit],
                                               source_player=player,
                                               item_id=unit_map[unit],
                                               operation=Operation.DIVIDE,
                                               object_attributes=effect_attribute)
                    else:
                        print(f"Warning, ThxDE: Unit ID '{unit}' of class '{unit_class}' " +
                              f"on WK does not exist on DE, skipping unit!")
        else:
            for player in range(1, number_of_players + 1):
                if effect_operation == Operation.ADD:
                    trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                       quantity=int(value),
                                       object_list_unit_id=object_id,
                                       source_player=player,
                                       item_id=object_id,
                                       operation=effect_operation,
                                       object_attributes=effect_attribute)

                trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                   quantity=int(value),
                                   object_list_unit_id=object_id,
                                   source_player=player,
                                   item_id=object_id,
                                   operation=effect_operation,
                                   object_attributes=effect_attribute)

                trigger.add_effect(Effect.MODIFY_ATTRIBUTE,
                                   quantity=100,
                                   object_list_unit_id=object_id,
                                   source_player=player,
                                   item_id=object_id,
                                   operation=Operation.DIVIDE,
                                   object_attributes=effect_attribute)
def ep_modify_resource(effect, target_object, attribute_or_operation, value):
    effect_operation = -10
    if "MOD" in effect:
        if attribute_or_operation in constants:
            effect_operation = int(constants[attribute_or_operation])
            if effect_operation == 0:
                effect_operation = 1
            elif effect_operation == 1:
                effect_operation = 2
            else:
                print(f"Error: Operation '{attribute_or_operation}' not found")
                exit()
        elif attribute_or_operation in trigger_map['operation']:
            effect_operation = trigger_map['operation'][attribute_or_operation]
        else:
            print(f"Error: Operation '{attribute_or_operation}' not found")
            exit()
    elif "MUL" in effect:
        effect_operation = Operation.MULTIPLY
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()

    effect_resource = -10
    if target_object in constants:
        effect_resource = int(constants[target_object])
        if effect_resource == 211:
            print(f"Warning, ThxDE: Resource '{target_object}' with id 211 has been changed on DE!")
    elif target_object in trigger_map['resource']:
        effect_resource = trigger_map['resource'][target_object]
        if effect_resource == 211:
            print(f"Warning, ThxDE: Resource '{target_object}' with id 211 has been changed on DE!")
    else:
        print(f"Error: Resource '{target_object}' not found")
        exit()

    trigger = trigger_manager.add_trigger(
        f"effect_amount {effect} {target_object} {attribute_or_operation} {value}")
    if "GAIA" in effect:
        if effect_operation == Operation.ADD:
            trigger.add_effect(Effect.MODIFY_RESOURCE,
                               quantity=100,
                               tribute_list=effect_resource,
                               source_player=Player.GAIA,
                               operation=Operation.MULTIPLY)
        trigger.add_effect(Effect.MODIFY_RESOURCE,
                           quantity=int(value),
                           tribute_list=effect_resource,
                           source_player=Player.GAIA,
                           operation=effect_operation)
        trigger.add_effect(Effect.MODIFY_RESOURCE,
                           quantity=100,
                           tribute_list=effect_resource,
                           source_player=Player.GAIA,
                           operation=Operation.DIVIDE)
    else:
        for player in range(1, number_of_players + 1):
            if effect_operation == Operation.ADD:
                trigger.add_effect(Effect.MODIFY_RESOURCE,
                                   quantity=100,
                                   tribute_list=effect_resource,
                                   source_player=player,
                                   operation=Operation.MULTIPLY)
            trigger.add_effect(Effect.MODIFY_RESOURCE,
                               quantity=int(value),
                               tribute_list=effect_resource,
                               source_player=player,
                               operation=effect_operation)
            trigger.add_effect(Effect.MODIFY_RESOURCE,
                               quantity=100,
                               tribute_list=effect_resource,
                               source_player=player,
                               operation=Operation.DIVIDE)

def write_triggers_from_effect_amount_command(effect_amount):
    effect = effect_amount['effect']
    target_object = effect_amount['target_object']
    attribute_or_operation = effect_amount['attribute_or_operation']
    value = effect_amount['value']

    found_effect = False
    if effect in constants:
        effect_id = int(constants[effect])
        for eft in trigger_map['effect']:
            if trigger_map['effect'][eft] == effect_id:
                effect = eft
                found_effect = True
                break
        if not found_effect:
            print(f"Error: Effect '{effect}' with id '{effect_id}' not found")
            exit()
    if effect in trigger_map['effect']:
        if effect.endswith("ATTRIBUTE"):
            found_attr = False
            if attribute_or_operation in constants:
                attr_id = int(constants[attribute_or_operation])
                for attr in trigger_map['attribute']:
                    if trigger_map['attribute'][attr] == attr_id:
                        attribute_or_operation = attr
                        found_attr = True
                        break
                if not found_attr:
                    print(f"Error: Attribute '{attribute_or_operation}' with id '{attr_id}' not found")
                    exit()
            if "COST" in attribute_or_operation:
                change_unit_cost(effect, target_object, attribute_or_operation, value)
            else:
                modify_attribute(effect, target_object, attribute_or_operation, value)
        elif effect.endswith("RESOURCE"):
            modify_resource(effect, target_object, attribute_or_operation, value)
        elif effect.endswith("TECH_COST"):
            change_tech_cost(effect, target_object, attribute_or_operation, value)
        elif effect.endswith("TECH_TIME"):
            change_tech_time(effect, target_object, attribute_or_operation, value)
        elif effect == "ENABLE_OBJECT":
            enable_object(effect, target_object, attribute_or_operation)
        elif effect == "UPGRADE_UNIT":
            replace_object(effect, target_object, attribute_or_operation)
        elif effect == "ENABLE_TECH":
            disable_enable_tech(effect, target_object, attribute_or_operation)
        elif effect == "DISABLE_TECH":
            disable_enable_tech(effect, target_object, attribute_or_operation)
        elif effect == "MODIFY_TECH":
            found_attr = False
            if attribute_or_operation in constants:
                attr_id = int(constants[attribute_or_operation])
                for attr in trigger_map['mod_tech_operation']:
                    if trigger_map['mod_tech_operation'][attr] == attr_id:
                        attribute_or_operation = attr
                        found_attr = True
                        break
                if not found_attr:
                    print(f"Error: Modify Tech Operation '{attribute_or_operation}' with id '{attr_id}' not found")
                    exit()
            if "SET_TIME" in attribute_or_operation:
                change_tech_time("MOD_TECH_TIME", target_object, "ATTR_SET", value)
            elif "ADD_TIME" in attribute_or_operation:
                change_tech_time("MOD_TECH_TIME", target_object, "ATTR_ADD", value)
            elif "SET" in attribute_or_operation and "COST" in attribute_or_operation:
                change_tech_cost("SET_TECH_COST", target_object,
                                 "AMOUNT_"+attribute_or_operation.replace("SET_", "").replace("_COST", ""), value)
            elif "ADD" in attribute_or_operation and "COST" in attribute_or_operation:
                change_tech_cost("ADD_TECH_COST", target_object,
                                 "AMOUNT_"+attribute_or_operation.replace("SET_", "").replace("_COST", ""), value)

        else:
            print("Error: The functionality of SET_PLAYER_DATA is unknown, you can help to make this tool better by" +
                  " notifying me at Alian713#0069 on discord, thank you!")
            exit()
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()
def write_triggers_from_effect_percent_command(effect_percent):
    effect = effect_percent['effect']
    target_object = effect_percent['target_object']
    attribute_or_operation = effect_percent['attribute_or_operation']
    value = effect_percent['value']

    found_effect = False
    if effect in constants:
        effect_id = int(constants[effect])
        for eft in trigger_map['effect']:
            if trigger_map['effect'][eft] == effect_id:
                effect = eft
                found_effect = True
                break
        if not found_effect:
            print(f"Error: Effect '{effect}' with id '{effect_id}' not found")
            exit()
    if effect in trigger_map['effect']:
        if effect.endswith("ATTRIBUTE"):
            found_attr = False
            if attribute_or_operation in constants:
                attr_id = int(constants[attribute_or_operation])
                for attr in trigger_map['attribute']:
                    if trigger_map['attribute'][attr] == attr_id:
                        attribute_or_operation = attr
                        found_attr = True
                        break
                if not found_attr:
                    print(f"Error: Attribute '{attribute_or_operation}' with id '{attr_id}' not found")
                    exit()
            if "COST" in attribute_or_operation:
                print(f"Error: Use effect_amount to change cost for {target_object}")
                exit()
            else:
                ep_modify_attribute(effect, target_object, attribute_or_operation, value)
        elif effect.endswith("RESOURCE"):
            ep_modify_resource(effect, target_object, attribute_or_operation, value)

        else:
            print(f"Error: Effect '{effect}' can only be used with effect_amount")
            exit()
    else:
        print(f"Error: Effect '{effect}' not found")
        exit()
def write_triggers_from_guard_state_command(guard_state):
    unit_or_class = guard_state['unit_or_class']
    resource = guard_state['resource']
    resource_delta = int(guard_state['resource_delta'])
    guard_flags = int(guard_state['guard_flags'])

    object_id = -10
    unit_class = -10
    if unit_or_class in constants:
        temp_id = int(constants[unit_or_class])
        if 900 < temp_id < 1000:
            unit_class = temp_id - 900
        else:
            object_id = unit_map[str(temp_id)]
        if unit_class < 0 and object_id < 0:
            print(f"ThxDE: Object '{unit_or_class}' on WK does not exist on DE")
            exit()
    elif unit_or_class in trigger_map['object']:
        object_id = unit_map[str(trigger_map['object'][unit_or_class])]
        if object_id < 0:
            print(f"ThxDE: Object '{unit_or_class}' on WK does not exist on DE")
            exit()
    elif unit_or_class in trigger_map['class']:
        unit_class = trigger_map['class'][unit_or_class] - 900
    else:
        print(f"Error: Object or Unit Class '{unit_or_class}' not found")
        exit()

    effect_resource = -10
    if resource in constants:
        effect_resource = int(constants[resource])
        if effect_resource == 211:
            print(f"Warning, ThxDE: Resource '{resource}' with id 211 has been changed on DE!")
    elif resource in trigger_map['resource']:
        effect_resource = trigger_map['resource'][resource]
        if effect_resource == 211:
            print(f"Warning, ThxDE: Resource '{resource}' with id 211 has been changed on DE!")
    else:
        print(f"Error: Resource '{resource}' not found")
        exit()

    guard_flag_victory = False
    guard_flag_resource = False
    guard_flag_inverse = False
    if guard_flags >= 4:
        guard_flag_inverse = True
        guard_flags -= 4
    if guard_flags >= 2:
        guard_flag_resource = True
        guard_flags -= 2
    if guard_flags >= 1:
        guard_flag_victory = True
        guard_flags -= 1

    for player in range(1, number_of_players+1):
        if guard_flag_victory:
            trigger = trigger_manager.add_trigger(f"guard_state {unit_or_class} {resource} {resource_delta}" +
                                                  f"{guard_flags} p{player}")
            if guard_flag_inverse:
                condition = trigger.add_condition(Condition.OWN_OBJECTS)
                condition.amount_or_quantity = 1
            else:
                condition = trigger.add_condition(Condition.OWN_FEWER_OBJECTS)
                condition.amount_or_quantity = 0
            condition.source_player = player
            if object_id >= 0:
                condition.object_list = object_id
            if unit_class >= 0:
                condition.object_group = unit_class
            effect = trigger.add_effect(Effect.DECLARE_VICTORY)
            effect.enabled_or_victory = 0
            effect.source_player = player
        if guard_flag_resource:
            trigger = trigger_manager.add_trigger(f"guard_state {unit_or_class} {resource} {resource_delta}" +
                                                  f"{guard_flags} p{player}")
            trigger.looping = 1
            if not guard_flag_inverse:
                condition = trigger.add_condition(Condition.OWN_OBJECTS)
                condition.amount_or_quantity = 1
            else:
                condition = trigger.add_condition(Condition.OWN_FEWER_OBJECTS)
                condition.amount_or_quantity = 0
            condition.source_player = player
            trigger.add_condition(Condition.TIMER, timer=1)
            if object_id >= 0:
                condition.object_list = object_id
            if unit_class >= 0:
                condition.object_group = unit_class

            effect = trigger.add_effect(Effect.MODIFY_RESOURCE)
            effect.quantity = 100
            effect.tribute_list = effect_resource
            effect.operation = Operation.MULTIPLY
            effect.source_player = player

            effect = trigger.add_effect(Effect.MODIFY_RESOURCE)
            effect.quantity = resource_delta
            effect.tribute_list = effect_resource
            effect.operation = Operation.ADD
            effect.source_player = player

            effect = trigger.add_effect(Effect.MODIFY_RESOURCE)
            effect.quantity = 100
            effect.tribute_list = effect_resource
            effect.operation = Operation.DIVIDE
            effect.source_player = player



path = "../"


for number_of_players in range(1, 9):
    tech_cost_mods = {}
    unit_cost_mods = {}
    gaia_tech_cost_mods = {}
    gaia_unit_cost_mods = {}
    tech_time_mods = {}
    gaia_tech_time_mods = {}
    scenario = AoE2Scenario.from_file(path+f"Parser Bases/Base {number_of_players}p.aoe2scenario", log_reading=False)
    trigger_manager = scenario.trigger_manager

    for cmd in effect_amount_commands:
        write_triggers_from_effect_amount_command(cmd)

    for cmd in effect_percent_commands:
        write_triggers_from_effect_percent_command(cmd)

    for cmd in guard_state_commands:
        write_triggers_from_guard_state_command(cmd)

    scenario.write_to_file(path+map_name+f" {number_of_players}p.aoe2scenario", log_writing=False)