.. _deployment-deployment:

Deployment
==========
Getting miros-rabbitmq working on one machine is relatively straightforward.
The hard part about building a distributed system is deploying its
infrastructure (Erlang, RabbitMQ, ...), the credentials needed to run it and the
encryption keys securely onto multiple machines.  By default, I have written
encryption into the library, but the tricky thing about encryption is keeping
your keys secret: transmitting and installing these keys in multiple locations
without exposing them to the Big Bad Internet, or to your code revision system.

As the author of the miros-rabbitmq framework, I accept the deployment problem
as part of my responsibility.  If I didn't at least try to take on this problem,
people would use miros-rabbitmq insecurely out of the box, and I would be
partially complicit in their decision.  So, here is a guide that will show you
one technique for keeping your secrets, secret.

If you are new to the technology, don't worry I'm going to step you through a
deployment process.

.. _deployment-deployment-specification:

Deployment Specification
------------------------
Here is the deployment process's requirements, assumptions and limitations:

* It should be secure
* It should be automated
* It should use standardized and known techniques (ssh, Ansible vault, .env files, ... )
* It should run from one machine and deploy to an arbitrary number of other computers/containers.
* It can only deploy to Linux computers/containers (WLS will not be supported).
* All machines in your system will have the same ``sudo`` password.
* All machines in your system will be considered secure.
* An encrypted vault file will be constructed on the computer that runs the
  deployment.
