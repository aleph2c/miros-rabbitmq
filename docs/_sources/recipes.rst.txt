.. _recipes-recipes:

Recipes
=======

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. _recipes-networked-statecharts:

Networked Statecharts
---------------------
.. _recipes-drawing-statecharts:

Drawing Statecharts
^^^^^^^^^^^^^^^^^^^
`UMLet <http://www.umlet.com/>`_ is a free tool that can be used to make
statechart diagrams (see their statemachine panel).  You can run UMLet from
most operating systems or from your web browser using `UMLetino <http://www.umlet.com/umletino/umletino.html>`_. Here is their training video:

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/3UHZedDtr28" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>

You can adjust their default templates to improve your drawing experience.

To export an UMLet picture from their native uxf to other formats:

.. code-block:: python

  umlet.exe -action=convert -format=pdf -filename=<your_file_name>.uxf
  umlet.exe -action=convert -format=svg -filename=<your_file_name>.uxf

.. _recipes-making-a-networkedactiveobject:

Making a NetworkedActiveObject
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you would like to make `polyamorous statecharts
<https://aleph2c.github.io/miros/recipes.html#what-a-state-does-and-how-to-structure-it>`_
using the flat method technique then the NetworkedActiveObject is for you.

.. code-block:: python

    from miros_rabbitmq import NetworkedActiveObject

    nao = NetworkedActiveObject(
            "name_of_statechart",
            rabbit_user="<rabbitmq_user_name>",
            rabbit_password="<rabbitmq_password>",
            tx_routing_key="heya.man",
            rx_routing_key="#.man",
            mesh_encryption_key=b'u3u...')

To make your :ref:`instrumentation <recipes-snoop-trace>` easier to understand, ensure that all the nodes in
your distributed system have :ref:`different names
<recipes-making-unique-names>`.

The rabbit_user and rabbit_password credentials need to match that of your
:ref:`RabbitMQ server <recipes-making-unique-names>`.

To build your own encryption key(s) see
:ref:`this<recipes-making-an-encryption-key>`.  You can set different encryption
keys for your instrumentation networks; the snoop trace network and the snoop
spy network.  If you do not specify these keys, these networks will use the
mesh_encryption_key.

If you want to specify different encryption keys for your instrumentation
networks:

.. code-block:: python

    from miros_rabbitmq import NetworkedActiveObject

    nao = NetworkedActiveObject(
            "name_of_statechart",
            rabbit_user="<rabbitmq_user_name>",
            rabbit_password="<rabbitmq_password>",
            tx_routing_key="heya.man",
            rx_routing_key="#.man",
            mesh_encryption_key=b'u3u...',
            trace_snoop_encryption_key=b'u4f...',  
            spy_snoop_encryption_key=b's44...',  
            )

The ``nao`` object will have a ``transmit`` method that can be used to put event's
into all of the other subscribed statecharts across the network.  To build your
statechart using the ``nao`` object, you would follow the rules used by 
an `ActiveObject <https://aleph2c.github.io/miros/recipes.html#states>`_.

.. _recipes-networkedfactory:

Making a NetworkedFactory
^^^^^^^^^^^^^^^^^^^^^^^^^^
If you have a preference to build up statecharts using a Factory, but you want
your statecharts to work together across a network, then the NetworkedFactory is
for you:

.. code-block:: python

  from miros_rabbitmq import NetworkedFactory

  nf = NetworkedActiveFactory(
          "name_of_statechart",
          rabbit_user="<rabbitmq_user_name>",
          rabbit_password="<rabbitmq_password>",
          tx_routing_key="heya.man",
          rx_routing_key="#.man",
          mesh_encryption_key=b'u3u...')

To make your :ref:`instrumentation <recipes-snoop-trace>` easier to understand, ensure that all the nodes in
your distributed system have :ref:`different names
<recipes-making-unique-names>`.

The rabbit_user and rabbit_password credentials need to match that of your
:ref:`RabbitMQ server <recipes-making-unique-names>`.

To build your own encryption key(s) see
:ref:`this<recipes-making-an-encryption-key>`.  You can set different encryption
keys for your instrumentation networks; the snoop trace network and the snoop
spy network.  If you do not specify these keys, these networks will use the
mesh_encryption_key.

If you want to specify different encryption keys for your instrumentation
networks:

