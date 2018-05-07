.. _reflection:

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Reflection
==========
If you build a complex distributed system using a statechart you will need some
way to debug it.  The miros-rabbitmq library provides two different encrypted
topic based networks called the snoop_trace and the snoop_spy network.  To turn
a network on, you enable it `before` calling ``start_at`` in your statechart.

.. _reflection-snoop-trace-network:

Snoop Trace Network
-------------------
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
NeNetworkedActiveObject or the NetworkedFactory, using the
``trace_snoop_encryption_key`` named attribute.  If you do not explicitly set
this key, the ``mesh_encryption_key`` will be used to encrypt the snoop trace
information.

To create an encryption key which will be accepted by this library, use Fernet:

.. code-block:: python

  from cryptography import Fernet
  Fernet.generate_key() # => b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='

The snoop trace stream of snoop trace network, consists of a lot of information
coming back from each of the contributing nodes in the distributed system.  To
make it easier to distinguish your locally running instance from the information
of the other nodes, it's name is colored in blue and the names of the other
nodes are colored in purple.

While this coloring is helpful while viewing things in your terminal it can
become problematic when trying to log.  For this reason, a
``enable_snoop_trace_no_color`` api is provided in both of the
NetworkedActiveObject and NetworkedFactory classes.  You would use the
``enable_snoop_trace_no_color`` call when you want your local instance to print
uncolored information to the terminal which could be re-directed into a log
without the ANSI color codes.

Both the NetworkedActiveObject and the NetworkedFactory classes provide a way to
make print statements into the snoop_trace_network.  To write custom information into
the snoop trace network, you would call the ``snoop_scribble`` method:

.. code-block:: python

  ao.snoop_scribble("Some message to be seen by all monitoring nodes")


.. _reflection-snoop-spy-network:

Snoop Spy Network
-----------------

.. _reflection-tracing-locally:

Tracing Locally
---------------

