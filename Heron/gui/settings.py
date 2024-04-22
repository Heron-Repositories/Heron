
from dearpygui import dearpygui as dpg
from os.path import dirname, join
import os
from pathlib import Path
import json
from Heron import general_utils as gu
import numpy as np

heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
with open(join(heron_path, 'settings.json'), 'r') as settings_file:
    settings_dict = json.load(settings_file)

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