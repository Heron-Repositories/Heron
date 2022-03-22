
import os
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

from Heron import general_utils as gu
Exec = os.path.abspath(__file__)


# <editor-fold desc="The following code is called from the GUI process as part of the generation of the node.
# It is meant to create node specific elements (not part of a generic node).
# This is where a new node's individual elements should be defined">

"""
Properties of the generated Node
"""
BaseName = 'Random Number Generator'
NodeAttributeNames = ['Parameters', 'Trigger', 'Random Out']
NodeAttributeType = ['Static', 'Input', 'Output']
ParameterNames = ['Visualisation', 'Numpy Function', 'a', 'b', 'c', 'd']
ParameterTypes = ['bool', 'list', 'str', 'str', 'str', 'str']
ParametersDefaultValues = [False, ['randint: a=low, b=high, c=size, d=dtype',
                                   'random: a=size, b=dtype, c=out', 'bytes: a=length', 'beta: a=a, b=b, c=size',
                                   'binomial: a=n, b=p, c=size', 'chisquare: a=df, b=size', 'dirichlet: a=alpha, b=size',
                                   'exponential: a=scale, b=size', 'f: a=dfnum, b=dfden, c=size',
                                   'gamma: a=shape, b=scale, c=size', 'geometric: a=p, b=size',
                                   'gumbel: a=loc, b=scale, c=size',
                                   'hypergeometric: a=ngood, b=nbad, c=nsample, b=size',
                                   'laplace: a=loc, b=scale, c=size',
                                   'logistic: a=loc, b=scale, c=size', 'lognormal: a=mean, b=sigma, c=size',
                                   'logseries: a=p, b=size', 'multinomial: a=n, b=pvals, c=size',
                                   'multivariate_hypergeometric: a=colors, b=nsample',
                                   'multivariate_normal: a=mean, b=cov, c=size',
                                   'negative_binomial: a=n, b=p, c=size', 'noncentral_chisquare: a=df, b=nonc, c=size',
                                   'noncentral_f: a=dfnum, b=dfden, c=nonc, d=size',
                                   'normal: a=loc, b=scale, c=size', ' pareto: a=a, b=size',
                                   'poisson: a=lam, b=size', ' power: a=a, b=size',
                                   'rayleigh: a=scale, b=size', ' standard_cauchy: a=size',
                                   'standard_exponential: a=size, b=dtype, c=method, c=out',
                                   'standard_gamma: a=shape, b=size, c=dtype, d=out',
                                   'standard_normal: a=size, b=dtype, c=out',
                                   'standard_t: a=df, b=size', 'triangular: a=left, b=mode, c=right, d=size',
                                   'uniform: a=low, b=high, c=size', 'vonmises: a=mu, b=kappa, c=size',
                                   'wald: a=mean, b=scale, c=size', 'weibull: a=a, b=size', 'zipf: a=a, b=size'],
                           'None', 'None', 'None', 'None']
WorkerDefaultExecutable = os.path.join(os.path.dirname(Exec), 'random_number_generator_worker.py')

# </editor-fold>


# <editor-fold desc="The following code is called as its own process when the editor starts the graph">
if __name__ == "__main__":
    random_number_generator_com = gu.start_the_transform_communications_process(NodeAttributeType, NodeAttributeNames)
    gu.register_exit_signals(random_number_generator_com.on_kill)
    random_number_generator_com.start_ioloop()
    random_number_generator_com.start_ioloop()

# </editor-fold>
