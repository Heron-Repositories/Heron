import time

from dearpygui import dearpygui as dpg
from os.path import join
import os
import ast
import numpy as np
import webbrowser
import subprocess
from pathlib import Path
from typing import Callable
import ctypes

from Heron.gui.fdialog import FileDialog
from Heron import general_utils as gu
from Heron.gui import settings
from Heron.gui import fonts


aliases_list = []
colours = {'Transform': [8, 132, 2], 'Sink': [161, 4, 9], 'Source': [0, 24, 152]}
node_type: str
group: str
path: str
node_data: dict
node_win: int
param_win: int
input_win: int
output_win: int
num_of_parameters = 0
num_of_inputs = 0
num_of_outputs = 0
parameter_types = ['bool', 'str', 'list', 'float', 'int']
heron_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
images_path = join(heron_path, 'resources', 'basic_icons')
add_node_to_tree_func: Callable
main_window_x_pos = 300


# The Code Editing
def generate_data(node_name_id):
    """
    Grabs the info supplied from the user and generates a dictionary of appropriate formatted values
    :param node_name_id: the id of the nade_name input text widget
    :return: Nothing
    """
    global node_data

    initial_data = {'node_name': dpg.get_value(node_name_id), 'node_path': path, 'parameter_names': [],
                    'parameter_types': [], 'parameter_defaults': [], 'inputs': [], 'outputs': [],
                    'node_tooltip': '', 'parameter_tooltips': [], 'in_out_tooltips': []}

    not_available_text = 'Documentation not available'
    param_tooltip_indices = []
    in_tooltip_indices = []
    out_tooltip_indices = []
    for alias in aliases_list:
        index = alias.split('_')[-1]
        if 'tooltip' not in alias:
            if 'parameter_name_' in alias:
                initial_data['parameter_names'].append(dpg.get_value(alias))
                param_tooltip_indices.append(index)
            if 'parameter_type_' in alias:
                initial_data['parameter_types'].append(dpg.get_value(alias))
            if 'parameter_default_' in alias:
                initial_data['parameter_defaults'].append(dpg.get_value(alias))
            if 'input_' in alias:
                initial_data['inputs'].append(dpg.get_value(alias))
                in_tooltip_indices.append(index)
            if 'output_' in alias:
                initial_data['outputs'].append(dpg.get_value(alias))
                out_tooltip_indices.append(index)
        if 'text_tooltip_node' in alias:
            text = dpg.get_value(alias)
            text = text.replace('\n', '\\n')
            initial_data['node_tooltip'] = text

    for index in param_tooltip_indices:
        if 'text_tooltip_parameter_' + index in aliases_list:
            alias = aliases_list[aliases_list.index('text_tooltip_parameter_' + index)]
            initial_data['parameter_tooltips'].append(dpg.get_value(alias))
        else:
            initial_data['parameter_tooltips'].append(not_available_text)

    for index in in_tooltip_indices:
        if 'text_tooltip_input_' + index in aliases_list:
            alias = aliases_list[aliases_list.index('text_tooltip_input_' + index)]
            initial_data['in_out_tooltips'].append(dpg.get_value(alias))
        else:
            initial_data['in_out_tooltips'].append(not_available_text)

    for index in out_tooltip_indices:
        if 'text_tooltip_output_' + index in aliases_list:
            alias = aliases_list[aliases_list.index('text_tooltip_output_' + index)]
            initial_data['in_out_tooltips'].append(dpg.get_value(alias))
        else:
            initial_data['in_out_tooltips'].append(not_available_text)

    node_com_file_name = initial_data['node_name'].lower().replace(' ', '_')+'_com.py'
    node_worker_file_name = initial_data['node_name'].lower().replace(' ', '_')+'_worker.py'

    node_data = {'BaseName': initial_data['node_name'], 'NodeAttributeNames': [], 'NodeAttributeType': [],
                 'ParameterNames': initial_data['parameter_names'], 'ParameterTypes': initial_data['parameter_types'],
                 'ParametersDefaultValues': initial_data['parameter_defaults'],
                 'WorkerDefaultExecutable': node_worker_file_name, 'ComExecutable': node_com_file_name,
                 'NodeTooltip': initial_data['node_tooltip'], 'ParameterTooltips':initial_data['parameter_tooltips'],
                 'InOutTooltips':initial_data['in_out_tooltips']}

    # Generate NodeAttributeNames and NodeAttributeType
    if len(initial_data['parameter_names']) > 0:
        node_data['NodeAttributeNames'].append('Parameters')
        node_data['NodeAttributeType'].append('Static')
    if len(initial_data['inputs']) > 0:
        for inp in initial_data['inputs']:
            node_data['NodeAttributeNames'].append(inp)
            node_data['NodeAttributeType'].append('Input')
    if len(initial_data['outputs']) > 0:
        for output in initial_data['outputs']:
            node_data['NodeAttributeNames'].append(output)
            node_data['NodeAttributeType'].append('Output')

    # Turn the default values from strings to literal values
    error = False
    for i, type in enumerate(node_data['ParameterTypes']):
        if type != 'str':
            try:
                node_data['ParametersDefaultValues'][i] = ast.literal_eval(node_data['ParametersDefaultValues'][i])
            except Exception as e:
                message = f"Default value {node_data['ParametersDefaultValues'][i]} of parameter " \
                          f"{node_data['ParameterNames'][i]}\ncannot be evaluated appropriately."
                print(message)
                with dpg.window(label=f'Error on parameter {i}', pos=[main_window_x_pos, 200+120*i],
                                height=120, width=300, show=True, popup=True):
                    dpg.add_text(default_value=message)
                error = True

    return False if error else True


