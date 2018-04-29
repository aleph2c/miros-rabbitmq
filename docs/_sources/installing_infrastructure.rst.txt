.. _installing_infrastructure-installing-required-programs:

DevOps
======
For us to run statecharts on different machines will require a few system
administration steps.  When such a process is automated, it is often called
Development Operations, or DevOps.

I found the installation documentation on the RabbitMQ website to be mostly
illegible to me as a new user, so I wrote this guide to save you the pain which
I went through.

.. _installing_infrastructure-installing-on-windows:

Installing On Windows
---------------------

If you are installing RabbitMQ on (>= Windows 7), try following this `video <https://www.youtube.com/watch?v=gKzKUmtOwR4>`_ and if that
doesn't work clear your afternoon's schedule, and work through `this <https://www.rabbitmq.com/install-windows.html>`_.  Pay special attention to the section titled `Synchronise Erlang Cookies <https://www.rabbitmq.com/install-windows-manual.html#erlang-cookie>`_.

.. _installing_infrastructure-installing-on-linux:

Installing On Linux
-------------------

For Linux, I automated the installation process of RabbitMQ using a simple Ansible
script.  If you haven't heard of Ansible before, it's a Python library that
allows you to automatically ssh into machines and run a series of sysadmin
commands.  So, you can use it to automatically deploy things.  For this to work
we will need to:
 * :ref:`Setup ssh so it can login without a password <installing_infrastructure-setting-up-ssh-so-you-don't-need-a-password>`
 * :ref:`Install Ansible <installing_infrastructure-install-ansible>`
 * :ref:`Tell Ansible where it should run <installing_infrastructure-tell-ansible-where-to-run>`
 * :ref:`Install RabbitMQ using Ansible <installing_infrastructure-have-ansible-install-rabbitmq>`

.. note::

  I tried to install RabbitMQ using my ansible scripts in windows using the WLS
  (Windows Linux Subsystem).  This didn't work,  but the miros-rabbitmq code
  will run from the WLS once you install RabbitMQ on windows using the windows
  procedure.

.. _installing_infrastructure-setting-up-ssh-so-you-don't-need-a-password:

Setting up SSH so you Don't Need a Password
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Ansible needs to be able to automatically ssh into the computer it is trying to
control.  To do this, you put the public ssh key of the computer running ansible
into the computer it is deploying software too.

Check to see if the machine you are going to be running Ansible from has public
keys:

.. code-block:: python

  > ls ~/.ssh | grep pub

If nothing appears, the deployment machine doesn't have a public key.  To make one do this (only run these
commands if you don't have a public key already):

.. code-block:: python
  
  > mkdir ~/.ssh
  > cd ~/.ssh
  > sudo ssh-keygen

When you see an option to enter a passphrase, just hit enter.

Now, let's see if we can ssh into our own machine without a password.

.. code-block:: python

  ssh $USER@localhost

If you can login without a password, great, Ansible can now deploy things to
this machine, from this machine.

If you can't SSH without a password to your localhost, we just have to put this
machine's public key into its *authorized_keys* file. (only run
this command if you can't ssh into your own machine without a password):

.. code-block:: python

  > sudo cat '~/.ssh/id_rsa.pub' >> '~/.ssh/authorized_keys'

Try to SSH into the machine again. You shouldn't need a password anymore.

Now let's push our public key onto the remote computer that we want to deploy
software to.  To do this you will need it's URL or IP address and the user name
of the account that has SSH enabled.  As an example, I'll assume that the
machine you are trying to set up has the IP address of 192.168.0.169 with a
username pi.  Change out the user name and IP address with your own for the
remainder of this example.

First we test if it already has this machine's public key:

.. code-block:: python

  ssh pi@192.168.0.169

If it asked for a password, it does not have our public key in it's
authorized_keys file.  If this is true, let's put our public key into it's
authorized_keys file:

.. code-block:: python

   > cat ~/.ssh/id_rsa.pub | ssh pi@192.168.0.169 'cat >> .ssh/authorized_keys'

Now test it:

.. code-block:: python

  ssh pi@192.168.0.169

The above command shouldn't ask for a password anymore.

Repeat this procedure for every machine onto which you would like to deploy RabbitMQ.

.. _installing_infrastructure-install-ansible:

Install Ansible
^^^^^^^^^^^^^^^
To install Ansible:

.. code-block:: python

  > sudo apt-get install ansible

.. _installing_infrastructure-tell-ansible-where-to-run:

