
`Ansible <http://docs.ansible.com/>`_ needs to know what machines to ssh into and with what usernames.  This information is kept in the ``/etc/ansible/hosts`` file; it is called an inventory.  To tell Ansible what machines you want it to run its scripts on, you first create a named configuration item, and below it place the contact information (IP/URL address and username) for each of the machines in that group.  Your deployment script references this name to know what computers to log in to and run on.

Suppose I have a bunch of raspberry pi computers on my network, I might want to name their group ``miros-rabbitmq`` in my `Ansible <http://docs.ansible.com/>`_ inventory.  They all have the same username, but they are on addresses, 192.168.0.71 and 192.168.0.169.  So, on the Linux machine that I will run my deployment scripts from, I would edit the ``/etc/ansible/hosts`` file like this:

.. code-block:: python

  sudo pico /etc/ansible/hosts

Then I would change the file to:

.. code-block:: python

  [miros-rabbitmq]
  192.168.0.71 ansible_user=pi
  192.168.0.169 ansible_user=pi

.. note::

  The default posix username for a raspberry pi is ``pi``.  If your usernames are different,
  update the above listing with your usernames.