def generate_folder_structure():
    """
    Using the node data generates the correct folder structure
    :return: Nothing
    """
    global group
    global node_data
    global path

    root_dir = path

    type_dir = node_type + 's'
    type_dir = type_dir[0].upper() + type_dir[1:]

    group_dir = group

    name_dir = node_data['BaseName'].replace(' ', '_')
    dirpath = os.path.join(root_dir, type_dir, group_dir, name_dir)
    topdir = os.path.join(root_dir, type_dir, group_dir, '__top__')

    node_data['WorkerDefaultExecutable'] = os.path.join(dirpath, node_data['WorkerDefaultExecutable'])
    node_data['ComExecutable'] = os.path.join(dirpath, node_data['ComExecutable'])

    try:
        os.makedirs(dirpath)
    except FileExistsError:
        pass

    try:
        os.makedirs(topdir)
        with open(os.path.join(topdir, 'ignore.gitignore'), 'wt') as f:
            pass
    except FileExistsError:
        pass

    time.sleep(0.2)


def write_code():
    """
    Using the node_data and the created folder structure it writes the _com.py and generates a formatted _worker.py
    file
    :return: Nothing
    """
    global node_data

    com_executable = os.path.split(node_data['ComExecutable'])[-1].split('.')[0]
    worker_executable = os.path.split(node_data['WorkerDefaultExecutable'])[-1]
    node_type_lower_case = node_type.lower()
    args_for_start_the_com_process = '' if node_type=='Sink' else 'NodeAttributeType, NodeAttributeNames'

    com_script = "import os\n" \
                 "import sys\n" \
                 "from os import path\n\n" \
                 "current_dir = path.dirname(path.abspath(__file__))\n" \
                 "while path.split(current_dir)[-1] != r'Heron':\n" \
                 "    current_dir = path.dirname(current_dir)\n" \
                 "sys.path.insert(0, path.dirname(current_dir))\n\n" \
                                                                        \
                 "from Heron import general_utils as gu\n" \
                 "Exec = os.path.abspath(__file__)\n\n\n" \
                                                        \
                 f"BaseName = '{node_data['BaseName']}'\n" \
                 f"NodeTooltip = '{node_data['NodeTooltip']}'\n" \
                 f"NodeAttributeNames = {node_data['NodeAttributeNames']}\n" \
                 f"NodeAttributeType = {node_data['NodeAttributeType']}\n" \
                 f"ParameterNames = {node_data['ParameterNames']}\n" \
                 f"ParameterTypes = {node_data['ParameterTypes']}\n" \
                 f"ParametersDefaultValues = {node_data['ParametersDefaultValues']}\n" \
                 f"ParameterTooltips = {node_data['ParameterTooltips']}\n" \
                 f"InOutTooltips = {node_data['InOutTooltips']}\n" \
                 f"WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), '{worker_executable}')\n\n\n" \
                 "if __name__ == '__main__':\n" \
                 f"    {com_executable} = gu.start_the_{node_type_lower_case}_communications_process({args_for_start_the_com_process})\n" \
                 f"    gu.register_exit_signals({com_executable}.on_kill)\n" \
                 f"    {com_executable}.start_ioloop()"

    with open(node_data['ComExecutable'], 'wt') as f:
        f.write(com_script)

    node_type_worker_class = f'{node_type}Worker'

    parameters_names = [node_data['ParameterNames'][i].lower().replace(' ', '_') for i in
                        range(len(node_data['ParameterNames']))]

    visualisation = True if 'Visualisation' in node_data['ParameterNames'] else False

    extra_indent = "    " if node_type == 'Source' else ""

    if node_type != 'Sink':
        number_of_outputs = np.sum([1 for i in range(len(node_data['NodeAttributeType']))
                                    if node_data['NodeAttributeType'][i] == 'Output'])
        ignore_string = "["
        for i in range(number_of_outputs):
            ignore_string += 'np.array([ct.IGNORE]), '
        ignore_string += "]"

    worker_script = "import sys\n" \
                    "from os import path\n" \
                    "import numpy as np\n" \
                    "import time\n" \
                    "from typing import List, Union\n\n" \
                    "current_dir = path.dirname(path.abspath(__file__))\n" \
                    "while path.split(current_dir)[-1] != r'Heron':\n" \
                    "    current_dir = path.dirname(current_dir)\n" \
                    "sys.path.insert(0, path.dirname(current_dir))\n\n" \
                                                                        \
                    "from Heron.communication.socket_for_serialization import Socket\n" \
                    "from Heron import general_utils as gu, constants as ct\n"

    worker_script += "from Heron.gui.visualisation_dpg import VisualisationDPG\n" if visualisation else ""

    worker_script += f"from Heron.communication.{node_type_lower_case}_worker import {node_type_worker_class}\n\n\n"

    for i in range(len(parameters_names)):
        if parameters_names[i] != 'visualisation':
            worker_script += f"{parameters_names[i]}: {node_data['ParameterTypes'][i]}\n"

    worker_script += "running = False\n" if node_type == 'Source' else ""

    worker_script += "vis: VisualisationDPG\n\n\n" if visualisation else "\n\n"

    worker_script += f"def initialise(worker_object: {node_type_worker_class}) -> bool:\n"
    worker_script += f"    global vis\n" if visualisation else ""

    for name in parameters_names:
        if name != 'visualisation':
            worker_script += f"    global {name}\n"
    worker_script += "\n"

    worker_script += "    # The args depend on what will be visualised. See Worker Templates on how to fill them in.\n" \
                     "    vis = VisualisationDPG(worker_object.node_name, worker_object.node_index, *args)\n\n" \
        if visualisation else "\n"

    worker_script += "    try:\n" \
                     "        parameters = worker_object.parameters\n" \

    for i, name in enumerate(parameters_names):
        if name != 'visualisation':
            worker_script += f"        {name} = parameters[{i}]\n"
        else:
            worker_script += f"        vis.visualisation_on = parameter[{i}]\n"

    worker_script += "    except:\n" \
                     "        return False\n\n"

    worker_script += "    # Add Saving the parameters every time they change if required:\n" \
                     f"    #  worker_object.savenodestate_create_parameters_df({parameters_names[0]}={parameters_names[0]}, \n"
    for name in parameters_names[1:]:
        worker_script += \
                     f"    #                                                   {name }={name},\n"
    worker_script += "    #                                                    )\n\n" \
                     "    # DO ANY OTHER INITIALISATION HERE \n\n"

    worker_script += "    return True\n\n\n"

    if node_type == 'Source':
        worker_script += "def work_function(worker_object: SourceWorker) -> None:\n"
    elif node_type == 'Transform':
        worker_script += "def work_function(data: List[Union[np.ndarray, dict]],\n" \
                         "                  parameters: List,\n" \
                         "                  savenodestate_update_substate_df: TransformWorker.savenodestate_update_substate_df) -> \\\n" \
                         "        List[Union[np.ndarray, dict]]:\n\n"
    elif node_type == 'Sink':
        worker_script += "def work_function(data: List[Union[np.ndarray, dict]],\n" \
                         "                  parameters: List,\n" \
                         "                  savenodestate_update_substate_df: TransformWorker.savenodestate_update_substate_df) -> None:\n\n\n"

    worker_script += "    global running\n" if node_type == 'Source' else ""
    worker_script += "    global vis\n" if visualisation else ""
    for name in parameters_names:
        if name != 'visualisation':
            worker_script += f"    global {name}\n"

    worker_script += "\n"

    if node_type == 'Source':
        worker_script += "    need_parameters = True\n" \
                         "    while need_parameters:\n" \
                         "        if worker_object.initialised:\n" \
                         "            need_parameters = False\n" \
                         "            running = True\n" \
                         "            time.sleep(0.01)\n\n"
    worker_script += "    while running:\n" if node_type == 'Source' else ""
    worker_script += f"    {extra_indent}try:\n"
    worker_script += f"        {extra_indent}#  Uncomment any of the parameter updates whose values\n" \
                     f"        {extra_indent}#  need to update as the Graph is running.\n"
    for i, name in enumerate(parameters_names):
        worker_script += f"        {extra_indent}vis.visualisation_on = parameters[{i}]\n" if name == 'visualisation' else \
            f"        {extra_indent}# {name} = parameters[{i}]\n"
    worker_script += f"        {extra_indent}pass\n"
    worker_script += f"    {extra_indent}except:\n" \
                     f"        {extra_indent}pass\n\n"

    if node_type != 'Source':
        worker_script += f"    {extra_indent}topic = data[0].decode('utf-8')\n\n" \
                         f"    {extra_indent}message = data[1:]\n" \
                         f"    {extra_indent}message = Socket.reconstruct_data_from_bytes_message(message)\n" \
                         f"    {extra_indent}# OR Socket.reconstruct_array_from_bytes_message_cv2correction(message) " \
                         "if the message data is an image\n\n"
    worker_script += f"    {extra_indent}# -----------------------\n" \
                     f"    {extra_indent}# MAIN CODE GOES HERE !!\n" \
                     f"    {extra_indent}# -----------------------\n\n" \
                     f"    {extra_indent}# SAVE TO SUBSTATE. arguments' syntax: arg_name_in_dataframe=variable_to_save \n"

    worker_script += f"        #  worker_object.savenodestate_update_substate_df(arg_name_in_dataframe=variable_to_save)\n\n" if node_type == 'Source' else \
                     f"    #  savenodestate_update_substate_df(arg_name_in_dataframe=variable_to_save)\n\n"

    if visualisation:
        worker_script += f"    {extra_indent}# Put the data you want to visualise here.\n" \
                         f"    {extra_indent}# Check that the way you set up the VisualiserGPD in the initialisation function is compatible.\n" \
                         f"    {extra_indent}vis.visualise(something_to_visualise)\n\n"

    if node_type != 'Sink':
        worker_script += f"    {extra_indent}# Create the result to be pushed to the next Node\n" \
                         f"    {extra_indent}# Here we are creating a list that pushes nothing, but you should\n" \
                         f"    {extra_indent}# create a list of numpy arrays or dictionaries for the Node to return.\n" \
                         f"    {extra_indent}result = {ignore_string}\n\n"

        if node_type == 'Source':
            worker_script += "        worker_object.send_data_to_com(result)\n" \
                             "        # You might want to add some delay here\n" \
                             "        # time.sleep(0.01)\n"
        else:
            worker_script += "    return result\n"

    worker_script += "\n\n"

    worker_script += "def on_end_of_life():\n"
    worker_script += "    global vis\n    vis.end_of_life()\n" if visualisation else ""
    worker_script += "    global running\n    running = False\n" if node_type == 'Source' else "\n"
    worker_script += "    # ADD HERE ANY OTHER PROCESS TERMINATION CODE\n"
    worker_script += "    pass\n\n\n" if (not visualisation and node_type != 'Sources') else "\n\n"

    worker_script += "if __name__ == '__main__':\n" \
                     f"    worker_object = gu.start_the_{node_type.lower()}_worker_process(work_function=work_function,\n" \
                     "                                                          end_of_life_function=on_end_of_life,\n" \
                     "                                                          initialisation_function=initialise)\n"
    worker_script += "    worker_object.start_ioloop()\n" if node_type != 'Source' else "\n"

    with open(node_data['WorkerDefaultExecutable'], 'wt') as f:
        f.write(worker_script)


