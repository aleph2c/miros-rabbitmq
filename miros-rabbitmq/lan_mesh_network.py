#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
This package is used to link a miros statechart into an encrypted mesh network
on a LAN.

RabbitMq serves this mesh network so each node will have to run a RabbitMq
server.  There are two different ways for this package to provide mesh
communications.  The first way uses 'topic_routing' and serialization; which
will allow any node to share any Python object, across the mesh network.  The
second way to communicate is to provide an instrumentation channel using the
'fanout' routing technique; this will allow the spy and trace outputs of each
statechart to route to one machine for debugging purposes.

The encryption keys used by the normal mesh will have to be common across all
nodes.  Likewise, the encryption keys used by the instrumentation mesh will have
to be common across all of its nodes.

  Normal Mesh Examples:

    To set the normal mesh encrytion key:
      NetworkTool.encryption_key = <new_key>

    To generate a new key:
      Fernet.generate_key()

    To set up a normal mesh transmitter:
      tx = MeshTransmitter(user="bob", password="dobbs", port=5672)

    To use a normal mesh transmitter:
      tx.message_to_other_channels(
        Event(
          signal=signals.Mirror,
          payload=[1, 2, 3]),
          routing_key = 'archer.mary')

    To set up a normal mesh receiver:
      rx = MeshReceiver(
        user='bob',
        password='dobbs',
        port=5672,
        routing_key='archer.#')

      # set up the callback which will receive the message
      def custom_rx_callback(ch, method, properties, body):
        print(" [+] {}:{}".format(method.routing_key, body))

      # register the callback with your receiver
      rx.register_live_callback(custom_rx_callback)

      # start the receivers thread to consume messages
      rx.start_consuming()

      # to stop this thread
      rx.stop_consuming()

  Instrumentation Mesh Examples:

    To generate a new encyption key:
      Fernet.generate_key()

    To use an instrumentation mesh transmitter:
      tx_instrument = SnoopTransmitter(
        user='bob',
        password='dobbs',
        port=5672,
        encryption_key=
          b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0='
      )

      # Given that ao is a statechart object you would register it's live
      # spy/trace output with the tx_instrument broadcast_spy and
      # broadcast_trace methods respectively:
      ao.register_live_spy_callback(tx_instrument.broadcast_spy)
      ao.register_live_trace_callback(tx_instrument.broadcast_trace)

      # Or you can broadcast messages directly to the connected spy and trace
      # exchanges:
      tx_instrument.broadcast_spy("Spy information")
      tx_instrument.broadcast_spy("Trace information")

    To use an instrumentation mesh receiver:
      rx_instrumentation = SnoopReceiver(
        user='bob',
        password='dobbs',
        port=5672,
        encryption_key=
          b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0=')

      rx_instrumentation.start_consuming()

      def custom_spy_callback(ch, method, properties, body):
        print(" [+s] {}:{}".format(method.routing_key, body))

      def custom_trace_callback(ch, method, properties, body):
        print(" [+t] {}:{}".format(method.routing_key, body))

      # register spy instrumentation callback with your rx_instrumentation
      rx_instrumentation.register_live_spy_callback(custom_spy_callback)

      # register trace instrumentation callback with your rx_instrumentation
      rx_instrumentation.register_live_trace_callback(custom_trace_callback)

  More Examples:
    To see specific examples of how to use this package see the bottom of the
    file.

  Notes:

    RabbitMq setup:
      To install RabbitMq use the ansible play book and the templates found
      here:
      https://github.com/aleph2c/miros/tree/master/experiment/rabbit/ansible

      For specific instructions on how to use the ansible files linked to above,
      read:
      https://aleph2c.github.io/miros/setting_up_rabbit_mq.html

    Routing keys:
      All topic routing keys have the destination IP address prepended to them

'''

# NOT in the standard library
import pika
import netifaces
from miros.hsm import pp
from miros.event import signals, Event  # "
from miros.hsm import HsmWithQueues, spy_on
from miros.activeobject import Factory
from miros.event import signals, Event, return_status

# in the standard library
import sys
import time
import uuid
import socket
import pickle
import subprocess
import cryptography
from functools import wraps
from threading import Thread
from types import SimpleNamespace
from miros.foreign import ForeignHsm
from cryptography.fernet import Fernet
from threading import Event as ThreadingEvent

class NetworkTool():
  '''
  A collection of networking static methods used by different objects within this
  package.

  API:
    # Get information
    NetworkTool.get_working_ip_address()  -> get your own ip address
    NetworkTool.ip_addresses_on_lan       -> get all IP addresses on LAN

    NetworkTool.serialize                 -> serialization decorator
    NetworkTool.deserialize               -> deserialization decorator

    NetworkTool.key()                     -> get the encryption key
    NetworkTool.ecrypt                    -> encryption decorator
    NetworkTool.decrypt                   -> decryption decorator

    NetworkTool.get_blocking_connection() -> get a blocking connection to a
                                            RabbitMq server

    # Set information
    NetworkTool.encryption_key = <new_key>

  '''
  # To generate a new key: Fernet.generate_key()
  encryption_key = b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
  exchange_name  = 'mirror'

  @staticmethod
  def get_working_ip_address():
    '''
    Get the ip of this computer:

    Example:
      my_ip = NetworkTool.get_working_ip_address()

    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      s.connect(('10.255.255.255', 1))
      ip = s.getsockname()[0]
    except:
      ip = '127.0.0.1'
    finally:
      s.close()
    return ip

  @staticmethod
  def key():
    '''
    Get the encryption key for this connection.  This key is used for encryption
    and decryption.

    Example:
      key = NetworkTool.key()

    Note:
      To generate a new key: Fernet.generate_key()
      A better way to do this is to get the key from your connected flash-drive.

    '''
    return NetworkTool.encryption_key

  @staticmethod
  def get_blocking_connection(user, password, ip, port):
    '''
    Create and get a blocking connection to a rabbitMq server running on this,
    or another machine:

    Example:
      connection = NetworkTool.get_blocking_connection(
        'bob', 'dobbs', '192.168.1.72', 5672)
    '''
    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(ip, port, '/', credentials)
    connection = pika.BlockingConnection(parameters=parameters)
    return connection

  @staticmethod
  def serialize(fn):
    '''
    A decorator which will turn arguments into a byte stream prior to encryption:

    Example:
      @NetworkTool.serialize  # <- HERE: 'message' turned into byte stream
      @NetworkTool.encrypt
      def message_to_other_channels(self, message):
        for channel in self.channels:
          ip = channel.extension.ip_address
          channel.basic_publish(exchange=NetworkTool.exchange_name,
              routing_key=ip, body=message)
          print(" [x] Sent \"{}\" to {}".format(message, ip))

    '''
    @wraps(fn)
    def _pickle_dumps(*args, **kwargs):
      routing_key = None
      if 'routing_key' in kwargs:
        routing_key = kwargs['routing_key']

      if len(args) == 1:
        message = args[0]
      else:
        message = args[1]

      # The event object is dynamically constructed and can't be serialized by
      # pickle, so we call it's custom serializer prior to pickling it
      if isinstance(message, Event):
        message = Event.dumps(message)

      pmessage = pickle.dumps(message)

      if len(args) == 1:
        fn(pmessage)
      else:
        if routing_key is None:
          fn(args[0], pmessage)
        else:
          fn(args[0], pmessage, routing_key=routing_key)

    return _pickle_dumps

  @staticmethod
  def encrypt(fn):
    '''
    A decorator which will encrypt a byte stream prior to transmission:

    Example:
      @NetworkTool.serialize
      @NetworkTool.encrypt   # <- HERE: 'message' bytestream encyrpted
      def message_to_other_channels(self, message):
        for channel in self.channels:
          ip = channel.extension.ip_address
          channel.basic_publish(exchange=NetworkTool.exchange_name,
              routing_key=ip, body=message)
          print(" [x] Sent \"{}\" to {}".format(message, ip))
    '''
    @wraps(fn)
    def _encrypt(*args, **kwargs):
      '''
      encrypt a byte stream
      '''
      routing_key = None
      if 'routing_key' in kwargs:
        routing_key = kwargs['routing_key']

      # To get around the self as the first argument issue
      if len(args) == 1:
        plain_text = args[0]
      else:
        plain_text = args[1]

      f = Fernet(NetworkTool.key())
      cyphertext = f.encrypt(plain_text)

      if len(args) == 1:
        fn(cyphertext)
      else:
        if routing_key is None:
          # args[0] is self
          fn(args[0], cyphertext)
        else:
          fn(args[0], cyphertext, routing_key=routing_key)
    return _encrypt

  @staticmethod
  def decrypt(fn):
    '''
    A decorator which will decrypt a received message into a byte stream.

    Example:
      @NetworkTool.decrypt  # <- HERE: 'body' decrypted into a byte stream
      @NetworkTool.deserialize
      def custom_rx_callback(ch, method, properties, body):
        print(" [+] {}:{}".format(method.routing_key, body))
    '''
    @wraps(fn)
    def _decrypt(ch, method, properties, cyphertext):
      '''LocalConsumer.decrypt()'''
      f = Fernet(NetworkTool.key())
      try:
        plain_text = f.decrypt(cyphertext)
      except cryptography.fernet.InvalidToken:
        plain_text = cyphertext
      fn(ch, method, properties, plain_text)
    return _decrypt

  @staticmethod
  def deserialize(fn):
    '''
    A decorator turn a serialized byte stream into a python object

    Example:
      @NetworkTool.decrypt
      @NetworkTool.deserialize  # <- HERE: 'body' bytestream turn into object
      def custom_rx_callback(ch, method, properties, body):
        print(" [+] {}:{}".format(method.routing_key, body))
    '''
    @wraps(fn)
    def _pickle_loads(ch, method, properties, p_plain_text):
      try:
        plain_text = pickle.loads(p_plain_text)
      except ValueError:
        plain_text = p_plain_text

      try:
        plain_text = Event.loads(plain_text)
      except:
        print("failing")

      fn(ch, method, properties, plain_text)
    return _pickle_loads

  @staticmethod
  def ip_addresses_on_lan():
    '''
    The Windows Linux Subsystem is currently broken, it does not support a lot
    of Linux networking commands - so, we can't use the nice tooling provided
    by the community.  Instead I call out to the cmd.exe file of DOS and send it
    the DOS version of arp to get a list of IP addresses on the LAN.

    The 'grep -Po 192\.\d+\.\d+\.\d+' applies the Perl regular expression
    with matching output only to our stream.  This will return all of the IP
    addresses in the class C family (192.xxx.xxx.xxx)

    Example:
      ip_addresses = NetworkTool.ip_addresses_on_lan()
    '''
    wsl_cmd   = 'cmd.exe /C arp.exe -a'
    linux_cmd = 'arp -a'

    grep_cmd = 'grep -Po 192\.\d+\.\d+\.\d+'
    candidates = []

    for cmd in [wsl_cmd, linux_cmd]:
      cmd_as_list = cmd.split(" ")
      grep_as_list = grep_cmd.split(" ")
      output = ''
      try:
        ps = subprocess.Popen(cmd_as_list, stdout=subprocess.PIPE)
        # output = subprocess.check_output(grep_as_list, stdin=ps.stdout, timeout=0.5)
        output = subprocess.check_output(grep_as_list, stdin=ps.stdout, timeout=1.5)
        ps.wait()
        if output is not '':
          candidates = output.decode('utf-8').split('\n')
          if len(candidates) > 0:
            break
      except:
        # our windows command did not work on Linux
        pass
    return list(filter(None, candidates))

  @staticmethod
  def ip_addresses_on_this_machine():
    '''
    There are situations where we would like to know all of the IP addresses
    connected to this one machine.

    Example:
      list_of_my_ips_address = NetworkTool.ip_addresses_on_this_machine()
    '''
    interfaces = [interface for interface in netifaces.interfaces()]
    local_ip_addresses = []
    for interface in interfaces:
      interface_network_types = netifaces.ifaddresses(interface)
      if netifaces.AF_INET in interface_network_types:
        ip_address = interface_network_types[netifaces.AF_INET][0]['addr']
        local_ip_addresses.append(ip_address)
    return local_ip_addresses


class ReceiveConnections():
  '''
  Receives connections on this ip address from port 5672

  It creates a NetworkTool.exchange_name exchange using direct routing where the
  routing key is this ip address as a string.

  The interface to this class should be done through the MeshReceiver

  Example:
    rx = ReceiveConnections(user="bob", password="dobbs")

  '''
  def __init__(self, user, password, port=5672, routing_key=None):
    # create a connection and a direct exchange called 'mirror', see
    # NetworkTool.exchange_name on this ip
    self.connection = NetworkTool.get_blocking_connection(user, password, NetworkTool.get_working_ip_address(), port)
    self.channel = self.connection.channel()
    self.channel.exchange_declare(exchange=NetworkTool.exchange_name, exchange_type='topic')

    # destroy the rabbitmq queue when done
    result = self.channel.queue_declare(exclusive=True)
    self.queue_name = result.method.queue

    self.channel.queue_bind(exchange=NetworkTool.exchange_name, queue=self.queue_name, routing_key=routing_key)

    # The 'start_consuming' method of the pika library will block the program.
    # for this reason we will put it in it's own thread so that it does not harm
    # our program flow, to communicate to it we use an Event from the threading
    # class
    self.task_run_event = ThreadingEvent()
    self.task_run_event.set()

    # We provide a default message callback, but it is more than likely that the
    # client will register their own (why else use this class?)
    self.live_callback = self.default_callback
    print(' [x] Waiting for messages. To exit press CTRL-C')

    # We wrap the tunable callback with decryption and a serial decoder
    # this way the client doesn't have to know about this complexity
    @NetworkTool.decrypt
    @NetworkTool.deserialize
    def callback(ch, method, properties, body):
      self.live_callback(ch, method, properties, body)

    # Register the above callback with the queue, turn off message
    # acknowledgements
    self.channel.basic_consume(callback, queue=self.queue_name, no_ack=True)

  def default_callback(self, ch, method, properties, body):
    '''
    This default callback is provided out of the box, it will be ignored by the
    client since they will register their own callback

    Example:
      # not needed, you won't use this
    '''
    print(" [x] {}:{}".format(method.routing_key, body))

  def register_live_callback(self, live_callback):
    '''
    Register a callback with this object.  It will be called once a message is
    received, decrypted and decoded.

    Example:

      def custom_rx_callback(ch, method, properties, body):
        print(" [+] {}:{}".format(method.routing_key, body))

      rx = MeshReceiver('bob', 'dobbs')
      rx.register_live_callback(custom_rx_callback)

    '''
    self.live_callback = live_callback

  def start_consuming(self):
    # We make a thread so that the channel.start_consuming doesn't steal our
    # program control.

    # The thread has it's own timeout callback (pika) which wakes up every 10
    # seconds and checks the self.trask_run_event, which is controlled outside
    # of the thread.  If it is set, it continues to work, if it isn't set it
    # stop the pika consumer and the thread dies.
    def channel_consumer(self):
      '''
      This timeout_callback is the only way to communicate with a pika channel
      once it has started consuming.  This time out checks to see if this
      thread should die, if so, it calls stop_consuming, if not, it arms
      another timeout callback.  (Working with the library)
      '''
      self.task_run_event.set()

      def timeout_callback():
        if self.task_run_event.is_set():
          self.connection.add_timeout(deadline=10, callback_method=timeout_callback)
        else:
          self.channel.stop_consuming()
          return

      # We are within our own thread, we arm a timeout callback
      self.connection.add_timeout(deadline=10, callback_method=timeout_callback)

      # This process will block forever, with the exception of calling the
      # timeout_callback every 10 seconds.
      self.channel.start_consuming()

    # Create and start the thread.  The thread can be stopped by clearing the
    # task_run_event Event.
    thread = Thread(target=channel_consumer, args=(self,), daemon=True)
    thread.start()

  def stop_consuming(self):
    '''
    This will kill the channel_consumer within the next 10 seconds
    '''
    self.task_run_event.clear()

class SnoopReceiver(ReceiveConnections):
  '''
  Receive spy/trace information from another program's SnoopTransmitter
  object.  This is useful for debugging statecharts working across a network.

  This class creates a 'spy' and 'trace' exchange using a 'fanout' routing
  strategy.

  Example:

    rx_instrumentation = SnoopReceiver(
      user='bob',
      password='dobbs',
      port=5672,
      encryption_key=
        b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0=')

    rx_instrumentation.start_consuming()

    # The rx_instrumentationt will have a ForeignHsm object from which you can
    # view all spy and trace information
    pp(rx_instrumentation.spy())
    print(rx_instrumentation.trace())

    # You can also tie a live_spy and live_trace callback method:
    def custom_spy_callback(ch, method, properties, body):
      print(" [+s] {}:{}".format(method.routing_key, body))

    def custom_trace_callback(ch, method, properties, body):
      print(" [+t] {}:{}".format(method.routing_key, body))

    # register spy instrumentation callback with your rx_instrumentation
    rx_instrumentation.register_live_spy_callback(custom_spy_callback)

    # register trace instrumentation callback with your rx_instrumentation
    rx_instrumentation.register_live_trace_callback(custom_trace_callback)

  '''

  def __init__(self, user, password, port=5672, encryption_key=None):
    self.rabbit_user = user
    self.rabbit_password = password

    if encryption_key is None:
      self.encryption_key = NetworkTool.encryption_key
    else:
      self.encryption_key = encryption_key

    credentials = pika.PlainCredentials(user, password)

    parameters = \
      pika.ConnectionParameters(
        NetworkTool.get_working_ip_address(), port, '/', credentials)

    self.connection = pika.BlockingConnection(parameters=parameters)
    self.channel = self.connection.channel()
    self.channel.exchange_declare(exchange='spy',   exchange_type='fanout')
    self.channel.exchange_declare(exchange='trace', exchange_type='fanout')

    # create new queues, and ensure they destroy themselves when we disconnect
    # from them
    spy_rx   = self.channel.queue_declare(exclusive=True)
    trace_rx = self.channel.queue_declare(exclusive=True)

    # queue names are random, so we need to get their names
    spy_queue_name   = spy_rx.method.queue
    trace_queue_name = trace_rx.method.queue

    # bind the exchanges to each of the queues
    self.channel.queue_bind(exchange='spy', queue=spy_queue_name)
    self.channel.queue_bind(exchange='trace', queue=trace_queue_name)

    # The 'start_consuming' method of the pika library will block the program.
    # for this reason we will put it in it's own thread so that it does not harm
    # our program flow, to communicate to it we use an Event from the threading
    # class
    self.task_run_event = ThreadingEvent()
    self.task_run_event.set()

    # make a ForeignHsm to track activity on another machine
    self.foreign_hsm = ForeignHsm()

    self.live_spy_callback = self.default_spy_callback
    self.live_trace_callback = self.default_trace_callback

    @SnoopReceiver.decrypt(self.encryption_key)
    def spy_callback(ch, method, properties, body):
      '''create a spy_callback function received messages in the queue'''
      foreign_spy_item = body
      self.foreign_hsm.append_to_spy(foreign_spy_item)
      self.live_spy_callback(ch, method, properties, body)

    @SnoopReceiver.decrypt(self.encryption_key)
    def trace_callback(ch, method, properties, body):
      '''create a trace_callback function received messages in the queue'''
      foreign_trace_item = body
      self.foreign_hsm.append_to_trace(foreign_trace_item)
      self.live_trace_callback(ch, method, properties, body)

    # register the spy_callback and trace_callback with a queue
    self.channel.basic_consume(spy_callback,
        queue=spy_queue_name,
        no_ack=True)

    self.channel.basic_consume(trace_callback,
        queue=trace_queue_name,
        no_ack=True)

  def default_spy_callback(self, ch, method, properties, body):
    '''
    The default spy callback.  It will be called when an item is received by the
    'spy' exchange and another callback has not been registered with this object
    using the register_live_spy_callback method
    '''
    print(" [xs] {}:{}".format(method.routing_key, body))

  def default_trace_callback(self, ch, method, properties, body):
    '''
    The default trace callback.  It will be called when an item is received by the
    'trace' exchange and another callback has not been registered with this object
    using the register_live_trace_callback method
    '''
    print(" [xt] {}:{}".format(method.routing_key, body))

  def register_live_spy_callback(self, live_callback):
    '''
    This is used to register a callback method which will be called when we have
    received spy information from a node in the mesh network.

    Example:
      rx_instrumentation = SnoopReceiver(
        user='bob', password='dobbs', port=5672, encryption_key=b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0=')
      rx_instrumentation.start_consuming()

      def custom_spy_callback(ch, method, properties, body):
        print(" [+s] {}:{}".format(method.routing_key, body))

      # register spy instrumentation callback with your rx_instrumentation
      rx_instrumentation.register_live_spy_callback(custom_spy_callback)

    '''
    self.live_spy_callback = live_callback

  def register_live_trace_callback(self, live_callback):
    '''
    This is used to register a callback method which will be called when we have
    received trace information from a node in the mesh network.

    Example:
      rx_instrumentation = SnoopReceiver(
        user='bob', password='dobbs', port=5672, encryption_key=b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0=')
      rx_instrumentation.start_consuming()

      def custom_trace_callback(ch, method, properties, body):
        print(" [+s] {}:{}".format(method.routing_key, body))

      # register trace instrumentation callback with your rx_instrumentation
      rx_instrumentation.register_live_trace_callback(custom_trace_callback)

    '''
    self.live_trace_callback = live_callback

  @staticmethod
  def decrypt(encryption_key):
    '''
    Parameterized descryption decorator.

    Example:
      @SnoopReceiver.decrypt(self.encryption_key)
      def spy_callback(ch, method, properties, body):
        foreign_spy_item = body
        self.foreign_hsm.append_to_spy(foreign_spy_item)
        self.live_spy_callback(ch, method, properties, body)
    '''
    def _decrypt(fn):
      @wraps(fn)
      def __decrypt(ch, method, properties, cyphertext):
        '''SnoopReceiver.decrypt()'''
        key = encryption_key
        f = Fernet(key)
        plain_text = f.decrypt(cyphertext).decode()
        fn(ch, method, properties, plain_text)
      return __decrypt
    return _decrypt


class EmitConnections():
  '''
  Scouts a range of IP addresses, creates a 'mirror' (see
  NetworkTool.exchange_name) exchange which can dispatch messages to any RabbitMq
  server it has detected in the IP range.  It uses a direct routing strategy
  where the routing_key is the IP address of the node it wishes to communicate
  with.

  Once it has access to a number of network nodes, it provide a method to
  communicate with them, 'message_to_other_channels'.  Any object that is sent
  to this message is serialized into bytes then encrypted prior to being
  dispatched across the network.

  This class should be accessed through the MeshTransmitter object

  Example:
    tx = EmitConnections(user, password)

  '''
  def __init__(self, user, password, port=5672):
    possible_ips  = NetworkTool.ip_addresses_on_lan()
    targets       = EmitConnections.scout_targets(possible_ips, user, password)
    self.channels = EmitConnections.get_channels(targets, user, password, port)

  @NetworkTool.serialize  # pickle.dumps
  @NetworkTool.encrypt
  def message_to_other_channels(self, message, routing_key=None):
    '''
    Send messages to all of confirmed channels, messages are not persistent
    '''
    for channel in self.channels:
      channel.basic_publish(exchange=NetworkTool.exchange_name, routing_key=routing_key, body=message)

  @staticmethod
  def scout_targets(targets, user, password, port=5672):
    '''
    Returns a subset of ip address from the targets.  The common feature of
    these subsets is that they can you can connect to the via rabbitmq.  To do
    this:
    * They have have a NetworkTool.exchange_name exchange
    * They need to be able to respond to a message with a routing_key that is
      the same as their ip address
    * They can descrypt the message we are sending to them
    * They need to be our working IP address

    Example:
      # assumptions, user and password or correct
      #              possible_ips is a list of IP addresses to check
      targets = EmitConnections.scout_targets(possible_ips, user, password)

    '''
    # get all local ip address
    local_ip_addresses = NetworkTool.ip_addresses_on_this_machine()

    # remove all local ip addresses from the targets
    possible_targets = [item for item in targets if item not in local_ip_addresses]

    # add our working ip address
    possible_targets.append(NetworkTool.get_working_ip_address())

    # some random message so that our encryption isn't easily broken
    message = uuid.uuid4().hex.upper()[0:12]

    for target in possible_targets[:]:
      try:
        connection = NetworkTool.get_blocking_connection(user, password, target, port)
        channel = connection.channel()
        channel.exchange_declare(exchange=NetworkTool.exchange_name, exchange_type='topic')

        @NetworkTool.serialize
        @NetworkTool.encrypt
        def send(message):
          channel.basic_publish(exchange=NetworkTool.exchange_name, routing_key=target, body=message)

        send(message)
        print(" [x] Sent \"{}\" to {}".format(message, target))
        connection.close()
      except:
        possible_targets.remove(target)
    return possible_targets

  @staticmethod
  def get_channels(targets, user, password, port=5672):
    '''
    Get a set of rabbitmq channels given a list of ip addresses and the user
    name and password of the local rabbitmq server.
    '''
    channels = []
    for target in targets:
      try:
        connection = NetworkTool.get_blocking_connection(user, password, target, port)
        channel = connection.channel()
        channel.exchange_declare(exchange=NetworkTool.exchange_name, exchange_type='topic')
        channel.extension = SimpleNamespace()
        setattr(channel.extension, 'ip_address', target)
        channels.append(channel)
      except:
        pass
    return channels

class SnoopTransmitter():
  '''
  Transmit spy/trace information from this computer to all other computers using
  the mesh network.

  You could create an instance of the object with the RabbitMq credentials then
  register your statechart's spy and trace instrumentation with it.

  Example:
    tx_instrument = SnoopTransmitter(
      user='bob',
      password='dobbs',
      port=5672,
      encryption_key=
       b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0='
    )

    # Given that ao is a statechart object you would register it's live
    # spy/trace output with the tx_instrument broadcast_spy and broadcast_trace
    # methods respectively:
    ao.register_live_spy_callback(tx_instrument.broadcast_spy)
    ao.register_live_trace_callback(tx_instrument.broadcast_trace)

    # Or you can broadcast messages directly to the connected spy and trace exchanges
    tx_instrument.broadcast_spy("Spy information")
    tx_instrument.broadcast_spy("Trace information")
  '''
  def __init__(self, user, password, port=5672, encryption_key=None):
    possible_ips = NetworkTool.ip_addresses_on_lan()
    # use the target information from EmitConnections.scout_targets
    targets = EmitConnections.scout_targets(possible_ips, user, password)
    self.spy_channels = SnoopTransmitter.get_spy_channels(targets, user, password, port)
    self.trace_channels = SnoopTransmitter.get_trace_channels(targets, user, password, port)

    @SnoopTransmitter.encrypt(encryption_key)
    def broadcast_spy(spy_information):
      for channel in self.spy_channels:
        channel.basic_publish(
            exchange='spy',
            routing_key='',
            body=spy_information
        )

    @SnoopTransmitter.encrypt(encryption_key)
    def broadcast_trace(trace_information):
      for channel in self.trace_channels:
        channel.basic_publish(
            exchange='trace',
            routing_key='',
            body=trace_information
        )

    self.broadcast_spy   = broadcast_spy
    self.broadcast_trace = broadcast_trace

  @staticmethod
  def get_spy_channels(targets, user, password, port):
    '''
    Get all spy channels associated with different working IP addresses that
    have a 'spy' fanout exchange
    '''
    return SnoopTransmitter.get_channels(targets, user, password, port, 'spy')

  @staticmethod
  def get_trace_channels(targets, user, password, port):
    '''
    Get all trace channels associated with different working IP addresses that
    have a 'trace' fanout exchange
    '''
    return SnoopTransmitter.get_channels(targets, user, password, port, 'trace')

  @staticmethod
  def get_channels(targets, user, password, port, exchange_name):
    '''
    Get all channels associated with different working IP addresses that
    have an 'exchange_name' fanout exchange
    '''
    channels = []
    for target in targets:
      try:
        connection = NetworkTool.get_blocking_connection(user, password, target, port)
        channel    = connection.channel()
        channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        channel.extension = SimpleNamespace()
        setattr(channel.extension, 'ip_address', target)
        channels.append(channel)
      except:
        pass
    return channels

  @staticmethod
  def encrypt(encryption_key):
    '''
    Parameterized encryption decorator.

    Example:
      @SnoopTransmitter.encrypt(encryption_key)
      def broadcast_spy(spy_information):
        for channel in self.spy_channels:
          channel.basic_publish(
              exchange='spy',
              routing_key='',
              body=spy_information
          )
    '''
    def _encrypt(fn):
      @wraps(fn)
      def __encrypt(plain_text):
        f = Fernet(encryption_key)
        cyphertext = f.encrypt(plain_text.encode())
        fn(cyphertext)
      return __encrypt
    return _encrypt

class MeshReceiver():
  '''
  Creates a rabbitmq receiver.  You can register a live callback which will be
  called when a message is received, then start consuming.  You can stop
  consuming and start consuming at a later time.

  Example:
    import time

    def custom_rx_callback(ch, method, properties, body):
      print(" [+] {}:{}".format(method.routing_key, body))

    # Assuming IP: 192.168.0.103
    # The routing key will be '192.168.0.103.archer.mary'
    rx = MeshReceiver(user='bob',
           password='dobbs',
           routing_key='archer.mary')

    rx.register_live_callback(custom_rx_callback)
    rx.start_consuming() # launches a consuming task
    time.sleep(10)
    rx.stop_consuming()  # kills consuming task
    rx.start_consuming() # launches a consuming task with same custom_rx_callback

  '''
  def __init__(self, user, password, port=5672, routing_key=None):
    self.user     = user
    self.password = password
    self.port     = port

    # create a channel with a direct routing key, the key is our ip address
    if routing_key is None or routing_key == '':
      routing_key = NetworkTool.get_working_ip_address() + '.#'
    else:
      routing_key = NetworkTool.get_working_ip_address() + '.' + routing_key
    self.routing_key = routing_key
    self.rx = ReceiveConnections(user, password, port, routing_key)

  def start_consuming(self):
    self.rx.start_consuming()

  def register_live_callback(self, live_callback):
    '''
    Register a callback with this object.  It will be called once a message is
    received, decrypted and decoded.

    Example:

      def custom_rx_callback(ch, method, properties, body):
        print(" [+] {}:{}".format(method.routing_key, body))

      rx = MeshReceiver(user='bob', password='dobbs')
      rx.register_live_callback(custom_rx_callback)

    '''
    self.live_callback = live_callback
    self.rx.register_live_callback(live_callback)

  def stop_consuming(self):
    self.rx.stop_consuming()
    del(self.rx)
    self.rx = ReceiveConnections(self.user, self.password, self.port, self.routing_key)
    # re-register our live callback with the next instantiation
    if hasattr(self, 'live_callback') is True:
      if self.live_callback is not None:
        self.rx.register_live_callback(self.live_callback)


class MeshTransmitter(EmitConnections):
  def __init__(self, user, password, port=5672):
    super().__init__(user, password, port)

  @NetworkTool.serialize  # pickle.dumps
  @NetworkTool.encrypt
  def message_to_other_channels(self, message, routing_key=None):
    '''
    Send messages to all of confirmed channels, messages are not persistent

    Sets postpends the '<ip_address>.' to the front of the routing key provided
    by the user.

    Example:
      # Assume confirmed connected IPs are: [192.168.0.102, 192.168.0.103]
      # The actual routing keys for this transmission are:
      #   '192.168.0.102.archer.mary'
      #   '192.168.0.103.archer.mary'
      tx = MeshTransmitter(user="bob", password="dobbs")
      tx.message_to_other_channels(
        Event(signal=signals.Mirror, payload=[1, 2, 3]),
          routing_key = 'archer.mary')
    '''
    # create a channel with a direct routing key, the key is our ip address
    if routing_key is None:
      routing_key = '.'
    else:
      routing_key = '.' + routing_key

    for channel in self.channels:
      ip = channel.extension.ip_address
      channel.basic_publish(exchange=NetworkTool.exchange_name, routing_key=ip + routing_key, body=message)

if __name__ == "__main__":
  pp('line to appease PEP8/lint F401 noise')

  # Set the encryption key for this session
  NetworkTool.encryption_key = b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0='

  # Custom receive callbacks
  def custom_rx_callback(ch, method, properties, body):
    print(" [+] {}:{}".format(method.routing_key, body))

  def ergotic_rx_callback(ch, method, properties, body):
    print(" [+e] {}:{}".format(method.routing_key, body))
  # Get the user input
  tranceiver_type = sys.argv[1:]
  if not tranceiver_type:
    sys.stderr.write("Usage: {} [rx]/[tx]/[er]\n".format(sys.argv[0]))

  rx_instrumentation = SnoopReceiver(
    user='bob', password='dobbs', port=5672, encryption_key=b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0=')
  rx_instrumentation.start_consuming()

  def custom_spy_callback(ch, method, properties, body):
    print(" [+s] {}:{}".format(method.routing_key, body))

  def custom_trace_callback(ch, method, properties, body):
    print(" [+t] {}:{}".format(method.routing_key, body))

  # register spy instrumentation callback with your rx_instrumentation
  rx_instrumentation.register_live_spy_callback(custom_spy_callback)

  # register trace instrumentation callback with your rx_instrumentation
  rx_instrumentation.register_live_trace_callback(custom_trace_callback)

  tx_instrument = SnoopTransmitter(
   user='bob',
   password='dobbs',
   port=5672,
   encryption_key=
    b'lV5vGz-Hekb3K3396c9ZKRkc3eDIazheC4kow9DlKY0='
  )

  # The user wants to receive messages directed to this node in the mesh network
  if tranceiver_type[0] == 'rx':
    rx = MeshReceiver(user='bob', password='dobbs', port=5672, routing_key='#')
    rx.register_live_callback(custom_rx_callback)
    rx.start_consuming()
    time.sleep(500)
    rx.stop_consuming()
    rx.start_consuming()
    time.sleep(10)
    rx.stop_consuming()

  # The user want's to transmit to all nodes in mesh network
  elif tranceiver_type[0] == 'tx':
    tx = MeshTransmitter(user="bob", password="dobbs")
    tx.message_to_other_channels(Event(signal=signals.Mirror, payload=[1, 2, 3]), routing_key = 'archer.mary')
    tx.message_to_other_channels(Event(signal=signals.Mirror, payload=[1, 2, 3]))
    tx.message_to_other_channels([1, 2, 3, 4], routing_key = 'archer.jane')
    tx_instrument.broadcast_spy("Spy information")
    tx_instrument.broadcast_spy("Trace information")

  # The user wants to both transmit to all nodes in the mesh and receive all
  # messeges sent to this node
  elif tranceiver_type[0] == 'er':
    tx = MeshTransmitter(user="bob", password="dobbs", port=5672)
    rx = MeshReceiver(user='bob', password='dobbs', port=5672, routing_key='archer.#')

    # Set up the receiver
    rx.register_live_callback(ergotic_rx_callback)
    rx.start_consuming()

    # Now start transmitting to the mesh
    message = uuid.uuid4().hex.upper()[0:12]
    for i in range(0, 300):
      tx.message_to_other_channels(
        Event(signal = signals.Mirror, payload=(message + '_' + str(i))),
        routing_key = 'archer.jessica')
      tx_instrument.broadcast_spy("Spy information from {}".format(NetworkTool.get_working_ip_address()))
      tx_instrument.broadcast_trace("Trace information from {}".format(NetworkTool.get_working_ip_address()))
      time.sleep(0.5)
    rx.stop_consuming()

  # User typo
  else:
    sys.stderr.write("Usage: {} [rx]/[tx]/[er]\n".format(sys.argv[0]))

