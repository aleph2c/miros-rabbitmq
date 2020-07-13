.. _how_it_works-how-the-plugin-works: 

How it Works
============

.. epigraph::

  *The most contrarian thing of all is not to oppose the crowd but to think for
  yourself.*

  -- Peter Thiel

.. note:: 

  You don't need to understand this page to use this library.  It has been added
  to round out the documentation and to be a guide for writing other network
  plugins for miros.  If a diagram is too small, click on it to see it's pdf.
  If you don't have a lot of time, your time would be better spent looking at
  the :ref:`next example <example>`.

There are two main classes that you will use with miros to build statecharts,
the `ActiveObject <https://aleph2c.github.io/miros/singlechartexample.html>`_ and
the `Factory <https://aleph2c.github.io/miros/towardsthefactoryexample.html#towardsthefactoryexample-using-the-factory-class>`_
class.  This plugin extends these two classes as the NetworkedActiveObject and
the NetworkedFactory class.

.. image:: _static/miros_rabbitmq_0.svg
    :target: _static/miros_rabbitmq_0.pdf
    :align: center

To build a state chart you would follow all of the same `rules that you learned
before <https://aleph2c.github.io/miros/recipes.html>`_ and you would get some
additional networking features.

So, if you wanted to have networked statecharts you would install miros,
miros-rabbitmq and RabbitMQ.  If you wanted to build your statechart using `flat
methods
<https://aleph2c.github.io/miros/recipes.html#boiler-plate-state-method-code>`_ you would use the NetworkedActiveObject class.  If you would rather
build it up using `callbacks <https://aleph2c.github.io/miros/recipes.html#creating-a-statechart-from-a-factory>`_ you would use the NetworkedFactory class.

Both of these networked classes share the same interface and communicate on the
same server infrastructure:  the miros-rabbitmq plugin builds up three topic
based AMPQ networks named the mesh, the snoop_trace and the snoop_spy.  Here is
a RabbitMQ style diagram of these networks.  If you don't understand the diagram
it is explained in more details further down this page.

.. image:: _static/miros_rabbitmq_network_0.svg
    :target: _static/miros_rabbitmq_network_0.pdf
    :class: scale-to-fit

The mesh network is used by the statecharts to send encrypted and serialized
events to one another.  The snoop_trace is used to share `trace instrumentation
<https://aleph2c.github.io/miros/recipes.html#using-the-trace>`_
output between all of the connected computers.  It provides the means to debug
your entire distributed system from one location.  The snoop_spy is like the
snoop_trace, but it shares the `spy information <https://aleph2c.github.io/miros/recipes.html#using-the-spy>`_ (a lot of information) between
all of your connected computers.  Each network can be configured with it's own
encryption key.  The snoop_trace and snoop_spy networks can be enabled and
disabled independently, but the mesh is always on.

This plugin's main methods are the ``transmit``, ``enable_snoop_trace``, and
``enable_snoop_spy``.  The NetworkedActiveObject and the NetworkedFactory share
the same interface.

.. image:: _static/miros_rabbitmq_1.svg
    :target: _static/miros_rabbitmq_1.pdf
    :class: scale-to-fit

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
    :class: scale-to-fit

The snoop_trace and snoop_spy networks will use the ``mesh_encryption_key`` if a
``snoop_trace_encryption_key`` or a ``snoop_spy_encryption_key`` are not
provided.

The NetworkedActiveObject and NetworkedFactory have a MirosNets object.

.. image:: _static/miros_rabbitmq_3.svg
    :target: _static/miros_rabbitmq_3.pdf
    :class: scale-to-fit

The MirosNets object is the thing that actually builds up the mesh, the snoop_trace and
the snoop_spy networks.  It also provides the means to specify a custom
serializer and de-serializer function.  If custom serialization routines are
not specified it will use pickle version 3.  A MirosNets object can be programmed with
custom callback functions that are triggered when messages are received on any
of the three networks.

.. note::

  It doesn't take long before UML class diagrams turn into a poem written for the
  poet himself, a work that no one else understands or wants to endure.  My
  pictures are about to reach this level of conceit; their utility
  diminishes with the addition of each detail.  If you're going to follow this
  design I recommend using whatever code navigation tool you have installed.
  I'll colour the parts of the diagram so you know what the docs are referencing
  in the picture.

.. image:: _static/miros_rabbitmq_4.svg
    :target: _static/miros_rabbitmq_4.pdf
    :class: scale-to-fit

The MirosNets class builds up and manages the three RabbitMQ networks which are
accessible from each node in your system.  Before I explain it I would like to
talk more about the networks, and how RabbitMQ structures its network topology.

Let's first talk about one network, then talk about all of the networks.

Each RabbitMQ node in the network needs one consumer and one or more producers: one producer for
every other node in the network.

Here is a simplified drawing of a single node on a network:

.. image:: _static/network_1.svg
    :target: _static/network_1.pdf
    :class: noscale-center

.. note::

  Normally RabbitMQ drawings contain and exchange and a queue, but we will remove
  this information from our drawings to make them easier to understand.

It is easy to build a consumer using pika with RabbitMQ.  You just need to know
the RabbitMQ credentials for the machine it is running on.

Things are a more complicated when you want to build a producer.  Each producer
needs to know the address and the RabbitMQ credentials for the server running on
the machine it wants to talk to.  Often your program won't know these details
when it starts.  It will have to search the network to find other machines it
can communicate with.

I'll try to express this idea with a picture. Consider three nodes in a network:

.. image:: _static/network_3.svg
    :target: _static/network_3.pdf
    :class: noscale-center

Before a node's producers can communicate with other nodes, they have to
discover that nodes network address.  Once a producer has this information, it
can establish a connection with that other node's consumer. (draw an arrow)

Let's add a bit more detail.  Each network will have a symmetric encryption key
and a serialization/deserialization (pickle) technique.  The consumer on the
local node and all of the producers on all other nodes will have to share these
ways of doing things.

I'll try to express these ideas with a picture of a network containing two
nodes:

.. image:: _static/network_2_complicated.svg
    :target: _static/network_2_complicated.pdf
    :class: scale-to-fit

Any message sent from a program will be serialized and encrypted then dispatched
to each of its producers.  Each producer will send this information out to it's
consumer.  After a consumer receives a message it will decrypt then deserialize
the message.  The deserilization process will turn the bytestream back into a
Python object.  This Python object will be sent out to the program using the
miros-rabbitmq library.

Now consider the RabbitMQ way of drawing our networks:

.. image:: _static/miros_rabbitmq_network_0.svg
    :target: _static/miros_rabbitmq_network_0.pdf
    :class: scale-to-fit

