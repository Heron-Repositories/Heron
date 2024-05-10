
from dearpygui import dearpygui as dpg
from os.path import join
import os
from pathlib import Path
import json
from typing import List
import threading
import time

from Heron.gui.fdialog import FileDialog
from Heron.gui import fonts

heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent


class Settings:
    def __init__(self, nodes_list: List=None):
        self.window_ids_list = []
        self.settings_file = join(heron_path, 'settings.json')
        if not os.path.isfile(self.settings_file):
            with open(join(heron_path, 'settings_default.json'), 'r') as sfd:
                self.settings_dict: dict = json.load(sfd)
                with open(join(heron_path, 'settings.json'), 'w') as sf:
                    json.dump(self.settings_dict, sf, indent=4)
        else:
            with open(join(heron_path, 'settings.json'), 'r') as sf:
                self.settings_dict: dict = json.load(sf)

        self.file_dialog_selectable_height = 16
        self.table_distance_to_bottom = -30 + 5 * self.file_dialog_selectable_height
        self.node_font = []
        self.editor_font = []
        self.editor_title_id = 0
        self.start_graph_button_id = 0
        self.end_graph_button_id = 0
        self.node_tree_title_id = 0
        self.node_selector_holder_id = 0
        self.node_editor_window_id = 0
        self.node_selector_id = 0
        self.add_node_button_ids = []

        self.nodes_list = nodes_list
        if nodes_list is not None:
            update_thread = threading.Thread(group=None, target=self.online_settings_updates, daemon=True)
            update_thread.start()

    def set_editor_widget_ids(self, editor_title_id: int=None, start_graph_button_id: int=None,
                              end_graph_button_id: int=None, node_tree_title_id: int=None,
                              node_selector_holder_id: int=None, node_editor_window_id: int=None,
                              node_selector_id: int=None, add_node_button_ids: List=None):

        if editor_title_id is not None:
            self.editor_title_id = editor_title_id

        if start_graph_button_id is not None:
            self.start_graph_button_id = start_graph_button_id

        if end_graph_button_id is not None:
            self.end_graph_button_id = end_graph_button_id

        if node_tree_title_id is not None:
            self.node_tree_title_id = node_tree_title_id

        if node_selector_holder_id is not None:
            self.node_selector_holder_id = node_selector_holder_id

        if node_editor_window_id is not None:
            self.node_editor_window_id = node_editor_window_id

        if node_selector_id is not None:
            self.node_selector_id = node_selector_id

        if add_node_button_ids is not None:
            self.add_node_button_ids = add_node_button_ids

    def save_settings(self):
        with open(self.settings_file, 'w') as sf:
            json.dump(self.settings_dict, sf, indent=4)

    '''
    def kill_existing_aliases(self):

        for alias in self.aliases_list:
            try:
                dpg.remove_alias(alias)
            except:
                pass
        self.aliases_list = []
    '''

    def on_close_main(self, sender, app_data, user_data):
        global node_win
        #self.kill_existing_aliases()
        dpg.delete_item(node_win)

    def on_close_main_with_buttons(self, sender, app_data, user_data):
        global node_win
        #self.kill_existing_aliases()
        dpg.delete_item(node_win)

    def on_browse(self, sender, app_data, user_data):
        input_txt = user_data[0]
        dirs_only = user_data[1]
        setting_keys = user_data[2]

        def on_path_selected(files_selected):
            file = files_selected[0]
            dpg.set_value(input_txt, file)
            if len(setting_keys) == 2:
                self.settings_dict[setting_keys[0]][setting_keys[1]] = dpg.get_value(input_txt)
            elif len(setting_keys) == 3:
                self.settings_dict[setting_keys[0]][setting_keys[1]][setting_keys[2]] = dpg.get_value(input_txt)
            self.save_settings()

        file_dialog = FileDialog(title=f'Select {"folder" if dirs_only else "folder"}', show_dir_size=False,
                                 modal=False, allow_drag=False, show_hidden_files=True, multi_selection=False,
                                 tag='file_dialog',  default_path=os.path.expanduser('~'), dirs_only=dirs_only,
                                 callback=on_path_selected)
        file_dialog.show_file_dialog()

    def online_settings_updates(self):

        while True:
            time.sleep(0.3)

            node_font = os.path.join(heron_path, 'resources', 'fonts',
                                     self.settings_dict['Appearance']['Node Font']['Font'])
            node_font_size = int(self.settings_dict['Appearance']['Node Font']['Size'])

            editor_font = os.path.join(heron_path, 'resources', 'fonts',
                                       self.settings_dict['Appearance']['Editor Font']['Font'])
            editor_font_size = int(self.settings_dict['Appearance']['Editor Font']['Size'])


            # Deal with Node font size
            if self.node_font != [node_font, node_font_size]:
                node_font_id = dpg.add_font(node_font, node_font_size, parent=fonts.font_registry)
                self.node_font = [node_font, node_font_size]
            for node in self.nodes_list:
                for item in node.widget_ids_with_text:
                    dpg.bind_item_font(item, node_font_id)

            # Deal with Editor font size
            if self.editor_font != [editor_font, editor_font_size]:
                editor_font_id = dpg.add_font(editor_font, editor_font_size, parent=fonts.font_registry)
                fonts.italic_font_id = dpg.add_font(fonts.italic_font, int(0.9 * editor_font_size),
                                                    parent=fonts.font_registry)
                bold_font_id = dpg.add_font(fonts.bold_font, int(1.2 * editor_font_size),
                                            parent=fonts.font_registry)
                self.editor_font = [editor_font, editor_font_size]

                dpg.bind_font(editor_font_id)

                if self.editor_title_id is not None:
                    dpg.bind_item_font(self.editor_title_id, editor_font_id)
                if self.node_editor_window_id is not None:
                    dpg.set_item_pos(self.node_editor_window_id,
                                     [int(90 + 10 * editor_font_size), int(15 + 1 * editor_font_size)])

                if self.start_graph_button_id is not None:
                    dpg.bind_item_font(self.start_graph_button_id, bold_font_id)
                    dpg.set_item_height(self.start_graph_button_id, int(20 + 0.8 * editor_font_size))
                    dpg.set_item_width(self.start_graph_button_id, int(25 + 5.1 * editor_font_size))
                if self.end_graph_button_id is not None:
                    dpg.bind_item_font(self.end_graph_button_id, bold_font_id)
                    dpg.set_item_height(self.end_graph_button_id, int(20 + 0.8 * editor_font_size))
                    dpg.set_item_width(self.end_graph_button_id, int(25 + 5.1 * editor_font_size))

                if self.node_tree_title_id is not None:
                    dpg.bind_item_font(self.node_tree_title_id, bold_font_id)
                    dpg.set_item_indent(self.node_tree_title_id, int(30 + 2 * editor_font_size))
                if self.node_selector_holder_id is not None:
                    dpg.set_item_pos(self.node_selector_holder_id, [5, 40 + 1.8 * editor_font_size])
                    dpg.set_item_width(self.node_selector_holder_id, int(70 + 10.3 * editor_font_size))
                if self.node_selector_id is not None:
                    dpg.set_item_width(self.node_selector_id, int(65 + 10.3 * editor_font_size))

                if self.add_node_button_ids is not None:
                    for button_id in self.add_node_button_ids:
                        dpg.set_item_width(button_id, int(60 + 10.5 * editor_font_size))
                        dpg.set_item_height(button_id, int(10 + 1 * editor_font_size))

            # Deal with Settings font size
            options_window_width = 100 + 5 * editor_font_size
            for window_id in self.window_ids_list:
                if dpg.does_item_exist(window_id):
                    if dpg.get_item_label(window_id) == 'Options':
                        dpg.set_item_width(window_id, options_window_width)
                    else:
                        dpg.set_item_pos(window_id, [options_window_width + 10, 30])

    def create_gui(self):
        side_windows = []
        editor_font_size = int(self.settings_dict['Appearance']['Editor Font']['Size'])
        options_window_width = 100 + 5 * editor_font_size

        def switch_windows(sender, app_data, user_data):
            for window in side_windows:
                if window == user_data:
                    dpg.configure_item(window, show=True)
                else:
                    dpg.configure_item(window, show=False)

        def update_setting(sender, app_data, user_data):
            if len(user_data) == 2:
                self.settings_dict[user_data[0]][user_data[1]] = dpg.get_value(sender)
            if len(user_data) == 3:
                self.settings_dict[user_data[0]][user_data[1]][user_data[2]] = dpg.get_value(sender)
            with open(self.settings_file, 'w') as sf:
                json.dump(self.settings_dict, sf, indent=4)

        fonts = [font for dirs in os.walk(os.path.join(heron_path, 'resources', 'fonts')) for font in dirs[2]]
        with dpg.window(label='Settings', width=1100 + 2 * editor_font_size, height=500, pos=[300, 200],
                        no_collapse=True) as setting_window:
            with dpg.group(horizontal=True) as settings_group:
                with dpg.child_window(label='Fonts', parent=settings_group, pos=[options_window_width + 10, 30],
                                      show=False) as fonts_window:
                    self.window_ids_list.append(fonts_window)
                    dpg.add_spacer(height=30)
                    dpg.add_text(default_value='Editor font')
                    dpg.add_spacer(height=20)
                    dpg.add_combo(items=fonts, label='Font type', default_value=self.settings_dict['Appearance']['Editor Font']['Font'],
                                  callback=update_setting, user_data=['Appearance', 'Editor Font', 'Font'])
                    dpg.add_spacer(height=20)
                    #dpg.add_input_int(label='Font size', width=120, default_value=self.settings_dict['Appearance']['Editor Font']['Size'],
                    #                  callback=update_setting, user_data=['Appearance', 'Editor Font', 'Size'], on_enter=True)
                    dpg.add_slider_int(label='Font size', width=480, default_value=self.settings_dict['Appearance']['Editor Font']['Size'],
                                       callback=update_setting, user_data=['Appearance', 'Editor Font', 'Size'],
                                       min_value=7, max_value=40)
                    dpg.add_spacer(height=60)
                    dpg.add_text(default_value='Node font')
                    dpg.add_spacer(height=20)
                    dpg.add_combo(items=fonts, label='Font type', default_value=self.settings_dict['Appearance']['Node Font']['Font'],
                                  callback=update_setting, user_data=['Appearance', 'Node Font', 'Font'])
                    dpg.add_spacer(height=20)
                    #dpg.add_input_int(label='Font size', width=120,
                    #                  default_value=self.settings_dict['Appearance']['Node Font']['Size'],
                    #                  callback=update_setting, user_data=['Appearance', 'Node Font', 'Size'], on_enter=True)
                    dpg.add_slider_int(label='Font size', width=480,
                                       default_value=self.settings_dict['Appearance']['Node Font']['Size'],
                                       callback=update_setting, user_data=['Appearance', 'Node Font', 'Size'],
                                       min_value=7, max_value=40)
                side_windows.append(fonts_window)

                with dpg.child_window(label='IDE', parent=settings_group, pos=[options_window_width + 10, 30],
                                      show=False) as ide_window:
                    self.window_ids_list.append(ide_window)
                    dpg.add_spacer(height=30)
                    ide_exe_input = dpg.add_input_text(label='IDE executable',
                                                       default_value=self.settings_dict['IDE']['IDE Path'],
                                                       callback=update_setting, user_data=['IDE', 'IDE Path'],
                                                       on_enter=True)
                    dpg.add_button(label='Browse', user_data=[ide_exe_input, False, ['IDE', 'IDE Path']], callback=self.on_browse)
                    dpg.add_spacer(height=30)
                    ide_project_input = dpg.add_input_text(label='Project',
                                                           default_value=self.settings_dict['IDE']['IDE Project Path'],
                                                           callback=update_setting, user_data=['IDE', 'IDE Project Path'],
                                                           on_enter=True)
                    dpg.add_button(label='Browse', user_data=[ide_project_input, True, ['IDE', 'IDE Project Path']],
                                   callback=self.on_browse)
                side_windows.append(ide_window)

                with dpg.child_window(label='Operation', parent=settings_group, pos=[options_window_width + 10, 30],
                                      show=False) as operation_window:
                    self.window_ids_list.append(operation_window)
                    dpg.add_spacer(height=30)
                    dpg.add_input_float(label='HEARTBEAT_RATE', default_value=self.settings_dict['Operation']['HEARTBEAT_RATE'],
                                        width=140, callback=update_setting, user_data=['Operation', 'HEARTBEAT_RATE'],
                                        on_enter=True)
                    dpg.add_spacer(height=20)
                    dpg.add_input_int(label='HEARTBEATS_TO_DEATH', default_value=self.settings_dict['Operation']['HEARTBEATS_TO_DEATH'],
                                      width=140, callback=update_setting, user_data=['Operation', 'HEARTBEATS_TO_DEATH'],
                                      on_enter=True)
                    dpg.add_spacer(height=20)
                    dpg.add_input_int(label='NUMBER_OF_INITIAL_PARAMETERS_UPDATES',
                                      default_value=self.settings_dict['Operation']['NUMBER_OF_INITIAL_PARAMETERS_UPDATES'],
                                      width=140, callback=update_setting, user_data=['Operation', 'NUMBER_OF_INITIAL_PARAMETERS_UPDATES'],
                                      on_enter=True)
                    dpg.add_spacer(height=20)
                    dpg.add_input_int(label='NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE',
                                      default_value=self.settings_dict['Operation']['NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE'],
                                      width=140, callback=update_setting, user_data=['Operation', 'NUMBER_OF_ITTERATIONS_BEFORE_SAVENODESTATE_SUBSTATE_SAVE'],
                                      on_enter=True)
                    dpg.add_spacer(height=20)
                    dpg.add_input_int(label='DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS',
                                      default_value=self.settings_dict['Operation'][
                                          'DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS'],
                                      width=140, callback=update_setting, user_data=['Operation', 'DELAY_BETWEEN_SENDING_DATA_TO_NEXT_NODE_MILLISECONDS'],
                                      on_enter=True)
                    dpg.add_spacer(height=20)
                    khf_input = dpg.add_input_text(label='KNOWN_HOSTS_FILE',
                                                   default_value=self.settings_dict['Operation']['KNOWN_HOSTS_FILE'],
                                                   callback=update_setting, user_data=['Operation', 'KNOWN_HOSTS_FILE'],
                                                   on_enter=True)
                    dpg.add_button(label='Browse', user_data=[khf_input, False, ['Operation', 'KNOWN_HOSTS_FILE']],
                                   callback=self.on_browse)
                side_windows.append(operation_window)

                with dpg.child_window(label='Options', parent=setting_window, width=options_window_width, pos=[5, 30]) \
                        as options_window:
                    self.window_ids_list.append(options_window)
                    with dpg.tree_node(label='Appearance', bullet=False) as appearance:
                        dpg.add_spacer(height=5)
                        dpg.add_button(label='Fonts', callback=switch_windows, user_data=fonts_window, small=True)
                        dpg.add_spacer(height=5)
                    dpg.add_button(label='IDE', callback=switch_windows, user_data=ide_window, indent=5)
                    dpg.add_spacer(height=5)
                    dpg.add_button(label='Operation', callback=switch_windows, user_data=operation_window, indent=5)