def generate_code(node_name_id):
    global path
    if generate_data(node_name_id):
        generate_folder_structure()
        write_code()
        gu.start_ide(node_data['ComExecutable'], node_data['WorkerDefaultExecutable'])
        add_node_to_tree_func(sender=None, app_data=None, user_data=[path])

        return True

    return False


# The GUI
def kill_existing_aliases():
    global aliases_list

    for alias in aliases_list:
        try:
            dpg.remove_alias(alias)
        except:
            pass
    aliases_list = []

    try:
        if dpg.does_alias_exist('add_param_cross'):
            dpg.remove_alias('add_param_cross')
        if dpg.does_alias_exist('add_param_txt'):
            dpg.remove_alias('add_param_txt')
        if dpg.does_alias_exist('type_selector'):
            dpg.remove_alias('type_selector')
        if dpg.does_alias_exist('group_selector'):
            dpg.remove_alias('group_selector')
        if dpg.does_alias_exist('file_dialog'):
            dpg.remove_alias('file_dialog')
    except:
        pass
    if node_type != 'Source':
        if dpg.does_alias_exist('add_input_cross'):
            dpg.remove_alias('add_input_cross')
        if dpg.does_alias_exist('add_input_txt'):
            dpg.remove_alias('add_input_txt')
    if node_type != 'Sink':
        if dpg.does_alias_exist('add_output_cross'):
            dpg.remove_alias('add_output_cross')
        if dpg.does_alias_exist('add_output_txt'):
            dpg.remove_alias('add_output_txt')