We see that the producers communicate their messages to an exchange, which is
actually running on many machines.  The RabbitMQ people merge their exchange
diagrams together in what I think is a kind of short hand.  There is an exchange
on your client, and there is an exchange with the same name on each of the nodes
it is talking to.  They show it as one exchange to simplify their network
drawings.

So, the statechart which wants to transmit and event across it's network will
use the ``transmit`` api of the NetworkedFactory or NetworkedActiveObject class.
It will be sent across the network, and end up in the queue of every other
attached active object, as if the event was posted into it's fifo.  The user
shouldn't have to worry about how this is done.

Now what happens when a new node is discovered on the network, but your program
has already been started?  No problem, the miros-rabbitmq library will update
all of it's producers lists in each of its networks so that this node can be
reached.

There is actually a concurrent statechart that manages this part of the library,
it is derived from the
:ref:`ProducerFactoryChart<how_it_works2-the-producer-factory-chart>` class.
The ProducerFactoryChart outputs all of it's newly discovered producers as an
item in a queue.  This item is in the form of a ProducerQueue named tuple.

.. image:: _static/medium_context_producer_factory.svg
    :target: _static/medium_context_producer_factory.pdf
    :class: noscale-center

To launch this producer discovery process, the ProducerFactoryChart needs to be
built within the MirosNets class with a queue from which it will pluck any new
producer list:

.. code-block:: python

  # top of program
  from queue import Queue as ThreadQueue
  # .
  # .
  # code in MirosNets __init__ method
  self.producers_queue = ThreadQueue()

  # The producer factory chart will update the producers_queue with new
  # producers as they are found
  self.producer_factory_chart = ProducerFactoryChart(
    producer_queue=self.producers_queue,
    mesh_routing_key=self.mesh.tx_routing_key,
    mesh_exchange_name=self.mesh.exchange_name,
    mesh_serialization_function=self.mesh.serializer,
    snoop_trace_routing_key=self.snoop.trace.routing_key,
    snoop_trace_exchange_name=self.snoop.trace.exchange_name,
    snoop_spy_routing_key=self.snoop.spy.routing_key,
    snoop_spy_exchange_name=self.snoop.spy.exchange_name)

  self.mesh.producers = []
  self.snoop.spy.producers = []
  self.snoop.trace.producers = []
    
The MirosNet object, which starts the ProducerFactoryChart monitors it's
producer queue at the moment it receives a transmit message:

.. code-block:: python

  def transmit(self, event):
    if self.update_producers():
      self.start_threads()
    for producer in self.mesh.producers:
      producer.post_fifo(event)

The ``update_producers`` method looks like this:

.. code-block:: python

  def update_producers(self):
    discovered = False
    if not self.producers_queue.empty():
      q = self.producers_queue.get(block=False)
      # if we have made producers before stop them now
      if self.mesh.producers:
        self.stop_threads()
      self.mesh.producers = q.mesh_producers
      self.snoop.trace.producers = q.snoop_trace_producers
      self.snoop.spy.producers = q.snoop_spy_producers
      discovered = True
    return discovered

To summarize the producer discovery process: MirosNets constructs a
:ref:`ProducerFactoryChart<how_it_works2-the-producer-factory-chart>` with a
queue.  The ``transmit`` method, will see if new producers have been put in this
queue.  If new producers were discovered, the old producers will have their threads turned
off, and the new producers will have their threads started and the item that is being
transmitted out to the network will be posted into the object that is running
each producer.

A producer is actually built using a PikaTopicPublisher object which wraps the
SimplePikaTopicPublisher with encryption and serialization methods.

The SimplePikaTopicPublisher is the thing that actually performs the network
publishing function of this library.  It is heavily based upon the `asynchronous
pika publisher example
<http://pika.readthedocs.io/en/0.11.2/examples/asynchronous_publisher_example.html>`_
provided in the pika library documentation.

Before using this example as a base for the publishing feature I used the
example provided on the RabbitMQ page.  The code based on these examples would
run for about 15 minutes prior to failing.  I gave up trying to troubleshoot the
issue because of the slow feedback time between failures.  Since re-writing
everything based on the much more complicated `asynchronous pika publisher
example
<http://pika.readthedocs.io/en/0.11.2/examples/asynchronous_publisher_example.html>`_
the connections have been stable.  

.. note::

  The pika example was very mysterious about how it was actually
  suppose to be used.  There are a lot of questions about it on stackover flow;
  more open secrets abound in this community.

The SimplePikaTopicPublisher class is different than the pika asynchronous
publisher example provided in their documentation, in that it has a thread who's
sole purpose is to wrap the ``run`` method provided by their example.  The ``run``
method runs forever, and no code below it in the file will ever have access to
the CPU.  So, by wrapping the ``run`` method in a thread, it can do its thing
without destroying the program flow.  This ``run`` method provides an event loop
in which pika can send out messages to the network using callbacks, the most
important of which is the ``producer_heart_beat``.  When this ``producer_heart_beat``
callback is called, it checks a queue to see if anyone in another thread wants to
send something.  If so, it creates a partial function from the
``publish_message`` callback using the message provided by the queue.  It then
schedules the new wrapped ``publish_message`` to be called immediately by the
pika event loop.  After clearing the queue in this way, it schedules itself with
the pika event loop so that it will be rerun sometime in the future.  I added
some code to control this time-out duration.  If there are a lot of messages in
the queue, the ``producer_heart_beat`` will occur quicker than it did before, if
there are no items in the queue it will relax its time-out duration to it's
slowest default tempo.  This tempo-time-control feature was made using a
PID controller.

.. image:: _static/miros_rabbitmq_network_0.svg
    :target: _static/miros_rabbitmq_network_0.pdf
    :class: scale-to-fit

The MirosNets only has one consumer per network.  The consumer's responsiblity is
to respond to messages coming from the RabbitMQ service, to decrypt,
de-serialize them then to dispatch them out to whatever needs to know about this
information.  In the case of the Mesh network, a message is dispatched into the
statechart's FIFO.  In the case of the snoop trace and snoop spy networks, the
messages are formatted with colour and output to the terminal.

.. image:: _static/miros_rabbitmq_6.svg
    :target: _static/miros_rabbitmq_6.pdf
    :class: noscale-center

The PikaTopicConsumer provides the decryption and deserialization for each
network consumer.  

PikaTopicConsumer is a subclass of SimplePikaTopicConsumer, which is heavily
based upon the `asynchronous pika consumer example.
<http://pika.readthedocs.io/en/0.11.2/examples/asynchronous_consumer_example.html>`_

