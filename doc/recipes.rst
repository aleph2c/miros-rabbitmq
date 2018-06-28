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
            snoop_trace_encryption_key=b'u4f...',  
            snoop_spy_encryption_key=b's44...',  
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
            snoop_trace_encryption_key=b'u4f...',  
            snoop_spy_encryption_key=b's44...',  
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

.. _recipes-credentials-and-encryption-keys:

Credentials and Encryption Keys
-------------------------------

.. _recipes-hiding-your-encryption-data-and-user-credentials:

Changing your RabbitMQ credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you are installing RabbitMQ using the :ref:`ansible script in the DevOps section
<installing_infrastructure-have-ansible-install-rabbitmq>`, set the
``rabbit_name`` to the username you want, and the ``rabbit_password`` to
whatever you want your password to be.  Update your code to use your new
credentials.

You can also change your user name and password with the :ref:`RabbitMQ
management GUI<reflection-rabbitmq-management>`.

.. _recipes-managing-your-encryption-keys-and-rabbitmq-credentials-(short-version):

Managing your Encryption Keys and RabbitMQ Credentials (Short Version)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Use this :ref:`deployment strategy<deployment-deployment>` to ensure a ``.env``
file is in your top level directory of your application (the same directory you
would find your .git directory).  Your RabbitMQ credentials and your
miros-rabbitmq :ref:`encryption keys<recipes-making-an-encryption-key>` will be in this ``.env``
file,  which will look something like this:

.. code-block:: python

  MESH_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  SNOOP_TRACE_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  SNOOP_SPY_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  RABBIT_USER=peter
  RABBIT_PASSWORD=rabbit
  RABBIT_PORT=5672
  RABBIT_HEARTBEAT_INTERVAL=3600
  CONNECTION_ATTEMPTS=3
  RABBIT_GUEST_USER=rabbit567
  
Then in your setup.py or your actual application code, include the following:

.. code-block:: python

  import os
  from dotenv import load_dotenv
  from pathlib import Path

  # write .env items to the environment
  env_path = Path('.') / '.env'
  if env_path.is_file():
    load_dotenv(env_path)
  else:
    # recurse outward to find .env file
    load_dotenv()

  RABBIT_USER = os.getenv('RABBIT_USER')
  RABBIT_PASSWORD = os.getenv('RABBIT_PASSWORD')
  MESH_ENCRYPTION_KEY = os.getenv("MESH_ENCRYPTION_KEY")
  SNOOP_TRACE_ENCRYPTION_KEY = os.getenv("SNOOP_TRACE_ENCRYPTION_KEY")
  SNOOP_SPY_ENCRYPTION_KEY = os.getenv("SNOOP_SPY_ENCRYPTION_KEY")
  # .. etc 

For details about how to set up your ``.env`` file without the mentioned
deployment procedure read the next section.

.. _recipes-encryption-keys-in-your-environment:

Managing your Encryption Keys and RabbitMQ Credentials (Long Verion)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To keep your :ref:`encryption keys <recipes-making-an-encryption-key>` and RabbitMQ
credentials out of your source code, you can put them into environment variables,
then load the contents of these environment variables into your program.  

A slight extension of this idea is to put your keys into a ``.env`` file, then load its
contents into environment variables, then load these variables into your program.  By
placing your :ref:`encryption keys <recipes-making-an-encryption-key>` and RabbitMQ
credentials into a ``.env`` file, it makes it easier to transfer them between the
machines in your distributed system.

.. note:: 
  
  By convention the ``.env`` file is kept in the outermost directory of your project,
  the same directory that you would find your .git folder.

The `python-dotenv <https://github.com/theskumar/python-dotenv>`_ package
converts the contents of a ``.env`` file into environment variables.  We will
use it in this recipe.  If you have installed ``miros-rabbitmq``, you will have this
package installed on your system already.

In the outermost directory of your project, create a ``setup.py`` file and add the following:

