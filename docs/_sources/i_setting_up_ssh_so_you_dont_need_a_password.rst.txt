`Ansible <http://docs.ansible.com/>`_ needs to be able to ssh into the computer it is trying to control.  To let it do this, you will have to first, place the public ssh key of the computer running Ansible into the computer it is deploying software too.

Check to see if the machine you are going to be running `Ansible <http://docs.ansible.com/>`_ from has public
keys:

.. code-block:: python

  > ls ~/.ssh | grep pub

If nothing appears, the deployment machine doesn't have a public key.  To make a public key, do the following (only run these
commands if you don't have a public key already):

.. code-block:: python
  
  > mkdir ~/.ssh
  > cd ~/.ssh
  > sudo ssh-keygen

When you see an option to enter a passphrase, just hit enter.

Now, let's see if we can ssh into our own machine without a password.

.. code-block:: python

  ssh $USER@localhost

If you can login without a password, great, `Ansible <http://docs.ansible.com/>`_ can now deploy things to this machine, from this machine.

If you can't SSH without a password to your localhost, we just have to put this machine's public key into its *authorized_keys* file. (only run this command if you can't ssh into your own machine without a password):

.. code-block:: python

  > sudo cat '~/.ssh/id_rsa.pub' >> '~/.ssh/authorized_keys'

Try to SSH into the machine again. You shouldn't need a password anymore.

Now let's push our public key onto the remote computer that we want to deploy software too.  To do this, you will need it's URL or IP address and the username of the account that has SSH enabled.  As an example, I'll assume that the machine you are trying to set up has the IP address of 192.168.0.169 with a username pi.  Change out the username and IP address with your own for the remainder of this example.

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
