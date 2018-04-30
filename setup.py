"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],

    name='miros-rabbitmq',
    py_modules=['miros-rabbitmq'],

    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.0.19',

    description='A rabbitmq network support library for miros',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/aleph2c/miros-rabbitmq',

    # Author details
    author='Scott Volk',
    author_email='scottvolk@gmail.com',

    # Choose your license
    license='Python 3.5 license',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Python Software Foundation License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    keywords='iot hsm HSM statechart hierarchical state machine statemachine miros pika rabbitmq netifaces cryptography botnet',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['docs', 'test', 'experiment', 'plan']),

    install_requires=[
      'pika',
      'miros',
      'netifaces',
      'cryptography',
    ],
)
