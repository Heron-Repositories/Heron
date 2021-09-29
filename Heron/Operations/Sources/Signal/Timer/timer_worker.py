
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import scipy.stats as ss
import scipy.optimize as so
from Heron import general_utils as gu

running = False
delay_generator = None


def constant(a, b, c):
    return a

def uniform(a, b, c):
    return np.random.randint(a, b)

def exponential(a, b, c):
    scale = 1/a
    return np.random.exponential(scale)


def trunc_exp_rv(low, high, scale):
    rnd_cdf = np.random.uniform(ss.expon.cdf(x=low, scale=scale),
                                ss.expon.cdf(x=high, scale=scale),
                                size=1)
    return ss.expon.ppf(q=rnd_cdf, scale=scale)


def solve_for_l(expected_mean, low, high):
    A = np.array([low, high])
    return 1/so.fmin(lambda L: ((np.diff(np.exp(-A*L)*(A*L+1)/L)/np.diff(np.exp(-A*L)))-expected_mean)**2,
                     x0=0.5,
                     full_output=False, disp=False)


def trunc_exp_corrected(a, b, c):
    expected_mean = a
    low = b
    high = c
    return trunc_exp_rv(low, high, solve_for_l(expected_mean, low, high))


def gaussian(a, b, c):
    mu = a
    std = b
    return np.random.normal(mu, std)


def run_timer(worker_object):
    running = False
    delay_generator = None

    while not running:
        try:
            worker_object.visualisation_on = worker_object.parameters[0]
            signal_out = worker_object.parameters[1]
            delay_generator_str = worker_object.parameters[2].split(':')[0]
            a, b, c = worker_object.parameters[3], worker_object.parameters[4], worker_object.parameters[5]

            if 'constant' in delay_generator_str:
                delay_generator = constant
            elif 'random uniform' in delay_generator_str:
                delay_generator = uniform
            elif 'random exponential' in delay_generator_str:
                delay_generator = exponential
            elif 'random truncated exponential' in delay_generator_str:
                delay_generator = trunc_exp_corrected
            elif 'random gaussian' in delay_generator_str:
                delay_generator = gaussian
            print(delay_generator)
            running = True
        except:
            gu.accurate_delay(1)

    while running:
        worker_object.visualisation_on = worker_object.parameters[0]
        worker_object.worker_visualisable_result = np.array([signal_out])
        worker_object.socket_push_data.send_array(worker_object.worker_visualisable_result, copy=False)

        if worker_object.visualisation_on:
            print(worker_object.worker_visualisable_result)

        sleep_for = 1000 * delay_generator(a, b, c)
        gu.accurate_delay(sleep_for)


def on_end_of_life():
    global running

    running = False


if __name__ == "__main__":
    gu.start_the_source_worker_process(run_timer, on_end_of_life)