.. code-block:: python

  import os
  from dotenv import load_dotenv
  from pathlib import Path

  # write .env items to the environment
  env_path = Path('.') / '.env'
  if env_path.is_file():
    load_dotenv(env_path)
  else:
    # recurse outward to find .env file
    load_dotenv()

  # get RabbitMQ credentials and encryption keys from the environment
  RABBIT_USER = os.getenv('RABBIT_USER')
  RABBIT_PASSWORD = os.getenv('RABBIT_PASSWORD')
  MESH_ENCRYPTION_KEY = os.getenv("MESH_ENCRYPTION_KEY")
  SNOOP_TRACE_ENCRYPTION_KEY = os.getenv("SNOOP_TRACE_ENCRYPTION_KEY")
  SNOOP_SPY_ENCRYPTION_KEY = os.getenv("SNOOP_SPY_ENCRYPTION_KEY")

This program will be able to read your :ref:`encryption keys
<recipes-making-an-encryption-key>` and RabbitMQ credentials, from either your shell's
environment variables or from a ``.env`` file.  

For the ``setup.py`` program to work there needs to be a ``.env`` file, so let's
make an empty one:

.. code-block:: python

  $ touch .env

Now we have options.  We can put our keys into our environment using shell
commands, or we can put them into the ``.env`` file.

Let's explore these options:

  * I will add the encryption keys to the shell's environment
  * Get the program working
  * Remove the encryption keys from the shell's environment
  * Show that the program crashes
  * Add the encryption keys to the ``.env`` file
  * Show that the program works
  * Talk about how to transfer the ``.env`` file securely.

To create an environment variable we use the shell's ``export`` command.

.. code-block:: python

  $ export MESH_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  $ export SNOOP_TRACE_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  $ export SNOOP_SPY_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  $ export RABBIT_USER=peter
  $ export RABBIT_PASSWORD=rabbit

In our main program, we can access these encryption keys by importing them from
our ``setup.py`` file:

.. code-block:: python

  # in miros-rabbitmq file
  from setup import MESH_ENCRYPTION_KEY
  from setup import SNOOP_TRACE_ENCRYPTION_KEY
  from setup import SNOOP_SPY_ENCRYPTION_KEY
  from setup import RABBIT_USER 
  from setup import RABBIT_PASSWORD

Now, when we construct a ``NetworkedActiveObject`` or a ``NetworkedFactory``
object we can use our environment variables rather than writing our secret encryption keys
directly into our code base.

.. code-block:: python

  # in miros-rabbitmq file
  ao = NetworkedActiveObject(
    make_name('ao'),
    rabbit_user=RABBIT_USER,
    rabbit_password=RABBIT_PASSWORD,
    tx_routing_key='heya.man',
    rx_routing_key='#.man',
    mesh_encryption_key=MESH_ENCRYPTION_KEY,
    snoop_spy_encryption_key=SNOOP_SPY_ENCRYPTION_KEY,
    snoop_trace_encryption_key=SNOOP_TRACE_ENCRYPTION_KEY)

If we set up our environment variables the same on all of our machines, our
distributed system will work.

Before we add our encryption keys to our ``.env`` file, lets first confirm that
we can break our program by removing them from our shell environment.  In your
shell type:

.. code-block:: python

  $ unset RABBIT_USER
  $ unset RABBIT_PASSWORD
  $ unset MESH_ENCRYPTION_KEY
  $ unset SNOOP_TRACE_ENCRYPTION_KEY
  $ unset TRACE_TRACE_ENCRYPTION_KEY

Then if we re-run the program we will see that it crashes for lack of
encryption keys.  By confirming that our program has crashed, we can trust that
the information that we will put into our ``.env`` file will be used rather than
the information we had previously placed in our environmental variables (we
won't fool ourselves into thinking are ``.env`` file is working if it isn't).
  
Let's move our encryption keys into the ``.env`` file.

.. code-block:: python

  # in .env file  
  MESH_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  SNOOP_TRACE_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  SNOOP_SPY_ENCRYPTION_KEY=u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=
  RABBIT_USER=peter
  RABBIT_PASSWORD=rabbit