def on_close_main(sender, app_data, user_data):
    kill_window = True
    if user_data:
        node_name_id = user_data
        kill_window = generate_code(node_name_id)
    if kill_window:
        kill_existing_aliases()
        if user_data:
            dpg.delete_item(node_win)


def on_close_main_with_buttons(sender, app_data, user_data):
    global node_win

    node_name_id, gen_data = user_data
    kill_window = True

    if gen_data:
        kill_window = generate_code(node_name_id)

    if kill_window:
        dpg.configure_item(node_win, show=False)
        kill_existing_aliases()
        dpg.delete_item(node_win)


def start(_add_node_to_tree_func):
    """
    The first function to be called which starts the process of showing consecutive windows to get all the info
    for a new Node. The first window is the Node type selector
    :return: Nothing
    """
    global add_node_to_tree_func
    add_node_to_tree_func = _add_node_to_tree_func

    def delete_error_popup_aliases():
        if dpg.does_alias_exist('modal_error_id'):
            dpg.delete_item('modal_error_id')

    def create_error_window(error_text, spacer):
        with dpg.window(label="Error Window", modal=True, show=True, id="modal_error_id",
                        no_title_bar=True, popup=True, pos=[500,300]):
            dpg.add_text(error_text)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=spacer)
                dpg.add_button(label="OK", width=75, callback=delete_error_popup_aliases)

    # Check if in Windows and running as an Admin
    if os.name == 'nt' and ctypes.windll.shell32.IsUserAnAdmin() == 0:
        error_text = 'In Windows you need to run the python that runs Heron\n' \
                     'with elevated credentials in order to create a symbolic link.\n' \
                     'Restart Heron with a python that has started with "Run as Administrator".'
        spacer = 160
        create_error_window(error_text, spacer)
    else:
        tag = 'type_selector'
        with dpg.window(label='Node Type Selector', tag=tag, width=380, height=100, pos=[500, 200], no_collapse=True,
                        on_close=on_close_main):
            dpg.add_combo(label="Pick the Node's type", items=['Source', 'Transform', 'Sink'], width=200,
                          callback=on_type_selected)


