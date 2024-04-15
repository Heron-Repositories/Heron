
from dearpygui import dearpygui as dpg
from os.path import dirname, join
import os
import ast
from Heron.gui.fdialog import FileDialog
import numpy as np

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
delete_texture: int
num_of_parameters = 0
num_of_inputs = 0
num_of_outputs = 0
parameter_types = ['bool', 'str', 'list', 'float', 'int']

images_path = join(dirname(dirname(os.path.realpath(__file__))), 'resources')


# The Code Editing
def generate_data(node_name_id):
    """
    Grabs the info supplied from the user and generates a dictionary of appropriate formatted values
    :param node_name_id: the id of the nade_name input text widget
    :return: Nothing
    """
    global node_data

    initial_data = {'node_name': dpg.get_value(node_name_id), 'node_path': path, 'parameter_names': [],
                    'parameter_types': [], 'parameter_defaults': [], 'inputs': [], 'outputs': []}
    for alias in aliases_list:
        if 'parameter_name_' in alias:
            initial_data['parameter_names'].append(dpg.get_value(alias))
        if 'parameter_type_' in alias:
            initial_data['parameter_types'].append(dpg.get_value(alias))
        if 'parameter_default_' in alias:
            initial_data['parameter_defaults'].append(dpg.get_value(alias))
        if 'input_' in alias:
            initial_data['inputs'].append(dpg.get_value(alias))
        if 'output_' in alias:
            initial_data['outputs'].append(dpg.get_value(alias))

    node_com_file_name = initial_data['node_name'].lower().replace(' ', '_')+'_com.py'
    node_worker_file_name = initial_data['node_name'].lower().replace(' ', '_')+'_worker.py'

    node_data = {'BaseName': initial_data['node_name'], 'NodeAttributeNames': [], 'NodeAttributeType': [],
                 'ParameterNames': initial_data['parameter_names'], 'ParameterTypes': initial_data['parameter_types'],
                 'ParametersDefaultValues': initial_data['parameter_defaults'],
                 'WorkerDefaultExecutable': node_worker_file_name,
                 'ComExecutable': node_com_file_name}

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

    node_data['ParametersDefaultValues'] = initial_data['parameter_defaults']

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
                with dpg.window(label=f'Error on parameter {i}', pos=[300, 200+120*i], height=120, width=300,
                                show=True, popup=True):
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
                 f"NodeAttributeNames = {node_data['NodeAttributeNames']}\n" \
                 f"NodeAttributeType = {node_data['NodeAttributeType']}\n" \
                 f"ParameterNames = {node_data['ParameterNames']}\n" \
                 f"ParameterTypes = {node_data['ParameterTypes']}\n" \
                 f"ParametersDefaultValues = {node_data['ParametersDefaultValues']}\n" \
                 f"WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), '{worker_executable}')\n\n\n" \
                 "if __name__ == '__main__':\n" \
                 f"    {com_executable} = gu.start_the_{node_type_lower_case}_communications_process(NodeAttributeType, NodeAttributeNames)\n" \
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

    worker_script += "    # The arguments depend on what will be visualised. See Worker Templates on how to fill them in.\n" \
                     "    vis = VisualisationDPG(arguments)\n\n" \
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
                     f"    #                                                   {name }={name}\n"
    worker_script += "    #                                                    )\n\n" \
                     "    # DO ANY OTHER INITIALISATION HERE \n\n\n"

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
                         "            gu.accurate_delay(10)\n\n"
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
        worker_script += f"    {extra_indent}topic = data[0]\n\n" \
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
                             "        # gu.accurate_delay(10)\n"
        else:
            worker_script += "    return result\n"

    worker_script += "\n\n"

    worker_script += "def on_end_of_life():\n"
    worker_script += "    global vis\n    vis.end_of_life()\n" if visualisation else ""
    worker_script += "    global running\n    running = False\n" if node_type == 'Source' else "\n"
    worker_script += "    # ADD HERE ANY OTHER PROCESS TERMINATION CODE\n"
    worker_script += "    pass\n\n\n" if (not visualisation and node_type != 'Sources') else "\n\n"

    worker_script += "if __name__ == '__main__':\n" \
                     "    worker_object = gu.start_the_transform_worker_process(work_function=work_function,\n" \
                     "                                                          end_of_life_function=on_end_of_life,\n" \
                     "                                                          initialisation_function=initialise)\n"
    worker_script += "    worker_object.start_ioloop()\n" if node_type != 'Source' else "\n"

    with open(node_data['WorkerDefaultExecutable'], 'wt') as f:
        f.write(worker_script)


def generate_code(node_name_id):
    if generate_data(node_name_id):
        generate_folder_structure()
        write_code()


# The GUI
def kill_existing_aliases(node_name_id):
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
    if node_type != 'Source':
        dpg.remove_alias('add_input_cross')
        dpg.remove_alias('add_input_txt')
    if node_type != 'Sink':
        dpg.remove_alias('add_output_cross')
        dpg.remove_alias('add_output_txt')


def on_close_main(sender, app_data, user_data):
    node_name_id = user_data
    generate_code(node_name_id)
    kill_existing_aliases(node_name_id)


def on_close_main_with_buttons(sender, app_data, user_data):
    global node_win

    node_name_id, gen_data = user_data
    if gen_data:
        generate_code(node_name_id)

    dpg.delete_item(node_win)


