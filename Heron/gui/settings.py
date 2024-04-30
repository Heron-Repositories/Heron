
from dearpygui import dearpygui as dpg
from os.path import join
import os
from pathlib import Path
import json

from Heron.gui.fdialog import FileDialog

heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
settings_file = join(heron_path, 'settings.json')
if not os.path.isfile(settings_file):
    with open(join(heron_path, 'settings_default.json'), 'r') as sfd:
        settings_dict: dict = json.load(sfd)
        with open(join(heron_path, 'settings.json'), 'w') as sf:
            json.dump(settings_dict, sf, indent=4)
else:
    with open(join(heron_path, 'settings.json'), 'r') as sf:
        settings_dict:dict = json.load(sf)

aliases_list = []


def save_settings():
    with open(settings_file, 'w') as sf:
        json.dump(settings_dict, sf, indent=4)


def kill_existing_aliases():
    global aliases_list

    for alias in aliases_list:
        try:
            dpg.remove_alias(alias)
        except:
            pass
    aliases_list = []


def on_close_main(sender, app_data, user_data):
    global node_win
    kill_existing_aliases()
    dpg.delete_item(node_win)


def on_close_main_with_buttons(sender, app_data, user_data):
    global node_win
    kill_existing_aliases()
    dpg.delete_item(node_win)


def on_browse(sender, app_data, user_data):
    input_txt = user_data[0]
    dirs_only = user_data[1]
    setting_keys = user_data[2]

    def on_path_selected(files_selected):
        file = files_selected[0]
        dpg.set_value(input_txt, file)
        if len(setting_keys) == 2:
            settings_dict[setting_keys[0]][setting_keys[1]] = dpg.get_value(input_txt)
        elif len(setting_keys) == 3:
            settings_dict[setting_keys[0]][setting_keys[1]][setting_keys[2]] = dpg.get_value(input_txt)
        save_settings()

    file_dialog = FileDialog(title=f'Select {"folder" if dirs_only else "folder"}', show_dir_size=False,
                             modal=False, allow_drag=False, show_hidden_files=True, multi_selection=False,
                             tag='file_dialog',  default_path=os.path.expanduser('~'), dirs_only=dirs_only,
                             callback=on_path_selected)
    file_dialog.show_file_dialog()


def start():
    side_windows = []

    def switch_windows(sender, app_data, user_data):
        for window in side_windows:
            if window == user_data:
                dpg.configure_item(window, show=True)
            else:
                dpg.configure_item(window, show=False)

    def update_setting(sender, app_data, user_data):
        if len(user_data) == 2:
            settings_dict[user_data[0]][user_data[1]] = dpg.get_value(sender)
        if len(user_data) == 3:
            settings_dict[user_data[0]][user_data[1]][user_data[2]] = dpg.get_value(sender)
        with open(settings_file, 'w') as sf:
            json.dump(settings_dict, sf, indent=4)

    fonts = [font for dirs in os.walk(os.path.join(heron_path, 'resources', 'fonts')) for font in dirs[2]]
    with dpg.window(label='Settings', width=950, height=500, pos=[300, 200], no_collapse=True) as setting_window:
        with dpg.group(horizontal=True) as settings_group:
            with dpg.child_window(label='Fonts', parent=settings_group, pos=[200, 30], show=False) as fonts_window:
                dpg.add_spacer(height=30)
                dpg.add_combo(items=fonts, label='Font type', default_value=settings_dict['Appearance']['Font']['Font'],
                              callback=update_setting, user_data=['Appearance', 'Font', 'Font'])
                dpg.add_spacer(height=30)
                dpg.add_input_int(label='Font size', width=120, default_value=settings_dict['Appearance']['Font']['Size'],
                                  callback=update_setting, user_data=['Appearance', 'Font', 'Size'], on_enter=True)
            side_windows.append(fonts_window)

            with dpg.child_window(label='IDE', parent=settings_group, pos=[200, 30], show=False) as ide_window:
                dpg.add_spacer(height=30)
                ide_exe_input = dpg.add_input_text(label='IDE executable',
                                                   default_value=settings_dict['IDE']['IDE Path'],
                                                   callback=update_setting, user_data=['IDE', 'IDE Path'],
                                                   on_enter=True)
                dpg.add_button(label='Browse', user_data=[ide_exe_input, False, ['IDE', 'IDE Path']], callback=on_browse)
                dpg.add_spacer(height=30)
                ide_project_input = dpg.add_input_text(label='Project',
                                                       default_value=settings_dict['IDE']['IDE Project Path'],
                                                       callback=update_setting, user_data=['IDE', 'IDE Project Path'],
                                                       on_enter=True)
                dpg.add_button(label='Browse', user_data=[ide_project_input, True, ['IDE', 'IDE Project Path']],
                               callback=on_browse)
            side_windows.append(ide_window)

            with dpg.child_window(label='Operation', parent=settings_group, pos=[200, 30], show=False) as operation_window:
                dpg.add_spacer(height=30)
                dpg.add_input_float(label='HEARTBEAT_RATE', default_value=settings_dict['Operation']['HEARTBEAT_RATE'],
                                    width=140, callback=update_setting, user_data=['Operation', 'HEARTBEAT_RATE'],
                                    on_enter=True)
                dpg.add_spacer(height=20)
                dpg.add_input_int(label='HEARTBEATS_TO_DEATH', default_value=settings_dict['Operation']['HEARTBEATS_TO_DEATH'],
                                  width=140, callback=update_setting, user_data=['Operation', 'HEARTBEATS_TO_DEATH'],
                                  on_enter=True)
                dpg.add_spacer(height=20)
                dpg.add_input_int(label='NUMBER_OF_INITIAL_PARAMETERS_UPDATES',
                                  default_value=settings_dict['Operation']['NUMBER_OF_INITIAL_PARAMETERS_UPDATES'],
                                  width=140, callback=update_setting, user_data=['Operation', 'NUMBER_OF_INITIAL_PARAMETERS_UPDATES'],
                                  on_enter=True)
                dpg.add_spacer(height=20)
                dpg.add_input_int(label='NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE',
                                  default_value=settings_dict['Operation']['NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE'],
                                  width=140, callback=update_setting, user_data=['Operation', 'NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE'],
                                  on_enter=True)
                dpg.add_spacer(height=20)
                dpg.add_input_int(label='DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS',
                                  default_value=settings_dict['Operation'][
                                      'DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS'],
                                  width=140, callback=update_setting, user_data=['Operation', 'DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS'],
                                  on_enter=True)
                dpg.add_spacer(height=20)
                khf_input = dpg.add_input_text(label='KNOWN_HOSTS_FILE',
                                               default_value=settings_dict['Operation']['KNOWN_HOSTS_FILE'],
                                               callback=update_setting, user_data=['Operation', 'KNOWN_HOSTS_FILE'],
                                               on_enter=True)
                dpg.add_button(label='Browse', user_data=[khf_input, False, ['Operation', 'KNOWN_HOSTS_FILE']],
                               callback=on_browse)
            side_windows.append(operation_window)

            with dpg.child_window(parent=setting_window, width=190, pos=[5, 30]) as options_window:
                with dpg.tree_node(label='Appearance', bullet=False) as appearance:
                    dpg.add_spacer(height=5)
                    dpg.add_button(label='Fonts', callback=switch_windows, user_data=fonts_window, small=True)
                    dpg.add_spacer(height=5)
                dpg.add_button(label='IDE', callback=switch_windows, user_data=ide_window, indent=5)
                dpg.add_spacer(height=5)
                dpg.add_button(label='Operation', callback=switch_windows, user_data=operation_window, indent=5)





