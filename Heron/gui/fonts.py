

from dearpygui import dearpygui as dpg
from os.path import join
import os
from pathlib import Path
import json

heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
available_fonts = [font for dirs in os.walk(os.path.join(heron_path, 'resources', 'fonts')) for font in dirs[2]]
registered_dpg_fonts = {}


settings_file = join(heron_path, 'settings.json')
with open(settings_file, 'r') as sf:
    settings_dict: dict = json.load(sf)

main_font_name = settings_dict['Appearance']['Editor Font']['Font']
main_font_size = settings_dict['Appearance']['Editor Font']['Size']

italic_font = os.path.join(heron_path, 'resources', 'fonts', 'Figtree-LightItalic.ttf')
bold_font = os.path.join(heron_path, 'resources', 'fonts', 'Figtree-SemiBold.ttf')
font_registry: int
italic_font_id: int


def add_to_registry():
    global font_registry
    global italic_font_id

    with dpg.font_registry() as font_registry:
        italic_font_id = dpg.add_font(italic_font, int(0.9 * main_font_size))
        dpg.add_font(bold_font, int(1.2 * main_font_size))
        default = dpg.add_font(os.path.join(heron_path, 'resources', 'fonts', main_font_name), main_font_size)

    dpg.bind_font(default)