def on_type_selected(sender, app_data):
    """
    The second window in the Node selection process. After the type is selected the user must select the Group
    the Node belongs to.
    :param sender: Sender of callback
    :param app_data: Data of callback
    :return: Nothing
    """
    global node_type
    node_type = app_data

    dpg.delete_item('type_selector')

    tag = 'group_selector'
    with dpg.window(label='Node Type Selector', tag=tag, width=480, height=100, pos=[500, 200], no_collapse=True,
                    on_close=on_close_main):
        dpg.add_input_text(label="Provide Node's Group (e.g. Vision)", width=200, default_value='General',
                           callback=on_group_selected, on_enter=True)


def on_group_selected(sender, app_data):
    """
    Once the Group of the Node is selected the third window (file editor) of selecting the path where the Node folder
    structure will be generated is called
    :param sender: Sender of callback
    :param app_data: Data of callback
    :return: Nothing
    """
    global group
    group = app_data

    dpg.delete_item('group_selector')
    file_dialog = FileDialog(title='Select Parent Folder For Node', show_dir_size=False, modal=False, allow_drag=False,
                             show_hidden_files=True, multi_selection=False, tag='file_dialog',
                             default_path=os.path.expanduser('~'), dirs_only=True, callback=on_path_selected)
    file_dialog.show_file_dialog()

    with dpg.window(label='Info', pos=[360, 200], height=180, width=580, show=True, no_collapse=True) as info:
        dpg.add_spacer(height=5)
        dpg.add_text(default_value="Select the Base (Repository) Folder of the Node's File Structure.", indent=10)
        with dpg.group(horizontal=True, indent=10):
            dpg.add_text(default_value="See:")
            doc = dpg.add_selectable(label='documentation', width=100,
                                     callback=lambda: webbrowser.open("https://heron-42ad.readthedocs.io/en/latest/source/documentation/adding_repos.html#creating-a-valid-heron-nodes-repository-from-scratch"))
            dpg.add_text(default_value='for the File Structure of a single or group of Nodes.')
        dpg.add_text(default_value="It is highly advisable to make this a git repository base folder!", indent=10)
        dpg.add_spacer(height=15)
        dpg.add_button(label='Ok', callback=lambda: dpg.delete_item(info), indent=250)

        dpg.bind_item_font(doc, fonts.italic_font)