The PikaTopicConsumer class is different from the `asynchronous pika consumer
example.
<http://pika.readthedocs.io/en/0.11.2/examples/asynchronous_consumer_example.html>`_
in that it wraps the ``run`` method in a thread (as in the producer). The
``run`` method starts a pika event loop.  A
``timeout_callback_method`` runs within pika producer's event loop.  It checks to see if
another thread wants to stop the consumer, if so, it kills the pika event loop,
if not, it registers itself as a callback sometime in the future.

The ``on_message`` of PikaTopicConsumer class is never called because it is
overloaded by the PikaTopicConsumer.  The ``on_message`` method of the
PikaTopicConsumer decrypts and deserializes any message received by RabbitMq.
It takes the result and passes it onto the
``message_callback`` that was registerd with the class.  This
``message_callback`` is provided in it's constructor.  It is the MirosNets class
which constructs 3 (one per network) of these objects and its ``on_message``
callback functions are provided by the NetworkedActiveObject and
NetworkedFactory.  The common ``on_message`` behavior of the
NetworkedActiveObject and NetworkedFactory are provided by the
MirosNetsInterface.

Slight Extension to the Diagramming Rules
-----------------------------------------
When building a statechart which publishes events and subscribes to events it is
important to see these locations on your map.  They are the inputs and outputs
of your statechart.  These pub/sub events are decoupled calls to software that
doesn't exist on the page, so I have added two little coloured dots on my
diagrams to make things easier to see.

* A red dot is placed near an event that is publishing a signal.  A publishing
  event puts something into a queue which is waiting for attention.  So, it is
  stopped, like being at a red light.
  
* A green dot is placed near an event that has been subscribed to and has been
  published somewhere else in the software system.  It is green, like a green
  light; it is time to go.

The payloads of the published and subscribed events act as an interface for this
asynchronous API.  To keep things clean, all payloads will exist as named
tuples.  These tuples will be put into 'note' icons near the place that they are
made (published) or consumed.

.. _how_it_works2-the-producer-factory-chart:

The Producer Factory Chart
--------------------------
The ``ProducerFactoryChart`` is used to build RabbitMQ producers as they are
discovered by the miros-rabbitmq library.

Before you can build a producer, you need to know what other RabbitMQ server it
is aimed at on the network.  Then you have to provide its constructor with all
of the RabbitMQ credentials, encryption keys and other parameters so that it is
build up properly.  Furthermore, the miros-rabbitmq library needs three
producers per target in the network, one for the mesh network and two for the
different instrumentation channels.  The ``ProducerFactoryChart`` tries to hide
all of this complexity from the user.  It was designed to:

* Initiate a search for other RabbitMQ servers on the LAN, using the :ref:`LanChart <how_it_works2-the-lanreccechart>`
* Initiate a search based on the user's manual network settings, using the :ref:`ManNetChart<how_it_works2-manual-netword-chart>`
* Respond to messages from unknown hosts with the correct encryption credentials
  (Aliens).
* React to the discovery of servers running RabbitMQ instances with the correct
  encryption and RabbitMQ credentials by building up instances of three
  different producers per discovery: a mesh producer and a snoop trace and snoop
  spy producer.
* Serve up it's constructed list of producers to another thread, using a queue.

To understand the point of the ``ProducerFactoryChart`` we need to look at the
RabbitMQ architectural diagram used by the miros-rabbitmq plugin:

.. image:: _static/miros_rabbitmq_network_0.svg
    :target: _static/miros_rabbitmq_network_0.pdf
    :class: scale-to-fit

The hard part about setting up the above diagram is building the producer
collections.

The three different networks each have their own producer objects which are
pre-loaded with the destination information of the servers that they want to
communicate with.  The members of the producer collection can change as new
servers are discovered, or removed from the network.  It is the job of the
``ProducerFactoryChart`` to keep these lists up to date for the other parts of
the program that need them.

The ``ProducerFactoryChart`` actually works by orchestrating a number of
different state charts.  It builds the
:ref:`ManNetChart<how_it_works2-manual-netword-chart>` and the :ref:`LanChart
<how_it_works2-the-lanreccechart>`, which in turn build the statecharts that
they need.

.. image:: _static/small_context_producer_factory.svg
    :target: _static/small_context_producer_factory.pdf
    :class: noscale-center

From a very high level the ``ProducerFactoryChart``, consumes
``CONNECTION_DISCOVERY`` events and puts its newly constructed producers into a
queue using the ``ProducerQueue`` namedtuple:

.. image:: _static/medium_context_producer_factory.svg
    :target: _static/medium_context_producer_factory.pdf
    :class: scale-to-fit

The thread which consumes this queue doesn't have to deal with any of the
producer construction complexity.  It will just check to see if a new item was
added to the queue, if so, it will update it's producers with the information in
this new item.

The actual architectural diagram of the ``ProducerFactoryChart`` can be seen
here:

.. image:: _static/miros_rabbitmq_producer_discovery.svg
    :target: _static/miros_rabbitmq_producer_discovery.pdf
    :class: noscale-center

The class which makes a RabbitMQ producer is called the ``ProducerFactory``, it is
subclassed as the ``MeshProducerFactory``, ``SnoopTraceProducerFactory`` and
``SnoopSpyProducerFactory``.  The ``ProducerFactoryAggregator`` class is a
subclass of the miros ``Factory``, its purpose is to contain all of the worker
methods that are custom to the ``ProducerFactoryChart``.

The ``ProducerFactoryChart`` inherits from the ``ProducerFactoryAggregator``, so
that it has access to all of its needed worker methods and the event processor
from the ``miros`` ``Factory`` class.

To build a ``ProducerFactoryChart``, you will first need to provide a custom
serializer function for dealing with miros Event objects and you will need a
queue where it will place it's results, then you provide the routing_key and
exchange information:

.. code-block:: python

  import queue
  def custom_serializer(obj):
    if isinstance(obj, Event):
      obj = Event.dumps(obj)
    pobj = pickle.dumps(obj)
    return pobj

  q = queue.Queue()

  producer_refactory = ProducerFactoryChart(
     producer_queue=q,
     mesh_routing_key = 'heya_man',
     mesh_exchange_name = 'miros.mesh.exchange',
     mesh_serialization_function=custom_serializer,
     snoop_trace_routing_key = 'snoop.trace',
     snoop_trace_exchange_name = 'miros.snoop.trace',
     snoop_spy_routing_key = 'snoop.spy',
     snoop_spy_exchange_name = 'miros.snoop.spy',
     live_trace=True
  )

In the above listing I also enabled the trace.  This is useful for debugging and
documenting how the ``ProducerFactoryChart`` state machine works.

Look at the state machine part of this diagram:

