.. _how_it_works-how-the-plugin-works:

How The Plugin Works
====================
You don't need to understand this page to use this library.  It has been added
to round out the documentation and to be a guide for me when I write other
network plugins for miros.

There are two main classes that you will use with miros to build statecharts,
the `ActiveObject <https://aleph2c.github.io/miros/scribbleexample.html>`_ and
the `Factory
<https://aleph2c.github.io/miros/towardsthefactoryexample.html#towardsthefactoryexample-using-the-factory-class>`_
class.  This plugin extends these two classes as the NetworkedActiveObject and
the NetworkedFactory class.

.. image:: _static/miros_rabbitmq_0.svg
    :target: _static/miros_rabbitmq_0.pdf
    :align: center

To build a state chart you would follow all of the same `rules that you learned
before <https://aleph2c.github.io/miros/recipes.html>`_ and you would get some
additional networking features.

So, if you wanted to have networked statecharts you would install miros,
miros-rabbitmq and RabbitMQ.  If you wanted to build your statechart using flat
methods you would use the NetworkedActiveObject class.  If you would rather
build it up using callbacks you would use the NetworkedFactory class.

Both of these networked classes share the same interface and communicate on the
same infrastructure:  the miros-rabbitmq plugin builds up three topic based AMPQ
networks named the mesh, the snoop_trace and the snoop_spy.

.. image:: _static/miros_rabbitmq_network_0.svg
    :target: _static/miros_rabbitmq_network_0.pdf
    :align: center

The mesh network is used by the statecharts to send encrypted and serialized
events to one another.  The snoop_trace is used to share trace instrumentation
output between all of the connected computers.  It provides the means to debug
your entire distributed system from one location.  The snoop_spy is like the
snoop_trace, but it shares the spy information (a lot of information) between
all of your connected computers.  Each network can be configured with it's own
encryption key.  The snoop_trace and snoop_spy networks can be enabled and
disabled independently, but the mesh is always on.

This plugin's main methods are the ``transmit``, ``enable_snoop_trace``, and
``enable_snoop_spy``.  The NetworkedActiveObject and the NetworkedFactory share
the same interface.

.. image:: _static/miros_rabbitmq_1.svg
    :target: _static/miros_rabbitmq_1.pdf
    :align: center

The ``transmit`` is used to send out an event to the mesh network.  When it is
received by another statechart, it's event is place in it's FIFO queue for
processing.   The statechart receiving such an event, has no notion that the
event came from another machine.  If it has been designed to respond to the
event it will.

The NetworkedActiveObject and NetworkedFactory require more information in their
constructors than do the ActiveObject and the Factory.  This information
describes the credentials required to connect to the RabbitMQ server and the
encryption key(s) for the three different networks.

.. image:: _static/miros_rabbitmq_2.svg
    :target: _static/miros_rabbitmq_2.pdf
    :align: center

The snoop_trace and snoop_spy networks will use the ``mesh_encyption_key`` if a
``trace_snoop_encryption_key`` or a ``spy_snoop_encryption_key`` are not
provided.

The NetworkedActiveObject and NetworkedFactory have a MirosNets object.

.. image:: _static/miros_rabbitmq_3.svg
    :target: _static/miros_rabbitmq_3.pdf
    :align: center

The MirosNets object is the thing that actually builds up the mesh, the snoop_trace and
the snoop_spy networks.  It also provides the means to specify a custom
serializer and de-serializer function.  If custom serialization routines are
not specified it will use pickle version 3.  A MirosNets object can be programmed with
custom callback functions that are triggered when messages are received on any
of the three networks.

The MirosNets class, uses a RabbitScout object to find other machines on the
network.  The RabbitScout builds up a LocalAreaNetwork object which finds all of
the IP addresses on the LAN by pinging the broadcast address, and filling the
ARP table of the machine it is running on.  It uses this ARP table to find a
short list of available IP addresses.  The RabbitScout then initiates contact to
these IP addresses and if a time out doesn't occur, it assumes connections are
possible with that IP address. It uses the working IP addresses to build up a
custom AMPQ_URL and assigns it to it's url attribute.

The MirosNets uses the AMPQ_URL addresses provided by the RabbitScout to build
it's producers.  There is one producer per network for every working AMPQ_URL
provided by the RabbitScout.  To build up a producer MirosNets uses the
PikaTopicPublisher object which wraps the SimplePikaTopicPublisher with
encryption and serialization methods.

The SimplePikaTopicPublisher is the thing that actually performs the network
publishing function of this library.  It is heavily based upon the example
provided in the pika library documentation.  Before using this example as a base
for the publishing feature I used the example provided on the RabbitMQ page.
The code based on these examples would run for about 15 minutes prior to
failing.  Since re-writing everything based on the much more complicated pika
working example the connections have been stable.  

The SimplePikaTopicPublisher class is different than the pika example provided
in their documentation, in that it has a thread and to deliver messages out to
the network, you post them to a fifo, which wakes up the thread.  The pika
example was very mysterious about how it was actually suppose to be used.  There
are a lot of questions about it on stackover flow, more open secrets abound in
this community.  I also added a PID to it's message transmission callback to
have it speed up when the queues are full and slow down when they are empty.


