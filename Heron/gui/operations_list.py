

from dearpygui.simple import *
from dearpygui.core import *
import os
from pathlib import Path
from importlib import import_module
from dataclasses import dataclass

root = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, 'Operations')

@dataclass
class Operation:
    name: str
    full_filename: str
    attributes: list
    attribute_types: list
    executable: str
    parent_dir: str
    node_extras: object


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

            temp =path.split('\\')
            i = -1
            parent = ''
            while temp[i] != 'Heron':
                parent = parent + temp[i] + '##'
                i = i - 1

            operation = Operation(full_filename=os.path.join(path, name),
                                  name=module.BaseName,
                                  attributes=module.NodeAttributeNames,
                                  attribute_types=module.NodeAttributeType,
                                  executable=module.Exec,
                                  parent_dir=parent,
                                  node_extras=module.node_extras)

            operations_list.append(operation)