.. image:: _static/miros_rabbitmq_producer_discovery.svg
    :target: _static/miros_rabbitmq_producer_discovery.pdf
    :class: noscale-center

We see that in the ``ProducerFactoryChart`` that there are three states, the
``producer_discovery``, the ``post_to_queue`` and the ``refactor_producers``
states.  When the ``ProducerFactoryChart`` is constructed, it immediately
transitions into the ``producer_discovery`` state.

The ``producer_discovery`` creates the
:ref:`ManNetChart<how_it_works2-manual-netword-chart>` and the
:ref:`LanChart<how_it_works2-mirosrabbitlanchart>` upon entry.  It subscribes to
the ``CONNECTION_DISCOVERY`` event and stops.  The ``ProducerFactoryChart``
doesn't know or care how connections are discovered, it is up to the other
charts to do this work.  All it does is convert new IP information into working
producers which can be used by the thread pending on it's output queue.  This
new IP information is delivered to it in ``CONNECTION_DISCOVERY`` events.

Upon receiving a ``CONNECTION_DISCOVERY`` event from either the
:ref:`ManNetChart<how_it_works2-manual-netword-chart>` object or the
:ref:`LanChart<how_it_works2-mirosrabbitlanchart>` object, it determines if any
new IP addresses were discovered.

The first time a ``CONNECTION_DISCOVERY`` event is received this will
undoubtedly be true.  It determines what the new IP addresses are and what all
of the IP addresses are.  If there is new information it will post a
``ips_discovered`` event to itself.  Then it tries to destroy which ever chart
delivered the message.  The actual destruction of the object will be done by the
Python garbage collector, the ``producer_discovery`` state just stops
referencing the object so that the garbage collector will see that it is no
longer being used.

The purpose of the ``post_to_queue`` state is to defer any
``CONNECTION_DISCOVERY`` events from occurring while the state chart is dealing
with an exception from posting to the ``producer_queue``.  This is an example of
the `deferred event
<https://aleph2c.github.io/miros/patterns.html#patterns-deferred-event>`_
statechart pattern.  By using this pattern, we are modifying the sequence of
events.  To make sense of this, place your eyes on the
``chart.producer_queue.put`` syntax in the ``refactor_producers`` part of the
statechart.  If there is an exception here, like if the queue is full because
the other part of the program hasn't cleared it yet, we need to try posting to
the queue again in the future.  So, we start a one_shot timer with a time
between 0.1 and 1 second.  We pick a random time so as to avoid any issues with
other parts of the program trying to do the same thing.  Now suppose we are
waiting to try posting to our queue again and another ``CONNECTION_DISCOVERY``
event comes in?  What do we do?  Well, we deferred the event into the deferred
event queue, only releasing it back to the statechart upon exiting the
``post_to_queue`` state.  Sometime in the future
the ``ips_discovered`` event is fired and captured by the ``post_to_queue``
state so that it can try to post the queue again.  If it succeeds, a ``ready``
event will fire, which will cause the ``exit`` event of the ``post_to_queue``
state to fire.  This will recall the ``CONNECTION_DISCOVERY`` event that was
salted away and the whole discovery process can be started again.

The ``refactor_producers`` state entry condition creates a set of new producers
using the ``make_mesh_producers``, ``make_snoop_trace_producers`` and the
``make_snoop_spy_producers`` worker functions defined within the
``ProducerFactoryAggregator`` class.  The new producers are appended into their
appropriate collections, then these collections are organized into the
``ProducerQueue`` namedtuple.  This namedtuple object is place into the queue.
If there is a problem with this process, the activity described in the previous
paragraph is followed.  If there are no problems, the thread pending on this
queue can extract the new producer information as it sees fit.  

After successfully putting the new producer information into the queue, the
statechart posts a ``ready`` signal to itself.  This will allow it to process
any pending ``CONNECTION_DISCOVERY`` events.

.. _how_it_works2_aliens:

The ProducerFactoryChart also has a way of reacting to a previously unknown
machine sending messages with the correct mesh encryption key, and using the
correct RabbitMQ credentials.  For lack of a better word, let's call these nodes
Aliens.  A machine that will not respond to a ping on the LAN and who's address
we forgot to add to our ``.miros_rabbitmq_hosts`` file, but who still knows
about us, is an example of an Alien.

.. image:: _static/medium_context_miros_nets.svg
    :target: _static/medium_context_miros_nets.pdf
    :class: noscale-center

It is the MirosNets class that can discover Aliens.  It has a list of
``ip_addresses`` that it updates when it receives items in it's
``producers_queue``.

It also receives messages from other nodes, and after it has decrypted the
message, it can look to see who sent the message during it's deserialization
step.

If it hasn't seen this address before, it constructs a
ConnectionDiscoveryPayload, adds it to a ``CONNECTION_DISCOVERY`` event and
feeds this to the ProducerFactoryChart.

The ProducerFactoryChart uses this information to create the three different
producers, and then feeds this information back to the MirosNets object using
the producers_queue.  The MirosNet's updates its list of known ``ip_addresses``
and starts communicating to the Alien using the producers provided to it by the
ProducerFactoryChart.  At this point, the Alien node is no longer really an
Alien anymore, because the node is known and it is being spoken too.

.. _how_it_works2-mirosrabbitlanchart:

LanChart
--------
The LanChart is responsible for finding other RabbitMQ servers on your Local
Area Network.  It publishes its results into a CONNECTION_DISCOVERY event.  It was
designed to:

* be created/started/destroyed within another statechart
* use cached information if it hasn't expired (to save time)
* perform a LAN discovery process if the cache is expired, then cache this
  result for the next run of the program
* output a set of working AMQP urls as the payload of the CONNECTION_DISCOVERY
  event.

The LanChart is built by the :ref:`ProducerFactoryChart<how_it_works2-the-producer-factory-chart>`.  The LanChart doesn't search the LAN or reference the cache directly, it gets this information from a :ref:`LanRecceChart<how_it_works2-the-lanreccechart>` and a :ref:`CacheFileChart<cfc>` object:

.. image:: _static/small_context_lan_chart.svg
    :target: _static/small_context_lan_chart.pdf
    :class: noscale-center

From a high level, the LanChart subscribes to 2 events and publishes 4 events:

.. image:: _static/medium_context_lan_chart.svg
    :target: _static/medium_context_lan_chart.pdf
    :class: scale-to-fit

Here is the architectural diagram for this statechart:

.. image:: _static/miros_rabbitmq_lan_discovery.svg
    :target: _static/miros_rabbitmq_lan_discovery.pdf
    :class: scale-to-fit

To construct a LanChart use the ``routing_key`` and the
``exchange_name`` of the RabbitMQ servers you are trying to connect to:

.. code-block:: python

  LanChart(
    routing_key='heya.man',
    exchange_name='miros.mesh.exchange',
    live_trace=True)  # to debug or document

By default it will look for a file called ``.miros_rabbitmq_lan_cache.json`` which
will look something like this:

.. code-block:: JSON

  {
    "addresses": [
      "192.168.1.75"
    ],
    "amqp_urls": [
      "amqp://bob:dobbs@192.168.1.75:5672/%2F?connection_attempts=3&heartbeat_interval=3600"
    ],
    "time_out_in_minutes": 30
  }

If the cached file is older than the ``time_out_in_minutes``,
LanChart will transition into it's ``discover_network`` state,
discover the network then write the ``.miros_rabbitmq_lan_cache.json`` file with
the results.

To change the cache file's time out, add ``time_out_in_minutes`` as a named
parameter when you are constructing your ``LanChart`` object.  Here
is an example of changing the timeout to 60 minutes:

.. code-block:: python

  LanChart(
    routing_key='heya.man',
    exchange_name='miros.mesh.exchange',
    time_out_in_minutes=60)

.. _how_it_works2-the-lanreccechart:

The LanRecceChart
-----------------
.. note::

  The word Recce is the Canadian/British way of saying recon.  Recon, is the
  short form of the word reconnaissance.  I didn't know this before I googled
  recon, but being a good Canadian I decided to use ``recce`` to name the
  objects and classes in the part of the design, instead of the word recon (we
  all have to do our parts to resist American cultural hegemony).

  Being new to the word I had to figure out how to say it, recce is pronounced
  like 'wreck-ee'. (I learned this from an American)

The LanRecceChart performs multiple scouting missions of your local area network
for compatible RabbitMQ consumers.  The LanRecceChart was designed to:

* be created/started/destroyed within another statechart
* hide the complexity of the local area networking search details
* build a set of search criterion based on it's LAN discovery process
* rely on the RabbitConsumerScoutChart specialists to perform the individual
  scouting missions for compatible RabbitMQ consumers.
* perform all of it's scouting missions in parallel
* work in Linux and on the Windows Linux Subsystem
* provide it's result in the form of asynchronous events to which other
  statecharts can subscribe.
* be easy to debug/document

The LanRecceChart is build by the
:ref:`LanChart<how_it_works2-mirosrabbitlanchart>` object and it builds many
different :ref:`RabbitConsumerScoutChart<how_it_works2-producescoutchart>`
objects:

.. image:: _static/small_context_lan_recce_chart.svg
    :target: _static/small_context_lan_recce_chart.pdf
    :class: noscale-center

From a high level, the LanRecceChart subscribes the ``RECCEN_LAN`` event and
publishes the ``LAN_RECCE_COMPLETE`` event.

.. image:: _static/medium_context_lan_recce_chart.svg
    :target: _static/medium_context_lan_recce_chart.pdf
    :class: scale-to-fit

Here is the design diagram for the LanRecceChart, if it is too small, click on
the picture to download a pdf of the diagram:

.. image:: _static/miros_rabbitmq_recce_chart.svg
    :target: _static/miros_rabbitmq_recce_chart.pdf
    :class: scale-to-fit

The LanRecce class, inherited by the LanRecceChart contains all of the methods
required to search your local area network and your local machine for the IP
addresses needed to begin a search for compatible RabbitMQ consumers.  The three
main methods used by the LanRecceChart during the dynamic portion of it's life
are:

  * ``LanRecce.get_working_ip_address``
  * ``ping_to_fill_arp_table``
  * ``candidiate_ip_addresses``

The rest of the methods help these main methods perform their required tasks.

To build a CacheFileChart with a live_trace:

.. code-block:: python

  lan_recce = LanRecceChart(
      routing_key='heya.man',
      exchange_name='miros.mesh.exchange',
      live_trace=True)

The LanRecceChart does not start itself.  The statechart that wants to start the
network reconnaissance will have to publish a ``RECCE_LAN`` event or use the
``post_fifo`` method on the ``LanRecceChart`` object with the ``RECCE_LAN``
event.  Let's just post to it directly using the ``post_fifo`` method:

.. code-block:: python

  lan_recce.post_fifo(Event(signals.RECCE_LAN))

Now let's look at the trace:

.. code-block:: python

  [2018-05-27 09:56:54.372046] [lan_recce_chart] e->start_at() top->private_search
  [2018-05-27 09:56:54.372522] [lan_recce_chart] e->recce_lan() private_search->fill_arp_table
  [2018-05-27 09:56:58.386858] [lan_recce_chart] e->arp_time_out() fill_arp_table->identify_all_ip_addresses
  [2018-05-27 09:56:58.454212] [lan_recce_chart] e->ip_addresses_found() identify_all_ip_addresses->recce_rabbit_consumers
  [2018-05-27 09:57:00.048376] [lan_recce_chart] e->lan_recce_complete() recce_rabbit_consumers->private_search

Compare this trace with it's statechart:

.. image:: _static/miros_rabbitmq_recce_chart.svg
    :target: _static/miros_rabbitmq_recce_chart.pdf
    :class: scale-to-fit

Compare the statechart within the ``LanRecceChart`` class to the sequence diagram with a description:

.. code-block:: python

  [Statechart: lan_recce_chart]
             top     private_search  fill_arp_table  identify_all_ip_addresses  recce_rabbit_consumers
              +-start_at()->|              |                      |                        |
              |    (1)      |              |                      |                        |
              |             +-recce_lan()->|                      |                        |
              |             |    (2)       |                      |                        |
              |             |              +----arp_time_out()--->|                        |
              |             |              |         (3)          |                        |
              |             |              |                      +--ip_addresses_found()->|
              |             |              |                      |          (4)           |
              |             +<-------------+----------------------+--lan_recce_complete()--|
              |             |              |                      |          (5)           |

1. The ``LanRecceChart`` starts itself in the ``private_search`` state.
   Immediately upon entering the ``private_search`` state the state machine
   subscribes to the ``RECCE_LAN`` and ``AMQP_CONSUMER_CHECK`` events.  The
   ``RECCE_LAN`` event will be used by some outside statechart to begin a search
   of the local network and the ``AMQP_CONSUMER_CHECK`` events will be initiated
   within the ``recce_rabbit_consumers`` state, talked about in step 4.
   
   After subscribing to the public events it uses the ``get_working_ip_address``
   static to get it's working IP address.

