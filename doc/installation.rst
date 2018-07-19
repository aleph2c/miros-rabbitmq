.. miros documentation master file, created by
   sphinx-quickstart on Mon Oct 16 06:18:38 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _installation-installation:

Installation
============

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Before you install miros-rabbitmq you first must :ref:`install RabbitMq <installing_infrastructure-installing-required-programs>` 

To install miros-rabbitmq:

.. code-block:: bash

  python3 -m venv
  . ./venv/bin/activate
  pip install miros-rabbitmq

miros-rabbitmq has been tested on Python 3.5 with pika 0.11.2.  It is dependent
upon miros, pika, netifaces, python-dotenv and cryptography.

:ref:`prev <installing_infrastructure-installing-required-programs>`, :ref:`top <top>`, :ref:`next<quick_start-quick-start>`
