.. _deployment-deployment:

.. epigraph::

  *If you think it's expensive to hire a professional to do the job, wait unit
  you hire an amateur.*

  -- Red Adair

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

* It should be automated
* It should use trusted open source technologies (ssh, Ansible vault, .env files, ... )
* It *can only deploy* to Linux computers/containers (WLS will not be supported).
* All of the remote machines in your system will have the same ``sudo`` password.
* It should run from one deployment machine and deploy to an arbitrary number of other remote computers/containers.
* All machines in your system will be assumed to be secure.
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
* It will securely transfer your secrets from your deployment machine onto your
  remote machines.

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

Where you are reading each section, you will find:

* a cheatsheet for fast reference
* a detailed written description of the things needed to do the step
* a summary of what you have accomplished at the end of the step

.. _deployment-set-up-your-deployment-computer:

1. Set Up Your Deployment Computer
----------------------------------

Our first step will be to setup our deployment computer:

* :ref:`install ansible<deployment-install-ansible-on-deployment-computer>`
* :ref:`setup private ssh keys<deployment-setup-private-keys-on-deployment-computer>`
* :ref:`make a deployment directory<deployment-make-a-deployment-directory>`
* :ref:`things accomplished so far<deployment-thing-accomplished-so-far-1>`

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

The deployment directory will contain all of the files that will tell Ansible
what we want it to do. Let's make the deployment directory.  

.. code-block:: python

  mkdir ~/miros_rabbitmq_deployment

.. _deployment-thing-accomplished-so-far-1:

Things Accomplished So Far
^^^^^^^^^^^^^^^^^^^^^^^^^^

After we have finished :ref:`this step <deployment-set-up-your-deployment-computer>` we have a ``id_rsa.pub`` file on our deployment
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

* :ref:`collect the addresses and ssh usernames for all remote machines <deployment-collect-the-addresses-and-ssh-usernames-for-all-remote-machines>`
* :ref:`ensure ssh passwordless access on all machines from deployment computer<deployment-ensure-ssh-passwordless-access-to-all-remote-machines>`
* :ref:`name the collection of addresses and usernames <deployment-name-the-collection-of-addresses-and-usernames>`
* :ref:`create ansible inventory file<deployment-create-ansbile-inventory-file>`
* :ref:`things accomplished so far<deployment-things-accomplished-so-far-2>`

.. image:: _static/d_determine_what_machines_you_want_in_your_distributed_system.svg
    :target: _static/d_determine_what_machines_you_want_in_your_distributed_system.pdf
    :align: center

.. _deployment-collect-the-addresses-and-ssh-usernames-for-all-remote-machines:

Collect the Addresses and ssh usernames for all Remote Machines
---------------------------------------------------------------
Ansible will deploy your software and push your files to each of your remote
machines using ssh.  So, we need to collect the addresses and usernames for all
of the machines/containers in your deployment.  The addresses can be in the form
of an IP address or a traditional URL.  The username will be user which you will
login as and under who's permissions you will be installing your code.  This
should not be the root user.

.. _deployment-ensure-ssh-passwordless-access-to-all-remote-machines:

Ensure SSH Passwordless Access to All Remote Machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _deployment-name-the-collection-of-addresses-and-usernames:

.. include:: i_setting_up_ssh_on_remote.rst

Name the Collection of Addresses and Usernames
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Ansible inventory file can be used for many different deployments, so it is
organized into named groups.  Come up with a named group for your miros-rabbitmq
deployment, what would you like to call your distributed system?.  Mine is
called ``scotty`` because that is the name of the raspberry pi it runs from.

Collect the IP addresses, or URLs of all of the machines that you want in your
distributed system.  Then collect the user names for each machine.

.. _deployment-create-ansbile-inventory-file:

Create Ansible Inventory File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: i_tell_ansible_where_to_run.rst

.. _deployment-things-accomplished-so-far-2:

Things Accomplished So Far
^^^^^^^^^^^^^^^^^^^^^^^^^^

After completing this :ref:`step<deployment-what-machine-do-you-want-in-your-distributed-system>`, this is what has been done so far:

.. image:: _static/deployment_machines_step_2.svg
    :target: _static/deployment_machines_step_2.pdf
    :align: center

.. _deployment-invent-your-credentials-and-secrets:

Invent your Credentials and Secrets
-----------------------------------
Let's create an unencrypted version of our vault file.  This will be broken down
into the following steps:

