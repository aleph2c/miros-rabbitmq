.. _example:

Example
========

.. toctree::
   :maxdepth: 1
   :caption: Single Chart Examples:

In this section I will show how to network some statecharts using the miros-rabbitmq plugin.

Here is a diagram that throws all of this example’s ideas at you at once:

.. image:: _static/test_miros_rabbitmq_2.svg
    :target: _static/test_miros_rabbitmq_2.pdf
    :align: center

We see:

* How you can link a NetworkedActiveObject or a NetworkedFactory to a statechart.
* How these networked classes are just generalizations of the miros classes. 
* How they have a standard interface, so they can share the same networking API.
* That they both contain a MirosNets object that does the lion's share of the
  networking for them.

In this example, I’ll create two different objects which implement the
statechart in the diagram. One will use the NetworkedActiveObject class, and the
other will use the NetworkedFactory class.

The pictured statechart is a simple ergotic design that can work on its own or
with one or more statecharts just like it.  If there is more than one of these
statecharts working together, they can run on the same computer in different
processes or on different computers across a network.

The statechart can send events to itself and others.  To avoid any confusion
about where events are coming from we follow a simple coding convention: any
event that is alien to the statechart will have the word 'other' pre-pended
to it's signal name.

Before you begin the example :ref:`get your RabbitMQ installation
working<installing_infrastructure-installing-required-programs>` , then install
the miros and the miros-rabbitmq packages using pip.

The example will be broken down into three parts:

* :ref:`Building a NetworkedActiveObject<example-networkedactiveobject>`
* :ref:`Building a NetworkedFactory<example-networkedfactory>`
* :ref:`Different ways to Troubleshoot Our Programs<example-different-ways-to-troubleshoot-our-programs>`

.. _example-networkedactiveobject:

Building a NetworkedActiveObject
--------------------------------
First we import the required libraries:

.. code-block:: python

  import time
  import uuid # to generate a unique name
  import random
  from miros.hsm import spy_on
  from miros.event import signals, Event, return_status
  from miros_rabbitmq.network import NetworkedActiveObject

Then we construct a function that will generate a unique name for our
statechart:

.. code-block:: python

  def make_name(post):
    return str(uuid.uuid4())[0:5] + '_' + post

Now we consider the statechart part of our design:

.. image:: _static/miros_rabbitmq_example_1.svg
    :target: _static/miros_rabbitmq_example_1.pdf
    :align: center

Then we implement the statechart using the flat-method technique required by
a miros ActiveObject:

.. code-block:: python
  :emphasize-lines: 7,22,50,52,71

  def outer_init(chart, e):
    chart.post_fifo(
      Event(signal=signals.to_inner),
      times=1,
      period=random.randint(2, 7),
      deferred=True)
    chart.transmit(Event(signal=signals.other_to_outer, payload=chart.name))
    return return_status.HANDLED

  def outer_to_inner(chart, e):
    return chart.trans(inner)

  def outer_other_to_inner(chart, e):
    return chart.trans(inner)

  def inner_entry(chart, e):
    chart.post_fifo(
      Event(signal=signals.to_outer),
      times=1,
      period=random.randint(2, 7),
      deferred=True)
    chart.transmit(Event(signal=signals.other_to_inner, payload=chart.name))
    return return_status.HANDLED

  def inner_exit(chart, e):
    chart.cancel_events(Event(signal=signals.to_outer))
    return return_status.HANDLED

  def inner_other_to_inner(chart, e):
    return return_status.HANDLED

  def inner_to_inner(chart, e):
    return return_status.HANDLED

  def inner_to_outer(chart, e):
    return chart.trans(outer)

  def inner_other_to_outer(chart, e):
    return chart.trans(outer)

  @spy_on
  def inner(chart, e):
    status = return_status.UNHANDLED
    if(e.signal == signals.ENTRY_SIGNAL):
      status = inner_entry(chart, e)
    elif(e.signal == signals.INIT_SIGNAL):
      status = return_status.HANDLED
    elif(e.signal == signals.to_outer):
      status = inner_to_outer(chart, e)
    elif(e.signal == signals.other_to_outer):
      status = inner_other_to_outer(chart, e)
    elif(e.signal == signals.other_to_inner):
      status = inner_other_to_inner(chart, e)
    elif(e.signal == signals.to_inner):
      status = inner_to_inner(chart, e)
    elif(e.signal == signals.EXIT_SIGNAL):
      status = inner_exit(chart, e)
    else:
      status, chart.temp.fun = return_status.SUPER, outer
    return status

  @spy_on
  def outer(chart, e):
    status = return_status.UNHANDLED
    if(e.signal == signals.ENTRY_SIGNAL):
      status = return_status.HANDLED
    elif(e.signal == signals.INIT_SIGNAL):
      status = outer_init(chart, e)
    elif(e.signal == signals.to_inner):
      status = outer_to_inner(chart, e)
    elif(e.signal == signals.other_to_inner):
      status = outer_other_to_inner(chart, e)
    elif(e.signal == signals.EXIT_SIGNAL):
      status = return_status.HANDLED
    else:
      status, chart.temp.fun = return_status.SUPER, chart.top
    return status

I have highlighted the `other` event signals in the code listing.  This is to
demonstrate how the statechart will react to such events when they have been
received from another statechart, and how to transmit them out to others.