def on_path_selected(files_selected):
    global path
    path = files_selected[0]
    make_node_window()


def delete_parameter(sender, app_data, user_data):
    global num_of_parameters
    global aliases_list

    param_group, tag_param_name, tag_param_type, tag_param_default = user_data

    tag_tooltip_edit_window = f'tooltip_{tag_param_name}'.replace('name_', '')
    tag_tooltip_text = 'text_' + tag_tooltip_edit_window

    del aliases_list[aliases_list.index(tag_param_name)]
    del aliases_list[aliases_list.index(tag_param_type)]
    del aliases_list[aliases_list.index(tag_param_default)]
    try:
        del aliases_list[aliases_list.index(tag_tooltip_edit_window)]
        del aliases_list[aliases_list.index(tag_tooltip_text)]
    except:
        pass

    dpg.delete_item(param_group)


def delete_input(sender, app_data, user_data):
    global num_of_inputs
    global aliases_list

    input_group, tag = user_data
    tag_draw = f"draw_in_{tag.replace('input_', '')}"
    tag_tooltip_edit_window = f'tooltip_{tag}'
    tag_tooltip_text = 'text_' + tag_tooltip_edit_window

    del aliases_list[aliases_list.index(tag)]
    del aliases_list[aliases_list.index(tag_draw)]
    try:
        del aliases_list[aliases_list.index(tag_tooltip_edit_window)]
        del aliases_list[aliases_list.index(tag_tooltip_text)]
    except:
        pass
    dpg.delete_item(input_group)


def delete_output(sender, app_data, user_data):
    global num_of_outputs
    global aliases_list

    output_group, tag = user_data
    tag_draw = f"draw_out_{tag.replace('output_', '')}"
    tag_tooltip_edit_window = f'tooltip_{tag}'
    tag_tooltip_text = 'text_' + tag_tooltip_edit_window

    del aliases_list[aliases_list.index(tag)]
    del aliases_list[aliases_list.index(tag_draw)]
    try:
        del aliases_list[aliases_list.index(tag_tooltip_edit_window)]
        del aliases_list[aliases_list.index(tag_tooltip_text)]
    except:
        pass
    dpg.delete_item(output_group)


def delete_add_parameter_button():
    dpg.delete_item('add_param_cross')
    dpg.delete_item('add_param_txt')