* :ref:`make a fake_vault file<deployment-make-a-fake_vault-file>`
* :ref:`invent RabbitMQ server credentials and settings<deployment-invent-rabbitmq-server-credentials-and-settings>`
* :ref:`create the RabbitMQ connection parameters <deployment-set-rabbitmq-connection-parameters>`
* :ref:`invent miros-rabbitmq encryption keys <deployment-invent-miros-rabbitmq-encryption-keys>`
* :ref:`add encryption keys to the fake_value <deployment-add-encryption-keys-to-the-fake-vault>`
* :ref:`things accomplished so far<deployment-things-accomplished-so-far-3>`

.. image:: _static/d_invent_credentials_and_secrets.svg
    :target: _static/d_invent_credentials_and_secrets.pdf
    :align: center

.. _deployment-make-a-fake_vault-file:

Make a fake_vault file
^^^^^^^^^^^^^^^^^^^^^^

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

.. _deployment-things-accomplished-so-far-3:

Things Accomplished So Far
^^^^^^^^^^^^^^^^^^^^^^^^^^

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
* :ref:`things accomplished so far<deployment-things-accomplished-so-far-4>`

.. image:: _static/d_setup_ansible_file_structure_on_deployment_computer.svg
    :target: _static/d_setup_ansible_file_structure_on_deployment_computer.pdf
    :align: center

Before we start this step make sure you working in your deployment directory of your deployment machine.  In my
case:

.. code-block:: python

  cd ~/miros_rabbitmq_deployment

.. _deployment-setting-up-the-ansible-directory-structure:

Setting Up the Ansible Directory Structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Our Ansible program will be partially organized into directories.  But, before we
talk about this, let's consider what we want:

* We want to keep some of our distributed system settings as plain text files
* We want to encrypt some of our information on our deployment machine
* We want to create some template files that will be used with our stored
  setting information to make new files.  These new files will be posted into
  specific locations in the directory structure of our remote computers.
* We want a set of instructions that will tell Ansible what software to deploy.
  These instructions will be dependent upon some of our settings.
* We want to keep all of these files under revision control, it's code afterall.

Ansible let's you assign your settings to variables which can be used to either
fill in a template file or run a playbook.  A playbook is a YAML file which
lists a series of deployment instructions, run against an inventory.  In our
case the inventory consists of the addresses and names we wrote into our
``/etc/ansible/hosts`` file.  Its name was ``scotty``.

Ansible has developed some customs since its inception.  If you have an encrypted vault file they
want you to organize your variable files as:

.. code-block:: code

  # plain text settings assigned to variables
  ./group_vars/<inventory_name>/vars

  # encrypted file, settings assigned to variables
  ./group_vars/<inventory_name>/vault

The playbooks at the top level directory can just reference the variable names
in these files without explicitly defining the path to them.

Ansible let's you leave your template files at the top level of your deployment
directory, or to salt them away into a templates directory.  If you put them
into a templates directory, you don't have to explicitly define the path to them
in your playbook, Ansible knows where they are.

Now that we understand this stuff, let's setup our directory structure:

.. code-block:: bash

  $ mkdir group_vars
  $ mkdir ./group_vars/scotty
  $ touch ./group_vars/scotty/vars
  $ mkdir ./templates

Our deployment directory structure will now look something like:

.. code-block:: python

    .
    ├── group_vars
    │   └── scotty
    │       └── vars
    └── templates

.. _deployment-setup-ansible-global-variable-used-by-all-remote-machines:

Setup Ansible Global Variable Used By all Remote Machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In this step we will assign all of our global variables.  The variables are
defined in the ``./group_vars`` subdirectory.  We will do this in several
stages.

**Encrypt credentials and secrets in the vault:**
We need to encrypt our ``fake_vault`` file.  To do this:

.. code-block:: python

  $ mv fake_vault ./group_vars/<inventory_name>/vault
  $ ansible-vault ./group_vars/<inventory_name>/vault

.. warning:: 

  Make sure you remember your vault encryption key ;)

To confirm that the file was encrypted, you can just look at it:

.. code-block:: python

  $ cat ./global_vars/scotty/vault

  $ANSIBLE_VAULT;1.1;AES256
  34363736353133336561626464646437613...

Here we see that the file was encrypted using AES256.

**Edit your encypted vault file:**  Let's confirm we can re-open this file and
then copy it's variable names, so that we can reference them in our ``vars``
file:

.. code-block:: yaml

  $ ansible-vault edit ./global_vars/scotty/vault

  ---
  vault_MESH_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_SNOOP_TRACE_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_SNOOP_SPY_ENCRYPTION_KEY: 'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  vault_RABBIT_HEARTBEAT_INTERVAL: 3600
  vault_CONNECTION_ATTEMPTS: 3
  vault_RABBIT_USER: peter
  vault_RABBIT_PASSWORD: rabbit
  vault_RABBIT_PORT: 5672
  vault_RABBIT_GUEST_PASSWORD: rabbit567

