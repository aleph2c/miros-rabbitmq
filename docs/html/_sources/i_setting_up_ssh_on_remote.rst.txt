Now let's push our public key onto a remote computer that we want to deploy software too.  To do this, you will need it's URL or IP address and the username of the account that has SSH enabled.  As an example, I'll assume that the machine you are trying to set up has the IP address of 192.168.0.169 with a username pi.  Change out the username and IP address with your own for the remainder of this example.

First we test if it already has this machine's public key:

.. code-block:: python

  ssh pi@192.168.0.169

If it asked for a password, it does not have our public key in its authorized_keys file.  If this is true, let's put our public key into its authorized_keys file:

.. code-block:: python

   > cat ~/.ssh/id_rsa.pub | ssh pi@192.168.0.169 'cat >> .ssh/authorized_keys'

Now test it:

.. code-block:: python

  ssh pi@192.168.0.169

The above command shouldn't ask for a password anymore.

Repeat this procedure for every machine onto which you would like to deploy RabbitMQ.