def start():
    """
    The first function to be called which starts the process of showing consecutive windows to get all the info
    for a new Node. The first window is the Node type selector
    :return: Nothing
    """
    tag = 'type_selector'
    with dpg.window(label='Node Type Selector', tag=tag, width=380, height=100, pos=[500, 200]):
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
    with dpg.window(label='Node Type Selector', tag=tag, width=480, height=100, pos=[500, 200]):
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

    with dpg.window(label='Info', pos=[300, 200], height=220, width=460, show=True) as info:
        dpg.add_spacer(height=5)
        dpg.add_text(default_value="Select the base folder of the Node's file structure.\n"
                                   "It is advisable to make this a git repository base folder.\n"
                                   "Once you are done creating the Node you need to link its folder\n"
                                   "to Heron's Operations folder using the\n"
                                   "Add new Operations Folder (as Symbolic Link from Existing Repo)\n"
                                   "in the Nodes dropdown of the menu bar.",
                     indent=10)
        dpg.add_spacer(height=15)
        dpg.add_button(label='Ok', callback=lambda: dpg.delete_item(info), indent=200)


def on_path_selected(files_selected):
    global path
    path = files_selected[0]
    make_node_window()


def delete_parameter(sender, app_data, user_data):
    global num_of_parameters
    global aliases_list

    param_group, tag_param_name, tag_param_type, tag_param_default = user_data

    del aliases_list[aliases_list.index(tag_param_name)]
    del aliases_list[aliases_list.index(tag_param_type)]
    del aliases_list[aliases_list.index(tag_param_default)]
    dpg.delete_item(param_group)

    #num_of_parameters -= 1


def delete_input(sender, app_data, user_data):
    global num_of_inputs
    global aliases_list

    input_group, tag = user_data
    del aliases_list[aliases_list.index(tag)]
    dpg.delete_item(input_group)


def delete_output(sender, app_data, user_data):
    global num_of_outputs
    global aliases_list

    output_group, tag = user_data
    del aliases_list[aliases_list.index(tag)]
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


def add_new_parameter(sender, app_data):
    global num_of_parameters
    num_of_parameters += 1
    tag_param_name = f'parameter_name_{num_of_parameters}'
    tag_param_type = f'parameter_type_{num_of_parameters}'
    tag_param_default = f'parameter_default_{num_of_parameters}'

    delete_add_parameter_button()
    with dpg.group(horizontal=True, parent=param_win) as param_group:
        dpg.add_image_button(delete_texture, width=20, height=20,
                             user_data=[param_group, tag_param_name, tag_param_type, tag_param_default],
                             callback=delete_parameter)
        dpg.add_input_text(default_value="Parameter's name", tag=tag_param_name, width=150)
        with dpg.tooltip(parent=tag_param_name):
            dpg.add_text(default_value='Add the name of the Parameter. If the name is Visualisation then the\n'
                                       'automatically generated code will include the VisualisationDPG module.')
        dpg.add_combo(items=parameter_types, tag=tag_param_type, width=80)
        dpg.add_input_text(default_value='Default value', tag=tag_param_default, width=200)
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
        dpg.add_input_text(default_value="Input's name", tag=tag)
        dpg.add_image_button(delete_texture, width=20, height=20, user_data=[input_group, tag], callback=delete_input)
    aliases_list.append(tag)
    aliases_list.append(draw_tag)
    make_add_input_button()


def add_new_output(sender, app_data):
    global num_of_outputs
    num_of_outputs += 1
    tag = f'output_{num_of_outputs}'
    draw_tag = f'draw_out_{num_of_outputs}'

    delete_add_output_button()
    with dpg.group(horizontal=True, parent=output_win, indent=55) as output_group:
        dpg.add_image_button(delete_texture, width=20, height=20, user_data=[output_group, tag], callback=delete_output)
        dpg.add_input_text(default_value="Output's name", tag=tag)
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
    global delete_texture

    tag_main = 'new_node_editor'
    tag_name_text = 'name_input'
    tag_param_window = 'parameterscontainer'
    tag_input_window = 'inputcontainer'
    tag_output_window = 'outputwindow'

    aliases_list.append(tag_main)
    aliases_list.append(tag_name_text)
    aliases_list.append(tag_param_window)
    aliases_list.append(tag_input_window)
    aliases_list.append(tag_output_window)

    width, height, channels, data = dpg.load_image(join(images_path, "Delete.png"))
    with dpg.texture_registry():
        delete_texture = dpg.add_static_texture(width, height, data)

    with dpg.window(label='New Node Editor', tag=tag_main, width=470, height=500, pos=[500, 200],
                    user_data=tag_name_text, on_close=on_close_main) as node_win:
        dpg.add_input_text(tag=tag_name_text, width=480, height=300, indent=5, default_value='Node Name')

        dpg.add_spacer(height=10)
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
            dpg.configure_item(node_win, height=620)

        with dpg.group(horizontal=True):
            dpg.add_button(label='OK', indent=200, callback=on_close_main_with_buttons, user_data=[tag_name_text, True])
            dpg.add_button(label='Cancel', callback=on_close_main_with_buttons, user_data=[tag_name_text, False])

    with dpg.theme() as container_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, colours[node_type], category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

    dpg.bind_item_theme(tag_name_text, container_theme)