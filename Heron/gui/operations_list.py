
import os
from pathlib import Path
from importlib import import_module
from dataclasses import dataclass
from typing import Optional
from Heron.general_utils import full_split_path

root = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, 'Operations')

@dataclass
class Operation:
    name: str
    full_filename: str
    attributes: list
    attribute_types: list
    parameters: list
    parameter_types: list
    parameters_def_values: list

    executable: str
    parent_dir: str
    worker_exec: str

    tooltip: Optional[str] = None
    attribute_tooltips: Optional[list] = None
    parameter_tooltips: Optional[list] = None


operations_list = []


def load_module(path, name):
    package = 'Heron.Operations'
    extra_package = []
    p = os.path.split(path)
    for i in range(3):
        extra_package.append(p[-1])
        p = os.path.split(p[0])
    package = package + '.' + extra_package[-1]
    package = package + '.' + extra_package[-2]
    package = package + '.' + extra_package[-3]

    module = import_module(package + '.' + name.split('.')[0])
    return module


def generate_operations_list():
    global operations_list
    operations_list = []

    for path, subdirs, files in os.walk(root, followlinks=True):
        for name in files:

            if '_com.py' in name and 'pycache' not in path:

                module = load_module(path, name)

                temp = full_split_path(path)
                i = -1
                parent = ''
                while temp[i] != 'Heron':
                    parent = parent + temp[i] + '##'
                    i = i - 1
                temp = ''
                for piece in parent.split('##')[1:]:
                    temp = temp + piece + '##'
                parent = temp[:-2]

                not_available_text = 'Documentation not available'
                try:
                    tooltip = module.NodeTooltip
                except AttributeError as e:
                    tooltip = not_available_text
                try:
                    params_tooltips = module.ParameterTooltips
                except AttributeError as e:
                    params_tooltips = [not_available_text] * len(module.ParameterNames)
                try:
                    input_output_tooltips = module.InOutTooltips
                except AttributeError as e:
                    input_output_tooltips = [not_available_text] * (
                        len([i for i in module.NodeAttributeType if i != 'Static']))

                operation = Operation(full_filename=os.path.join(path, name),
                                      name=module.BaseName,
                                      attributes=module.NodeAttributeNames,
                                      attribute_types=module.NodeAttributeType,
                                      parameters=module.ParameterNames,
                                      parameter_types=module.ParameterTypes,
                                      parameters_def_values=module.ParametersDefaultValues,
                                      executable=module.Exec,
                                      parent_dir=parent,
                                      worker_exec=module.WorkerDefaultExecutable,
                                      tooltip=tooltip,
                                      parameter_tooltips=params_tooltips,
                                      attribute_tooltips=input_output_tooltips)
                operations_list.append(operation)

    return operations_list


def create_operation_from_dictionary(op_dict):
    op = Operation(name=op_dict['name'], full_filename=op_dict['full_filename'],
                   attributes=op_dict['attributes'], attribute_types=op_dict['attribute_types'],
                   executable=op_dict['executable'], parent_dir=op_dict['parent_dir'], parameters=op_dict['parameters'],
                   parameter_types=op_dict['parameter_types'], parameters_def_values=op_dict['parameters_def_values'],
                   worker_exec=op_dict['worker_exec'], tooltip=op_dict['tooltip'],
                   parameter_tooltips=op_dict['parameter_tooltips'], attribute_tooltips=op_dict['attribute_tooltips'])
    return op


