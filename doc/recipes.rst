.. _recipes-recipes:

Recipes
=======

.. epigraph::

  *MacArthur! I can't even get McDonald's!*

  -- Julian Simon

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

.. code-block:: python

  # nsc could be a NetworkedActiveObject or a NetworkedFactory 
  nsc.enable_snoop_trace()
  nsc.start_at(<state_you_want_to_start_at>)

Trace instrumentation is useful for seeing what events caused what state
transitions. They provide you with information about how your design is reacting
to its incoming events.

The snoop trace is an extension of this idea.  It is a network which connects
all of the live trace streams of all of the statecharts that are working
together.  You can see the live trace instrumentation of all of the contributing
nodes, by opting into this snoop trace network.  To do this, you call
``enable_snoop_trace`` prior to starting your statechart (see the code listing
above).

It doesn't take long before this information is hard to see. For this reason, I
coloured the node names. The name of your local machine’s statechart will be
blue, and any other name will be purple in your snoop trace output. You can see
this colouring in the following video:

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/MI8Sym3rCO0?start=36" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>

In the video, I have logged into two different computers that are running the
same statechart program as part of a distributed system.  You can see that the
blue names are different in each terminal window, because we are viewing the
system from two different computers who's statecharts have their own local name.

To print something into the snoop trace use the :ref:`snoop_scribble <recipes-snoop-scribble>`.  

If you want to :ref:`log your snoop trace <recipes-logging-the-snoop-spy>` enable
your trace without the ANSI color codes:

.. code-block:: python

  # nsc could be a NetworkedActiveObject or a NetworkedFactory 
  nsc.enable_snoop_trace_no_color()
  nsc.start_at(<state_you_want_to_start_at>)

You can use the results of your snoop trace to :ref:`generate network sequence
diagrams <recipes-drawing-sequence-diagrams>` for you.

The trace output hides a lot of the details about how your event processor is
searching your statechart to determine how to react to an event.  For this
reason, some statechart dynamics will be invisible to the trace stream; like a
`hook <https://aleph2c.github.io/miros/patterns.html#patterns-ultimate-hook>`_.
If you want to see everything that your statechart is doing, or if you want to
see everything that your entire network is doing turn on the :ref:`snoop_spy <recipes-snoop-spy>`.

.. _recipes-snoop-scribble:

Snoop Scribble
^^^^^^^^^^^^^^
Use the snoop scribble to output custom strings into the snoop trace and snoop
spy networks.

.. code-block:: python

  ao.snoop_scribble("broadcast to all monitoring snoop programs")

The snoop_scribble output is coloured a dark grey so it can be distinguished
from the other parts of the network instrumentation.

If you want to turn off this colouring:

.. code-block:: python

  ao.snoop_scribble("broadcast to all monitoring snoop programs",
                     enable_color=False)

.. _recipes-drawing-sequence-diagrams:

Drawing Sequence Diagrams
^^^^^^^^^^^^^^^^^^^^^^^^^
The text output of a snoop trace can be used to generate sequence diagrams using
the `sequence tool <https://github.com/aleph2c/sequence>`_:

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/GQRh5Bd91O8" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>


.. _recipes-snoop-spy:

Snoop Spy
^^^^^^^^^
.. code-block:: python

  # nsc could be a NetworkedActiveObject or a NetworkedFactory 
  nsc.enable_snoop_spy()
  nsc.start_at(<state_you_want_to_start_at>)

The spy instrumentation shows you *all of the work done* by an event processor.
This really isn't that useful since you will be drown in information.  If you
are having issues with your statechart, you should debug it as a singular
instance before you connect it to a distributed system.  But, if your problem
demands that you see everything that is going on at once, the snoop spy network
provides this capability.

Instead of viewing everything, you could turn on the spy instrumentation on one
machine and have it routed to another machine.  The snoop spy network has an opt
in model, to snoop on others, you need to let them snoop on you.  So to route
another machine's snoop information onto your machine, you will need to release
your information into the snoop spy network.  This may clutter your log stream
with unwanted information.  If this is a concern, you can create a grep filter
using the name of the other node that you are trying to monitor.

It is easy to lose track of the context of what is going on while viewing a
snoop spy, for this reason you might want to enable the snoop spy and snoop
trace at the same time.  You can use the snoop trace output to delimit the
deluge of spy information within the context of state transitions.

.. raw:: html

  <center>
  <iframe width="560" height="315" src="https://www.youtube.com/embed/U_F5icOP87w?start=8" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
  </center>

The name of the local nodes in the distributed system will appear blue and
the names of other nodes will appear purple.

.. _recipes-logging-the-snoop-trace:

Logging The Snoop Trace
^^^^^^^^^^^^^^^^^^^

To removed the ANSI clutter from your log.txt file you can do something like
this (cargo-culted from stack overflow):

.. code-block:: python

  python3 networkable_active_object.py 2>&1 | \
     sed -r 's/'$(echo -e "\033")'\[[0-9]{1,2}(;([0-9]{1,2})?)?[mK]//g' | \
     tee log.txt grep -F [+s] log.txt | grep <name>

Or, turn the colour off when you enable the snoop trace in your code:

.. code-block:: python

  nsc.enable_snoop_trace_no_color()
  nsc.start_at(<state_you_want_to_start_at>)

Then write your trace information to the log.txt without the command-line complexity:

.. code-block:: python

  python3 networkable_active_object.py >> log.txt
 
.. _recipes-logging-the-snoop-spy:

Logging the Snoop Spy
^^^^^^^^^^^^^^^^^^^^^

To removed the ANSI clutter from your log.txt file you can do something like
this (cargo-culted from stack overflow):

.. code-block:: python

  python3 networkable_active_object.py 2>&1 | \
     sed -r 's/'$(echo -e "\033")'\[[0-9]{1,2}(;([0-9]{1,2})?)?[mK]//g' | \
     tee log.txt grep -F [+s] log.txt | grep <name>

Or, turn the colour off when you enable the snoop spy in your code:

.. code-block:: python

  nsc.enable_snoop_spy_no_color()
  nsc.start_at(<state_you_want_to_start_at>)

Then write your spy information to the log.txt without the command-line complexity:

.. code-block:: python

  python3 networkable_active_object.py >> log.txt

.. _recipes-changing-your-rabbitmq-credentials:

Changing your RabbitMQ credentials
----------------------------------
If you are installing RabbitMQ using the :ref:`ansible script in the DevOps section
<installing_infrastructure-have-ansible-install-rabbitmq>`, set the
``rabbit_name`` to the username you want, and the ``rabbit_password`` to
whatever you want your password to be.  Update your code to use your new
credentials.

You can also change your user name and password with the :ref:`RabbitMQ
management GUI<reflection-rabbitmq-management>`.

:ref:`prev <example>`, :ref:`top <top>`, :ref:`next <reflection>`