Copy the variable names, you will be using them in the next step.
Close the file.  This will automatically re-encrypt it.

**Add vars file**:

.. code-block:: python

  pico ./global_vars/scotty/vars

Now add your settings information to the vars file:

.. code-block:: yaml

  ---
  # public
  python_packages_to_install:
    - miros-rabbitmq
  rabbit_tags:
   - administrator

  # secrets
  rabbit_user: "{{ vault_RABBIT_USER }}"
  rabbit_password: "{{ vault_RABBIT_PASSWORD }}"
  rabbit_port: "{{ vault_RABBIT_PORT }}"
  rabbit_heartbeat_interval: "{{ vault_RABBIT_HEARTBEAT_INTERVAL }}"
  connection_attempts: "{{ vault_CONNECTION_ATTEMPTS }}"
  rabbit_guest_password: "{{ vault_RABBIT_GUEST_PASSWORD }}"
  mesh_encryption_key: "{{ vault_MESH_ENCRYPTION_KEY }}"
  snoop_trace_encryption_key: "{{ vault_SNOOP_TRACE_ENCRYPTION_KEY }}"
  snoop_spy_encryption_key: "{{ vault_SNOOP_SPY_ENCRYPTION_KEY }}"
  rabbit_heart_beat_interval: "{{ vault_RABBIT_HEARTBEAT_INTERVAL }}"

.. note:: 

  Notice that the secret variable names reference the vault variable names
  Things are done this way, so that someone writing a play book using our vault
  can know what a variable name is without knowing how to decrypt the vault
  file.

.. _deployment-determine-where-you-will-install-your-software-one-your-remote-machines:

