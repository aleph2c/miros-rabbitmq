.. _reflection:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Reflection
==========

.. epigraph::

  *We cannot solve our problems with the same thinking we used when we created
  them.*

  -- Albert Einstein

If you build a complex distributed system using a statechart you will need some
way to debug it.  The miros-rabbitmq library provides two different encrypted
topic based networks called the
:ref:`snoop_trace<reflection-snoop-trace-network>` and the
:ref:`snoop_spy<reflection-snoop-spy-network>` network.  To turn a network on,
you enable it `before` calling ``start_at`` in your statechart.

RabbitMQ has :ref:`management plugin<reflection-rabbitmq-management>` which can
be viewed to understand it's infrastruture.

.. _reflection-snoop-trace-network:

Snoop Trace Network
-------------------

.. code-block:: python

  chart.enable_snoop_trace() # enable snoop trace network
  chart.start_at(outer)      # the start the chart

To use this network, call ``enable_snoop_trace`` on your NetworkedActiveObject
or NetworkedFactory prior to calling the ``start_at`` method of the statechart.

Enabling the trace does two things, a program instance will:

* send it's trace information to every other enabled-snoop-trace-instance in
  the distributed system.
* receive the trace information from every other enabled-snoop-trace-instance in
  the distributed system.

For the snoop network to work all of the enabled-snoop-trace-instances will need
the same symmetric encryption key, and the snoop_trace network can have a
different symmetric encryption key from the mesh and the snoop_spy networks.
You would set this encryption key in the initialization call of the
NetworkedActiveObject or the NetworkedFactory, using the
``snoop_trace_encryption_key`` named attribute.  If you do not explicitly set
this key, the ``mesh_encryption_key`` will be used to encrypt the snoop trace
information.

To create an encryption key which will be accepted by this library, use Fernet:

.. code-block:: python

  from cryptography import Fernet
  Fernet.generate_key() # => b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='

Your snoop trace stream will have a lot of information coming back from each of
the contributing nodes in the distributed system. The library colours the names
in the trace stream to help you distinguish where the log data is coming from:
the local process names are blue, and the names of the logs coming from other
nodes are purple.

While this colouring is helpful in your terminal, it can become problematic when
trying to log; the ANSI colour codes look like garbage in your log file. For
this reason, an enable_snoop_trace_no_color API is provided in both of the
NetworkedActiveObject and NetworkedFactory classes. You would use the
``enable_snoop_trace_no_color`` call on the node where you would redirect the
snoop_trace output to a log file:

.. code-block:: python
  
  chart.enable_snoop_trace_no_color()
  chart.start_at(outer)

Then you could redirect the trace streams into your log file in your call to the
program:

.. code-block:: python

  > python3 <name_of_distrubed_instance>.py >> distributed_trace.log

Both the NetworkedActiveObject and the NetworkedFactory classes provide a way to
make print statements into the snoop_trace_network. To write custom information
into the snoop trace network, you would call the ``snoop_scribble`` method:

.. code-block:: python

  ao.snoop_scribble("Some message to be seen by all monitoring nodes")

.. _reflection-snoop-spy-network:

Snoop Spy Network
-----------------
The snoop spy network behaves the same as the snoop trace network.  But it
outputs a lot more information than the trace; the kind that would be useful
while debugging a local statechart; but would quickly become overwhelming in a
distributed system.  For this reason, you will want to log this information to
file, then examine this file after the fact using filters (grep).

Like the snoop trace, the snoop spy must be enabled to participate in the snoop
network:

.. code-block:: python

  chart.enable_snoop_spy_no_color()   # enable the snoop spy network
  chart.start_at(outer)               # the start the chart

By enabling the snoop spy, a program instance will:

* send it's spy information to every other enabled-snoop-spy-instance in
  the distributed system.
* receive the spy information from every other enabled-snoop-spy-instance in
  the distributed system.

For the snoop network to work all of the enabled-snoop-spy-instances will need
the same symmetric encryption key, and the snoop_spy network can have a
different symmetric encryption key from the mesh and the snoop_trace networks.
You would set this encryption key in the initialization call of the
NeNetworkedActiveObject or the NetworkedFactory, using the
``snoop_spy_encryption_key`` named attribute.  If you do not explicitly set
this key, the ``mesh_encryption_key`` will be used to encrypt the snoop trace
information.

To create an encryption key which will be accepted by this library, use Fernet:

.. code-block:: python

  from cryptography import Fernet
  Fernet.generate_key() # => b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='

If you would like to debug your local statechart while seeing how it behaves
with the other nodes in your distributed system, you might enabled the snoop spy
on one machine and the snoop trace on the rest of the machines.  This would
output the spy log peppered with trace information describing the state changes
of the other contributing members.  If you were to debug this way you might want
the colored turned on, so that the name of the spy information of your local
instance is blue:

On the machine where you will monitor the spy information:

.. code-block:: python

  # On machine where you want to see it's spy information
  chart.enable_snoop_spy()    # enable the snoop spy network
  chart.enable_snoop_trace()  # enable the snoop trace network
  chart.start_at(outer)       # the start the chart