2. In response to our posted ``RECCE_LAN`` event the chart posts a private
   ``recce_lan`` event and begins a search of the local area network.  Notice
   that while the state machine is within the ``lan_recce`` state, all
   additional ``RECCE_LAN`` events will be deferred until the state is exited.
   This is an example of the `deferred event pattern <https://aleph2c.github.io/miros/patterns.html#patterns-deferred-event>`_.

   After the event processor enters the ``lan_recce`` state, it's initialization
   signal causes a transition into the ``fill_arp_table``.  Upon entering the
   ``file_arp_table`` the state machine pings the broadcast address of the local
   network to fill the arp table and triggers a one shot event called
   ``ARP_FILL_TIME_OUT`` to fire in ``lan.arp_time_sec``.  This value can be
   passed into the LanRecceChart as an optional parameter, by default it is set
   to 2 seconds.

3. 2 seconds after step 2, the ``ARP_FILL_TIME_OUT`` one shot is fired, causing
   a transition into the ``identify_all_ip_addresses`` state.  Upon entering
   this state the state machine determines what the network addresses are by
   reading the arp table within a call to the ``candidiate_ip_addresses``
   method.  It then posts the ``ip_address_found`` event to itself.

4. At this stage, each of the discovered IP addresses is used to begin a
   scouting mission.  The missions run in parallel using their own
   ``RabbitConsumerScoutChart`` instance.  When a mission is completed, the
   result is published by the ``RabbitConsumerScoutChart`` within the payload of
   the ``AMQP_CONSUMER_CHECK`` event and caught and handled within the
   ``recce_rabbit_consumers`` state.

   When all of the searches have returned their respect ``AMQP_CONSUMER_CHECK``
   the IP addresses that have been confirmed to have a RabbitMQ consumer are put
   into the payload of a ``LAN_RECCE_COMPLETE`` event and published to the task
   fabric so that any statechart subscribing to this event will receive the
   results of the reconnaissance of the local network.

.. _how_it_works2-producescoutchart:

The Rabbit Consumer Scout Chart
-------------------------------
The RabbitConsumerScoutChart searches an IP address to see if there is a
compatible RabbitMQ consumer running on it.  The RabbitConsumerScoutChart was
designed to:

* be created/started/destroyed within another statechart
* run in parallel with other instances of itself (to speed up searches of large LANs)
* ensure that the RabbitMQ credentials were not in the code base
* ensure that the encryption secrets where not in the code base
* hide the complexity of the pika producer's creation process
* provide the capability to be run many times with different search criterion
* provide it's answers in the form of asynchronous events to which other
  statecharts can subscribe.
* be easy to debug/document

The RabbitConsumerScoutChart is built by
:ref:`ManNetChart<how_it_works2-manual-netword-chart>` and the
:ref:`LanRecceChart<how_it_works2-the-lanreccechart>` objects:

.. image:: _static/small_context_rabbit_consumer_scout_chart.svg
    :target: _static/small_context_rabbit_consumer_scout_chart.pdf
    :class: noscale-center

From a high level, the RabbitConsumerScoutChart sends a message after it has
been constructed with the required RabbitMQ credentials.  It's search can also
be refactored with the REFACTOR_SEARCH event:

.. image:: _static/medium_context_rabbit_consumer_scout_chart.svg
    :target: _static/medium_context_rabbit_consumer_scout_chart.pdf
    :class: noscale-center

To perform a scouting mission for a given IP address, you will need the
routing_key and an exchange_name that you want to connect to, then do something
like this:

.. code-block:: python
  
  scout1 = RabbitConsumerScoutChart(
    '192.168.1.77',
    routing_key='heya.man',
    exchange='miros.mesh.exchange',
    live_trace=True)  # to debug the chart

The above call would construct a statechart, start it and scout the network with
the provided information.  

Upon completing it's scouting mission, the ``scout1`` object would answer in
the form of an asynchronous event named ``AMQP_CONSUMER_CHECK``.  The answer
will be in the payload of the event in the form of a namedtuple: 

``AMQPConsumerCheckPayload(ip_address, result, routing_key, exchange_name)``:

To get access to this answer within the statechart initiating the search, it
would have to be subscribed to the event (usually done in the entry condition of
the outer state):

.. code-block:: python

  chart.subscribe(Event(signals.AMQP_CONSUMER_CHECK))

For the subscribing state machine to extract the answer it would need to react
to the ``AMQP_CONSUMER_CHECK`` event. Here is how you would do that within a
miros Factory object:

.. code-block:: python

  # The callback used to see the event
  def callback_AMQP_CONSUMER_CHECK(lan, e):
    status = return_status.HANDLED
    ip = e.payload.ip_address
    result = e.payload.result
    routing_key = e.payload.routing_key
    exchange_name = e.payload.exchange_name

    if result:
      print("AMQP consumer at searched location")
    else:
      print("AMQP consumer NOT at searched location")


  # linking a state to an event and it's callback
  some_state = recce.create(state='some_state'). \
    catch(signals.AMQP_CONSUMER_CHECK, 
          handler=recce_rabbit_consumers_AMQP_CONSUMER_CHECK). \
    to_method()

To perform another search on the same ``scout1`` object, post a ``REFACTOR_SEARCH`` event to it:

