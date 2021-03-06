.. _installing_infrastructure-installing-required-programs:

DevOps
======

.. epigraph:: 

  *Information is not knowledge.*

  -- W. Edwards Deming


For us to run statecharts on different machines will require a few system
administration steps.  When such a process is automated, it is often called
Development Operations, or DevOps.

I found the installation documentation on the RabbitMQ website to be mostly
illegible to me as a new user, so I wrote this guide to save you the pain which
I went through.

Once you are familiar with the miros-rabbitmq library, you can reference this
full :ref:`deployment procedure <deployment-deployment>` for setting up your
distributed system.  

For now, in this section, we will describe procedures for setting up RabbitMQ so
that our miros-rabbitmq derived programs can talk to each other through it.

.. _installing_infrastructure-installing-on-windows:

RabbitMQ On Windows and the WSL
-------------------------------

If you are installing RabbitMQ on (>= Windows 7), try following this `video <https://www.youtube.com/watch?v=gKzKUmtOwR4>`_ and if that
doesn't work clear your afternoon's schedule, and work through `this <https://www.rabbitmq.com/install-windows.html>`_.  Pay special attention to the section titled `Synchronise Erlang Cookies <https://www.rabbitmq.com/install-windows-manual.html#erlang-cookie>`_.

.. _installing_infrastructure-installing-on-linux:

RabbitMQ On Linux
-------------------
For Linux, I automated the installation process of RabbitMQ using a simple `Ansible <http://docs.ansible.com/>`_ script.  If you haven't heard of `Ansible <http://docs.ansible.com/>`_ before, it's a Python library that
allows you to automatically ssh into machines and run a series of sysadmin commands.  You can use it to deploy things automatically.  For this to work we will need to:

 * :ref:`Setup ssh so it can login without a password <installing_infrastructure-setting-up-ssh-so-you-don't-need-a-password>`
 * :ref:`Install Ansible <installing_infrastructure-install-ansible>`
 * :ref:`Tell Ansible where it should run <installing_infrastructure-tell-ansible-where-to-run>`
 * :ref:`Install RabbitMQ using Ansible <installing_infrastructure-have-ansible-install-rabbitmq>`

.. note::

  I tried to install RabbitMQ using my ansible scripts in windows using the WSL
  (Windows Subsystem for Linux).  This didn't work,  but the miros-rabbitmq code
  will run from the WSL once you install RabbitMQ on windows using the windows
  procedure.

.. _installing_infrastructure-setting-up-ssh-so-you-don't-need-a-password:

Setting up SSH so you Don't Need a Password
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: i_setting_up_ssh.rst
.. include:: i_setting_up_ssh_on_remote.rst

.. _installing_infrastructure-install-ansible:

Install Ansible
^^^^^^^^^^^^^^^

.. include:: i_install_ansible.rst

.. _installing_infrastructure-tell-ansible-where-to-run:

Tell Ansible Where to Run and with What User Name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: i_tell_ansible_where_to_run.rst

Have Ansible Install RabbitMQ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now that `Ansible <http://docs.ansible.com/>`_ knows what user names and addresses to use, we need to tell it to do
something.  `Ansible <http://docs.ansible.com/>`_ scripts are just yml files; they are easy to read.  The
only people I know, who don't like yml files, are minecraft administrators.  So,
here is the yml file that will install RabbitMq onto all of the computers in my
``scotty`` group, I called it ``rabbit_install.yml``:

.. code-block:: ansible

  ---
  - hosts: scotty
    vars:

      rabbit_name: peter
      rabbit_password: rabbit
      rabbit_tags:
        - administrator
      guest_password: energizer

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

This file references a couple of `jinja2 <http://jinja.pocoo.org/docs/2.10/>`_ templates, rabbitmq-env.conf.j2 and
rabbitmq.config.j2.  Normally an `Ansible <http://docs.ansible.com/>`_ script would populate the variables in
a `jinja2 <http://jinja.pocoo.org/docs/2.10/>`_ template, then write the resulting file to disk, but in this example it
just writes out the template file without any alteration.

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
  .

.. note::

  The rabbitmq.config file is actually Erlang.  I lost many hours trying to get
  RabbitMq to install using the example rabbit.config file from RabbitMQ repo.  It was
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


