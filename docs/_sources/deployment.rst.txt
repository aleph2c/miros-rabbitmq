.. _deployment-deployment:

Deployment
==========
In this section I will show how to use Ansible to deploy a miros-rabbitmq system.
There are many different ways this can be done, this guide will provide a minimal
example, showing how to install RabbitMQ and how to place your secrets and credentials
into ``.env`` files on your remote servers into the top level directory of your
miros-rabbitmq project.

Given that the server configuration is coupled with the design of your distributed
system, its setup should be under revision control.  This can be done with an Ansible
playbook, and some files that hold your variables and some jinja2 templates.

.. _deployment-the-inventory:

The Inventory
-------------

But to begin with we will start with the ``/etc/ansible`` directory of the machine that will
do the deployments.

.. code-block:: text

    .
    ├── ansible.cfg
    └── hosts

In your ``/etc/ansible/hosts`` we see an example of an inventory, this one describes a
group called ``scotty``.  It has a list of some addresses and their ansible_user names.
From now on, when you see the group ``scotty`` remember we are thinking about these
machines, with these users:

.. code-block:: ansible

  [scotty]
  192.168.1.71 ansible_user=pi
  192.168.1.69 ansible_user=pi

.. _deployment-the-playbook-directory:

The Ansible Working Directory
-----------------------------
You can place your Ansible files and folders where every you want in your file system.
Just ensure that they are under revision control.  Your Ansible working directory could
look something like this:

.. code-block:: text

    ├── group_vars
    │   └── scotty
    │       ├── vars
    │       └── vault
    ├── miros_rabbitmq_install.yml
    ├── rabbitmq.config.j2
    ├── rabbitmq-env.conf.j2
    └── .env.j2

We see that there is a group_vars directory, which has a subdirectory called scotty.
This subdirectory contains all of the variables needed for our deployment.
There are public vars and their is a vault.  

The var file contains all of the public variables.

The vault is an encrypted file (AES256) which can be added to your revision
control system.  I will talk about how to place your secrets into this file and how to
access these secrets from your vars file shortly.  

But first look at the ``miros_rabbitmq_install.yml`` file.  This is the play book that
contains the instructions about what should be deployed and where and how.  The files
with the ``j2`` extension are just jinja2 templates which will be used by the playbook
when it's writing new files, populated with the contents of your ``group_vars`` folder,
onto your remote servers.

For your ``miros-rabbitmq`` library to work, it needs to install the Erlang programming
language, RabbitMQ and several plugins for the RabbitMQ server.  Then in needs to place
your RabbitMQ credentials and the miros-rabbitmq secrets in to the .env file at the base
of your software system.  Where this is will be configured directly in the playbook, all
other variables will be pulled out of the ``group_vars`` folders.

.. _deployment-the-miros-rabbitmq-install-playbook:

The Miros RabbitMQ Install Playbook
-----------------------------------
The playbook is written in yaml, so it is easy to read:

.. code-block:: yaml
  :linenos:

  ---
  - hosts: scotty
    vars:
      miros_rabbitmq_project_directory: '~/miros-rabbitmq'
    tasks:
     - name: Install rabbitmq-server
       become: true
       apt: name={{ item }} state=present update_cache=false
       with_items:
         - erlang
         - rabbitmq-server

     - name: Remove user
       become: true 
       shell: rabbitmqctl delete_user {{rabbit_user}}
       ignore_errors: True

     - name: Create a user with password
       become: true 
       shell: rabbitmqctl add_user {{rabbit_user}} {{rabbit_password}}
       ignore_errors: True

     - name: Assign a tag to the user
       become: true 
       shell: "rabbitmqctl set_user_tags {{rabbit_user}} {{rabbit_tags | join(' ')}}"
       ignore_errors: True

     - name: Set permissions
       become: true
       shell: rabbitmqctl set_permissions -p / {{rabbit_user}} ".*" ".*" ".*"
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
       shell: service rabbitmq-server restart
       ignore_errors: True

     - name: Write the .env file
       template:
         src: ./.env.j2
         dest: "{{ miros_rabbitmq_project_directory }}/.env"
         mode: "u=rw,g=r,o=r"

The file is basically self documenting.  On line 2 we see that we want this playbook to
reference our ``scotty`` inventory.  This will have ansible load all of the variables
described in the ``scotty`` subdirectory of the global_var folder.

On line 3-4 we see that there is a playbook scoped variable named
``miros_rabbitmq_project_directory``.  This is the path in which we will place the
``.env`` file needed for our project.  This ``.env`` file will have all of the
encryption keys and RabbitMQ credentials for our deployment to work.  We see lines 5-60
are just a repeat of the playbook we used in the devops section for installing RabbitMQ.
Lines 62-66 fill our ``.env.j2`` template with our variables and the writes it to the
directory specified by the ``miros_rabbitmq_project_directory`` variable at the top of
the playbook.

