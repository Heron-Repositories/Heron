from setuptools import setup

setup(
    name='Heron',
    version='0.6.0',
    description='A python framework for experimental pipelines',
    url='https://github.com/Heron-Repositories/Heron',
    author='George Dimitriadis',
    author_email = 'gdimitri@hotmail.com',
    license='MIT',
    keywords=['Scientific', 'Cluster', 'Experiments'],
    packages=['Heron'],
    install_requires=['pyzmq>=20.x',
                      'numpy',
                      'dearpygui>=1.2',
                      'paramiko',
                      'opencv-python>=4.5'
                      'pandas',
                      'h5py',
                      'tornado',
                      'pynput',
                      'serial'
                      ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
)
