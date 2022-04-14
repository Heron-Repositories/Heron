
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
from Heron import general_utils as gu, constants as ct


def initialise(worker_object):
    try:
        visualisation_on = worker_object.parameters[0]
        function_name = worker_object.parameters[1].split(':')[0]
        a, b, c, d = worker_object.parameters[2:]
    except:
        return False

    worker_object.relic_create_parameters_df(visualisation_on=visualisation_on, function_name=function_name,
                                             a=a, b=b, c=c, d=d)
    return True


def create_evaulation_string(parameters):
    function_name = parameters[1].split(':')[0]
    functions_arguments = [t.split('=')[1] for t in parameters[1].split(':')[1].split(',')]
    number_of_variables = len(parameters[1].split(':')[1].split(','))
    string_to_evaluate = 'np.random.{}('.format(function_name)
    for i in range(number_of_variables):
        if parameters[i + 2] != 'None':
            string_to_evaluate = '{}{}={},'.format(string_to_evaluate, functions_arguments[i], parameters[i + 2])
    string_to_evaluate = string_to_evaluate[:-1] + ')'

    return string_to_evaluate


def random_number(data, parameters):

    if parameters is None:
        return np.array([ct.IGNORE])
    else:
        visualisation_on = parameters[0]
        evaluated_string = create_evaulation_string(parameters)
        result = eval(evaluated_string)
        if type(result) is not np.ndarray:
            result = np.array([result])

        if visualisation_on:
            print(result)

        return [result]


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=random_number,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