.. _deployment-the-dot-env-file:

The Dot Env File
----------------
The ``.env`` file will contain the secrets needed for a server to communicate with
another server.  It is derived from the ``.env.js`` template which looks like this:

.. code-block:: python

  MESH_ENCRYPTION_KEY={{mesh_encryption_key}}
  SNOOP_TRACE_ENCRYPTION_KEY={{snoop_trace_encryption_key}}
  SNOOP_SPY_ENCRYPTION_KEY={{snoop_spy_encryption_key}}
  RABBIT_USER={{rabbit_user}}
  RABBIT_PASSWORD={{rabbit_password}}
  RABBIT_PORT={{rabbit_port}}
  RABBIT_HEARTBEAT_INTERVAL={{rabbit_heart_beat_interval}}
  CONNECTION_ATTEMPTS={{connection_attempts}}

The ``.env`` will placed in the directory specified by the
``miros_rabbitmq_project_directory`` variable at the top of the ``miros_rabbitmq.yml``
playbook.

.. _deployment-the-vault-file:

The vault File
--------------
The vault file is an encrypted file that can be added to your code revision system.  It
contains all of your system's secrets and credentials.  You would decrypt it at the
moment you issue the ``ansible-playbook`` command.

It is placed within the group_vars/scotty directory of your Ansible working directory.

.. code-block:: python

   ├── group_vars
       └── scotty
           ├── vars
           └── vault

To create a vault file:

.. code-block:: bash

      ansible-vault create group_vars/scotty/vault
    > New Vault password: 
    > Confirm New Vault password:

To edit this vault file, you can enter this command:

.. code-block:: python

  ansible-vault edit vault --vault-id @prompt
  > Vault password (default): 

If you enter the correct password, your vault file will
be decrypted and opened with your default editor.  After you have edited your file, the
closing process of your editor would cause ansible to re-encrypt it, locking it down.

Let's add our RabbitMQ credentials and miros-rabbitmq encryption keys to our file:

.. code-block:: yaml

  ---
  vault_MESH_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_SNOOP_TRACE_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_SNOOP_SPY_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_RABBIT_USER: peter
  vault_RABBIT_PASSWORD: rabbit
  vault_RABBIT_PORT: 5672
  vault_RABBIT_HEARTBEAT_INTERVAL: 3600
  vault_CONNECTION_ATTEMPTS: 3

.. note::
  
  Make sure you wrap your encryption keys within a set of single-quotes characters
  otherwise the yaml interpretor will get confused by the key's ``-`` and ``=`` characters
  and your deployment won't work.

.. _deployment-the-vars-file:

The vars File
-------------
The vars file contains all of the variables that your playbook and it's template files
need.  Ours will look something like this:

.. code-block:: yaml

  ---
  rabbit_user: "{{ vault_RABBIT_USER }}"
  rabbit_password: "{{ vault_RABBIT_PASSWORD }}"
  rabbit_port: "{{ vault_RABBIT_PORT }}"
  rabbit_heartbeat_interval: "{{ vault_RABBIT_HEARTBEAT_INTERVAL }}"
  connection_attempts: "{{ vault_CONNECTION_ATTEMPTS }}"
  rabbit_tags:
    - administrator
  guest_password: rabbit123
  mesh_encryption_key: "{{ vault_MESH_ENCRYPTION_KEY }}"
  snoop_trace_encryption_key: "{{ vault_SNOOP_TRACE_ENCRYPTION_KEY }}"
  snoop_spy_encryption_key: "{{ vault_SNOOP_SPY_ENCRYPTION_KEY }}"
  rabbit_heart_beat_interval: 3600

See how some of the variables are just using items from the vault?

This is done so that the vault variable names don't remain a secret from your playbook.  If
you pass off their contents into publicly available variable names, then they can be
used by someone who doesn't have the encryption key for the vault file.

.. _deployment-to-deploy

To Deploy
---------
To have your playbook run on each of the servers defined in your inventory, you would
run:

.. code-block:: python

  ansible-playbook -K miros_rabbit_install.yml --ask-vault-pass
  BECOME password:
  Vault password:

The ``BECOME password`` is the password to run ``sudo`` commands on the remote server,
and the ``Vault password`` is the password you used to encrypt your vault file.

.. raw:: html

  <a class="reference internal" href="docs.html"><span class="std std-ref">prev</span></a>,
  <a class="reference internal" href="index.html#top"><span class="std std-ref">top</span></a>,
  <span class="inactive-link">next</span>