.. code-block:: python

  scout1.postfifo(
    Event(signal=signals.REFACTOR_SEARCH,
      payload={
        'ip_address':192.168.1.77,
        'routing_key': 'archer.bob'
        'exchange_name': 'miros.mesh.exchange', 
        }
    )

Here is the design diagram from the RabbitConsumerScoutChart, if you can't see
it, click on it to download a pdf of the diagram:

.. image:: _static/miros_rabbitmq_consumer_scout_chart.svg
    :target: _static/miros_rabbitmq_consumer_scout_chart.pdf
    :class: scale-to-fit

The ``RabbitConsumerScout`` class contains the data and methods that are used by
the ``RabbitConsumerScoutChart``.  The ``RabbitConsumerScout`` class basically
hides the complexity of building a RabbitMQ producer by asking the
``RabbitTopicPublisherMaker`` object to make the producer for it.  This
``RabbitTopicPublisherMaker`` object, accesses the hidden credentials from the
``.env`` file tucked away somewhere in an outer directory.  The diagram tries to
describe how this information is stored in an ``.env`` file, loaded into the
environment then used by the ``RabbitTopidPublisherMaker`` class to build up a
topic publisher.

The ``RabbitConsumerScoutChart`` inherits from the ``RabbitConsumerScout``
class, so it gets the publisher as part of the deal.  The client basically needs
to provide it an IP address, a routing key and an exchange name and it is ready
to perform a search.  A user can provide the ``live_trace`` and ``live_spy``
arguments if they need to debug the statechart encased within the
``RabbitConsumerScoutChart``, but by default this instrumentation is off.  Let's
turn this instrumentation on and then describe what it is doing.  We will search
for an address that doesn't have a RabbitMQ server running on it:

.. code-block:: python

  scout1 = RabbitConsumerScoutChart(
    '192.168.1.77',
    routing_key='heya.man',
    exchange='miros.mesh.exchange',
    live_trace=True)  # to debug the chart

This will result in the following trace instrumentation:

.. code-block:: python

  [2018-05-25 18:50:34.888810] [192.168.1.77] e->start_at() top->producer_thread_engaged
  [2018-05-25 18:50:34.990279] [192.168.1.77] e->try_to_connect_to_consumer() producer_thread_engaged->producer_post_and_wait
  [2018-05-25 18:50:35.569538] [192.168.1.77] e->consumer_test_complete() producer_post_and_wait->no_amqp_consumer_server_found
  AMQPConsumerCheckPayload(ip_address='192.168.1.77', result=False, routing_key='heya.man', exchange_name='miros.mesh.exchange')

To see what is going on, compare the above trace to the state machine in this diagram:

.. image:: _static/miros_rabbitmq_consumer_scout_chart.svg
    :target: _static/miros_rabbitmq_consumer_scout_chart.pdf
    :class: scale-to-fit

Here we will turn the trace into a sequence diagram, then explain what happens
during each event:

.. code-block:: python

  [Statechart: 192.168.1.77]
                 top   producer_thread_engaged          producer_post_and_wait    no_amqp_consumer_server_found
                  +--start_at()-->|                                |                             |
                  |     (1)       |                                |                             |
                  |               +--try_to_connect_to_consumer()->|                             |
                  |               |              (2)               |                             |
                  |               |                                +--consumer_test_complete()-->|
                  |               |                                |            (3)              |
  (4) -> 
    AMQPConsumerCheckPayload(
      ip_address='192.168.1.69',
      result=False,
      routing_key='heya.man',
      exchange_name='miros.mesh.exchange')

1.  We see that when the state machine starts, it initializes itself into the
    ``search`` state which builds a ``scout.producer`` object and subscribes the
    machine with the global ``REFACTOR_SEARCH`` event.  Upon completing these
    tasks the ``search`` state is issued the ``INIT_SIGNAL`` which causes the
    state machine to enter the ``producer_thread_engaged`` state.  Upon entering
    this state the ``scout.produer``'s thread is started and a delayed one-shot
    ``try_to_connect_to_consumer`` event is built, then started.  This
    one-shot is intended to give the ``scout.producer`` thread enough time to
    turn itself on before we start using it.

2.  About 200 ms after step 1, the ``try_to_connect_to_consumer``
    one-shot event causes a transition out of the ``producer_thread_engaged``
    state into the ``producer_post_and_wait`` state.  Upon entering the
    ``producer_post_and_wait`` state, the state machine sends a test message out
    to any consumer that might exist on the IP address being searched.  There is
    a lot happening in the background; the message is setup as a random string
    of character, it's encrypted and serialized by the ``scout.producer``, it's
    routing key and exchange information and RabbitMQ credentials are stamped
    onto it.  This is really of no concern to the state machine, all of this
    work is being done within the ``scout.producer`` object.

    Once the message is sent the ``producer_post_and_wait`` state arms a
    ``consumer_test_complete`` one-shot to fire in 500 ms.  This means that the
    consumer, if it exists has half a second to respond to our search otherwise
    the state machine will conclude that it is not there.

3.  The ``consumer_test_complete`` event is fired roughly 500 ms after the end
    of step 2.  This causes a call to the signal hygiene ``cancel_events`` method,
    then the state machine checks the results of the producer's search by looking at
    it's ``scout.producer.connect_error`` flag.  In this case no connection was
    made so the flag is set to True.  This causes a transition into the
    ``no_amqp_consumer_server_found`` state.  Upon entering the state the public
    event ``AMQP_CONSUMER_CHECK`` is made with a four element tuple result:

    .. code-block:: python

       ('192.168.1.77', False, 'heya.man', 'miros.mesh.exchange')

4. Some other statechart that has subscribed to the ``AMQP_CONSUMER_CHECK``
   will catch this event and determine that the address 192.168.1.77 will not
   respond to the RabbitMQ credentials, the encryption key with the current
   topic key and exchange name.


.. _cfc:

The Cache File Chart
--------------------
The CacheFileChart is used to read and write the network discovery cache
information.  It was designed to:

* be created/started/destroyed within another statechart
* allow one cache file to be readable and writable from thousands of different
  programs running at the same time.
* hide the complexity of concurrent file reads from the user
* hide the complexity of concurrent file writes from the user
* have a stochastic-exponential-timeout mechanism for pending read/write waits 
* Write a file based on an asynchronous event published from another statechart
* Convert a file read into an asynchronous event which can be subscribed to
  by another statechart
* be easy to debug/document
* run even if the json file doesn't exist or is empty

The network discovery process is expensive, so we will cache its results to a
JSON file.

The cache will persist beyond the life of the program that wrote it.  When the
next program runs, it will read the cache, determine if it is young enough to be
useful, and if so, it will skip the expensive network discovery process.

We use the JSON format since we will be transmitting this cache to other hosts
and JSON has become the standard format for transmitting data.

There could be thousands of processes trying to read and write to this cache
file at the same time.  To address this concern, we wrap this file access into
an active object which will check if the file is writable before trying to read
from it or write to it.  If the file is writable, the statechart will determine
that no other program is using the file.  The statechart that manages this file
access is called the CacheFileChart.

The CacheFileChart is build by the
:ref:`ManNetChart<how_it_works2-manual-netword-chart>` and the
:ref:`LanChart<how_it_works2-mirosrabbitlanchart>`.

.. image:: _static/small_context_cache_file_chart.svg
    :target: _static/small_context_cache_file_chart.pdf
    :class: noscale-center

From a high level, the CacheFileChart responds to three messages and delivers
one:

.. image:: _static/medium_context_cache_file_chart.svg
    :target: _static/medium_context_cache_file_chart.pdf
    :class: scale-to-fit

The architectural diagram for the CacheFileChart is here:

.. image:: _static/miros_rabbitmq_cache_file_chart.svg
    :target: _static/miros_rabbitmq_cache_file_chart.pdf
    :class: scale-to-fit

To construct the ``CacheFileChart`` with a live trace, for debugging:

.. code-block:: python

  cache_file = CacheFileChart(live_trace=True, default_json="")

To read the file, subscribe to the ``CACHE`` event, then publish a
``CACHE_FILE_READ`` event to the active fabric and wait for a ``CACHE`` event to
come back.  This ``CACHE`` event will contain a dictionary version of the JSON
cache file.

Here is a bit about how it works:

The design was intended to be built within another statechart and to start
itself upon being constructed.  The CacheFileChart subscribes to the
``CACHE_FILE_WRITE`` and the ``CACHE_FILE_READ`` events.  If any other part of the
program wants to see what is in the cache, they would post a ``CACHE_FILE_READ``.
The CacheFileChart will send a ``CACHE`` event with the contents of the cache and
whether the cache has been expired.

If any other statechart would like to write the cache, they would place the
contents of the write into a dict as the payload of the ``CACHE_FILE_WRITE``.

Internally the ``CACHE_FILE_READ`` and ``CACHE_FILE_WRITE`` public events are turned
into the ``file_read`` and ``file_write`` events.  When the state chart sees that such
an event is posted it will try to enter the file_read or file_write states.
Such transitions can be blocked if the file is not writable (set by the OS).  In
the case that the event is blocked, the statechart re-posts the same event to
itself at a future time, then stops running.  The re-posting time is a random
number between 0.001 and a timeout.  This timeout parameter increases for each
re-posting failure, to a maximum value of 5 seconds.

If a ``file_read`` or ``file_write`` event succeeds to transition past the file access
state, it will lock the file by making it un-writable.  This global state, put
onto the file by the operating system will make the file exclusive to this
program.  When the file is read or written, the CacheFileChart will post either
a read_successful or write_successful event to itself.  This will cause an exit
signal to occur on the file_accessed state, which will make the file writable.
Other programs will now have the ability to access the same file when their
deferred ``file_read`` or ``file_write`` events fire.

The internal code within the file_read and file_write states was taken from
various stack overflow articles describing how to safely read and write a file
in a very short period of time, in an environment where many other programs are
trying to do the same thing.

.. note::

  The CacheFileChart was designed to work within the limited POSIX file features
  offered by the Windows Linux Subsystem.  So, it should run on Windows, Linux
  and the various Apple operating systems.


.. _how_it_works2-manual-netword-chart:

Manual Network Chart
--------------------
The ManNetChart lets a user to specify the addresses they
want to use in their network. It was designed to:

* Reference a simple JSON file for it's information
* By default this file is called ``.miros_rabbitmq_hosts.json``, but this can be
  overridden by setting a path in the ManNetChart constructor.
* This JSON file will contain host information in the form of an IP address or
  as a standard URL (not the complicated AMQP URL)
* Test all manual addresses prior delivering them to the ProducerFactoryChart.
* Re-evaluate the hosts file to see if any connections that were listed that
  didn't work, are working.

The ManNetChart is built by the :ref:`ProducerFactoryChart<how_it_works2-the-producer-factory-chart>`.  The ManNetChart makes one
:ref:`CacheFileChart<cfc>` object and many different :ref:`RabbitConsumerScoutChart<how_it_works2-producescoutchart>` objects:

.. image:: _static/small_context_man_net_chart.svg
    :target: _static/small_context_man_net_chart.pdf
    :class: noscale-center

The ManNetChart subscribes to 3 events and publishes 2 events.

.. image:: _static/medium_context_man_net_chart.svg
    :target: _static/medium_context_man_net_chart.pdf
    :class: scale-to-fit

The file that the ``ManNetChart`` uses defaults to
``.miros_rabbitmq_hosts.json``.  It is just a JSON file listing the hosts that
you want in your networks:

.. code-block:: JSON

  {
    "hosts": [
      "192.168.1.75",
      "www.my_host_as_a_url.com"
    ]
  }

You would specify the path to the file in the constructor, along with the mesh
routing key, the mesh exchange name and, if you want instrumentation turned on:

.. code-block:: python

    man_net_chart = ManNetChart(
      routing_key="heya.man",
      exchange_name="sex_change",
      cache_file_path=".miros_rabbitmq_hosts.json")

The cache_file_path is an optional parameter, if you don't set it, it will
default to using the .miros_rabbitmq_cache_file_chart in the current directory.
Likewise the ``live_trace`` and ``live_spy`` are default parameters, they default
to ``False``.

The ManNetChart architectural diagram can be seen here:

.. image:: _static/miros_rabbitmq_manual_discovery.svg
    :target: _static/miros_rabbitmq_manual_discovery.pdf
    :class: scale-to-fit

The ``MirosRabbitManualNetwork`` class inherits from the miros ``Factory``
class, so it has the event processor and all of the other required state chart
features provided by the miros library.  It also contains all of the worker
functions and useful attribute names that are needed by the ``ManNetChart``
class.

When the ``ManNetChart`` is created it immediately starts in the
``read_and_evaluate_network_details`` state.  It subscribes to the
``AMQP_CONSUMER_CHECK`` event.  It constructs a
``CacheFileChart``, subscribes to this chart's ``CACHE`` event then publishes a
``CACHE_FILE_READ`` to it and stops processing.

When the ``CACHE`` event is heard, if the ``CACHE`` event contains a file name
that matches to one provided to the ``ManNetChart`` constructor, it assigns it
to the hosts attribute and transitions to the ``evaluate_network`` state.

Upon entering the ``evaluate_network`` state, a RecceNode named tuple is made
for each host address that was listed in the hosts file.  Within this RecceNode
named tuple is a :ref:`RabbitConsumerScoutChart<how_it_works2-producescoutchart>`.

The ``RabbitConsumerScoutChart`` will start itself and determine if the address
provided to it has another miros-rabbitmq program running on it with the same
encryption keys and RabbitMQ credentials.  It finishes it search by sending out
the ``AMQP_CONSUMER_CHECK`` event with the results in its payload.

The ``AMQP_CONSUMER_CHECK`` could be coming at this chart from another part of
the system, so we confirm that its results are something that we care about then
process it:

* setting the scout attribute of the RecceNode named tuple to None so that the
  Python garbage collector will remove the ``RabbitConsumerScoutChart`` that was
  used to conduct the search
* assigning the ``live_hosts``, ``list_amqp_urls``, ``dead_hosts`` and
  ``dead_amqp_urls`` attributes.
* determining if our search is complete by looking at the ``searched`` attribute all
  of our candidate RecceNodes.

If the search is complete, we post a ``network_evaluated`` event, which is
caught by a hook in the outer state.

The ``network_evaluated`` hooks publishes the ``CONNECTION_DISCOVERY`` event
with the ``live_hosts`` and the ``live_amqp_urls`` tabulated during the
``evaluate_network``.

Notice that the ``ManNetChart`` stays in the ``evaluate_network`` state upon
completing a search.  If another search is required, the ``EVALUATE_HOSTS_FILE``
event can be sent to the chart.  It might makes sense to send such an event
periodically if you would like to see if any of the dead hosts have become
responsive.

