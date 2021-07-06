
import os
from pathlib import Path
from importlib import import_module
from dataclasses import dataclass
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


operations_list = []


def load_module(path):
    package = 'Heron.Operations'
    extra_package = []
    p = os.path.split(path)
    for i in range(2):
        extra_package.append(p[-1])
        p = os.path.split(p[0])
    package = package + '.' + extra_package[-1]
    package = package + '.' + extra_package[-2]

    module = import_module(package + '.' + name.split('.')[0])
    return module


for path, subdirs, files in os.walk(root):
    for name in files:
        if '_com' in name and 'pycache' not in path:

            module = load_module(path)

            temp = full_split_path(path)
            i = -1
            parent = ''
            while temp[i] != 'Heron':
                parent = parent + temp[i] + '##'
                i = i - 1

            operation = Operation(full_filename=os.path.join(path, name),
                                  name=module.BaseName,
                                  attributes=module.NodeAttributeNames,
                                  attribute_types=module.NodeAttributeType,
                                  parameters=module.ParameterNames,
                                  parameter_types=module.ParameterTypes,
                                  parameters_def_values=module.ParametersDefaultValues,
                                  executable=module.Exec,
                                  parent_dir=parent,
                                  worker_exec=module.WorkerDefaultExecutable)
            operations_list.append(operation)


def create_operation_from_dictionary(op_dict):
    op = Operation(name=op_dict['name'], full_filename=op_dict['full_filename'],
                   attributes=op_dict['attributes'], attribute_types=op_dict['attribute_types'],
                   executable=op_dict['executable'], parent_dir=op_dict['parent_dir'], parameters=op_dict['parameters'],
                   parameter_types=op_dict['parameter_types'], parameters_def_values=op_dict['parameters_def_values'],
                   worker_exec=op_dict['worker_exec'])

    return op