def delete_add_input_button():
    dpg.delete_item('add_input_cross')
    dpg.delete_item('add_input_txt')


def delete_add_output_button():
    dpg.delete_item('add_output_cross')
    dpg.delete_item('add_output_txt')


def make_add_parameter_button():
    with dpg.group(horizontal=True, parent=param_win):
        dpg.add_button(label='+', callback=add_new_parameter, tag='add_param_cross')
        dpg.add_text('Add a new Parameter', tag='add_param_txt')


def make_add_input_button():
    with dpg.group(horizontal=True, parent=input_win):
        dpg.add_button(label='+', callback=add_new_input, tag='add_input_cross')
        dpg.add_text('Add a new Input', tag='add_input_txt')


def make_add_output_button():
    with dpg.group(horizontal=True, parent=output_win):
        dpg.add_button(label='+', callback=add_new_output, tag='add_output_cross')
        dpg.add_text('Add a new Output', tag='add_output_txt')


def on_edit_tooltip(sender, app_data, user_data):
    if 'parameter' in user_data:
        tag_tooltip_edit_window = f"tooltip_parameter_{user_data.split('_')[-1]}"
    else:
        tag_tooltip_edit_window = f'tooltip_{user_data}'

    tag_tooltip_text = 'text_' + tag_tooltip_edit_window

    if tag_tooltip_edit_window in aliases_list:
        dpg.configure_item(tag_tooltip_edit_window, show=True)
    else:
        aliases_list.append(tag_tooltip_edit_window)
        aliases_list.append(tag_tooltip_text)

        with dpg.window(label='Documentation', tag=tag_tooltip_edit_window, modal=True, no_collapse=True,
                        show=True, width=500, height=300, pos=[850, 100], no_close=True):
            dpg.add_input_text(default_value='', width=-10, height=220, multiline=True, tag=tag_tooltip_text)
            with dpg.group(horizontal=True):
                dpg.add_button(label='Ok', indent=220,
                               callback=lambda: dpg.configure_item(tag_tooltip_edit_window, show=False))


def add_new_parameter(sender, app_data):
    global num_of_parameters
    num_of_parameters += 1
    tag_param_name = f'parameter_name_{num_of_parameters}'
    tag_param_type = f'parameter_type_{num_of_parameters}'
    tag_param_default = f'parameter_default_{num_of_parameters}'

    delete_add_parameter_button()
    with dpg.group(horizontal=True, parent=param_win) as param_group:
        dpg.add_image_button('delete_texture', width=20, height=20,
                             user_data=[param_group, tag_param_name, tag_param_type, tag_param_default],
                             callback=delete_parameter)
        dpg.add_input_text(default_value="Name", tag=tag_param_name, width=200)
        with dpg.tooltip(parent=tag_param_name):
            dpg.add_text(default_value='Add the name of the Parameter. If the name is Visualisation then the\n'
                                       'automatically generated code will include the VisualisationDPG module.')
        dpg.add_combo(items=parameter_types, tag=tag_param_type, width=60)
        dpg.add_input_text(default_value='Default value', tag=tag_param_default, width=170)
        dpg.add_image_button('edit_texture', width=20, height=20, callback=on_edit_tooltip, user_data=tag_param_name)
    aliases_list.append(tag_param_name)
    aliases_list.append(tag_param_type)
    aliases_list.append(tag_param_default)
    make_add_parameter_button()


def add_new_input(sender, app_data):
    global num_of_inputs
    num_of_inputs += 1
    tag = f'input_{num_of_inputs}'
    draw_tag = f'draw_in_{num_of_inputs}'

    delete_add_input_button()
    with dpg.group(horizontal=True, parent=input_win) as input_group:
        with dpg.drawlist(width=20, height=20):
            with dpg.draw_node(tag=draw_tag):
                dpg.draw_circle(center=[10, 10], radius=5, color=[234, 225, 5], fill=[234, 225, 5])
        dpg.add_image_button('delete_texture', width=20, height=20, user_data=[input_group, tag],
                              callback=delete_input)
        dpg.add_input_text(default_value="Name", tag=tag, width=200)
        dpg.add_image_button('edit_texture', width=20, height=20, callback=on_edit_tooltip, user_data=tag)
    aliases_list.append(tag)
    aliases_list.append(draw_tag)
    make_add_input_button()


