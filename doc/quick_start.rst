.. _quick_start-quick-start: 

Quick Start
===========

.. epigraph::

  *Failure is the seed of success* 

  -- Kaoru Iskikawa

``miros-rabbitmq`` uses a ping-broadcast to your local area network (LAN) to
fill your ARP table with the IP addresses of all of your locally connected
devices.  Then it tries to connect to the addresses in the ARP table using
RabbitMQ and the encryption key you provide to it's constructor.  If it can
connect, it will communicate with this device when you transmit messages from
your NetworkedActiveObject or NetworkedFactory objects.

To construct a NetworkedActiveObject or NetworkedFactory:

.. code-block:: python

  from miros_rabbitmq import NetworkedActiveObject, NetworkedFactory

  # treat the above classes as ActiveObject and Factory but with changes to
  # their constructor, a way to transmit and a way to turn on the live trace and
  # spy across the network

  ao =  NetworkedActiveObject("name_1",
          rabbit_user = 'peter',
          rabbit_password = 'rabbit', 
          tx_routing_key = 'bob.marley',
          rx_routing_key = '#.marley',
          mesh_encyption_key = b'u3u..')

  fo =  NetworkedFactory("name_1",
          rabbit_user = 'peter',
          rabbit_password = 'rabbit', 
          tx_routing_key = 'bob.marley',
          rx_routing_key = '#.marley',
          mesh_encyption_key = b'u3u..')

To make a new encryption key:

.. code-block:: python

  from cryptography import Fernet
  Fernet.generate_key() # => b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='

To start your network threads:

.. code-block:: python

  # just use the start_at method as you would before
  ao.start_at(<name_of_state>)
  fo.start_at(<name_of_state>)

To transmit events to another statechart in the network:

.. code-block:: python

  from miros.event import Event
  from miros.event import signals

  # This will let you post into the FIFOs of machines that have a rx_routing_key
  # that matches your tx_routing_key and has the correct encryption information
  ao.transmit(Event(signal=signals.HI_FROM_ANOTHER_MACHINE))
  fo.transmit(Event(signal=signals.HELLO_FROM_A_NETWORKED_FACTORY))

To turn on the live trace for a network:

.. code-block:: python

  # Run this code prior to the start_at method
  ao.enable_snoop_trace()
  ao.start_at(<state_you_want_to_start_at>)

To turn on the live spy you would just use the ``enable_snoop_spy()`` method
instead.

:ref:`prev<installation-installation>`, :ref:`top <top>`, :ref:`next<how_it_works-how-the-plugin-works>`
