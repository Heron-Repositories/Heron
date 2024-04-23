
from dearpygui import dearpygui as dpg
from os.path import join
import os
from pathlib import Path
import json
import numpy as np

heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
settings_file = join(heron_path, 'settings.json')
if not os.path.isfile(settings_file):
    with open(join(heron_path, 'settings_default.json'), 'r') as sfd:
        settings_dict = json.load(sfd)
        with open(join(heron_path, 'settings.json'), 'w') as sf:
            json.dump(settings_dict, sf, indent=4)
else:
    with open(join(heron_path, 'settings.json'), 'r') as sf:
        settings_dict = json.load(sf)

aliases_list = []


def kill_existing_aliases():
    global aliases_list

    for alias in aliases_list:
        try:
            dpg.remove_alias(alias)
        except:
            pass
    aliases_list = []

    try:
        dpg.remove_alias('add_param_cross')
        dpg.remove_alias('add_param_txt')
    except:
        pass


def on_close_main(sender, app_data, user_data):
    node_name_id = user_data
    kill_existing_aliases(node_name_id)


def on_close_main_with_buttons(sender, app_data, user_data):
    global node_win
    dpg.delete_item(node_win)


def start():
    tag = 'type_selector'
    with dpg.window(label='Node Type Selector', tag=tag, width=380, height=100, pos=[500, 200], no_collapse=True):
        pass