def add_new_output(sender, app_data):
    global num_of_outputs
    num_of_outputs += 1
    tag = f'output_{num_of_outputs}'
    draw_tag = f'draw_out_{num_of_outputs}'

    delete_add_output_button()
    with dpg.group(horizontal=True, parent=output_win, indent=230) as output_group:
        dpg.add_image_button('delete_texture', width=20, height=20, user_data=[output_group, tag], callback=delete_output)
        dpg.add_input_text(default_value="Name", tag=tag, width=200)
        dpg.add_image_button('edit_texture', width=20, height=20, callback=on_edit_tooltip, user_data=tag)
        with dpg.drawlist(width=20, height=20):
            with dpg.draw_node(tag=draw_tag):
                dpg.draw_circle(center=[10, 10], radius=5, color=[234, 225, 5], fill=[234, 225, 5])
    aliases_list.append(tag)
    aliases_list.append(draw_tag)
    make_add_output_button()


def make_node_window():
    """
    The fourth window in the Node creation process (Node's name, parameters, inputs and outputs) gets generated
    :return: Nothing
    """
    global aliases_list
    global node_win
    global param_win
    global input_win
    global output_win

    tag_main = 'new_node_editor'
    tag_name_text = 'name_input'
    tag_param_window = 'parameterscontainer'
    tag_input_window = 'inputcontainer'
    tag_output_window = 'outputwindow'
    tag_delete_texture = 'delete_texture'
    tag_edit_texture = 'edit_texture'

    aliases_list.append(tag_main)
    aliases_list.append(tag_name_text)
    aliases_list.append(tag_param_window)
    aliases_list.append(tag_input_window)
    aliases_list.append(tag_output_window)
    aliases_list.append(tag_delete_texture)
    aliases_list.append(tag_edit_texture)

    wdel, hdel, cdel, ddel = dpg.load_image(join(images_path, "DeleteG.png"))
    wedit, hedit, cedit, dedit = dpg.load_image(join(images_path, "EditG.png"))
    with dpg.texture_registry():
        dpg.add_static_texture(wdel, hdel, ddel, tag=tag_delete_texture)
        dpg.add_static_texture(wedit, hedit, dedit, tag=tag_edit_texture)

    with dpg.window(label='New Node Editor', tag=tag_main, width=550, height=430, pos=[main_window_x_pos, 100],
                    user_data=tag_name_text, on_close=on_close_main, no_collapse=True) as node_win:
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag=tag_name_text, width=-30, height=40, indent=5, default_value='Node Name')
            dpg.add_image_button('edit_texture', width=20, height=20, callback=on_edit_tooltip, user_data='node')
        dpg.add_spacer(height=2)
        dpg.add_separator()
        
        with dpg.child_window(tag=tag_param_window, height=150, border=False) as param_win:
            make_add_parameter_button()

        if node_type != 'Source':
            dpg.add_spacer(height=10)
            dpg.add_separator()
            with dpg.child_window(tag=tag_input_window, height=150, border=False) as input_win:
                make_add_input_button()

        if node_type != 'Sink':
            dpg.add_spacer(height=10)
            dpg.add_separator()
            with dpg.child_window(tag=tag_output_window, height=150, border=False) as output_win:
                make_add_output_button()

        if node_type == 'Transform':
            dpg.configure_item(node_win, height=605)

        with dpg.group(horizontal=True):
            dpg.add_button(label='OK', indent=240, callback=on_close_main_with_buttons, user_data=[tag_name_text, True])
            dpg.add_button(label='Cancel', callback=on_close_main_with_buttons, user_data=[tag_name_text, False])

    with dpg.theme() as node_name_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, gu.choose_color_according_to_operations_type(node_type+'s'),
                                category=dpg.mvThemeCat_Core)

    with dpg.theme() as node_editor_name_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [20, 20, 20, 255], category=dpg.mvThemeCat_Core)
            #dpg.add_theme_color(dpg.mvThemeCol_Text, [217, 194, 76], category=dpg.mvThemeCat_Core)

    dpg.bind_item_theme(tag_name_text, node_name_theme)
    dpg.bind_item_theme(node_win, node_editor_name_theme)