.. code-block:: python

    from miros_rabbitmq import NetworkedActiveObject

    nf = NetworkedFactory(
            "name_of_statechart",
            rabbit_user="<rabbitmq_user_name>",
            rabbit_password="<rabbitmq_password>",
            tx_routing_key="heya.man",
            rx_routing_key="#.man",
            mesh_encryption_key=b'u3u...',
            trace_snoop_encryption_key=b'u4f...',  
            spy_snoop_encryption_key=b's44...',  
            )

The ``nf`` object will have a ``transmit`` method that can be used to put event's
into all of the other subscribed statecharts across the network.  To build your
statechart using the ``nf`` object, you would follow the rules used by 
a miros `Factory <https://aleph2c.github.io/miros/recipes.html#creating-a-statechart-from-a-factory>`_.


.. _recipes-making-unique-names:

Making Unique Names
^^^^^^^^^^^^^^^^^^^

A simple way to make a unique name:

.. code-block:: python

  import uuid

  def make_name(post):
    return str(uuid.uuid4())[0:5] + '_' + post

  make_name('bob') # => 0ca32_bob

.. _recipes-transmitting-an-event:

Transmitting an Event
^^^^^^^^^^^^^^^^^^^^^
To transmit an event to other connected statecharts use the ``transmit`` method.
This method works the same for a NetworkedActiveObject and a NetworkedFactory:

.. code-block:: python

  from miros.event import signals, Event, return_status

  # where 'chart' is a NetworkedFactory or NetworkedActiveObject object
  def some_function(chart, e):  
    chart.transmit(Event(signal=signals.other_name_of_signal))
    return return_status.HANDLED

When a networked statechart receives this event, it will be posted into it's first
in first out queue.  The statechart will not be able to distinguish that
it was an event coming back from the network.

Follow some sort of signal naming-standard so that you know if your events are
generated locally or from somewhere else on the network.  In this example, the
signal is pre-pended with the word ``other_``, for this reason.


.. _recipes-transmitting-a-payload-in-an-event:

Transmitting a Payload in an Event
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
All information that is passed between networked nodes is serialized, encrypted, decrypted
and de-serialized.  Therefore you can pass an object into your payload that can
be serialized using the standard pickle algorithm for python 3.  So to pass
objects between your statecharts, you can just put them into the payload of an
event.

.. code-block:: python

  from miros.event import signals, Event, return_status

  # where 'chart' is a NetworkedFactory or NetworkedActiveObject object
  def some_function(chart, e):  
    chart.transmit(Event(signal=signals.other_with_payload, payload="a string"))
    return return_status.HANDLED

.. _recipes-node-discovery:

Node Discovery
^^^^^^^^^^^^^^

This is taken care of by the library.  If your node is on your local area network
and it's IP address is in the ARP table or it's computer will respond to a ping;
The miros-rabbitmq library should find it.  If two nodes are on the same network
and share encryption and rabbit credentials they will be able to communicate.

.. _recipes-making-an-encryption-key:

Making an Encryption Key
^^^^^^^^^^^^^^^^^^^^^^^^
The miro-rabbitmq library uses Fernet symmetric encryption.  The same keys need
to be used by all nodes.

To make a new key:

.. code-block:: python

   from cryptography import Fernet
   new_encryption_key = Fernet.generate_key()
    print(new_encryption_key) # => b'u3u...' # => copy this

.. _recipes-snoop-trace:

Snoop Trace
^^^^^^^^^^^

.. _recipes-drawing-sequence-diagrams:

Drawing Sequence Diagrams
^^^^^^^^^^^^^^^^^^^^^^^^^

.. _recipes-snoop-spy:

Snoop Spy
^^^^^^^^^

.. _recipes-logging-snoop-trace:

Logging Snoop Trace
^^^^^^^^^^^^^^^^^^^

.. _recipes-logging-the-snoop-spy:

Logging the Snoop Spy
^^^^^^^^^^^^^^^^^^^^^

.. _recipes-devops:

Devops
------

.. _recipes-setting-up-ssh:

Setting up SSH
^^^^^^^^^^^^^^

.. _recipes-installing-ansible:

Installing Ansible
^^^^^^^^^^^^^^^^^^

.. _recipes-installing-rabbitmq-using-ansible:

Installing RabbitMQ using Ansible
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

