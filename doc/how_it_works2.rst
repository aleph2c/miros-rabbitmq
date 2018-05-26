How it Works (Design Re-write in Progress)
==========================================


.. _how_it_works2-the-cache-file-chart:

The Cache File Chart
--------------------
The network discovery process is expensive, so we will cache its results to a
JSON file.

The cache will persist beyond the life of the program that wrote it.  When the
next program runs, it will read the cache, determine if it is young enough to be
useful, and if so, it will skip the expensive network discovery process.

We use the JSON format since we will be transmitting this cache to other hosts
and JSON has become the standard format for transmitting data.

But there could be thousands of processes trying to read and write to this cache
file at the same time.  To address this concern, we wrap this file access into
an active object which will check if the file is writable before trying to read
or write from it.  If the file is writable, the statechart will determine that
no other program is using the file.

.. image:: _static/miros_rabbitmq_cache_file_chart.svg
    :target: _static/miros_rabbitmq_cache_file_chart.pdf
    :align: center

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

To perform a scouting mission for a given IP address, you will also need the
routing_key and an exchange_name you want to connect to, then do something like
this:

.. code-block:: python
  
  scout1 = RabbitConsumerScoutChart(
    '192.168.1.77',
    routing_key='heya.man',
    exchange='miros.mesh.exchange',
    live_trace=True)  # to debug the chart

The answer will come back to you in the payload of an asynchronous event named ``AMQP_CONSUMER_CHECK``.
The answer-payload consist of a tuple: ``(<ip address>, <True/False>, <routing_key>, <exchange>)``:

.. code-block:: python

  # Other state chart would catch this 
  # if the IP has a working consumer:
  Event(signal=signals.AMQP_CONSUMER_CHECK,
    payload=(192.168.1.77, True, 'heya.man', 'miros.mesh.exchange'))

  # Other state chart would catch this
  # if the IP does not have a working consumer:
  Event(signal=signals.AMQP_CONSUMER_CHECK,
    payload=(192.168.1.77, False, 'heya.man', 'miros.mesh.exchange'))

To perform another search on the same scout, in another statechart you would
post a ``REFACTOR_SEARCH`` event:

.. code-block:: python

  chart.postfifo(
    Event(signal=signals.REFACTOR_SEARCH,
      payload={
        'ip_address':192.168.1.77,
        'routing_key': 'archer.bob'
        'exchange_name': 'miros.mesh.exchange', 
        }
    )

Later, assuming this search resulted in a miss, the chart that sent out the
``REFACTOR_SEARCH`` would receive the following signal:

.. code-block:: python

  Event(signal=signals.AMQP_CONSUMER_CHECK,
    payload=(192.168.1.77, False, 'archer.bob', 'miros.mesh.exchange'))

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
arguments if they need to debug the statechart encase within the
``RabbitConsumerScoutChart``, but by default this instrumentation is off.  Let's
turn this instrumentation on and then describe what it is doing.  We will do
this twice, once for an address that doesn't have a RabbitMQ server running on
it and a second time with an address that does.

Let's start with failure:

.. code-block:: python

  scout1 = RabbitConsumerScoutChart(
    '192.168.1.77',
    routing_key='heya.man',
    exchange='miros.mesh.exchange',
    live_trace=True)  # to debug the chart

This will result in the following trace instrumentation:

.. code-block:: python
   fontSize: 8

  [2018-05-25 18:50:34.888810] [192.168.1.77] e->start_at() top->producer_thread_engaged
  [2018-05-25 18:50:34.990279] [192.168.1.77] e->try_to_connect_to_consumer() producer_thread_engaged->producer_post_and_wait
  [2018-05-25 18:50:35.569538] [192.168.1.77] e->consumer_test_complete() producer_post_and_wait->no_amqp_consumer_server_found
  ('192.168.1.77', False, 'heya.man', 'miros.mesh.exchange')

Comparing it it's statemachine:

.. image:: _static/search_machine.svg
    :target: _static/search_machine.pdf
    :align: center

Then viewing the information as a sequence diagram:

.. code-block:: python

  [Statechart: 192.168.1.77]
                 top   producer_thread_engaged          producer_post_and_wait    no_amqp_consumer_server_found
                  +--start_at()-->|                                |                             |
                  |     (1)       |                                |                             |
                  |               +--try_to_connect_to_consumer()->|                             |
                  |               |              (2)               |                             |
                  |               |                                +--consumer_test_complete()-->|
                  |               |                                |            (3)              |
  (4) -> ('192.168.1.77', False, 'heya.man', 'miros.mesh.exchange')

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

A very similar process would have been followed had the IP address of
``192.168.1.77`` had a RabbitMQ consumer with the correct credentials.


