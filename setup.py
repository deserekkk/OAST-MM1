from setuptools import setup

setup(
    name='OAST Simulator',
    version='0.1',
    description='M/M/1 queue simulator',
    install_requires=[
        'numpy',
        'scipy'
    ],
    packages=['simulation']
)