Determine Where you will Install your Software one your Remote Machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the previous step we defined a bunch of variables that can be used by our
playbook (which we haven't written yet).  We defined a lot of things, but we
didn't establish what directory, on our remote machines, we would like to
install our application into.

This playbook won't deploy any application code, but it will put the ``.env``
file at the top level of its directory.  This directory setting, will be stored
as the ``miros_rabbitmq_project_directory`` variable at the top of the playbook
(when we write it). We will keep it here rather than in the ``global_vars`` directory,
so that it is easy to change while editing the playbook.

.. code-block:: yaml

  # this will be where we want to put our code on the remote machines
  miros_rabbitmq_project_directory: '~/miros-rabbitmq'

.. _deployment-add-our-template-files:

Add Our Template Files
^^^^^^^^^^^^^^^^^^^^^^

Now we will write our template files for our deployment, so far we need three
things:

* a file to tell RabbitMQ about its environment
* a file to configure the RabbitMQ server
* the ``.env`` template.
* a file to tell your program what other nodes to talk to 
* a cache file for its automatic discovery phase

.. code-block:: python

  $ touch ./templates/rabbit-env.config.j2
  $ touch ./templates/rabbit.config.j2
  $ touch ./templates/.env.j2
  $ touch ./templates/.miros_rabbit_hosts.json.j2
  $ touch ./templates/.miros_rabbitlan_cache.j2

The ``j2`` extension is our hint that these files are jinja2 template files.
Here is my barebones ``rabbit-env.config.j2`` template:

.. code-block:: python

  RABBITMQ_CONFIG_FILE=/etc/rabbitmq/rabbitmq
  NODE_IP_ADDRESS=0.0.0.0

Here is the ``rabbitmq.config.j2`` template file:

.. code-block:: erlang

  [
    {rabbit,
      [
        {loopback_users,[]}
      ]
    }
  ]
  .

Neither of the above templates actually used our Ansible variables.  This is OK,
we leave them in the templates directory, so that in the future we have the
option of parameterizing them with our settings.

Now we will create the ``.env.j2`` template, it *will* use our Ansible variables:

.. code-block:: yaml

  ---
  MESH_ENCRYPTION_KEY={{mesh_encryption_key}}
  SNOOP_TRACE_ENCRYPTION_KEY={{snoop_trace_encryption_key}}
  SNOOP_SPY_ENCRYPTION_KEY={{snoop_spy_encryption_key}}
  RABBIT_USER={{rabbit_user}}
  RABBIT_PASSWORD={{rabbit_password}}
  RABBIT_PORT={{rabbit_port}}
  RABBIT_HEARTBEAT_INTERVAL={{rabbit_heart_beat_interval}}
  CONNECTION_ATTEMPTS={{connection_attempts}}
  RABBIT_GUEST_USER={{rabbit_guest_user}}

The ``.miros_rabbit_hosts.json.j2`` file is used to manually set the IP
addresses that will be used by your program to talk to other nodes in your
distributed system.  Well, you wrote this list into your inventory file, so
let's just have Ansible write out the ``.miros_rabbit_host.json`` file for us.
Here is its template file:

.. code-block:: jinja2
  
  {
    "hosts": [
    {% for host in ansible_play_batch %}
    "{{ host }}"{% if not loop.last %},{% endif %}
    {% endfor %}

    ]
  }

Finally, miros-rabbitmq uses another file called ``.miros_rabbitlan_cache.json``
which contains a list of all of the other nodes like it that it has discovered
in it's LAN.  We don't know anything about that so we will write a file that has
the correct structure, but it empty and will force a search the first time you
run your program after you have deployed it.  Here is its template file:

.. code-block:: jinja2

  {
    "addresses": [
    ],
    "amqp_urls": [
    ],
    "time_out_in_minutes": 0
  }

When we have finished this step our deployment directory will look like:

.. code-block:: python

  .
  ├── group_vars
  │   └── scotty
  │       ├── vars
  │       └── vault
  └── templates
      ├── .env.j2
      ├── .miros_rabbitlan_cache.json.j2
      ├── .miros_rabbit_hosts.json.j2
      ├── rabbitmq.config.j2
      └── rabbitmq-env.conf.j2

.. _deployment-create-the-miros-rabbitmq-playbook:

Create the miros-rabbitmq playbook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now that we have defined our vault, variables and template files.  We will build
our Ansible playbook, so Ansible can deploy our system.

First we create a file:

.. code-block:: python

  $ touch ./miros_rabbitmq_install.yml

The play book it yet another YAML file.  Now let's write the file:

.. code-block:: yaml

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

     - name: Write the .miros_rabbitlan_cache.json file
         template:
           src: .miros_rabbitlan_cache.json.j2
           dest: "{{ miros_rabbitmq_project_directory }}/.miros_rabbitlan_cache.json"
           mode: "u=rw,g=r,o=r"
         tags:
           - 'cache'

       - name: Write the .miros_rabbit_hosts.json file
         template:
           src: .miros_rabbit_hosts.json.j2
           dest: "{{ miros_rabbitmq_project_directory }}/.miros_rabbit_hosts.json"
           mode: "u=rw,g=rw,o=r"
         tags:
           - 'hosts'

.. note:: 
  
  Extend this playbook to customize your deployment.

.. _deployment-things-accomplished-so-far-4:

Things Accomplished So Far
^^^^^^^^^^^^^^^^^^^^^^^^^^
We encrypted our vault file in this step.  Our secrets and infrastructure are
ready to be deployed to the system:

.. image:: _static/deployment_machines_step_4.svg
    :target: _static/deployment_machines_step_4.pdf
    :align: center

Our deployment directory will look like this:

.. code-block:: text

    ├── group_vars
    │   └── scotty
    │       ├── vars
    │       └── vault
    ├── miros_rabbitmq_install.yml
    └── templates
      ├── .miros_rabbitlan_cache.json.j2
      ├── .miros_rabbit_hosts.json.j2
      ├── rabbitmq.config.j2
      ├── rabbitmq-env.conf.j2
      └── .env.j2

.. _deployment-deploy-your-infrastructure-credentials-and-secrets-to-all-machines:

Deploy Your Infrastructure Credentials and Secrets to all Machines
------------------------------------------------------------------

.. image:: _static/d_deploy_your_infrastructure_credentials_and_secrets_to_all_machines.svg
    :target: _static/d_deploy_your_infrastructure_credentials_and_secrets_to_all_machines.pdf
    :align: center

To have your playbook run on each of the servers defined in your inventory, you would
run:

.. code-block:: python

  ansible-playbook -K miros_rabbit_install.yml --ask-vault-pass
  BECOME password:
  Vault password:

The ``BECOME password`` is the password to run ``sudo`` commands on the remote server,
and the ``Vault password`` is the password you used to encrypt your vault file.

Upon completing this step:

.. image:: _static/deployment_machines_step_5.svg
    :target: _static/deployment_machines_step_5.pdf
    :align: center

.. raw:: html

  <a class="reference internal" href="docs.html"><span class="std std-ref">prev</span></a>,
  <a class="reference internal" href="index.html#top"><span class="std std-ref">top</span></a>,
  <span class="inactive-link">next</span>