* The key, or phrase, used to decrypt the vault file will be kept in your head (or written down).
* The vault file can be kept in your revision control system.
* The mesh, snoop_trace and snoop_spy network keys will be kept in the vault file.
* The RabbitMQ credentials will be kept in the vault file.
* It will **not** deploy your code (I don't know what revision control system you have)
* It will **not** install miros-rabbitmq.  (I don't know how you want to set up your Python environment).
* It will deploy the .env file, with the RabbitMQ credentials and miros-rabbitmq secrets into your working folder
* It will install Erlang
* It will install RabbitMQ and it's management plugin
* It will configure your RabbitMQ servers to use the credentials in your vault file.
* It should be easy to extend the deployment process to meet your needs.
* It should be easy to change your keys 

Here is a high level view of the secrets in our system:

.. image:: _static/deployment_machines.svg
    :target: _static/deployment_machines.pdf
    :align: center

We will talk about how to transfer the secrets in the next couple of sections.

When you install the miros-rabbitmq package and your code on each computer (by
extending this deployment process to suit your needs), your code should automatically
use the .env file you have installed into your working directory.  You shouldn't
have to care about the RabbitMQ server, the .env file should contain everything
required for the miros-rabbitmq library to work.

.. _deployment-high-level-view:

High Level View
---------------
Here are the five step we will make in this deployment:

* :ref:`set up deployment computer<deployment-set-up-your-deployment-computer>`
* :ref:`determine what machines you want in your distributed system<deployment-what-machine-do-you-want-in-your-distributed-system>`
* :ref:`invent credentials and secrets<deployment-invent-your-credentials-and-secrets>`
* :ref:`setup ansible file structure on deployment computer<deployment-setup-ansible-file-structure-on-the-deployment-computer>`
* :ref:`deploy your infrastructure, credentials and secrets to all machines<deployment-deploy-your-infrastructure-credentials-and-secrets-to-all-machines>`

.. image:: _static/deployment_statechart_1.svg
    :target: _static/deployment_statechart_1.pdf
    :align: center

.. _deployment-set-up-your-deployment-computer:

Set Up Your Deployment Computer
-------------------------------

Our first step will be to setup our deployment computer:

* :ref:`install ansible<deployment-install-ansible-on-deployment-computer>`
* :ref:`setup private ssh keys<deployment-setup-private-keys-on-deployment-computer>`
* :ref:`make a deployment directory<deployment-make-a-deployment-directory>`

.. image:: _static/d_setup_deployment_computer.svg
    :target: _static/d_setup_deployment_computer.pdf
    :align: center

.. _deployment-install-ansible-on-deployment-computer:

Install Ansible on Deployment Computer
--------------------------------------

.. include:: i_install_ansible.rst

.. _deployment-setup-private-keys-on-deployment-computer:

Setup Private Keys on Deployment Computer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: i_setting_up_ssh.rst


.. _deployment-make-a-deployment-directory:

Make a Deployment Directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The files needed to tell Ansible what to do need to be placed in a directory.
Suppose we want this directory in the home folder of our deployment machine:

.. code-block:: python

  mkdir ~/miros_rabbitmq_deployment

After we have finished this step we have a ``id_rsa.pub`` file on our deployment
computer.

.. image:: _static/deployment_machines_step_1.svg
    :target: _static/deployment_machines_step_1.pdf
    :align: center

.. _deployment-what-machine-do-you-want-in-your-distributed-system:

What Machines do you want in your Distributed System
-------------------------------------------------------------
In this second deployment step we will determine what computers we want in our
system, create secure connections between them and our deployment computer, then
put some information into an Ansible inventory file, so Ansible will know which
machines we want to deploy to:

* :ref:`ensure ssh passwordless access on all machines from deployment computer<deployment-ensure-ssh-passwordless-access-to-all-remote-machines>`
* :ref:`create ansible inventory file<deployment-create-ansbile-inventory-file>`

.. image:: _static/d_determine_what_machines_you_want_in_your_distributed_system.svg
    :target: _static/d_determine_what_machines_you_want_in_your_distributed_system.pdf
    :align: center

The Ansible inventory file can be used for many many different deployments, so
it is organized into named groups.  Come up with a named group for your
miros-rabbitmq deployment, mine is called ``scotty`` because that is the name of
the raspberry pi it runs from.

Collect the IP addresses, or URLs of all of the machines that you want in your
distributed system.  Then collect the user names for each machine.

.. _deployment-ensure-ssh-passwordless-access-to-all-remote-machines:

Ensure SSH Passwordless Access to All Remote Machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: i_setting_up_ssh_on_remote.rst

.. _deployment-create-ansbile-inventory-file:

Create Ansible Inventory File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: i_tell_ansible_where_to_run.rst

Let's look at what we have done so far:

.. image:: _static/deployment_machines_step_2.svg
    :target: _static/deployment_machines_step_2.pdf
    :align: center

.. _deployment-invent-your-credentials-and-secrets:

Invent your Credentials and Secrets
-----------------------------------
Let's create an unencrypted version of our vault file.  This will be broken down
into the following steps:

* :ref:`invent RabbitMQ server credentials and settings<deployment-invent-rabbitmq-server-credentials-and-settings>`
* :ref:`create the RabbitMQ connection parameters <deployment-set-rabbitmq-connection-parameters>`
* :ref:`invent miros-rabbitmq encryption keys <deployment-invent-miros-rabbitmq-encryption-keys>`
* :ref:`add encryption keys to the fake_value <deployment-add-encryption-keys-to-the-fake-vault>`

.. image:: _static/d_invent_credentials_and_secrets.svg
    :target: _static/d_invent_credentials_and_secrets.pdf
    :align: center

On our deployment computer we make a fake_vault file in our deployment
directory:

.. code-block:: bash

  cd ~/miros_rabbitmq_deployment
  touch fake_vault

.. warning::

  Keep this ``fault_vault`` file out of your code revision system.

The ``fake_vault`` file is called this so we don't forget that it isn't
encrypted.  Eventually we will encrypt it and place it within the Ansible file structure,
but for now, let's just leave where it is and treat it as a ``yaml`` file.

.. _deployment-invent-rabbitmq-server-credentials-and-settings:

Invent RabbitMQ Server Credentials and Settings
-----------------------------------------------

Let's start adding our secrets to this file.  We will start with our RabbitMQ
credentials and parameters:

.. code-block:: yaml

  vault_RABBIT_USER: peter
  vault_RABBIT_PASSWORD: rabbit
  vault_RABBIT_PORT: 5672
  vault_RABBIT_GUEST_PASSWORD: rabbit567

.. note::

  The ``vault`` word prepended to our variables is a ansible coding convention.
  It means that the values associated with the variable are intended to be
  encrypted.

.. _deployment-set-rabbitmq-connection-parameters:

Set RabbitMQ Connection Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now let's add our rabbit_heart_beat_interval and connection_attempts settings to
our file:

.. code-block:: yaml

  vault_RABBIT_HEARTBEAT_INTERVAL: 3600
  vault_CONNECTION_ATTEMPTS: 3
  vault_RABBIT_USER: peter
  vault_RABBIT_PASSWORD: rabbit
  vault_RABBIT_PORT: 5672
  vault_RABBIT_GUEST_PASSWORD: rabbit567

Save and close the ``fake_vault`` file.  

.. _deployment-invent-miros-rabbitmq-encryption-keys:

Invent miros-rabbitmq Encryption Keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now we need to generate some encryption keys for the
mesh, snoop_trace and snoop_spy networks.  To do this, open the python3
terminal, import ``cryptography`` and use it to generate some keys:

.. code-block:: python

  $ python3
  from cryptography import Fernet
  encryption_key = Fernet.generate_key()
  print(encryption_key) # => u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg=

You can do this once per needed key, or just use the same key each time.  In
this example I will just use the same key over and over again.

.. _deployment-add-encryption-keys-to-the-fake-vault:

Add Encryption Keys to the Fake Vault
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now re-open the ``fake_vault`` file and set the mesh, snoop_trace and snoop_spy
encryption keys:

.. code-block:: python
  
  vault_MESH_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_SNOOP_TRACE_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_SNOOP_SPY_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_RABBIT_HEARTBEAT_INTERVAL: 3600
  vault_CONNECTION_ATTEMPTS: 3
  vault_RABBIT_USER: peter
  vault_RABBIT_PASSWORD: rabbit
  vault_RABBIT_PORT: 5672
  vault_RABBIT_GUEST_PASSWORD: rabbit567

.. warning::

  The ``fault_vault`` file needs to be in yaml format.  The yaml interpretor
  used by ansible will get confused by your encryption key unless you put it
  between quotation makes.  In fact the error message will spill your secrets
  for everyone to see.

Let's look at what we have done so far:

.. image:: _static/deployment_machines_step_3.svg
    :target: _static/deployment_machines_step_3.pdf
    :align: center

.. _deployment-setup-ansible-file-structure-on-the-deployment-computer:

Setup Ansible File Structure on the Deployment Computer
-------------------------------------------------------
At this point we have an unencrypted vault file, ``fake_vault``, we have setup
the Ansible inventory so that it knows what machines we want to connect to and
our deployment computer can communicate with our remote devices using SSH without
needing to provide a password.

Now we will design our Ansible deployment system:

* :ref:`setup ansible directory structure<deployment-setting-up-the-ansible-directory-structure>`
* :ref:`setup global variables used for all computers in your distributed system<deployment-setup-ansible-global-variable-used-by-all-remote-machines>`
* :ref:`determine where you want your software on your remote machines<deployment-determine-where-you-will-install-your-software-one-your-remote-machines>`
* :ref:`add template files <deployment-add-our-template-files>`
* :ref:`create the ansible playbook <deployment-create-the-miros-rabbitmq-playbook>`

.. image:: _static/d_setup_ansible_file_structure_on_deployment_computer.svg
    :target: _static/d_setup_ansible_file_structure_on_deployment_computer.pdf
    :align: center

.. _deployment-setting-up-the-ansible-directory-structure:

Setting Up the Ansible Directory Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _deployment-setup-ansible-global-variable-used-by-all-remote-machines:

Setup Ansible Global Variable Used By all Remote Machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _deployment-determine-where-you-will-install-your-software-one-your-remote-machines:

Determine Where you will Install your Software one your Remote Machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _deployment-add-our-template-files:

Add Our Template Files
^^^^^^^^^^^^^^^^^^^^^^

.. _deployment-create-the-miros-rabbitmq-playbook:

Create the miros-rabbitmq playbook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _deployment-deploy-your-infrastructure-credentials-and-secrets-to-all-machines:

Deploy Your Infrastructure Credentials and Secrets to all Machines
------------------------------------------------------------------

.. image:: _static/d_deploy_your_infrastructure_credentials_and_secrets_to_all_machines.svg
    :target: _static/d_deploy_your_infrastructure_credentials_and_secrets_to_all_machines.pdf
    :align: center

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