.. warning::

  Don't put the ``.env`` file into your code revision system.  If you do, you
  might as well leave the encryption keys in your source code.

  Add ``.env`` to your ``.gitignore`` file so you don't accidentally add it in
  the future.  
  
  If you have added ``.env`` to git, remove it: ``git rm --cached .env``, then
  change your :ref:`encryption keys <recipes-making-an-encryption-key>`.  

.. note::

  There *is* a ``.env`` file in the examples directory of this code base.  It was
  included so you can see how to do things.

Now we re-run our program and confirm that it works.

This ``.env`` file can be shared between machines, but transfer it using scp, or
using a flash key or in other ways that you can keep your secrets, secret.
Don't use email.

Here is a reminder about how to use scp:

.. code-block:: bash

  # scp <source> <destination>
  $ scp /path/to/.env <username>@ip/path/to/destination/.env

If you use this :ref:`deployment strategy<deployment-deployment>`, the ``.env``
files will be placed at the top level of all of working directory on all of the
machines in your distributed system.

.. _recipes-networking:

Networking
----------
The problem of how to network your distributed system can be broken into two different pieces:

  * how to deploy your servers, code, secrets and infrastructure
  * how a node can discover other nodes in the same system

To read about a deployment strategy see :ref:`this deployment example<deployment-deployment>`.

A node determines what other nodes it can talk to, by using two different strategies:

  * it uses a list of addresses in the ``.miros_rabbit_hosts.json`` file.
  * it automatically discovers other nodes like itself on your LAN, then it caches this information into the ``.miros_rabbitlan_cache.json`` file.

The ``.miros_rabbit_hosts.json`` and ``.miros_rabbitlan_cache.json`` files are kept in the same directory as the code that is using the miros-rabbitmq package.

.. _recipes-node-discovery:

.. _recipes-manually-setting-node-addresses:

Manually setting Node Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``.miros_rabbit_hosts.json`` file in the same directory as your
miros-rabbitmq program looks like this:

.. code-block:: python

  {
    "hosts": [
      "192.168.1.71",
      www.myurl.xyz
    ]
  }

This file will be written for you at your top level directory if you use this
:ref:`deployment strategy<deployment-deployment>`.

Node Discovery on your LAN
^^^^^^^^^^^^^^^^^^^^^^^^^^
This is taken care of by the library.  If your node is on your local area network
and it's IP address is in the ARP table or it's computer will respond to a ping;
The miros-rabbitmq library should find it.  If two nodes are on the same network
and share encryption and rabbit credentials they will be able to communicate.

The results of the process are cached in the ``.miros_rabbitlan_cache`` file
which looks something like this:

.. code-block:: json

  {
    "addresses": [
      "192.168.1.75",
      "192.168.1.71"
    ],
    "amqp_urls": [
      "amqp://bob:dobbs@192.168.1.75:5672/%2F?connection_attempts=3&heartbeat_interval=3600",
      "amqp://bob:dobbs@192.168.1.71:5672/%2F?connection_attempts=3&heartbeat_interval=3600"
    ],
    "time_out_in_minutes": 30
  }

To force your program to update this cache, change the ``time_out_in_minutes``
setting to 0 and re-run your program.  Your application will cause another LAN
search and update the ``time_out_in_minutes`` back to it's default setting.

.. _recipes-aliens,-and-what-to-do-about-them:

Aliens, and what to do about them
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
An Alien is a node that can talk to you, but that you didn't know about when
your program started.  There are many reasons why you might not know about a
node that knows about you:

* Your LAN cache hadn't expired while a new node was added to your LAN
* The Alien machine does not respond to ping requests
* the machine is beyond your LAN and you don't have it's address in your
  ``.miros_rabbit_hosts`` file.

The Alien policy is, if it can talk to us we will talk to it too.  If the node
knows about us, has the correct encryption keys and RabbitMQ credentials, then
it's secure and we can work with it.   So, if an Alien is discovered, the
miros-rabbitmq package will respond by building producers to talk to it.  To see
how this is done you can read :ref:`this <how_it_works2_aliens>`.

:ref:`prev <example>`, :ref:`top <top>`, :ref:`next <reflection>`


