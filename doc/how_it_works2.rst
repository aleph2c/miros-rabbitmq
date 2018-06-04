How it Works (Design Re-write in Progress)
==========================================

.. _how_it_works2-the-cache-file-chart:

.. epigraph::

  *You go to war with the army you have, not the army you might want or wish to
  have at a later time*

  -- Donald Rumsfeld

.. _how_it_works2-slight-extension-to-the-diagramming-rules:

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
  light; it is time to go, to act on the event.

The payloads of the published and subscribed events act as an interface for this
asynchronous API.  To keep things clean, all payloads will exist as named
tuples.  These tuples will be put into 'note' icons near the place that they are
made (published) or consumed.

The Cache File Chart
--------------------
The CacheFileChart is used to read and write the network discovery cache
information.  It was designed to:

* be created/started/destroyed within another statechart
* allow one cache file to be readable and writable from thousands of different
  programs running at the same time.
* hide the complexity of a concurrent file read into JSON from the user
* hide the complexity of a file write from JSON from the user
* have a stochastic-exponential-timeout mechanism for pending read/write waits 
* Write a file based on an asynchronous event published from another statechart
* Convert a file read into an asynchronous event which can be subscribed to
  by another statechart
* be easy to debug/document

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
or write from it.  If the file is writable, the statechart will determine that
no other program is using the file.

.. image:: _static/miros_rabbitmq_cache_file_chart.svg
    :target: _static/miros_rabbitmq_cache_file_chart.pdf
    :align: center

To construct the ``CacheFileChart`` with a live trace, for debugging:

.. code-block:: python

  cache_file = CacheFileChart(live_trace=True)

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
    :align: center

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
    :align: center

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
  like 'wreck-ee'.

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

Here is the design diagram for the LanRecceChart, if it is too small, click on
the picture to download a pdf of the diagram:

.. image:: _static/miros_rabbitmq_recce_chart.svg
    :target: _static/miros_rabbitmq_recce_chart.pdf
    :align: center

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
    :align: center

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

.. _how_it_works2-mirosrabbitlanchart:

MirosRabbitLanChart
-------------------
The MirosRabbitLanChart is responsible for publishing all of the working RabbitMQ
consumers that exist on your LAN within a CONNECTION_DISCOVERY event.  It was designed to:

* be created/started/destroyed within another statechart
* use cached information if it hasn't expired (to save time)
* perform a LAN discovery process if the cache is expired, then cache this
  result for the next run of the program
* output a set of working AMQP urls as the payload of the CONNECTION_DISCOVERY
  event.  This will be used by another chart.

.. image:: _static/miros_rabbitmq_lan_discovery.svg
    :target: _static/miros_rabbitmq_lan_discovery.pdf
    :align: center

To build a MirosRabbitLanChart, you will need to know the ``routing_key`` and the
``exchange_name`` that you are trying to connect to:

.. code-block:: python

  MirosRabbitLanChart(
    routing_key='heya.man',
    exchange_name='miros.mesh.exchange',
    live_trace=True)  # to debug or document

By default it will look for a file called ``.miros_rabbitmq_lan_cache.json`` which
will look something like this:

.. code-block:: python

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
MirosRabbitLanChart will transition into it's ``discover_network`` state,
discover the network then write the ``.miros_rabbitmq_lan_cache.json`` file with
the results.

To change the cache file's time out, add ``time_out_in_minutes`` as a named
parameter when you are constructing your ``MirosRabbitLanChart`` object.  Here
is an example of changing the timeout to 60 minutes:

.. code-block:: python

  MirosRabbitLanChart(
    routing_key='heya.man',
    exchange_name='miros.mesh.exchange',
    time_out_in_minutes=60)