Tell Ansible Where to Run and with What User Name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Ansible needs to know what machines to ssh into and with what user names.  This
information is kept in the ``/etc/ansible/hosts`` file, it is called an
inventory.  Basically, you create a named configuration item, and below it place
the contact information (IP/URL address and username) for each of the machines
in that group.  Your deployment script references this name to know what
computers to run against.

Suppose I have a bunch of raspberry pi computers on my network, I might want to
name their group ``pis`` in my Ansible inventory.  They all have the same user
name but they are on addresses, 192.168.0.169, 192.168.0.170 and 192.168.0.171.
So, on the Linux machine that I will run my deployment scripts from, I would edit
the ``/etc/ansible/hosts`` file like this:

.. code-block:: python

  sudo pico /etc/ansible/hosts

Then I would change the file to:

.. code-block:: python

  [pis]
  192.168.0.169 ansible_user=pi
  192.168.0.170 ansible_user=pi
  192.168.0.171 ansible_user=pi

.. _installing_infrastructure-have-ansible-install-rabbitmq:

Have Ansible Install RabbitMQ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now that Ansible knows what user names and addresses to use, we need to tell it to do
something.  Ansible scripts are just yml files; they are easy to read.  The
only people I know who don't like yml files are minecraft administrators.  So,
here is the yaml file that will install RabbitMq onto all of the computers in my
``pis`` group, I called it ``rabbit_install.yml``:

.. code-block:: ansible

  ---
  - hosts: pis
    vars:

      rabbit_name: bob
      rabbit_password: dobbs
      rabbit_tags:
        - administrator
      guest_password: rabbit123

    tasks:
     - name: Install rabbitmq-server
       become: true
       apt: name={{ item }} state=present update_cache=false
       with_items:
         - erlang
         - rabbitmq-server

     - name: Remove user
       become: true 
       shell: rabbitmqctl delete_user {{rabbit_name}}
       ignore_errors: True

     - name: Create a user with password
       become: true 
       shell: rabbitmqctl add_user {{rabbit_name}} {{rabbit_password}}
       ignore_errors: True

     - name: Assign a tag to the user
       become: true 
       shell: "rabbitmqctl set_user_tags {{rabbit_name}} {{rabbit_tags | join(' ')}}"
       ignore_errors: True

     - name: Set permissions
       become: true
       shell: rabbitmqctl set_permissions -p / {{rabbit_name}} ".*" ".*" ".*"
       ignore_errors: True
    
     - name: Change default admin password
       become: true
       shell: rabbitmqctl change_password guest {{guest_password}}
       ignore_errors: True

     - name: Setup environment variables
       become: true
       template:
         src: ./rabbitmq-env.conf.j2
         dest: /etc/rabbitmq/rabbitmq-env.conf
         mode: 644

     - name: Setup configuration file
       become: true
       template:
         src: ./rabbitmq.config.j2
         dest: /etc/rabbitmq/rabbitmq.config
         mode: 644

     - name: Enable the management plugin
       become: true
       shell: rabbitmq-plugins enable rabbitmq_management
       ignore_errors: True

     - name: Restart the rabbitmq-server service
       become: true
       shell: sudo service rabbitmq-server restart
       ignore_errors: True

This file references a couple of jinja2 templates, rabbitmq-env.conf.j2 and
rabbitmq.config.j2.

Here is the ``rabbit-env.conf.j2`` file:

.. code-block:: ansible

  RABBITMQ_CONFIG_FILE=/etc/rabbitmq/rabbitmq
  NODE_IP_ADDRESS=0.0.0.0

Here is the ``rabbitmq.config.j2`` file:

.. code-block:: ansible

  [
    {rabbit,
      [
        {loopback_users,[]}
      ]
    }
  ]

.. note::

  The rabbitmq.config file is actually Erlang.  I lost many hours trying to get
  RabbitMq to install using the example rabbit.config file from their repo.  It was
  broken, too many brackets or something.  Not knowing anything about RabbitMQ
  or Erlang, it took me a while to figure out that the problem was with their
  code and not with my setup.

So, copy the above ``rabbit_install.yml``, ``rabbit-env.conf.j2`` and the
``rabbitmq.config.j2`` files into your deployment directory, change the user
name and passwords to whatever you want them to be and perform a deployment:

.. code-block:: python

  > ansible-playbook -K rabbit_install.yml

The above command will ask you for the root password required to sudo into the
machines listed in your inventory.  Enter it and hit enter.

*bon chance mon ami.*