The `other` event signals received from another statechart are placed in the
FIFO of the active object by the miros-rabbitmq library.  As for as the event
processor is concerned, they are no different than any native event; the only
way that we know they are alien is that we have pre-pended the word 'other' to
them, as a coding convention.

To send a message out to another statechart, you use the ``transmit`` api
provided by the NetworkedActiveObject.

.. note::

  Be careful where you place your transmit calls in your statecharts, since it is
  easy to create an event oscillation between your networked charts.  I tend to
  send out `other` events to the network when a state has been initialized, or
  entered (when it the inner most state).

.. image:: _static/miros_rabbitmq_example_2.svg
    :target: _static/miros_rabbitmq_example_2.pdf
    :align: center

Here we see how to link our statechart to a NetworkedActiveObject.  To link a
statechart to the network, we construct the NetworkedActiveObject with the
networking credentials we use for our RabbitMQ server and our encryption
information.  We turn on whatever instrumentation we would like our statechart
to participate in, then we call the ``start_at`` method.  The call to this
``start_at`` method causes the NetworkedActiveObject object's event
processor to link itself to the statechart we constructed, then it starts up the
state.

.. note:: 
  Remember, ActiveObjects and thereby NetworkedActiveObjects are `polyamourous
  <https://aleph2c.github.io/miros/recipes.html#what-a-state-does-and-how-to-structure-it>`_.
  The same statechart structure can by used be many different
  NetworkedActiveObject's since they hold no state about themselves; they merely
  act as a blueprint.  All of the state information is held within the
  NetworkedActiveObject.

Now that we have a statechart we need to link it to a NetworkedActiveObject.
But before we do that, we need to build the NetworkedActiveObject using:

* the networking credentials we have set up our RabbitMQ server
* a tx_routing key
* a rx_routing key
* the encryption keys that will be used by the other programs in our network.

.. code-block:: python

  ao = NetworkedActiveObject('make_name('ao'),
    rabbit_user='peter',
    rabbit_password='rabbit',
    tx_routing_key='heya.man',
    rx_routing_key='#.man',
    mesh_encryption_key=b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=')

We name our ao using the ``make_name`` function that we built at the top of the
example, it pre-pends 5 digits of a UUID to the front of ``_ao``.
The rabbit_user and rabbit_password, networking credentials are specified when you `install your RabbitMQ server
<installing_infrastructure-installing-required-programs>`_.  The topic
tx_routing_key are used by the RabbitMQ exchanges to publish to different
queues.  A consumer can subscribe to different topics `using a simple pattern
matching technique <https://www.rabbitmq.com/tutorials/tutorial-five-python.html>`_
specified with its rx_routing_key.  In our case our program will receive any
network message from exchanges with the last word of 'man' in their topic.

RabbitMQ supports SSL, but this library doesn't get involved in that.  If you
would like to install SSL, you can, and if it is working this library will
happily sit on top of it and not know that it is transmitting through a secure
connection.  This library does, however, have its own encryption layer for each
of its networks.  It uses symmetric encryption, so that the same key can be used to
encrypt and decrypt an object.

I am about to talk about some of the miros-rabbitmq package details, but you
don't need to know this stuff to make your example work.  So if you want to just
skip over this information and get back to the example click :ref:`here
<back_to_the_example>`.

Let's look at the networks that are turned on with the miros-rabbitmq library
(click to open it as a pdf):

.. image:: _static/miros_rabbitmq_network_1.svg
    :target: _static/miros_rabbitmq_network_1.pdf
    :align: center

The miros-rabbitmq package constructs the following:

* mesh network - used to transmit and receive messages between statecharts
* snoop_trace network - to debug your entire network using `trace
  <https://aleph2c.github.io/miros/recipes.html#using-the-trace>`_ instrumentation
* snoop_spy network - to debug the entire network using the `spy
  <https://aleph2c.github.io/miros/recipes.html#using-the-spy>`_

When you turn on your NetworkedActiveObject, it will scan your LAN looking for
other machines that have the same rabbit credentials that you are using, then it
will create a producer for each of them in each of the networks, so you don't
have to worry about feeding it IP addresses, it will find them if they are
connected in the same TCP/IP network.

Each of the networks can have their own encryption key, but if you only specify
the ``mesh_encryption_key`` in the NetworkedActiveObject constructor it will be
used by all of the networks.  The snoop_trace and snoop_spy encryption handles
for the NetworkedActiveObject constructor, are ``trace_snoop_encryption_key`` and
``spy_snoop_encryption_key``.

To build an encryption key for your distributed system:

.. code-block:: python

  from cryptography.fernet import Fernet
  new_encryption_key = Fernet.generate_key()

As an application developer you just need to know what goes in, and what comes
out of each of the miros-rabbitmq networks.  The mesh network is fed an item
using it's ``transmit`` method.  This information will pop out on every connected
machine with the same credentials, posted into the fifo of another other
connected NetworkedActiveObject or NetworkedFactory object as if that local
machine posted that event to itself as:

.. code-block:: python

  ao.post_fifo(e) # but with e provided from the network


.. _back_to_the_example:



.. _example-networkedfactory:

Building a NetworkedFactory
---------------------------

.. _example-different-ways-to-troubleshoot-our-programs:

Different ways to Troubleshoot Our Programs
-------------------------------------------