On the other machines (or processes) in your distributed system:

.. code-block:: python

  # On every other machine to provide context for the spy trace
  chart.enable_snoop_trace()
  chart.start_at(outer)

The spy information will be invisible to all machines which have not turned it
on.  Only the first machine will have spy information written to it's terminal.

If you wanted to output all spy information, on all machines, then log it to
file:

.. code-block:: python

  # On every other machine to provide context for the spy trace
  chart.enable_snoop_spy()    # everyone outputs and receives the spy
  chart.enable_snoop_trace()  # (optional)
  chart.start_at(outer)

Then in the terminal you would redirect this stream to a log file:

.. code-block:: python

  > python3 <name_of_distrubed_instance>.py >> distributed.log

To view the spy information for one instance in the log, say it was called
``2771f_ao``, you could use grep to first find your spy logs then to find this
name:

.. code-block:: python

  grep -F [+s] distributed.log | grep 2771f_ao

The result would look like a typical non-networked, spy log of that machine as
if you were looking at it within it's instance alone.

Both the NetworkedActiveObject and the NetworkedFactory classes provide a way to
make print statements into the snoop_spy_network. To write custom information
into the snoop spy network, you would call the ``snoop_scribble`` method:

.. code-block:: python

  ao.snoop_scribble("Some message to be seen by all monitoring nodes")

.. _reflection-local-instrumentation:

Local Instrumentation
---------------------
In many situations you might want to mix a local trace or spy with their
networked version.

For instance, you may want to do this if you using the orthogonal component
pattern.  The orthogonal component will not output it's trace or spy information
into the managing thread's instrumentation stream; so to see if you will have to
explicitly write it to the screen.

There is nothing stopping you from turning on your local instrumentation while
participating with the snoop networks.

.. _reflection-rabbitmq-management:

RabbitMQ Management
-------------------
To see what your RabbitMQ server is doing, you can run it's management web app
by typing `<IP Address>:15672 <http://localhost:15672/#/>`_ into your browser.
Then log into it using the rabbit_name and rabbit_password you used in your
installation process.  If you installed your rabbitMQ server using the
:ref:`ansible script in the DevOps section
<installing_infrastructure-have-ansible-install-rabbitmq>`, the expected
Username is **peter** and the Password is **rabbit**.

Once you have logged in, you should see this page:

.. image:: _static/RabbitMQ.PNG
    :align: center

From this portal you can change your user name and password (then make sure to
update the credentials in your miros-rabbitmq calls).


.. _reflection-network-information:

Reflecting upon the Network Information
---------------------------------------

.. _reflection-accessing-all-ip-address-seen-on-the-lan:

Accessing all IP address seen on the LAN
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  from miros_rabbitmq import NetworkedActiveObject

  nao = NetworkedActiveObject(
          "name_of_statechart",
          rabbit_user="<rabbitmq_user_name>",
          rabbit_password="<rabbitmq_password>",
          tx_routing_key="heya.man",
          rx_routing_key="#.man",
          mesh_encryption_key=b'u3u...')

  print(nao.lan.other.addresses) # => \\
    ['192.168.1.66',
    '192.168.1.69',
    '192.168.1.70',
    '192.168.1.71',
    '192.168.1.254']

.. _reflection-this-ip-address:

This IP address
^^^^^^^^^^^^^^^
.. code-block:: python

  from miros_rabbitmq import NetworkedActiveObject

  nao = NetworkedActiveObject(
          "name_of_statechart",
          rabbit_user="<rabbitmq_user_name>",
          rabbit_password="<rabbitmq_password>",
          tx_routing_key="heya.man",
          rx_routing_key="#.man",
          mesh_encryption_key=b'u3u...')

  print(nao.lan.this.address) # => 192.168.1.75

.. _reflection-viewing-other-node-amqp-urls:

Viewing Other Node AMQP URLs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To view the AMQP URLS used by the mesh, snoop_trace and snoop_spy networks:

.. code-block:: python

  from miros_rabbitmq import NetworkedActiveObject

  nao = NetworkedActiveObject(
          "name_of_statechart",
          rabbit_user="<rabbitmq_user_name>",
          rabbit_password="<rabbitmq_password>",
          tx_routing_key="heya.man",
          rx_routing_key="#.man",
          mesh_encryption_key=b'u3u...')

  print(nao.other_urls()) # => \\
    ['amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600']

.. _reflection-thisnodeampqpurl:

Viewing this Node's AMQP URL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

  from miros_rabbitmq import NetworkedActiveObject

  nao = NetworkedActiveObject(
          "name_of_statechart",
          rabbit_user="<rabbitmq_user_name>",
          rabbit_password="<rabbitmq_password>",
          tx_routing_key="heya.man",
          rx_routing_key="#.man",
          mesh_encryption_key=b'u3u...')

  print(nao.this_url()) # => \\
    ['amqp://bob:dobbs@192.168.1.75:5672/%2F?connection_attempts=3&heartbeat_interval=3600']

:ref:`prev <recipes-recipes>`, :ref:`top <top>`, :ref:`next <management-describing-your-system>`
