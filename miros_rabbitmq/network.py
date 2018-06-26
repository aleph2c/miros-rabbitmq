#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import pika
import uuid
import time
import json
import queue
import pickle
import pprint
import socket
import random
import logging
import ipaddress
import netifaces  # pip3 install netifaces --user
import functools
import subprocess
from miros import pp
from pathlib import Path
from miros import Factory
from os import F_OK, W_OK
from threading import Thread
from miros.event import Event
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
from collections import namedtuple
from queue import Queue as ThreadQueue
from cryptography.fernet import Fernet
from miros.activeobject import Factory
from threading import Event as ThreadEvent
from miros.activeobject import ActiveObject
from miros import signals, Event, return_status
from datetime import datetime as stdlib_datetime
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR

env_path = Path('.') / '.env'
load_dotenv()

def to_snake(camel_case):
  '''Convert a CamelCase name into a camel_case, snake style name'''
  s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
  snake = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
  return snake

class EnvContractBroken(Exception):
  pass

class LoadEnvironmentalVariables():
  def __init__(self):
    if os.getenv('RABBIT_PASSWORD') is None:
      load_dotenv()  # climb out of this dir to find dir containing .env file

    # What this package needs from the .env file for this software to run.
    # if the file is missing any of this information, crash now
    if not os.getenv('RABBIT_PASSWORD'):
      raise EnvContractBroken('RABBIT_PASSWORD is missing from your .env file')

    if not os.getenv('RABBIT_USER'):
      raise EnvContractBroken('RABBIT_USER is missing from your .env file')

    if not os.getenv('RABBIT_PORT'):
      raise EnvContractBroken('RABBIT_PORT is missing from your .env file')

    if not os.getenv('RABBIT_HEARTBEAT_INTERVAL'):
      raise EnvContractBroken('RABBIT_HEARTBEAT_INTERVAL is missing from your .env file')

    if not os.getenv('CONNECTION_ATTEMPTS'):
      raise EnvContractBroken('CONNECTION_ATTEMPTS is missing from your .env file')

    if not os.getenv('MESH_ENCRYPTION_KEY'):
      raise EnvContractBroken('MESH_ENCRYPTION_KEY is missing from your .env file')

    if not os.getenv('SNOOP_TRACE_ENCRYPTION_KEY'):
      raise EnvContractBroken('SNOOP_TRACE_ENCRYPTION_KEY is missing from your .env file')

    if not os.getenv('SNOOP_SPY_ENCRYPTION_KEY'):
      raise EnvContractBroken('SNOOP_SPY_ENCRYPTION_KEY is missing from your .env file')

class RabbitHelper2():
  def __init__(self):
    '''Create a scout memory interface'''
    LoadEnvironmentalVariables()
    self.rabbit_user = os.getenv('RABBIT_USER')
    self.rabbit_password = os.getenv('RABBIT_PASSWORD')
    self.rabbit_port = os.getenv('RABBIT_PORT')
    self.rabbit_heartbeat_interval = os.getenv('RABBIT_HEARTBEAT_INTERVAL')
    self.connection_attempts = os.getenv('CONNECTION_ATTEMPTS')

  def make_amqp_url(self,
               ip_address,
               rabbit_user=None,
               rabbit_password=None,
               rabbit_port=None,
               connection_attempts=None,
               heartbeat_interval=None):
    '''Make a RabbitMq url.

      **Example**:

      .. code-block:: python

        amqp_url = \\
          self.make_amqp_url(
              ip_address=192.168.1.1,    # only mandatory argument
              rabbit_user='peter',       # if any of the following args not given
              rabbit_password='rabbit',  # the .env file will be used
              connection_attempts='3',
              heartbeat_interval='3600')

        print(amqp_url)  # =>
          'amqp://bob:dobbs@192.168.1.1:5672/%2F?connection_attempts=3&heartbeat_interval=3600'

    '''
    if rabbit_port is None:
      rabbit_port = self.rabbit_port
    if connection_attempts is None:
      connection_attempts = self.connection_attempts
    if heartbeat_interval is None:
      heartbeat_interval = self.rabbit_heartbeat_interval

    amqp_url = \
      "amqp://{}:{}@{}:{}/%2F?connection_attempts={}&heartbeat_interval={}".format(
          self.rabbit_user,
          self.rabbit_password,
          ip_address,
          rabbit_port,
          connection_attempts,
          heartbeat_interval)
    return amqp_url


class CacheFile(Factory):

  def __init__(self, name, file_path, system_read_signal_name=None):
    '''A collection of attributes and worker methods that will be used by the
       CacheFileChart'''
    super().__init__(name)
    self.file_path = file_path

    self.json = None
    self.created_at = None
    self.last_modified = None

    if system_read_signal_name is None:
      self.system_read_signal_name = signals.CACHE
    else:
      self.system_read_signal_name = system_read_signal_name

  def exists(self):
    return os.access(self.file_path, F_OK)

  def writeable(self):
    return os.access(self.file_path, W_OK)

  def write_access_off(self):
    os.chmod(self.file_path, S_IREAD | S_IRGRP | S_IROTH)

  def write_access_on(self):
    os.chmod(self.file_path, S_IWUSR | S_IREAD | S_IRGRP | S_IROTH)

  def temp_file_name(self):
    return "temp_file_{}".format(uuid.uuid4().hex.upper()[0:12])

  def expired(self):
    last_modified = datetime.fromtimestamp(self.last_modified)
    duration = datetime.now() - last_modified
    try:
      timeout = timedelta(minutes=self.dict['time_out_in_minutes'])
      is_expired = True if timeout == timedelta(0) else False
      if duration > timeout:
        is_expired = True
    except:
      is_expired = False
    return is_expired

CacheReadPayload = \
  namedtuple('CacheReadPayload',
    ['dict', 'last_modified', 'created_at', 'expired', 'file_name'])

CacheWritePayload = \
  namedtuple('CacheWritePayload', ['json', 'file_name'])


class CacheFileChart(CacheFile):
  '''Provides the ability for multiple programs to the same JSON file.
  To see the documentation and the map for this statechart: `link <https://aleph2c.github.io/miros-rabbitmq/how_it_works.html#cfc>`_
  '''
  def __init__(self, file_path=None, live_trace=None, live_spy=None, default_json=None):
    if file_path is None:
      file_path = str(Path('.') / '.miros_rabbitmq_cache.json')
    self.file_name = os.path.basename(file_path)
    super().__init__(self.file_name, file_path=file_path)
    self.default_json = default_json

    self.file_access_waiting = self.create(state='file_access_waiting'). \
        catch(signal=signals.ENTRY_SIGNAL, handler=self.faw_entry). \
        catch(signal=signals.CACHE_FILE_READ, handler=self.faw_CACHE_FILE_READ). \
        catch(signal=signals.CACHE_FILE_WRITE, handler=self.faw_CACHE_FILE_WRITE). \
        catch(signal=signals.faw_CACHE_DESTROY, handler=self.faw_CACHE_DESTROY). \
        catch(signal=signals.cache_file_read, handler=self.faw_cache_file_read). \
        catch(signal=signals.cache_file_write, handler=self.faw_cache_file_write). \
        to_method()

    self.file_accessed = self.create(state='file_accessed'). \
        catch(signal=signals.ENTRY_SIGNAL, handler=self.fa_entry). \
        catch(signal=signals.EXIT_SIGNAL, handler=self.fa_exit). \
        to_method()

    self.file_read = self.create(state='file_read'). \
        catch(signal=signals.ENTRY_SIGNAL, handler=self.fr_entry). \
        catch(signal=signals.read_successful, handler=self.fr_read_successful). \
        to_method()

    self.file_write = self.create(state='file_write'). \
        catch(signal=signals.ENTRY_SIGNAL, handler=self.fw_entry). \
        catch(signal=signals.write_successful, handler=self.fw_write_successful). \
        to_method()

    self.nest(self.file_access_waiting, parent=None). \
        nest(self.file_accessed, parent=self.file_access_waiting). \
        nest(self.file_read, parent=self.file_accessed). \
        nest(self.file_write, parent=self.file_accessed)

    if live_trace is None:
      live_trace = False
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy
    self.start_at(self.file_access_waiting)
    #self.post_fifo(Event(signal=signals.CACHE_FILE_READ))

  @staticmethod
  def timeout(times):
    top_timeout = 0.1 + (1.2**times)
    top_timeout = 5 if top_timeout > 5 else top_timeout
    _timeout = random.uniform(0.001, top_timeout)
    return _timeout

  @staticmethod
  def faw_entry(cache, e):
    '''The file_access_waiting state ENTRY_SIGNAL event handler'''
    cache.subscribe(Event(signal=signals.CACHE_FILE_READ))
    cache.subscribe(Event(signal=signals.CACHE_FILE_WRITE))

    # check if file exists, if not make it the default json provided by our
    # client
    if not os.path.isfile(cache.file_path):
      f = open(cache.file_path, 'w')
      f.write(cache.default_json)
      f.flush()
      os.fsync(f.fileno())
      f.close()
    return return_status.HANDLED

  @staticmethod
  def faw_CACHE_FILE_READ(cache, e):
    '''The file_access_waiting state global CACHE_FILE_READ event handler'''
    cache.post_fifo(Event(signal=signals.cache_file_read, payload={'times': 0}))
    return return_status.HANDLED

  @staticmethod
  def faw_CACHE_FILE_WRITE(cache, e):
    '''The file_access_waiting state global CACHE_FILE_WRITE event handler'''
    if e.payload.file_name == cache.file_name:
      cache.json = e.payload.json  # kept for debugging
      cache.dict = json.load(open(cache.file_path, 'r'))
      assert('time_out_in_minutes' in cache.dict)
      cache.post_fifo(Event(signal=signals.cache_file_write, payload={'times': 0, 'dict': cache.dict}))
    return return_status.HANDLED

  @staticmethod
  def faw_CACHE_DESTROY(cache, e):
    '''The file_access_waiting state global faw_CACHE_DESTROY event handler'''
    # write empty cache with a timeout of 0 to meet our contract, yet to cause a
    # timeout
    payload = \
      CacheWritePayload(
        json=json.dumps({'time_out_in_minutes': 0}),
        file_name=cache.file_name)
    cache.post_fifo(Event(signal=signals.cache_file_write), payload=payload)
    return return_status.HANDLED

  @staticmethod
  def faw_cache_file_read(cache, e):
    '''The file_access_waiting state private cache_file_read event handler'''
    if cache.writeable():
      status = cache.trans(cache.file_read)
    else:
      # wait a short amount of time then try again
      times = e.payload['times']
      timeout = random.uniform(0.001, cache.timeout(times))
      cache.post_fifo(Event(signal=signals.cache_file_read, payload={'times': times + 1}),
        period=timeout,
        times=1,
        deferred=True)
      status = return_status.HANDLED
    return status

  @staticmethod
  def faw_cache_file_write(cache, e):
    '''The file_access_waiting state private cache_file_write event handler'''
    status = return_status.HANDLED
    if cache.writeable():
      status = cache.trans(cache.file_write)
    else:
      times = e.payload['times']
      timeout = random.uniform(0.001, cache.timeout(times))
      # wait a short amount of time then try again sending the same payload
      cache.post_fifo(
        Event(signal=signals.cache_file_write, payload={'times': times + 1, 'dict': cache.dict}),
        period=timeout,
        times=1,
        deferred=True)
    return status

  @staticmethod
  def fa_entry(cache, e):
    '''The file_accessed state ENTRY_SIGNAL event handler'''
    cache.write_access_off()
    return return_status.HANDLED

  @staticmethod
  def fa_exit(cache, e):
    '''The file_accessed state EXIT_SIGNAL event handler'''
    cache.write_access_on()
    return return_status.HANDLED

  @staticmethod
  def fr_entry(cache, e):
    '''The file_read state ENTRY_SIGNAL event handler'''
    cache.dict = json.load(open(cache.file_path, 'r'))
    cache.json = json.dumps(cache.dict, sort_keys=True, indent=2)
    cache.last_modified = os.path.getmtime(cache.file_path)
    cache.created_at = time.ctime(os.path.getctime(cache.file_path))
    payload = CacheReadPayload(
      dict=cache.dict,
      last_modified=cache.last_modified,
      created_at=cache.created_at,
      expired=cache.expired(),
      file_name = cache.file_name
    )
    cache.publish(Event(signal=signals.CACHE, payload=payload))
    cache.post_lifo(Event(signal=signals.read_successful))
    # pp(cache.json)
    return return_status.HANDLED

  @staticmethod
  def fr_read_successful(cache, e):
    return cache.trans(cache.file_access_waiting)

  @staticmethod
  def fw_write_successful(cache, e):
    return cache.trans(cache.file_access_waiting)

  @staticmethod
  def fw_entry(cache, e):
    '''The file_write state ENTRY_SIGNAL event handler'''
    status = return_status.HANDLED
    temp_file = cache.temp_file_name()
    f = open(temp_file, "w")
    f.write(cache.json)
    # write the file to disk
    f.flush()
    os.fsync(f.fileno())
    f.close()
    # atomic replacement of cache.file_name with temp_file
    os.rename(temp_file, cache.file_path)
    cache.post_lifo(Event(signal=signals.write_successful))
    return status

class PikaTopicPublisherMaker():
  '''A class which removes as much of the tedium from building a pika producer as is possible.'''
  HEARTBEAT_INTERVAL_SEC = 3600
  CALLBACK_TEMPO = 0.1
  CONNECTION_ATTEMPTS = 3

  def __init__(self,
                ip_address,
                routing_key,
                exchange_name,
                connection_attempts=None,
                heartbeat_interval=None,
                callback_tempo=None):

    LoadEnvironmentalVariables()

    self.ip_address = ip_address
    self.routing_key = routing_key
    self.exchange_name = exchange_name

    self.rabbit_user = os.getenv('RABBIT_USER')
    self.rabbit_password = os.getenv('RABBIT_PASSWORD')
    self.rabbit_port = os.getenv('RABBIT_PORT')
    self.encryption_key = os.getenv('MESH_ENCRYPTION_KEY')

    # contract for this make class to work
    assert(self.rabbit_user)
    assert(self.rabbit_password)
    assert(self.rabbit_port)
    assert(self.encryption_key)

    if heartbeat_interval is None:
      self.heartbeat_interval = os.getenv('RABBIT_HEARTBEAT_INTERVAL')
      if not self.heartbeat_interval:
        self.heartbeat_interval = PikaTopicPublisherMaker.HEARTBEAT_INTERVAL_SEC
    else:
      self.heartbeat_interval = heartbeat_interval

    if callback_tempo is None:
      self.callback_tempo = PikaTopicPublisherMaker.CALLBACK_TEMPO
    else:
      self.callback_tempo = callback_tempo

    if connection_attempts is None:
      connection_attempts = PikaTopicPublisherMaker.CONNECTION_ATTEMPTS

    self.rabbit_helper = RabbitHelper2()
    self.amqp_url = self.rabbit_helper.make_amqp_url(
        ip_address=self.ip_address,
        rabbit_user=self.rabbit_user,
        rabbit_password=self.rabbit_password,
        rabbit_port=self.rabbit_port,
        connection_attempts=connection_attempts,
        heartbeat_interval=heartbeat_interval)

    self.producer = PikaTopicPublisher(
        amqp_url = self.amqp_url,
        routing_key = self.routing_key,
        publish_tempo_sec = self.callback_tempo,
        exchange_name = self.exchange_name,
        encryption_key = self.encryption_key)

AMQPConsumerCheckPayload = \
  namedtuple('AMQPConsumerCheckPayload',
    ['ip_address', 'result', 'routing_key', 'exchange_name'])

class RabbitConsumerScout(Factory):
  CONNECTION_ATTEMPTS    = 1

  SCOUT_TEMPO_SEC        = 0.01
  SCOUT_TIMEOUT_SEC      = 0.5

  def __init__(self, ip_address, routing_key, exchange_name):
    super().__init__(ip_address)

    self.ip_address = ip_address
    self.routing_key = routing_key
    self.exchange_name = exchange_name

  def get_amqp_consumer_check_payload(self, result):
    return AMQPConsumerCheckPayload(
      ip_address=self.ip_address,
      result=result,
      routing_key=self.routing_key,
      exchange_name=self.exchange_name)

class RabbitConsumerScoutChart(RabbitConsumerScout):
  '''The RabbitConsumerScoutChart searches an IP address to see if there is a compatible RabbitMQ consumer running on it.

  To see the map and design information for this chart: `link <https://aleph2c.github.io/miros-rabbitmq/how_it_works.html#the-rabbit-consumer-scout-chart>`_
  '''

  def __init__(self, ip_address, routing_key, exchange_name, live_trace=None, live_spy=None):
    super().__init__(ip_address, routing_key, exchange_name)

    self.search = self.create(state='search'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.search_entry). \
      catch(signal=signals.AMQP_CONSUMER_CHECK, handler=self.search_AMPQ_CONSUMER_CHECK).  \
      catch(signal=signals.INIT_SIGNAL, handler=self.search_init). \
      to_method()

    self.producer_thread_engaged = self.create(state='producer_thread_engaged'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.producer_thread_engaged_entry). \
      catch(signal=signals.EXIT_SIGNAL, handler=self.producer_thread_engaged_exit). \
      catch(signal=signals.try_to_connect_to_consumer, handler=self.producer_try_to_contact_consumer). \
      catch(signal=signals.consumer_test_complete, handler=self.producer_thread_engaged_consumer_test_complete). \
      to_method()

    self.producer_post_and_wait = self.create(state='producer_post_and_wait'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.producer_post_and_wait_entry). \
      to_method()

    self.amqp_consumer_server_found = self.create(state="amqp_consumer_server_found"). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.amqp_consumer_server_found_entry).  \
      to_method()

    self.no_amqp_consumer_server_found = self.create(state="no_amqp_consumer_server_found"). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.no_amqp_consumer_server_found_entry). \
      to_method()

    self.nest(self.search, parent=None). \
      nest(self.producer_thread_engaged, parent=self.search). \
      nest(self.producer_post_and_wait, parent=self.producer_thread_engaged). \
      nest(self.amqp_consumer_server_found, parent=self.search). \
      nest(self.no_amqp_consumer_server_found, parent=self.search)

    if live_trace is None:
      live_trace = False
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy
    self.start_at(self.search)

  @staticmethod
  def search_entry(scout, e):
    status = return_status.HANDLED
    scout.producer = PikaTopicPublisherMaker(
        ip_address=scout.ip_address,
        routing_key=scout.routing_key,
        exchange_name=scout.exchange_name,
        connection_attempts=RabbitConsumerScout.CONNECTION_ATTEMPTS,
        callback_tempo=RabbitConsumerScout.SCOUT_TEMPO_SEC).producer
    scout.subscribe(Event(signal=signals.AMQP_CONSUMER_CHECK))
    return status

  @staticmethod
  def search_AMPQ_CONSUMER_CHECK(scout, e):
    status = return_status.HANDLED
    if scout.live_trace or scout.live_spy:
     # pp(e.payload)
     pass
    return status

  @staticmethod
  def search_init(scout, e):
    return scout.trans(scout.producer_thread_engaged)

  @staticmethod
  def producer_thread_engaged_entry(scout, e):
    status = return_status.HANDLED
    scout.producer.start_thread()
    scout.post_fifo(Event(
      signal=signals.try_to_connect_to_consumer),
      times=1,
      period=0.1,
      deferred=True)
    return status

  @staticmethod
  def producer_try_to_contact_consumer(scout, e):
    status = scout.trans(scout.producer_post_and_wait)
    return status

  @staticmethod
  def producer_thread_engaged_exit(scout, e):
    status = return_status.HANDLED
    scout.cancel_events(
      Event(signal=signals.try_to_connect_to_consumer))
    scout.producer.stop_thread()
    return status

  @staticmethod
  def producer_thread_engaged_consumer_test_complete(scout, e):
    status = return_status.HANDLED
    if scout.producer.connect_error:
      status = scout.trans(scout.no_amqp_consumer_server_found)
    else:
      status = scout.trans(scout.amqp_consumer_server_found)
    return status

  @staticmethod
  def producer_post_and_wait_entry(scout, e):
    status = return_status.HANDLED
    # send a unexpected message to make it harder to decrypt
    scout.producer.post_fifo(uuid.uuid4().hex.upper()[0:12])
    scout.post_fifo(
      Event(signal=signals.consumer_test_complete),
      times=1,
      period=RabbitConsumerScout.SCOUT_TIMEOUT_SEC,
      deferred=True
    )
    return status

  @staticmethod
  def amqp_consumer_server_found_entry(scout, e):
    status = return_status.HANDLED
    payload = scout.get_amqp_consumer_check_payload(True)
    scout.publish(Event(signal=signals.AMQP_CONSUMER_CHECK, payload=payload))
    return status

  @staticmethod
  def no_amqp_consumer_server_found_entry(scout, e):
    status = return_status.HANDLED
    payload = scout.get_amqp_consumer_check_payload(False)
    scout.publish(Event(signal=signals.AMQP_CONSUMER_CHECK, payload=payload))
    return status

class Attribute():
  def __init__(self):
    pass

RecceNode = namedtuple('RecceNode', ['searched', 'result', 'scout'])

class LanRecce(Factory):
  def __init__(self, routing_key, exchange_name, name=None,):
    if name is None:
      name = 'lan_recce_chart'
    super().__init__(name)
    self.my  = Attribute()
    self.other = Attribute()
    self.routing_key = routing_key
    self.exchange_name = exchange_name
    self.candidates = None

  def get_ipv4_network(self):
    ip_address = LanRecce.get_working_ip_address()
    netmask    = self.netmask_on_this_machine()
    inet4      = ipaddress.ip_network(ip_address + '/' + netmask, strict=False)
    return inet4

  def netmask_on_this_machine(self):
    interfaces = [interface for interface in netifaces.interfaces()]
    local_netmask = None
    working_address = LanRecce.get_working_ip_address()
    for interface in interfaces:
      interface_network_types = netifaces.ifaddresses(interface)
      if netifaces.AF_INET in interface_network_types:
        if interface_network_types[netifaces.AF_INET][0]['addr'] == working_address:
          local_netmask = interface_network_types[netifaces.AF_INET][0]['netmask']
          break
    return local_netmask

  def ping_to_fill_arp_table(self):
    linux_cmd = 'ping -b {}'
    inet4 = self.get_ipv4_network()

    if inet4.num_addresses <= 256:
      broadcast_address = inet4[-1]
      fcmd = linux_cmd.format(broadcast_address)
      fcmd_as_list = fcmd.split(" ")
      try:
        ps = subprocess.Popen(fcmd_as_list, stdout=open(os.devnull, "wb"))
        ps.wait(2)
      except:
        ps.kill()
    return

  def candidate_ip_addresses(self):
    lan_ip_addresses = []
    a = set(self.ip_addresses_on_lan())
    b = set(self.ip_addresses_on_this_machine())
    c = set([LanRecce.get_working_ip_address()])
    candidates = list(a - b ^ c)
    inet4 = self.get_ipv4_network()
    for host in inet4.hosts():
      shost = str(host)
      if shost in candidates:
        lan_ip_addresses.append(shost)
    return lan_ip_addresses

  def ip_addresses_on_lan(self):
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
        output = subprocess.check_output(grep_as_list, stdin=ps.stdout, timeout=0.5)
        ps.wait()
        if output is not '':
          candidates = output.decode('utf-8').split('\n')
          if len(candidates) > 0:
            break
      except:
        # our windows command did not work on Linux
        pass
    return list(filter(None, candidates))

  def ip_addresses_on_this_machine(self):
    interfaces = [interface for interface in netifaces.interfaces()]
    local_ip_addresses = []
    for interface in interfaces:
      interface_network_types = netifaces.ifaddresses(interface)
      if netifaces.AF_INET in interface_network_types:
        ip_address = interface_network_types[netifaces.AF_INET][0]['addr']
        local_ip_addresses.append(ip_address)
    return local_ip_addresses

  @staticmethod
  def get_working_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      s.connect(('10.255.255.255', 1))
      ip = s.getsockname()[0]
    except:
      ip = '127.0.0.1'
    finally:
      s.close()
    return ip

RecceCompletePayload = \
  namedtuple('RecceCompletePayload', ['other_addresses', 'my_address'])

class LanRecceChart(LanRecce):
  '''The LanRecceChart performs multiple scouting missions of your local area network for compatible RabbitMQ consumers.

  To see it's design and diagram click `here <https://aleph2c.github.io/miros-rabbitmq/how_it_works.html#how-it-works2-the-lanreccechart>`_'''

  ARP_TIME_OUT_SEC = 2.0

  def __init__(self, routing_key, exchange_name, live_trace=None, live_spy=None, arp_timeout_sec=None):

    super().__init__(routing_key, exchange_name, name='lan_recce_chart')

    if arp_timeout_sec is None:
      self.arp_timeout_sec = LanRecceChart.ARP_TIME_OUT_SEC

    self.private_search = self.create(state="private_search"). \
      catch(signals.ENTRY_SIGNAL, handler=self.private_search_entry). \
      catch(signals.RECCE_LAN, handler=self.private_search_RECCE_LAN). \
      catch(signals.recce_lan, handler=self.private_recce_lan). \
      catch(signal=signals.LAN_RECCE_COMPLETE, handler=self.private_search_RECCE_COMPLETE). \
      to_method()

    self.lan_recce = self.create(state='recce'). \
      catch(signals.RECCE_LAN, handler=self.lan_recce_RECCE_LAN). \
      catch(signals.INIT_SIGNAL, handler=self.lan_recce_init). \
      catch(signals.EXIT_SIGNAL, handler=self.lan_recce_exit). \
      catch(signal=signals.ip_addresses_found, handler=self.lan_recce_ip_addresses_found). \
      to_method()

    self.fill_arp_table = self.create(state='fill_arp_table'). \
      catch(signals.ENTRY_SIGNAL, handler=self.fill_arp_table_entry). \
      catch(signals.EXIT_SIGNAL, handler=self.fill_arp_table_exit). \
      catch(signal=signals.arp_time_out, handler=self.fill_arp_table_ARP_TIME_OUT). \
      to_method()

    self.identify_all_ip_addresses = self.create(state='identify_all_ip_addresses'). \
      catch(signals.ENTRY_SIGNAL, handler=self.identify_all_ip_addresses_entry). \
      to_method()

    self.recce_rabbit_consumers = self.create(state='recce_rabbit_consumers'). \
      catch(signals.ENTRY_SIGNAL, handler=self.recce_rabbit_consumers_entry). \
      catch(signals.AMQP_CONSUMER_CHECK, handler=self.recce_rabbit_consumers_AMQP_CONSUMER_CHECK). \
      catch(signals.lan_recce_complete, handler=self.recce_rabbit_consumers_lan_recce_complete). \
      to_method()

    self.nest(self.private_search, parent=None). \
      nest(self.lan_recce, parent=self.private_search). \
      nest(self.fill_arp_table, parent=self.lan_recce). \
      nest(self.identify_all_ip_addresses, parent=self.lan_recce). \
      nest(self.recce_rabbit_consumers, parent=self.lan_recce)

    if live_trace is None:
      live_trace = False
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy
    self.start_at(self.private_search)

  @staticmethod
  def private_search_entry(lan, e):
    status = return_status.HANDLED
    lan.subscribe(Event(signals.RECCE_LAN))
    lan.subscribe(Event(signals.AMQP_CONSUMER_CHECK))
    lan.subscribe(Event(signal=signals.LAN_RECCE_COMPLETE))
    lan.my.address = LanRecce.get_working_ip_address()
    return status

  @staticmethod
  def private_search_RECCE_LAN(lan, e):
    status = return_status.HANDLED
    lan.post_fifo(Event(signal=signals.recce_lan))
    return status

  @staticmethod
  def private_recce_lan(lan, e):
    status = lan.trans(lan.lan_recce)
    return status

  @staticmethod
  def private_search_RECCE_COMPLETE(lan, e):
    status = return_status.HANDLED
    pp(e.payload)
    return status

  @staticmethod
  def lan_recce_RECCE_LAN(lan, e):
    status = return_status.HANDLED
    lan.defer(e)
    return status

  @staticmethod
  def lan_recce_init(lan, e):
    status = lan.trans(lan.fill_arp_table)
    return status

  @staticmethod
  def lan_recce_exit(lan, e):
    status = return_status.HANDLED
    lan.recall()
    return status

  @staticmethod
  def lan_recce_ip_addresses_found(lan, e):
    status = lan.trans(lan.recce_rabbit_consumers)
    return status

  @staticmethod
  def fill_arp_table_entry(lan, e):
    status = return_status.HANDLED
    lan.ping_to_fill_arp_table()
    lan.post_fifo(
      Event(signal=signals.arp_time_out),
      times=1,
      period=lan.arp_timeout_sec,
      deferred=True)
    return status

  @staticmethod
  def fill_arp_table_exit(lan, e):
    status = return_status.HANDLED
    lan.cancel_events(Event(signal=signals.arp_time_out))
    return status

  @staticmethod
  def fill_arp_table_ARP_TIME_OUT(lan, e):
    status = lan.trans(lan.identify_all_ip_addresses)
    return status

  @staticmethod
  def identify_all_ip_addresses_entry(lan, e):
    status = return_status.HANDLED
    lan.my.addresses = lan.candidate_ip_addresses()
    lan.other.addresses = list(set(lan.my.addresses) - set(lan.my.address))
    lan.post_fifo(Event(signal=signals.ip_addresses_found))
    return status

  @staticmethod
  def recce_rabbit_consumers_entry(lan, e):
    status = return_status.HANDLED
    lan.candidates = {}
    for ip_address in lan.my.addresses:
      scout = \
        RabbitConsumerScoutChart(ip_address, lan.routing_key, lan.exchange_name)
      lan.candidates[ip_address] = RecceNode(
        searched=False,
        result=False,
        scout=scout
      )
    return status

  @staticmethod
  def recce_rabbit_consumers_lan_recce_complete(lan, e):
    return lan.trans(lan.private_search)

  @staticmethod
  def recce_rabbit_consumers_AMQP_CONSUMER_CHECK(lan, e):
    status = return_status.HANDLED
    ip, result = e.payload.ip_address, e.payload.result
    is_one_of_my_ip_addresses = ip in lan.my.addresses
    is_my_routing_key = e.payload.routing_key is lan.routing_key
    is_my_exchange_name = e.payload.exchange_name is lan.exchange_name

    if is_one_of_my_ip_addresses and is_my_routing_key and is_my_exchange_name:
      lan.candidates[ip] = RecceNode(searched=True, result=result, scout=None)

    search_complete = all([node.searched for node in lan.candidates.values()])

    if search_complete:
      working_ip_addresses = []
      for ip_address, lan_recce_node in lan.candidates.items():
        if lan_recce_node.result:
          working_ip_addresses.append(ip_address)
      payload = RecceCompletePayload(
                  other_addresses=working_ip_addresses,
                  my_address=lan.my.address)
      lan.publish(Event(signal=signals.LAN_RECCE_COMPLETE, payload=payload))
      lan.post_fifo(Event(signal=signals.lan_recce_complete))
    return status

ConnectionDiscoveryPayload = \
  namedtuple('ConnectionDiscoveryPayload', ['hosts', 'amqp_urls', 'dispatcher'])

class MirosRabbitLan(Factory):
  time_out_in_minutes = 30

  def __init__(self, name, routing_key, exchange_name, time_out_in_minutes=None, cache_file_path=None):
    super().__init__(name)
    self.routing_key = routing_key
    self.exchange_name = exchange_name

    self.dict = {}
    self.addresses = None
    self.amqp_urls = None
    self.rabbit_helper = RabbitHelper2()

  def change_time_out_in_minutes(self, time_out_in_minutes):
    self.time_out_in_minutes = time_out_in_minutes

  def make_amqp_url(self, ip_address):
    return self.rabbit_helper.make_amqp_url(ip_address)

class LanChart(MirosRabbitLan):
  '''The LanChart is responsible for finding other RabbitMQ servers on your
  Local Area Network

  To see it's documentation and a map of this statechart, click `here
  <https://aleph2c.github.io/miros-rabbitmq/how_it_works.html#lanchart>`_'''

  DEFAULT_JSON = '''
{
  "addresses": [
  ],
  "amqp_urls": [
  ],
  "time_out_in_minutes": 0
}
'''

  def __init__(self,
        routing_key, exchange_name, time_out_in_minutes=None,
        cache_file_path=None, live_trace=None, live_spy=None):

    if time_out_in_minutes is None:
      self.time_out_in_minutes = MirosRabbitLan.time_out_in_minutes
    else:
      self.time_out_in_minutes = time_out_in_minutes

    if cache_file_path:
      self.cache_file_path = cache_file_path
    else:
      self.cache_file_path = None

    super().__init__(to_snake(str(self.__class__.__name__)),
        routing_key,
        exchange_name,
        self.change_time_out_in_minutes,
        self.cache_file_path)

    self.read_or_discover_network_details = self.create(state='read_or_discover_network_details'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.rodnd_entry). \
      catch(signal=signals.connections_discovered, handler=self.rodnd_connection_discovered). \
      catch(signal=signals.CACHE, handler=self.rodnd_CACHE). \
      to_method()

    self.discover_network = self.create(state='discover_network'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.dn_entry). \
      catch(signal=signals.LAN_RECCE_COMPLETE, handler=self.dn_LAN_RECCE_COMPLETE). \
      to_method()

    self.nest(self.read_or_discover_network_details, parent=None). \
        nest(self.discover_network, parent=self.read_or_discover_network_details)

    if live_trace is None:
      live_trace = False
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy
    self.start_at(self.read_or_discover_network_details)

  @staticmethod
  def rodnd_entry(chart, e):
    status = return_status.HANDLED
    if not hasattr(chart, 'cache_file_chart'):
      if chart.cache_file_path is None:
        chart.file_path = '.miros_rabbitmq_lan_cache.json'
      chart.file_name = os.path.basename(chart.file_path)
      chart.cache_file_chart = \
        CacheFileChart(
          file_path=chart.file_path,
          live_trace=chart.live_trace,
          live_spy=chart.live_spy,
          default_json=LanChart.DEFAULT_JSON
        )
    if not hasattr(chart, 'rabbitmq_lan_recce_chart'):
      chart.rabbit_lan_reccee_chart = LanRecceChart(
        chart.routing_key,
        chart.exchange_name,
        live_trace=chart.live_trace,
        live_spy=chart.live_spy)
    chart.subscribe(Event(signal=signals.LAN_RECCE_COMPLETE))
    chart.subscribe(Event(signal=signals.CACHE))
    chart.publish(Event(signal=signals.CACHE_FILE_READ))
    return status

  @staticmethod
  def rodnd_connection_discovered(chart, e):
    status = return_status.HANDLED
    payload = ConnectionDiscoveryPayload(
      hosts=chart.addresses,
      amqp_urls=chart.amqp_urls,
      dispatcher=chart.name)
    chart.publish(Event(signal=signals.CONNECTION_DISCOVERY, payload=payload))
    return status

  @staticmethod
  def rodnd_CACHE(chart, e):
    status = return_status.HANDLED
    if e.payload.file_name == chart.file_name:
      if e.payload.expired:
        status = chart.trans(chart.discover_network)
      else:
        chart.addresses = e.payload.dict['addresses']
        chart.amqp_urls = e.payload.dict['amqp_urls']
        chart.post_fifo(Event(signal=signals.connections_discovered))
    return status

  @staticmethod
  def dn_entry(chart, e):
    status = return_status.HANDLED
    chart.publish(Event(signal=signals.RECCE_LAN))
    return status

  @staticmethod
  def dn_LAN_RECCE_COMPLETE(chart, e):
    status = return_status.HANDLED
    chart.addresses = e.payload.other_addresses
    chart.amqp_urls = [chart.make_amqp_url(a) for a in chart.addresses]
    chart.post_fifo(Event(signal=signals.connections_discovered))
    chart.dict['addresses'] = chart.addresses
    chart.dict['amqp_urls'] = chart.amqp_urls
    chart.dict['time_out_in_minutes'] = chart.time_out_in_minutes
    payload = \
      CacheWritePayload(
        json=json.dumps(chart.dict, indent=2, sort_keys=True),
        file_name=chart.file_name)
    chart.publish(Event(signal=signals.CACHE_FILE_WRITE, payload=payload))
    return status

class MirosRabbitManualNetwork(Factory):
  def __init__(self, name, routing_key, exchange_name, file_path=None):
    super().__init__(name)
    self.routing_key = routing_key
    self.exchange_name = exchange_name
    self.dict = {}

    self.rabbit_helper = RabbitHelper2()
    self.hosts = None
    self.live_hosts = None
    self.live_amqp_urls = None
    self.dead_hosts = None
    self.dead_amqp_urls = None
    self.manual_file_path = None

  def make_amqp_url(self, ip_address):
    return self.rabbit_helper.make_amqp_url(ip_address)


class ManNetChart(MirosRabbitManualNetwork):
  '''The ManNetChart lets a user specify the addresses they want to use in their network.
  To see it's documentation and diagrams click `here <https://aleph2c.github.io/miros-rabbitmq/how_it_works.html#manual-network-chart>`_.
  '''

  DEFAULT_JSON = '''{
  "hosts": [
  ]
}
'''

  def __init__(self, routing_key, exchange_name, cache_file_path=None, live_trace=None, live_spy=None):
    if cache_file_path:
      self.cache_file_path = cache_file_path
    else:
      self.cache_file_path = None

    super().__init__(to_snake(str(self.__class__.__name__)),
        routing_key,
        exchange_name,
        self.cache_file_path)

    self.read_and_evaluate_network_details = \
      self.create(state='read_and_evaluate_network_details') .\
        catch(signal=signals.ENTRY_SIGNAL, handler=self.raend_entry). \
        catch(signal=signals.network_evaluated, handler=self.raend_network_evaluated). \
        catch(signal=signals.CONNECTION_DISCOVERY, handler=self.raend_CONNECTION_DISCOVERY). \
        catch(signal=signals.CACHE, handler=self.raend_CACHE). \
        to_method()

    self.evaluated_network = \
      self.create(state='evaluated_network'). \
        catch(signal=signals.ENTRY_SIGNAL, handler=self.en_entry). \
        catch(signal=signals.AMQP_CONSUMER_CHECK, handler=self.en_AMQP_CONSUMER_CHECK). \
        catch(signal=signals.CACHE, handler=self.en_CACHE). \
        to_method()

    self. \
      nest(self.read_and_evaluate_network_details, parent=None). \
      nest(self.evaluated_network, parent=self.read_and_evaluate_network_details)

    if live_trace is None:
      live_trace = False
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy

    self.start_at(self.read_and_evaluate_network_details)

  # raend
  @staticmethod
  def raend_entry(chart, e):
    status = return_status.HANDLED
    if not hasattr(chart, 'manual_file_chart'):
      chart.file_path = '.miros_rabbitmq_hosts.json'
      chart.file_name = os.path.basename(chart.file_path)
      chart.manual_file_chart = \
        CacheFileChart(
          file_path=chart.file_path,
          live_trace=chart.live_trace,
          live_spy=chart.live_spy,
          default_json=ManNetChart.DEFAULT_JSON
        )
    chart.subscribe(Event(signal=signals.CACHE))
    chart.subscribe(Event(signal=signals.AMQP_CONSUMER_CHECK))
    # chart.subscribe(Event(signal=signals.CONNECTION_DISCOVERY))
    chart.publish(Event(signal=signals.CACHE_FILE_READ))
    return status

  @staticmethod
  def raend_network_evaluated(chart, e):
    status = return_status.HANDLED
    payload = ConnectionDiscoveryPayload(
      hosts=chart.live_hosts,
      amqp_urls=chart.live_amqp_urls,
      dispatcher=chart.name)
    chart.publish(Event(signal=signals.CONNECTION_DISCOVERY, payload=payload))
    return status

  @staticmethod
  def raend_CONNECTION_DISCOVERY(chart, e):
    status = return_status.HANDLED
    #pp(e.payload)
    return status

  @staticmethod
  def raend_CACHE(chart, e):
    status = return_status.HANDLED
    if e.payload.file_name == chart.file_name:
      chart.hosts = e.payload.dict['hosts']
      chart.live_hosts, chart.live_amqp_urls = [], []
      status = chart.trans(chart.evaluated_network)
    return status

  @staticmethod
  def en_entry(chart, e):
    status = return_status.HANDLED
    chart.candidates = {}
    for host in chart.hosts:
      # This will cause AMQP_CONSUMER_CHECK events to be published
      chart.candidates[host] = \
        RecceNode(
            searched=False,
            result=False,
            scout=RabbitConsumerScoutChart(
              host,
              chart.routing_key,
              chart.exchange_name))
    return status

  @staticmethod
  def en_CACHE(chart, e):
    status = return_status.HANDLED
    return status

  @staticmethod
  def en_AMQP_CONSUMER_CHECK(chart, e):
    status = return_status.HANDLED
    h, result = e.payload.ip_address, e.payload.result
    is_one_of_my_hosts = h in chart.hosts
    is_my_routing_key = e.payload.routing_key in chart.routing_key
    is_my_exchange_name = e.payload.exchange_name in chart.exchange_name
    if is_one_of_my_hosts and is_my_routing_key and is_my_exchange_name:
      chart.candidates[h] = RecceNode(searched=True, result=result, scout=None)
      if result:
        chart.live_hosts.append(h)
        chart.live_amqp_urls.append(chart.make_amqp_url(h))
      else:
        chart.dead_hosts.append(h)
        chart.dead_amqp_urls.append(chart.make_amqp_url(h))
    search_completed = all([node.searched for node in chart.candidates.values()])
    if search_completed:
      chart.post_fifo(Event(signal=signals.network_evaluated))
    return status

class ProducerFactory():
  PublishTempoSec = 0.1

  def __init__(self,
                ip_address,
                routing_key,
                exchange_name,
                serialization_function=None,
                publish_tempo_sec=None):

    self.rabbit_helper = RabbitHelper2()
    LoadEnvironmentalVariables()
    self.exchange_name = exchange_name
    self.routing_key   = routing_key
    if publish_tempo_sec is None:
      self.publish_tempo_sec = ProducerFactory.PublishTempoSec
    if serialization_function:
      self.serialization_function = serialization_function
    else:
      self.serialization_function = None
    self.amqp_url = self.rabbit_helper.make_amqp_url(ip_address)

  def make_producer(self):
    if not self.serialization_function:
      producer = PikaTopicPublisher(
          amqp_url=self.amqp_url,
          routing_key=self.routing_key,
          publish_tempo_sec=self.publish_tempo_sec,
          exchange_name=self.exchange_name,
          encryption_key=self.encryption_key)
    else:
      producer = PikaTopicPublisher(
          amqp_url=self.amqp_url,
          routing_key=self.routing_key,
          publish_tempo_sec=self.publish_tempo_sec,
          exchange_name=self.exchange_name,
          serialization_function=self.serialization_function,
          encryption_key=self.encryption_key)
    producer.start_thread()
    return producer

class MeshProducerFactory(ProducerFactory):
  def __init__(self,
                ip_address,
                routing_key,
                exchange_name,
                serialization_function):
    super().__init__(ip_address,
                      routing_key,
                      exchange_name,
                      serialization_function)
    self.encryption_key = os.getenv('MESH_ENCRYPTION_KEY')

class SnoopTraceProducerFactory(ProducerFactory):
  def __init__(self,
                ip_address,
                routing_key,
                exchange_name):
    super().__init__(ip_address,
                      routing_key,
                      exchange_name)
    self.encryption_key = os.getenv('SNOOP_TRACE_ENCRYPTION_KEY')

class SnoopSpyProducerFactory(ProducerFactory):
  def __init__(self,
                ip_address,
                routing_key,
                exchange_name):
    super().__init__(ip_address,
                      routing_key,
                      exchange_name)
    self.encryption_key = os.getenv('SNOOP_SPY_ENCRYPTION_KEY')

ProducerQueue = \
  namedtuple('ProducerQueue',
    ['mesh_producers', 'snoop_trace_producers', 'snoop_spy_producers', 'ip_addresses'])

class ProducerFactoryAggregator(Factory):
  def __init__(self,
               name,
               producers_queue,
               mesh_routing_key,
               mesh_exchange_name,
               mesh_serialization_function,
               snoop_trace_routing_key,
               snoop_trace_exchange_name,
               snoop_spy_routing_key,
               snoop_spy_exchange_name):

    super().__init__(name)

    self.producers_queue = producers_queue
    self.mesh_routing_key = mesh_routing_key
    self.mesh_exchange_name = mesh_exchange_name
    self.mesh_serialization_function = mesh_serialization_function
    self.mesh_producers = []

    self.snoop_trace_routing_key = snoop_trace_routing_key
    self.snoop_trace_exchange_name = snoop_trace_exchange_name
    self.snoop_trace_producers = []

    self.snoop_spy_routing_key = snoop_spy_routing_key
    self.snoop_spy_exchange_name = snoop_spy_exchange_name
    self.snoop_spy_producers = []

    self.set_of_ips = set([])
    self.set_of_new_ips = set([])

  def get_ip_for_hostname(self, host):
    return socket.gethostbyname(host)

  def make_mesh_producer(self, ip):
    mesh_producer = \
      MeshProducerFactory(ip,
        routing_key=self.mesh_routing_key,
        exchange_name=self.mesh_exchange_name,
        serialization_function=self.mesh_serialization_function).make_producer()
    return mesh_producer

  def make_snoop_trace_producer(self, ip):
    snoop_trace_producer = \
      SnoopTraceProducerFactory(ip,
        routing_key=self.snoop_trace_routing_key,
        exchange_name=self.snoop_trace_exchange_name).make_producer()
    return snoop_trace_producer

  def make_snoop_spy_producer(self, ip):
    snoop_spy_producer = \
      SnoopSpyProducerFactory(ip,
        routing_key=self.snoop_spy_routing_key,
        exchange_name=self.snoop_spy_exchange_name).make_producer()
    return snoop_spy_producer


class ProducerFactoryChart(ProducerFactoryAggregator):
  '''The ProducerFactoryChart is used to build RabbitMQ producers as they are discovered by the miros-rabbitmq library.

  To read the documentation and see diagrams for this statechart click `here <https://aleph2c.github.io/miros-rabbitmq/how_it_works.html#the-producer-factory-chart>`_.'''
  def __init__(self,
               producers_queue,
               mesh_routing_key,
               mesh_exchange_name,
               mesh_serialization_function,
               snoop_trace_routing_key,
               snoop_trace_exchange_name,
               snoop_spy_routing_key,
               snoop_spy_exchange_name,
               live_trace=None,
               live_spy=None):

    chart_name = to_snake(str(self.__class__.__name__))
    super().__init__(
      chart_name,
      producers_queue,
      mesh_routing_key,
      mesh_exchange_name,
      mesh_serialization_function,
      snoop_trace_routing_key,
      snoop_trace_exchange_name,
      snoop_spy_routing_key,
      snoop_spy_exchange_name)

    self.producer_discovery = self.create(state='producer_discovery'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.pd_entry). \
      catch(signal=signals.ips_discovered, handler=self.pd_ips_discovered). \
      catch(signal=signals.CONNECTION_DISCOVERY, handler=self.pd_CONNECTION_DISCOVERY). \
      to_method()

    self.post_to_queue = self.create(state='post_to_queue'). \
      catch(signal=signals.CONNECTION_DISCOVERY, handler=self.ptq_CONNECTION_DISCOVERED). \
      catch(signal=signals.EXIT_SIGNAL, handler=self.ptq_exit). \
      catch(signal=signals.ready, handler=self.ptq_ready). \
      catch(signal=signals.ips_discovered, handler=self.ptq_ips_discovered). \
      to_method()

    self.refactor_producers = self.create(state='refactor_producers'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.rp_entry). \
      to_method()

    self.nest(self.producer_discovery, parent=None). \
      nest(self.post_to_queue, parent=self.producer_discovery). \
      nest(self.refactor_producers, parent=self.post_to_queue)

    if live_trace is None:
      live_trace = False
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy

    self.start_at(self.producer_discovery)

  @staticmethod
  def pd_entry(chart, e):
    status = return_status.HANDLED
    chart.mesh_producers = []
    chart.snoop_trace_producers = []
    chart.snoop_spy_producers = []
    chart.subscribe(Event(signal=signals.CONNECTION_DISCOVERY))

    if not hasattr(chart, 'man_net_chart'):
      chart.man_net_chart = ManNetChart(chart.mesh_routing_key,
        chart.mesh_exchange_name,
        live_trace=chart.live_trace,
        live_spy=chart.live_spy)

    if not hasattr(chart, 'lan_chart'):
      chart.lan_chart = LanChart(chart.mesh_routing_key,
        chart.mesh_exchange_name,
        live_trace=chart.live_trace,
        live_spy=chart.live_spy)

    chart.set_of_ips = set([])
    return status

  @staticmethod
  def pd_CONNECTION_DISCOVERY(chart, e):
    status = return_status.HANDLED
    try:
      set_of_payload_ips = set(chart.get_ip_for_hostname(host) for host in e.payload.hosts)
    except:
      return status

    chart.set_of_new_ips = set_of_payload_ips - chart.set_of_ips
    chart.set_of_ips |= set_of_payload_ips

    if(len(chart.set_of_new_ips) > 0):
      chart.post_fifo(Event(signal=signals.ips_discovered))

    if e.payload.dispatcher == 'man_net_chart':
      if hasattr(chart, 'man_net_chart'):
        del chart.man_net_chart
    elif e.payload.dispatcher == 'lan_chart':
      if hasattr(chart, 'lan_chart'):
        del chart.lan_chart
    return status

  @staticmethod
  def pd_ips_discovered(chart, e):
    status = chart.trans(chart.refactor_producers)
    return status

  @staticmethod
  def ptq_CONNECTION_DISCOVERED(chart, e):
    status = return_status.HANDLED
    chart.defer(e)
    return status

  @staticmethod
  def ptq_exit(chart, e):
    status = return_status.HANDLED
    chart.set_of_new_ips = set([])
    chart.recall()
    return status

  @staticmethod
  def ptq_ips_discovered(chart, e):
    return chart.trans(chart.refactor_producers)

  @staticmethod
  def ptq_ready(chart, e):
    return chart.trans(chart.producer_discovery)

  @staticmethod
  def rp_entry(chart, e):
    status = return_status.HANDLED
    new_ips = list(chart.set_of_new_ips)

    new_mesh_producers = \
      [chart.make_mesh_producer(ip) for ip in new_ips]
    new_snoop_trace_producers = \
      [chart.make_snoop_trace_producer(ip) for ip in new_ips]
    new_snoop_spy_producers = \
      [chart.make_snoop_spy_producer(ip) for ip in new_ips]

    chart.mesh_producers += new_mesh_producers
    chart.snoop_trace_producers += new_snoop_trace_producers
    chart.snoop_spy_producers += new_snoop_spy_producers

    payload = ProducerQueue(
      mesh_producers=chart.mesh_producers,
      snoop_trace_producers=chart.snoop_trace_producers,
      snoop_spy_producers=chart.snoop_spy_producers,
      ip_addresses=new_ips)

    try:
      chart.producers_queue.put(payload, block=False)
    except queue.Full:
      chart.post_fifo(Event(signal=signals.ips_discovered), times=1, period=1, deferred=True)
    else:
      chart.post_fifo(Event(signal=signals.ready))
    return status
'''
This package is a RabbitMq (amqp) networking plugin for the Python statechart
miros library.

It extends the miros.activeobject.ActiveObject class and the
miros.activeobject.Factory class to communicate using RabbitMq.  This enables
any statechart that is accessed or constructed using these classes to
communicate with other networked statecharts.

To build a NetworkedActiveObject:

  from miros_rabbitmq import NetworkedActiveObject
  # from cryptography import Fernet
  # new_encryption_key = Fernet.generate_key()
  # print(new_encryption_key) # => b'u3u...'

  ao = NetworkedActiveObject(
        "name_of_statechart",
        rabbit_user="<rabbitmq_user_name>",
        rabbit_password="<rabbitmq_password>",
        tx_routing_key="heya.man",
        rx_routing_key="#.man",
        mesh_encryption_key=b'u3u...')

  # ao will have all of the methods of an ActiveObject and:
  ao.enable_snoop_trace()  # useful
  ao.enable_snoop_spy()    # too much information for most purposes
  ao.start_at(<starting_state>)  # this will turn on mesh and snoop networks
  ao.transmit(Event(signal=signals.example_networked_event, payload="hello world")

  # if another statechart has sent you an event with the tx_routing_key that
  # matches your rx_routing_key pattern it will be placed into the FIFO queue of
  # the statechart.

To build a NetworkedFactory:

  from miros_rabbitmq import NetworkedActiveObject
  # from cryptography import Fernet
  # new_encryption_key = Fernet.generate_key()
  # print(new_encryption_key) # => b'u3u...'

  fo = NetworkedFactory(
        "name_of_statechart",
        rabbit_user="<rabbitmq_user_name>",
        rabbit_password="<rabbitmq_password>",
        tx_routing_key="heya.man",
        rx_routing_key="#.man",
        mesh_encryption_key=b'u3u...')

  # build up your statechart using the Factory API.
  # ..
  # ..
  fo.enable_snoop_trace()  # useful
  fo.enable_snoop_spy()    # too much information for most purposes
  fo.start_at(<starting_state>)  # this will turn on mesh and snoop networks
  fo.transmit(Event(signal=signals.example_networked_event, payload="hello world")

  # if another statechart has sent you an event with the tx_routing_key that
  # matches your rx_routing_key pattern it will be placed into the FIFO queue of
  # the statechart.

  NetworkedFactory and NetworkedActiveObject can work together across the
  network.
'''

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
        '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
#logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

class SimplePikaTopicConsumer():
  """
  This is a pika (Python-RabbitMq) message consumer (topic routing), which is
  heavily based on the asynchronous example provided in the pike documentation.
  It should handle unexpected interactions with RabbitMQ such as channel and
  connection closures.

  If RabbitMQ closes the connection, it will reopen it. You should
  look at the output, as there are limited reasons why the connection may
  be closed, which usually are tied to permission related issues or
  socket timeouts.

  If the channel is closed, it will indicate a problem with one of the
  commands that were issued and that should surface in the output as well.

  **Example**:

  .. code-block:: python

    pc = PikaTopicConsumer(
      amqp_url='amqp://bob:dobbs@localhost:5672/%2F',
      routing_key='pub_thread.text',
      exchange_name='sex_change',
      queue_name='g_queue',
    )
    pc.start_thread()

  """
  EXCHANGE_TYPE = 'topic'
  KILL_THREAD_CALLBACK_TEMPO = 1.0  # how long it will take the thread to quit
  RPC_QUEUE_NAME = 'RPC_QUEUE'
  QUEUE_TTL_IN_MS = 500

  def __init__(self,
    amqp_url,
    routing_key,
    exchange_name,
    message_ttl_in_ms=None):
    """Create a new instance of the consumer class, passing in the AMQP
    URL used to connect to RabbitMQ.

    :param str amqp_url: The AMQP url to connect with

    """
    self._connection = None
    self._channel = None
    self._closing = False
    self._consumer_tag = None
    self._url = amqp_url
    self._task_run_event = ThreadEvent()
    self._exchange_name = exchange_name
    self._routing_key = routing_key
    self._queue_name = None

    if not message_ttl_in_ms:
      self._message_ttl_in_ms = self.QUEUE_TTL_IN_MS
    else:
      self._message_ttl_in_ms = message_ttl_in_ms

  def connect(self):
    """This method connects to RabbitMQ, returning the connection handle.
    When the connection is established, the on_connection_open method
    will be invoked by pika.

    :rtype: pika.SelectConnection

    """
    LOGGER.info('Connecting to %s', self._url)
    return pika.SelectConnection(pika.URLParameters(self._url),
                   self.on_connection_open,
                   stop_ioloop_on_close=False)

  def on_connection_open(self, unused_connection):
    """This method is called by pika once the connection to RabbitMQ has
    been established. It passes the handle to the connection object in
    case we need it, but in this case, we'll just mark it unused.

    :type unused_connection: pika.SelectConnection

    """
    LOGGER.info('Connection opened')
    self.add_on_connection_close_callback()
    self.open_channel()

  def add_on_connection_close_callback(self):
    """This method adds an on close callback that will be invoked by pika
    when RabbitMQ closes the connection to the publisher unexpectedly.

    """
    LOGGER.info('Adding connection close callback')
    self._connection.add_on_close_callback(self.on_connection_closed)

  def on_connection_closed(self, connection, reply_code, reply_text):
    """This method is invoked by pika when the connection to RabbitMQ is
    closed unexpectedly. Since it is unexpected, we will reconnect to
    RabbitMQ if it disconnects.

    :param pika.connection.Connection connection: The closed connection obj
    :param int reply_code: The server provided reply_code if given
    :param str reply_text: The server provided reply_text if given

    """
    self._channel = None
    if self._closing:
      self._connection.ioloop.stop()
    else:
      LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
               reply_code, reply_text)
      self._connection.add_timeout(5, self.reconnect)

  def reconnect(self):
    """Will be invoked by the IOLoop timer if the connection is
    closed. See the on_connection_closed method.

    """
    # This is the old connection IOLoop instance, stop its ioloop
    self._connection.ioloop.stop()

    if not self._closing:

      # Create a new connection
      self._connection = self.connect()

      # There is now a new connection, needs a new ioloop to run
      self._connection.ioloop.start()

  def open_channel(self):
    """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
    command. When RabbitMQ responds that the channel is open, the
    on_channel_open callback will be invoked by pika.

    """
    LOGGER.info('Creating a new channel')
    self._connection.channel(on_open_callback=self.on_channel_open)

  def on_channel_open(self, channel):
    """This method is invoked by pika when the channel has been opened.
    The channel object is passed in so we can make use of it.

    Since the channel is now open, we'll declare the exchange to use.

    :param pika.channel.Channel channel: The channel object

    """
    LOGGER.info('Channel opened')
    self._channel = channel
    self.add_on_channel_close_callback()
    self.setup_exchange(self._exchange_name)

  def add_on_channel_close_callback(self):
    """This method tells pika to call the on_channel_closed method if
    RabbitMQ unexpectedly closes the channel.

    """
    LOGGER.info('Adding channel close callback')
    self._channel.add_on_close_callback(self.on_channel_closed)

  def on_channel_closed(self, channel, reply_code, reply_text):
    """Invoked by pika when RabbitMQ unexpectedly closes the channel.
    Channels are usually closed if you attempt to do something that
    violates the protocol, such as re-declare an exchange or queue with
    different parameters. In this case, we'll close the connection
    to shutdown the object.

    :param pika.channel.Channel: The closed channel
    :param int reply_code: The numeric reason the channel was closed
    :param str reply_text: The text reason the channel was closed

    """
    LOGGER.warning('Channel %i was closed: (%s) %s',
             channel, reply_code, reply_text)
    self._connection.close()

  def setup_exchange(self, exchange_name):
    """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
    command. When it is complete, the on_exchange_declareok method will
    be invoked by pika.

    :param str|unicode exchange_name: The name of the exchange to declare

    """
    LOGGER.info('Declaring exchange %s', exchange_name)
    self._channel.exchange_declare(
        callback=self.on_exchange_declareok,
        exchange=exchange_name,
        exchange_type=self.EXCHANGE_TYPE,
        durable=False)

  def on_exchange_declareok(self, unused_frame):
    """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
    command.

    :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

    """
    LOGGER.info('Exchange declared')
    self.setup_queue()

  def setup_queue(self):
    """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
    command. When it is complete, the on_queue_declareok method will
    be invoked by pika.

    :param str|unicode queue_name: The name of the queue to declare.

    """
    LOGGER.info('Declaring queue')
    self._channel.queue_declare(
        callback=self.on_queue_declareok,
        arguments={'x-message-ttl': 50000},
        exclusive=True)

  def on_queue_declareok(self, method_frame):
    """Method invoked by pika when the Queue.Declare RPC call made in
    setup_queue has completed. In this method we will bind the queue
    and exchange together with the routing key by issuing the Queue.Bind
    RPC command. When this command is complete, the on_bindok method will
    be invoked by pika.

    :param pika.frame.Method method_frame: The Queue.DeclareOk frame

    """
    self._queue_name = method_frame.method.queue
    self._channel.queue_bind(self.on_bindok, self._queue_name,
                 self._exchange_name, self._routing_key)
    LOGGER.info('Binding %s to %s with %s',
          self._exchange_name, self._queue_name, self._routing_key)

  def on_bindok(self, unused_frame):
    """Invoked by pika when the Queue.Bind method has completed. At this
    point we will start consuming messages by calling start_consuming
    which will invoke the needed RPC commands to start the process.

    :param pika.frame.Method unused_frame: The Queue.BindOk response frame

    """
    LOGGER.info('Queue bound')
    self.start_consuming()

  def start_consuming(self):
    """This method sets up the consumer by first calling
    add_on_cancel_callback so that the object is notified if RabbitMQ
    cancels the consumer. It then issues the Basic.Consume RPC command
    which returns the consumer tag that is used to uniquely identify the
    consumer with RabbitMQ. We keep the value to use it when we want to
    cancel consuming. The on_message method is passed in as a callback pika
    will invoke when a message is fully received.

    """
    LOGGER.info('Issuing consumer related RPC commands')
    self.add_on_cancel_callback()
    self._consumer_tag = self._channel.basic_consume(self.on_message,
                             self._queue_name)

  def add_on_cancel_callback(self):
    """Add a callback that will be invoked if RabbitMQ cancels the consumer
    for some reason. If RabbitMQ does cancel the consumer,
    on_consumer_cancelled will be invoked by pika.

    """
    LOGGER.info('Adding consumer cancellation callback')
    self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

  def on_consumer_cancelled(self, method_frame):
    """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
    receiving messages.

    :param pika.frame.Method method_frame: The Basic.Cancel frame

    """
    LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
          method_frame)
    if self._channel:
      self._channel.close()

  def on_message(self, unused_channel, basic_deliver, properties, body):
    """Invoked by pika when a message is delivered from RabbitMQ. The
    channel is passed for your convenience. The basic_deliver object that
    is passed in carries the exchange, routing key, delivery tag and
    a redelivered flag for the message. The properties passed in is an
    instance of BasicProperties with the message properties and the body
    is the message that was sent.

    :param pika.channel.Channel unused_channel: The channel object
    :param pika.Spec.Basic.Deliver: basic_deliver method
    :param pika.Spec.BasicProperties: properties
    :param str|unicode body: The message body

    """
    LOGGER.info('Received message # %s from %s: %s',
          basic_deliver.delivery_tag, properties.app_id, body)
    self.acknowledge_message(basic_deliver.delivery_tag)

  def acknowledge_message(self, delivery_tag):
    """Acknowledge the message delivery from RabbitMQ by sending a
    Basic.Ack RPC method for the delivery tag.

    :param int delivery_tag: The delivery tag from the Basic.Deliver frame

    """
    LOGGER.info('Acknowledging message %s', delivery_tag)
    try:
      self._channel.basic_ack(delivery_tag)
    except:
      LOGGER.info('Acknowledgment requires an open channel')

  def nak_message(self, delivery_tag):
    LOGGER.info('Not acknowledging message %s', delivery_tag)
    try:
      self._channel.basic_nack(delivery_tag)
    except:
      LOGGER.info('Acknowledgment requires an open channel')

  def stop_consuming(self):
    """Tell RabbitMQ that you would like to stop consuming by sending the
    Basic.Cancel RPC command.

    """
    if self._channel:
      LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
      self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

  def on_cancelok(self, unused_frame):
    """This method is invoked by pika when RabbitMQ acknowledges the
    cancellation of a consumer. At this point we will close the channel.
    This will invoke the on_channel_closed method once the channel has been
    closed, which will in-turn close the connection.

    :param pika.frame.Method unused_frame: The Basic.CancelOk frame

    """
    LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer')
    self.close_channel()

  def close_channel(self):
    """Call to close the channel with RabbitMQ cleanly by issuing the
    Channel.Close RPC command.

    """
    LOGGER.info('Closing the channel')
    self._channel.close()

  def run(self):
    """Run the example consumer by connecting to RabbitMQ and then
    starting the IOLoop to block and allow the SelectConnection to operate.

    """
    self._connection = self.connect()
    try:
      self._connection.ioloop.start()
    except Exception as e:
      # if we are turning off the task, ignore exceptions from callbacks
      if not self._task_run_event.is_set():
        pass
      else:
        raise(e)

  def stop(self):
    """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
    with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
    will be invoked by pika, which will then closing the channel and
    connection. The IOLoop is started again because this method is invoked
    when CTRL-C is pressed raising a KeyboardInterrupt exception. This
    exception stops the IOLoop which needs to be running for pika to
    communicate with RabbitMQ. All of the commands issued prior to starting
    the IOLoop will be buffered but not processed.
    """
    LOGGER.info('Stopping')
    self._closing = True
    self.stop_consuming()
    self._connection.ioloop.stop()
    LOGGER.info('Stopped')

  def close_connection(self):
    """This method closes the connection to RabbitMQ."""
    LOGGER.info('Closing connection')
    self._connection.close()

  def timeout_callback_method(self, provide_callback=False):
    # This syntax is a bit strange, so I'll explain what is going on.
    #
    # I am trying to build a partial function from a method, providing a default
    # value for 'self'.  I previously wrote this code as:
    #   timeout_callback = functools.partial(self.timeout_callback_method, self=self)
    # Which was wrong.
    #
    # The correct way to turn a method into a callback
    # function, with a frozen value of 'self', is like this:
    #   timeout_callback = functools.partial(self.timeout_callback_method)
    timeout_callback = functools.partial(self.timeout_callback_method, provide_callback)
    LOGGER.info('Timout callback being registered')

    if self._task_run_event.is_set():
      self._connection.add_timeout(deadline=self.KILL_THREAD_CALLBACK_TEMPO, callback_method=timeout_callback)
    else:
      if not self._closing:
        LOGGER.info('Consuming thread is being shutdown')
        self.stop()

    if provide_callback:
      return timeout_callback

  def start_thread(self):
    """Add a thread so that the run method doesn't steal our program control."""
    self._task_run_event.set()
    self._connection = self.connect()

    def thread_runner(self):
      LOGGER.info('The Thread is Running')
      if self._task_run_event.is_set():
        self._closing = False
        self.run()
      LOGGER.info('The Thread is Dead')

    thread = Thread(target=thread_runner, args=(self,), daemon=True)
    thread.start()

  def stop_thread(self):
    self._task_run_event.clear()
    timeout_callback = functools.partial(self.timeout_callback_method, provide_callback=True)
    self._connection.add_timeout(deadline=0.01, callback_method=timeout_callback)

class PikaTopicConsumer(SimplePikaTopicConsumer):
  """This is a subclass of SimplePikaTopicConsumer which extends its
  capabilities.  It can de-serialize and decrypt received messages and issues
  those messages to client callback methods.  While constructing a 
  PikaTopicConsumer, you provide it with a symmetric encrytion key, and options
  functions for decrypting and deserializing.

  It has a ``start_thread`` and ``stop_thread`` method to control the thread in which
  the rabbit consumer is running.  Without this thread, you would lose program
  control after the ``run`` call.  The encryption key can be changed while the
  service is running.


  **Example**:

  .. code-block:: python

    # make a callback that will get your messages
    def on_message_callback(unused_channel,
                            basic_deliver,
                            properties,
                            body):

      LOGGER.info('Received message # %s from %s: %s',
                   basic_deliver.delivery_tag,
                   properties.app_id, body)

    consumer = PikaTopicConsumer(
      amqp_url='amqp://bob:dobbs@localhost:5672/%2F',
      routing_key='pub_thread.text',
      exchange_name='sex_change',
      queue_name='g_queue',
      message_callback=on_message_callback,
      encryption_key=b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
    )
    consumer.start_thread()
    consumer.stop_thread()

  """
  def __init__(self,
               amqp_url,
               routing_key,
               exchange_name,
               encryption_key,
               message_callback,
               decryption_function=None,
               deserialization_function=None):
    super().__init__(
               amqp_url,
               routing_key,
               exchange_name)

    self._encryption_key  = encryption_key
    self._rabbit_user     = self.get_rabbit_user(amqp_url)
    self._rabbit_password = self.get_rabbit_password(amqp_url)
    self._message_callback = message_callback

    # saved decryption function
    self._sdf = None

    def default_decryption_function(message, encryption_key):
      return Fernet(encryption_key).decrypt(message)

    def default_deserialization_function(obj):
      return pickle.loads(obj)

    if decryption_function is None:
      self._sdf = default_decryption_function
    else:
      self._sdf = decryption_function

    self._decryption_function = \
      functools.partial(self._sdf, encryption_key=encryption_key)

    if deserialization_function is None:
      self._deserialization_function = default_deserialization_function
    else:
      self._deserialization_function = deserialization_function

  def change_encyption_key(self, encryption_key):
    """Change the encryption_key:

    **Example**:

    .. code-block:: python

      # Fernet.generate_key() <= to make a new key
      consumer.change_encyption_key(
        b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
      )

    .. note::

      The consumer key must match the key used by the producer
    """
    self.stop_thread()
    self._decryption_function = \
        functools.partial(self._sdf,
          encryption_key=encryption_key)
    self.start_thread()

  def get_rabbit_user(self, url):
    user = url.split(':')[1][2:]
    return user

  def get_rabbit_password(self, url):
    password = url.split(':')[2].split('@')[0]
    return password

  def deserialize(self, item):
    return self._deserialization_function(item)

  def decrypt(self, item):
    return self._decryption_function(item)

  def on_message(self, unused_channel, basic_deliver, properties, xsbody):

    ignore = False
    try:
      sbody = self.decrypt(xsbody)
    except:
      sbody = xsbody
      ignore = True

    try:
      body  = self.deserialize(sbody)
    except:
      body = sbody
      ignore = True
    #  body = self.deserialize(self.decrypt(xsbody))
    LOGGER.info('Received message # %s from %s: %s',
          unused_channel.connection.params, properties.app_id, body)
    if not ignore:

      self._message_callback(unused_channel, basic_deliver, properties, body)
      self.acknowledge_message(basic_deliver.delivery_tag)
    else:
      self.nak_message(basic_deliver.delivery_tag)

class PID():
  def __init__(self, kp, kd, ki, i_max, i_min, dt):
    self.err   = [0, 0]
    self.int   = [0, 0]
    self.der   = 0
    self.i_max = i_max
    self.i_min = i_min
    self.kp    = kp
    self.kd    = kd
    self.ki    = ki
    self.dt    = dt

  def next(self, x):
    '''A simple PID'''
    # err[0] = ref - x
    # err[1] = err[0] from the last sample
    # int[0] = int[1] + err[0]
    # int[1] = int[0] from the last sample
    # der = err[1] + err[0]
    # dt  = sample period in sec
    # output = kp*err[0] + (ki*int[0]*dt) + (kd*der/dt)
    output      = None
    ref         = 0
    self.err[0] = ref - x
    self.int[0] = self.int[1] + self.err[0]
    self.der    = self.err[1] + self.err[0]

    self.int[0] = self.i_max if self.int[0] > self.i_max else self.int[0]
    self.int[0] = self.i_min if self.int[0] < self.i_min else self.int[0]

    output  = self.kp * self.err[0]
    output += self.ki * self.int[0] * self.dt

    if self.dt != 0:
      output += self.kd * self.der / self.dt

    self.output = output
    self.err[1] = self.err[0]
    self.int[1] = self.int[0]
    return output

  def reset(self):
    self.err = [0, 0]
    self.int = [0, 0]
    self.der = 0


class QueueToSampleTimeControl(PID):
  def __init__(self, i_max, dt):
    super().__init__(kp=0.07, kd=0.05, ki=0.4, i_max=i_max, i_min=-1 * i_max, dt=dt)
    if i_max != 0:
      self.min_tempo = 1 / i_max
    else:
      self.min_tempo = 0.000001

  def next(self, x):
    '''Invert the output of our PID -> large amounts of control need to express
       short durations in time'''
    output = super().next(x)

    # if the controller is working accelerate the wind-down of the integrator
    # (the queue can't be negative, so help it out)
    if output <= 0:
      self.int[1] /= 1.1
      self.err[1] /= 1.1
      output =  1 / self.dt

    # start with the baseline tempo
    time_recommendation = self.dt

    if output != 0:
      time_recommendation = 1 / output

    # clamps
    time_recommendation = \
      self.min_tempo if time_recommendation < self.min_tempo else time_recommendation

    time_recommendation = \
      self.dt if time_recommendation > self.dt else time_recommendation

    return time_recommendation

class SimplePikaTopicPublisher():
  '''
  This is a pika (Python-RabbitMq) message publisher heavily based on the
  asychronous example provided in the pika documentation.  It should handle
  unexpected interactions with RabbitMQ such as channel and connection closures.

  If RabbitMQ closes the connection, an object of this class should reopen it.
  (You should look at the output, as there are limited reasons why the connection
  may be closed, which usually are tied to permission related issues or socket
  timeouts.)

  **Example**:

  .. code-block:: python

    # set a callback mechanism to sample the task's input queue every 1.5 seconds
    # name the exchange in the RabbitMq server at the url to 'g_pika_producer_exchange'
    # name the RabbitMq queue on the server at the url to 'g_queue'
    # set the topic routing key to 'pub_thread.text'

    publisher = \
      SimplePikaTopicPublisher(
        amqp_url='amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600',
        publish_tempo_sec=1.5,
        exchange_name='g_pika_producer_exchange',
        routing_key='pub_thread.text',
      )

    # to start the thread so pika won't block your code:
    publisher.start_thread()

    # to actually write messages (publish) to the amqp_url:
    publish.post_fifo("Some Message")

    # to stop the thread but keep the connection
    publisher.start_thread()

    # to start the thread again
    publisher.start_thread()

    # to stop the connection and the thread
    publisher.stop()

    # to reconnect and start the thread
    publisher.start_thread()

  .. note::

    It uses delivery confirmations and illustrates one way to keep track of
    messages that have been sent and if they've been confirmed by RabbitMQ.
    This confirmation mechanism will not work if message tempo exceeds the
    publish_tempo (the messages will get through but the confirmation mechanism
    will indicate there is a problem when there isn't one.)

    If the input queue has more than one item they will all be sent out to the
    network and the queue sampler callback's frequency will temporarily
    increase to deal with queue bursting.

  '''
  EXCHANGE_TYPE             = 'topic'
  PUBLISH_FAST_INTERVAL_SEC = 0.000001  # right now
  PRODUCER_VERSION          = u'1.0'

  def __init__(self,
               amqp_url,
               routing_key,
               publish_tempo_sec,
               exchange_name):
    '''Setup the example publisher object, passing in the URL we will use
    to connect to RabbitMQ.

    :param str amqp_url: The URL for connecting to RabbitMQ

    '''
    self._channel = None
    self._connection = None

    self._acked = 0
    self._nacked = 0
    self._deliveries = []
    self._message_number = 0

    self._closing = False
    self._stopping = False
    self.connect_error = False

    self.amqp_url = amqp_url
    self._task_run_event = ThreadEvent()
    self._publish_tempo_sec = publish_tempo_sec
    self._thread_queue = ThreadQueue(maxsize=500)

    self._tempo_controller = QueueToSampleTimeControl(
      i_max=1 / self.PUBLISH_FAST_INTERVAL_SEC,
      dt = publish_tempo_sec)

    # will set the exchange, queue and routing_keys names for the RabbitMq
    # server running on amqp_url
    self._rabbit_exchange_name = exchange_name
    self._routing_key = routing_key

  def connect(self):
    '''This method connects to RabbitMQ, returning the connection handle.
    When the connection is established, the on_connection_open method
    will be invoked by pika. If you want the reconnection to work, make
    sure you set stop_ioloop_on_close to False, which is not the default
    behavior of this adapter.

    :rtype: pika.SelectConnection

    '''
    LOGGER.info('Connecting to %s', self.amqp_url)
    return pika.SelectConnection(pika.URLParameters(self.amqp_url),
                   self.on_connection_open,
                   stop_ioloop_on_close=False)

  def on_connection_open(self, unused_connection):
    '''This method is called by pika once the connection to RabbitMQ has
    been established. It passes the handle to the connection object in
    case we need it, but in this case, we'll just mark it unused.

    :type unused_connection: pika.SelectConnection

    '''
    LOGGER.info('Connection opened')
    self.add_on_connection_close_callback()
    self.open_channel()

  def add_on_connection_close_callback(self):
    '''This method adds an on close callback that will be invoked by pika
    when RabbitMQ closes the connection to the publisher unexpectedly.

    '''
    LOGGER.info('Adding connection close callback')
    self._connection.add_on_close_callback(self.on_connection_closed)

  def on_connection_closed(self, connection, reply_code, reply_text):
    '''This method is invoked by pika when the connection to RabbitMQ is
    closed unexpectedly. Since it is unexpected, we will reconnect to
    RabbitMQ if it disconnects.

    :param pika.connection.Connection connection: The closed connection obj
    :param int reply_code: The server provided reply_code if given
    :param str reply_text: The server provided reply_text if given

    '''
    self._channel = None
    if self._closing:
      self._connection.ioloop.stop()
    else:
      LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
               reply_code, reply_text)
      self._connection.add_timeout(5, self.reconnect)

  def reconnect(self):
    '''Will be invoked by the IOLoop timer if the connection is
    closed. See the on_connection_closed method.

    '''
    self._deliveries = []
    self._acked = 0
    self._nacked = 0
    self._message_number = 0

    # This is the old connection IOLoop instance, stop its ioloop
    self._connection.ioloop.stop()

    # Create a new connection
    self._connection = self.connect()

    # There is now a new connection, needs a new ioloop to run
    self._connection.ioloop.start()

  def open_channel(self):
    '''This method will open a new channel with RabbitMQ by issuing the
    Channel.Open RPC command. When RabbitMQ confirms the channel is open
    by sending the Channel.OpenOK RPC reply, the on_channel_open method
    will be invoked.

    '''
    LOGGER.info('Creating a new channel')
    self._connection.channel(on_open_callback=self.on_channel_open)

  def on_channel_open(self, channel):
    '''This method is invoked by pika when the channel has been opened.
    The channel object is passed in so we can make use of it.

    Since the channel is now open, we'll declare the exchange to use.

    :param pika.channel.Channel channel: The channel object

    '''
    LOGGER.info('Channel opened')
    self._channel = channel
    self.add_on_channel_close_callback()
    self.setup_exchange(self._rabbit_exchange_name)

  def add_on_channel_close_callback(self):
    '''This method tells pika to call the on_channel_closed method if
    RabbitMQ unexpectedly closes the channel.

    '''
    LOGGER.info('Adding channel close callback')
    self._channel.add_on_close_callback(self.on_channel_closed)

  def on_channel_closed(self, channel, reply_code, reply_text):
    '''Invoked by pika when RabbitMQ unexpectedly closes the channel.
    Channels are usually closed if you attempt to do something that
    violates the protocol, such as re-declare an exchange or queue with
    different parameters. In this case, we'll close the connection
    to shutdown the object.

    :param pika.channel.Channel: The closed channel
    :param int reply_code: The numeric reason the channel was closed
    :param str reply_text: The text reason the channel was closed

    '''
    LOGGER.warning('Channel was closed: (%s) %s', reply_code, reply_text)
    if not self._closing:
      self._connection.close()

  def setup_exchange(self, exchange_name):
    '''Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
    command. When it is complete, the on_exchange_declareok method will
    be invoked by pika.

    :param str|unicode exchange_name: The name of the exchange to declare

    '''
    LOGGER.info('Declaring exchange %s', exchange_name)
    self._channel.exchange_declare(
                     callback=self.on_exchange_declareok,
                     exchange=exchange_name,
                     exchange_type=self.EXCHANGE_TYPE,
                     durable=False)

  def on_exchange_declareok(self, unused_frame):
    '''Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
    command.

    :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

    '''
    LOGGER.info('Exchange declared')

    self.start_publishing()


  def start_publishing(self):
    '''This method will enable delivery confirmations and schedule the
    first message to be sent to RabbitMQ

    '''
    LOGGER.info('Issuing consumer related RPC commands')
    self.enable_delivery_confirmations()
    self.schedule_next_producer_heart_beat(self._publish_tempo_sec)

  def enable_delivery_confirmations(self):
    '''Send the Confirm.Select RPC method to RabbitMQ to enable delivery
    confirmations on the channel. The only way to turn this off is to close
    the channel and create a new one.

    When the message is confirmed from RabbitMQ, the
    on_delivery_confirmation method will be invoked passing in a Basic.Ack
    or Basic.Nack method from RabbitMQ that will indicate which messages it
    is confirming or rejecting.

    '''
    LOGGER.info('Issuing Confirm.Select RPC command')
    self._channel.confirm_delivery(self.on_delivery_confirmation)

  def on_delivery_confirmation(self, method_frame):
    '''Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
    command, passing in either a Basic.Ack or Basic.Nack frame with
    the delivery tag of the message that was published. The delivery tag
    is an integer counter indicating the message number that was sent
    on the channel via Basic.Publish. Here we're just doing house keeping
    to keep track of stats and remove message numbers that we expect
    a delivery confirmation of from the list used to keep track of messages
    that are pending confirmation.

    :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame

    '''
    confirmation_type = method_frame.method.NAME.split('.')[1].lower()
    LOGGER.info('Received %s for delivery tag: %i',
          confirmation_type,
          method_frame.method.delivery_tag)
    if confirmation_type == 'ack':
      self._acked += 1
    elif confirmation_type == 'nack':
      self._nacked += 1

    item = method_frame.method.delivery_tag
    # only remove items that exist in our list (if a previous thread was
    # canceled and this one was started we would receive delivery_tags which we
    # didn't send - this could cause the remove method to crash the producer
    if item in self._deliveries:
      self._deliveries.remove(method_frame.method.delivery_tag)
      LOGGER.info('Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked',
            self._message_number, len(self._deliveries),
            self._acked, self._nacked)
    else:
      LOGGER.info('Received delivery tag for something we did not send')

  def schedule_next_producer_heart_beat(self, timeout):
    '''If we are not closing our connection to RabbitMQ, schedule another
    message to be delivered in self._publish_tempo_sec seconds.

    '''
    if self._stopping:
      return

    # Scheduling next Task queue check
    LOGGER.info('Task queue check in %0.4f seconds', timeout)
    self._connection.add_timeout(timeout, self.producer_heart_beat)

  def publish_message(self, message):
    '''If the class is not stopping, publish a message to RabbitMQ,
    appending a list of deliveries with the message number that was sent.
    This list will be used to check for delivery confirmations in the
    on_delivery_confirmations method.

    **Example**:

    .. code-block:: python

      # get the message from somewhere
      message = self._thread_queue.get()

      # user partial of this method to make a custom callback with your message as an input
      cb = functools.partial(self.publish_message, message=message)

      # then load it into a timer
      self._connection.add_timeout(self.PUBLISH_FAST_INTERVAL_SEC, cb)
    '''
    if self._stopping:
      return
    properties = pika.BasicProperties(app_id='miros-rabbitmq-publisher',
                      content_type='application/json',
                      headers={u'version': self.PRODUCER_VERSION})

    self._channel.basic_publish(self._rabbit_exchange_name, self._routing_key,
                  message,
                  properties)

    self._message_number += 1
    self._deliveries.append(self._message_number)
    LOGGER.info('Published message # %i', self._message_number)

  def close_channel(self):
    '''Invoke this command to close the channel with RabbitMQ by sending
    the Channel.Close RPC command.'''
    LOGGER.info('Closing the channel')
    if self._channel:
      self._channel.close()

  def run(self):
    '''Run the example code by connecting and then starting the IOLoop. '''
    self._connection = self.connect()
    self._connection.ioloop.start()

  def stop(self):
    '''Stop the example by closing the channel and connection and releasing the
    thread. We set a flag here so that we stop scheduling new messages to be
    published. The IOLoop is started because this method is
    invoked by the Try/Catch below when KeyboardInterrupt is caught.
    Starting the IOLoop again will allow the publisher to cleanly
    disconnect from RabbitMQ.
    '''
    LOGGER.info('Stopping')
    self._stopping = True
    self.close_channel()
    self.close_connection()
    self._task_run_event.clear()
    self._connection.ioloop.start()
    LOGGER.info('Stopped')

  def close_connection(self):
    '''This method closes the connection to RabbitMQ.'''
    LOGGER.info('Closing connection')
    self._closing = True
    self._connection.close()

  def producer_heart_beat(self):
    '''This is the callback that is called ever publish_tempo_sec to check to
    see if something is in the thread_queue.  If there are items in this queue
    it schedules other callbacks to send out the messages, and temporarily
    increases its frequecy to deal with queue bursting.
    '''
    if self._task_run_event.is_set():
      if self._stopping:
        return
      # messages tend to bunch up, they are bursty, so speed up our
      # producer_heart_beat if there were messages in our queue
      queue_length = self._thread_queue.qsize()
      new_tempo_period_sec = self._tempo_controller.next(queue_length)
      self.schedule_next_producer_heart_beat(new_tempo_period_sec)

      # send out all messages in the queue
      if queue_length >= 1:
        for i in range(queue_length):
          message = self._thread_queue.get()
          cb = functools.partial(self.publish_message, message=message)
          self._connection.add_timeout(self.PUBLISH_FAST_INTERVAL_SEC, cb)
          LOGGER.info('Scheduling next output message in %0.6f seconds', self.PUBLISH_FAST_INTERVAL_SEC)

  def post_fifo(self, message):
    '''use this to post messages to the network'''
    self._thread_queue.put(message)

  def start_thread(self):
    '''Add a thread so that the run method doesn't steal our program control.'''
    self._task_run_event.set()
    self._stopping = False

    def thread_runner(self):
      # The run method will turn on pika's callback hell.
      # To see how this is turned off look at the producer_heart_beat
      try:
        self.run()
      except:
        self.stop_thread()
        self.connect_error = True

    thread = Thread(target=thread_runner, args=(self,), daemon=True)
    thread.start()

  def stop_thread(self):
    '''stop the thread, but keep the connection open.  To close the connection
    and stop the thread, use the 'stop' api'''
    self._task_run_event.clear()

class PikaTopicPublisher(SimplePikaTopicPublisher):
  '''This is subclass of SimplePikaTopicPublisher which extends its capabilities.

  It can serialize and encrypt messages before it transmits them.
  While constructing it, you provide it with a
  symmetric encryption key, and optional functions for encrypting and
  serializing messages.

  **Example**:

  .. code-block:: python

    publisher = \\
      PikaTopicPublisher(
        amqp_url='amqp://bob:dobbs@192.168.1.69:5672/%2F?connection_attempts=3&heartbeat_interval=3600',
        routing_key='pub_thread.text',
        publish_tempo_sec=1.5,
        exchange_name='sex_change',
        encryption_key=b'u3Uc-qAi9iiCv3fkBfRUAKrM1gH8w51-nVU8M8A73Jg='
      )

    publisher.start_thread()
    publisher.post_fifo("Publish a Message")
    publisher.stop_thread()
  '''
  def __init__(self,
               amqp_url,
               routing_key,
               publish_tempo_sec,
               exchange_name,
               encryption_key,
               encryption_function=None,
               serialization_function=None):

    super().__init__(
               amqp_url,
               routing_key,
               publish_tempo_sec,
               exchange_name)

    self._encryption_key  = encryption_key
    self._rabbit_user     = self.get_rabbit_user(amqp_url)
    self._rabbit_password = self.get_rabbit_password(amqp_url)

    # saved encryption function
    self._sef = None

    def default_encryption_function(message, encryption_key):
      return Fernet(encryption_key).encrypt(message)

    def default_serialization_function(obj):
      return pickle.dumps(obj)

    if encryption_function is None:
      self._sef = default_encryption_function
    else:
      self._sef = encryption_function

    self._encryption_function = functools.partial(self._sef,
        encryption_key=encryption_key)

    if serialization_function is None:
      self._serialization_function = default_serialization_function
    else:
      self._serialization_function = serialization_function

  def change_encryption_key(self, encryption_key):
    self.stop_thread()
    self._encryption_function = functools.partial(self._sef, encryption_key=encryption_key)
    self.start_thread()

  def get_rabbit_user(self, url):
    user = url.split(':')[1][2:]
    return user

  def get_rabbit_password(self, url):
    password = url.split(':')[2].split('@')[0]
    return password

  def encrypt(self, item):
    return self._encryption_function(item)

  def serialize(self, item):
    return self._serialization_function(item)

  def post_fifo(self, item):
    xsitem = self.encrypt(self.serialize(item))
    super().post_fifo(xsitem)

class LocalAreaNetwork():
  '''Provides the ip_addresses of the local area network (LAN)

  **Example**:

  .. code-block:: python

    lan = LocalAreaNetwork()

    print(lan.addresses)  # => \\
      ['192.168.1.66'
       '192.168.1.69',
       '192.168.1.70',
       '192.168.1.71',
       '192.168.1.75',
       '192.168.1.254']

    print(lan.this.address)  # => '192.168.1.75'

    print(lan.other.addresses)  # => \\
      ['192.168.1.66',
      '192.168.1.69',
      '192.168.1.70',
      '192.168.1.71',
      '192.168.1.254']

    print(LocalAreaNetwork.get_working_ip_address())  # => \\
      '192.168.1.75'

  '''
  def __init__(self):
    self.this  = Attribute()
    self.other = Attribute()
    self.this.address = LocalAreaNetwork.get_working_ip_address()
    self.addresses = self.candidate_ip_addresses()
    self.other.addresses = list(set(self.addresses) - set([self.this.address]))

  @staticmethod
  def get_working_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      s.connect(('10.255.255.255', 1))
      ip = s.getsockname()[0]
    except:
      ip = '127.0.0.1'
    finally:
      s.close()
    return ip

  def get_ipv4_network(self):
    ip_address = LocalAreaNetwork.get_working_ip_address()
    netmask    = self.netmask_on_this_machine()
    inet4 = ipaddress.ip_network(ip_address + '/' + netmask, strict=False)
    return inet4

  def fill_arp_table(self):
    linux_cmd = 'ping -b {}'
    inet4 = self.get_ipv4_network()

    if inet4.num_addresses <= 256:
      broadcast_address = inet4[-1]
      fcmd = linux_cmd.format(broadcast_address)
      fcmd_as_list = fcmd.split(" ")
      try:
        ps = subprocess.Popen(fcmd_as_list, stdout=open(os.devnull, "wb"))
        ps.wait(2)
      except:
        ps.kill()
    return

  def ip_addresses_on_lan(self):
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
        output = subprocess.check_output(grep_as_list, stdin=ps.stdout, timeout=0.5)
        ps.wait()
        if output is not '':
          candidates = output.decode('utf-8').split('\n')
          if len(candidates) > 0:
            break
      except:
        # our windows command did not work on Linux
        pass
    return list(filter(None, candidates))

  def netmask_on_this_machine(self):
    interfaces = [interface for interface in netifaces.interfaces()]
    local_netmask = None
    working_address = LocalAreaNetwork.get_working_ip_address()
    for interface in interfaces:
      interface_network_types = netifaces.ifaddresses(interface)
      if netifaces.AF_INET in interface_network_types:
        if interface_network_types[netifaces.AF_INET][0]['addr'] == working_address:
          local_netmask = interface_network_types[netifaces.AF_INET][0]['netmask']
          break
    return local_netmask

  def ip_addresses_on_this_machine(self):
    interfaces = [interface for interface in netifaces.interfaces()]
    local_ip_addresses = []
    for interface in interfaces:
      interface_network_types = netifaces.ifaddresses(interface)
      if netifaces.AF_INET in interface_network_types:
        ip_address = interface_network_types[netifaces.AF_INET][0]['addr']
        local_ip_addresses.append(ip_address)
    return local_ip_addresses

  def candidate_ip_addresses(self):
    self.fill_arp_table()
    lan_ip_addresses = []
    a = set(self.ip_addresses_on_lan())
    b = set(self.ip_addresses_on_this_machine())
    c = set([LocalAreaNetwork.get_working_ip_address()])
    candidates = list(a - b ^ c)
    inet4 = self.get_ipv4_network()
    for host in inet4.hosts():
      shost = str(host)
      if shost in candidates:
        lan_ip_addresses.append(shost)
    return lan_ip_addresses

class RabbitHelper():
  CONNECTION_ATTEMPTS    = 3
  HEARTBEAT_INTERVAL_SEC = 3600
  PORT                   = 5672

  @staticmethod
  def make_amqp_url(ip_address,
               rabbit_user,
               rabbit_password,
               rabbit_port=None,
               connection_attempts=None,
               heartbeat_interval=None):
    '''Make a RabbitMq url.

      **Example**:

      .. code-block:: python

        amqp_url = \\
          RabbitHelper.make_amqp_url(
              ip_address=192.168.1.1,
              rabbit_user='bob',
              rabbit_password='dobb',
              connection_attempts='3',
              heartbeat_interval='3600')

        print(amqp_url)  # =>
          'amqp://bob:dobbs@192.168.1.1:5672/%2F?connection_attempts=3&heartbeat_interval=3600'

    '''
    if rabbit_port is None:
      rabbit_port = RabbitHelper.PORT
    if connection_attempts is None:
      connection_attempts = RabbitHelper.CONNECTION_ATTEMPTS
    if heartbeat_interval is None:
      heartbeat_interval = RabbitHelper.HEARTBEAT_INTERVAL_SEC

    amqp_url = \
      "amqp://{}:{}@{}:{}/%2F?connection_attempts={}&heartbeat_interval={}".format(
          rabbit_user,
          rabbit_password,
          ip_address,
          rabbit_port,
          connection_attempts,
          heartbeat_interval)
    return amqp_url

class MirosApiException(BaseException):
  pass

class MirosNets:

  SPY_ROUTING_KEY   = 'snoop.spy'
  TRACE_ROUTING_KEY = 'snoop.trace'

  MESH_EXCHANGE     = 'miros.mesh.exchange'
  SPY_EXCHANGE      = 'miros.snoop.spy.exchange'
  TRACE_EXCHANGE    = 'miros.snoop.trace.exchange'

  CONNECTION_ATTEMPTS    = 3
  HEARTBEAT_INTERVAL_SEC = 3600
  PORT                   = 5672

  def __init__(self,
                miros_object,
                rabbit_user,
                rabbit_password,
                mesh_encryption_key,
                tx_routing_key,
                rx_routing_key=None,
                on_mesh_rx=None,
                on_spy_rx=None,
                on_trace_rx=None,
                spy_snoop_encryption_key=None,
                trace_snoop_encryption_key=None,
                addresses=None):

    self.name = miros_object.name

    self.this = Attribute()
    self.mesh = Attribute()

    self.snoop = Attribute()
    self.snoop.spy = Attribute()
    self.snoop.trace = Attribute()
    self.producers_queue = ThreadQueue()

    self.mesh.encryption_key = mesh_encryption_key
    self._rabbit_user = rabbit_user
    self._rabbit_password = rabbit_password
    self._this_ip_address = LocalAreaNetwork.get_working_ip_address()

    if spy_snoop_encryption_key is None:
      self.snoop.spy.encryption_key = mesh_encryption_key
    else:
      self.snoop.spy.encryption_key = spy_snoop_encryption_key

    if trace_snoop_encryption_key is None:
      self.snoop.trace.encryption_key = mesh_encryption_key
    else:
      self.snoop.trace.encryption_key = trace_snoop_encryption_key

    self.mesh.tx_routing_key = tx_routing_key

    if rx_routing_key is None:
      self.mesh.rx_routing_key = tx_routing_key
    else:
      self.mesh.rx_routing_key = rx_routing_key

    self.snoop.spy.routing_key   = MirosNets.SPY_ROUTING_KEY
    self.snoop.trace.routing_key = MirosNets.TRACE_ROUTING_KEY

    self.mesh.exchange_name        = MirosNets.MESH_EXCHANGE
    self.snoop.spy.exchange_name   = MirosNets.SPY_EXCHANGE
    self.snoop.trace.exchange_name = MirosNets.TRACE_EXCHANGE

    self.mesh.on_message_callback = \
      functools.partial(MirosNets.on_mesh_message_callback,
        custom_rx_callback=on_mesh_rx)

    self.snoop.spy.on_message_callback =  \
      functools.partial(MirosNets.on_snoop_spy_message_callback,
        custom_rx_callback=on_spy_rx)

    self.snoop.trace.on_message_callback = \
      functools.partial(MirosNets.on_snoop_trace_message_callback,
        custom_rx_callback=on_trace_rx)

    self.ip_addresses = []

    def custom_serializer(obj):
      ip_address = self._this_ip_address
      if isinstance(obj, Event):
        obj = Event.dumps(obj)
      pobj = pickle.dumps((ip_address, obj))
      return pobj

    def custom_deserializer(ppobj):
      tuple_ = pickle.loads(ppobj)
      ip_address = tuple_[0]
      pobj = tuple_[1]

      # search for aliens (SETI)
      if ip_address not in self.ip_addresses:
        print('Alien!: {}'.format(ip_address))
        hosts = [ip_address]
        amqp_urls = [RabbitHelper.make_amqp_url(
          ip_address=ip_address,
          rabbit_user=self._rabbit_user,
          rabbit_password=self._rabbit_password,
          connection_attempts=self.CONNECTION_ATTEMPTS,
          heartbeat_interval=self.HEARTBEAT_INTERVAL_SEC)]
        dispatcher = 'alien'
        payload = ConnectionDiscoveryPayload(
          hosts=hosts,
          amqp_urls=amqp_urls,
          dispatcher=dispatcher)
        self.producer_factory_chart.post_fifo(Event(signal=signals.CONNECTION_DISCOVERY, payload=payload))

      try:
        obj = Event.loads(pobj)
      except:
        obj = pobj
      return ip_address, obj

    self.mesh.serializer   = custom_serializer
    self.mesh.deserializer = custom_deserializer

    api_ok = True
    api_ok &= hasattr(miros_object.__class__, 'post_fifo')
    api_ok &= hasattr(miros_object.__class__, 'post_lifo')
    api_ok &= hasattr(miros_object.__class__, 'start_at')
    api_ok &= hasattr(miros_object.__class__, 'register_live_spy_callback')
    api_ok &= hasattr(miros_object.__class__, 'register_live_trace_callback')

    if api_ok is False:
      raise MirosApiException("miros_object {} doesn't have the required attributes".format(miros_object))

    # The producer factory chart will update the producers_queue with new
    # producers as they are found
    self.producer_factory_chart = ProducerFactoryChart(
      producers_queue=self.producers_queue,
      mesh_routing_key=self.mesh.tx_routing_key,
      mesh_exchange_name=self.mesh.exchange_name,
      mesh_serialization_function=self.mesh.serializer,
      snoop_trace_routing_key=self.snoop.trace.routing_key,
      snoop_trace_exchange_name=self.snoop.trace.exchange_name,
      snoop_spy_routing_key=self.snoop.spy.routing_key,
      snoop_spy_exchange_name=self.snoop.spy.exchange_name)

    self.mesh.producers = []
    self.snoop.spy.producers = []
    self.snoop.trace.producers = []

    this_address = LocalAreaNetwork.get_working_ip_address()
    self.this.url = RabbitHelper.make_amqp_url(
                      ip_address=this_address,
                      rabbit_user=rabbit_user,
                      rabbit_password=rabbit_password,
                      connection_attempts=self.CONNECTION_ATTEMPTS,
                      heartbeat_interval=self.HEARTBEAT_INTERVAL_SEC)

    self.build_mesh_consumer()
    self.build_snoop_consumers()

    self.snoop.spy.enabled = False
    self.snoop.trace.enabled = False
    self.mesh.started = False
    self.snoop.spy.started = False
    self.snoop.trace.started = False

  def enable_snoop_spy(self):
    self.snoop.spy.enabled = True

  def enable_snoop_trace(self):
    self.snoop.trace.enabled = True

  def start_threads(self):
    if self.mesh.started is False:
      for producer in self.mesh.producers:
        producer.start_thread()
      self.mesh.consumer.start_thread()
      self.mesh.started = True

    if self.snoop.spy.started is False and self.snoop.spy.enabled:
      for spy_producer in self.snoop.spy.producers:
        spy_producer.start_thread()
      self.snoop.spy.consumer.start_thread()
      self.snoop.spy.enabled = True

    if self.snoop.trace.started is False and self.snoop.trace.enabled:
      for trace_producer in self.snoop.trace.producers:
        trace_producer.start_thread()
      self.snoop.trace.consumer.start_thread()
      self.snoop.trace.enabled = True

  def stop_threads(self):
    if self.mesh.started is True:
      for producer in self.mesh.producers:
        producer.stop_thread()
      self.mesh.consumer.stop_thread()
      self.mesh.started = False

    if self.snoop.spy.started is True:
      for spy_producer in self.snoop.spy.producers:
        spy_producer.stop_thread()
      self.snoop.spy.consumer.stop_thread()
      self.snoop.spy.enabled = False

    if self.snoop.trace.started is True:
      for trace_producer in self.snoop.trace.producers:
        trace_producer.stop_thread()
      self.snoop.trace.consumer.stop_thread()
      self.snoop.trace.enabled = False

  def build_mesh_consumer(self):
    self.mesh.consumer = \
      PikaTopicConsumer(
        amqp_url=self.this.url,
        routing_key=self.mesh.rx_routing_key,
        exchange_name=self.mesh.exchange_name,
        message_callback=self.mesh.on_message_callback,
        deserialization_function=self.mesh.deserializer,
        encryption_key=self.mesh.encryption_key)

  def build_snoop_consumers(self):
    self.snoop.spy.consumer = \
      PikaTopicConsumer(
        amqp_url=self.this.url,
        routing_key=self.snoop.spy.routing_key,
        exchange_name=self.snoop.spy.exchange_name,
        message_callback=self.snoop.spy.on_message_callback,
        encryption_key=self.snoop.spy.encryption_key)
    self.snoop.trace.consumer = \
      PikaTopicConsumer(
        amqp_url=self.this.url,
        routing_key=self.snoop.trace.routing_key,
        exchange_name=self.snoop.trace.exchange_name,
        message_callback=self.snoop.trace.on_message_callback,
        encryption_key=self.snoop.trace.encryption_key)

  @staticmethod
  def on_mesh_message_callback(unused_channel, basic_deliver, properties, body, custom_rx_callback=None):
    if custom_rx_callback is None:
      print("Received mesh message # {} from {}: {}".format(
            basic_deliver.delivery_tag, properties.app_id, body))
    else:
      custom_rx_callback(unused_channel, basic_deliver, properties, body)

  @staticmethod
  def on_snoop_spy_message_callback(unused_channel, basic_deliver, properties, body, custom_rx_callback=None):
    if custom_rx_callback is None:
      print("Received snoop-spy message # {} from {}: {}".format(
            basic_deliver.delivery_tag, properties.app_id, body))
    else:
      custom_rx_callback(unused_channel, basic_deliver, properties, body)

  @staticmethod
  def on_snoop_trace_message_callback(unused_channel, basic_deliver, properties, body, custom_rx_callback=None):
    if custom_rx_callback is None:
      print("Received snoop-spy message # {} from {}: {}".format(
            basic_deliver.delivery_tag, properties.app_id, body))
    else:
      custom_rx_callback(unused_channel, basic_deliver, properties, body)

  def update_producers(self):
    discovered = False
    if not self.producers_queue.empty():
      q = self.producers_queue.get(block=False)
      for ip in q.ip_addresses:
        if ip not in self.ip_addresses:
          self.ip_addresses.append(ip)
      # if we have made producers before stop them now
      if self.mesh.producers:
        self.stop_threads()
      self.mesh.producers = q.mesh_producers
      self.snoop.trace.producers = q.snoop_trace_producers
      self.snoop.spy.producers = q.snoop_spy_producers
      discovered = True
    return discovered

  def transmit(self, event):
    self.update_producers()
    for producer in self.mesh.producers:
      producer.post_fifo(event)

  def broadcast_spy(self, message):
    for producer in self.snoop.spy.producers:
      producer.post_fifo(self.name + " " + message)

  def broadcast_trace(self, message):
    for producer in self.snoop.trace.producers:
      producer.post_fifo(message)

  def change_mesh_encyption_key(self, encryption_key):
    for producer in self.mesh.producers:
      producer.change_encyption_key(encryption_key)
    self.mesh.consumer.change_encyption_key(encryption_key)

  def change_spy_encyption_key(self, encryption_key):
    for producer in self.snoop.spy.producers:
      producer.change_encyption_key(encryption_key)
    self.snoop.spy.consumer.change_encyption_key(encryption_key)

  def change_trace_encyption_key(self, encryption_key):
    for producer in self.snoop.trace.producers:
      producer.change_encyption_key(encryption_key)
    self.snoop.trace.consumer.change_encyption_key(encryption_key)

class AnsiColors:
  BrightBlack = '\u001b[30;1m'
  BrightWhite = '\u001b[37;1m'
  Blue        = '\u001b[34m'
  Red         = '\u001b[31m'
  Purple      = '\u001b[35m'
  Reset       = '\u001b[0m'

  MyColor     = Blue
  OtherColor  = Purple

class MirosNetsInterface():

  def on_network_message(self, unused_channel, basic_deliver, properties, payload):
    ip_address, event = payload
    if isinstance(event, Event):
      #print("heard {} from {}".format(event.signal_name, ip_address))
      if event.payload != self.name:
        self.post_fifo(event)
    else:
      print("rx non-event {}".format(event))

  def transmit(self, event):
    self.nets.transmit(event)

  def enable_snoop_trace(self):
    self.live_trace = True
    self.register_live_trace_callback(self.nets.broadcast_trace)
    self.nets.enable_snoop_trace()

  def enable_snoop_spy(self):
    self.live_spy = True
    self.register_live_spy_callback(self.nets.broadcast_spy)
    self.nets.enable_snoop_spy()

  def snoop_scribble(self, message, enable_color=True):
    if not enable_color:
      named_message = "[{}] [{}] # {}".format(
          stdlib_datetime.strftime(stdlib_datetime.now(), "%Y-%m-%d %H:%M:%S.%f"),
          self.name,
          message)
    else:
      named_message = "[{}] [{}] {}# {}{}".format(
          stdlib_datetime.strftime(stdlib_datetime.now(), "%Y-%m-%d %H:%M:%S.%f"),
          self.name,
          AnsiColors.BrightBlack,
          message,
          AnsiColors.Reset)
    if self.nets.snoop.trace.enabled:
      self.nets.broadcast_trace(named_message)
    elif self.nets.snoop.spy.enabled:
      self.nets.broadcast_spy(named_message)
    else:
      self.scribble(named_message)

  def on_network_spy_message(self, ch, method, properties, body):
    if self.name in body:
      nbody = body.replace(self.name,
          "{color}{name}{reset}".format(color=AnsiColors.MyColor,
        name=self.name, reset=AnsiColors.Reset), 1)
    else:
      m = re.search('(.+? ){1}(.+)', body)
      try:
        other_name = m.group(1)
        nbody = body.replace(other_name,
            "{color}{name}{reset}".format(color=AnsiColors.OtherColor,
          name=other_name, reset=AnsiColors.Reset), 1)
      except:
        nbody = body
    '''create a on_network_trace_message function received messages in the queue'''
    print(" [+s] {}".format(nbody))

  def on_network_trace_message(self, ch, method, properties, body):
    if self.name in body:
      nbody = body.replace(self.name,
          "{color}{name}{reset}".format(color=AnsiColors.MyColor,
        name=self.name, reset=AnsiColors.Reset), 1)
    else:
      m = re.search('(\[.+?\] ){1}\[(.+)\]', body)
      try:
        other_name = m.group(2)
        nbody = body.replace(other_name,
            "{color}{name}{reset}".format(color=AnsiColors.OtherColor,
          name=other_name, reset=AnsiColors.Reset), 1)
      except:
        nbody = body
    '''create a on_network_trace_message function received messages in the queue'''
    print(" [+t] {}".format(nbody.replace('\n', '')))

  def on_network_spy_message_no_color(self, ch, method, properties, body):
    print(" [+s] {}".format(body))

  def on_network_trace_message_no_color(self, ch, method, properties, body):
    print(" [+t] {}".format(body.replace('\n', '')))

  def enable_snoop_spy_no_color(self):
    self.nets.snoop.spy.on_message_callback = \
      functools.partial(
        MirosNets.on_snoop_spy_message_callback,
        custom_rx_callback=self.on_network_spy_message_no_color)
    self.nets.build_snoop_consumers()
    self.enable_snoop_spy()

  def enable_snoop_trace_no_color(self):
    self.nets.snoop.trace.on_message_callback = \
      functools.partial(
        MirosNets.on_snoop_trace_message_callback,
        custom_rx_callback=self.on_network_trace_message_no_color)
    self.nets.build_snoop_consumers()
    self.enable_snoop_trace()

  def this_url(self):
    '''Get this ampq URL'''
    return self.nets.this.url

  def other_urls(self):
    '''Get IP addresses which have a RabbitMQ server running on them'''
    return self.nets.scout.other.urls


class NetworkedActiveObject(ActiveObject, MirosNetsInterface):
  '''
    **Example**:

    .. code-block:: python

      print(oa.lan.other.addresses) => \\
        ['192.168.1.66',
        '192.168.1.69',
        '192.168.1.70',
        '192.168.1.71',
        '192.168.1.254']

      print(oa.lan.this.address)  # => '192.168.1.75'

      print(oa.lan.get_working_ip_address()) # => \\
        '192.168.1.75'
  '''
  def __init__(self,
                name,
                rabbit_user,
                rabbit_password,
                mesh_encryption_key,
                tx_routing_key=None,
                rx_routing_key=None,
                spy_snoop_encryption_key=None,
                trace_snoop_encryption_key=None):
    super().__init__(name)
    self.lan = LocalAreaNetwork()

    on_message_callback = functools.partial(self.on_network_message)
    on_trace_message_callback = functools.partial(self.on_network_trace_message)
    on_spy_message_callback = functools.partial(self.on_network_spy_message)

    if tx_routing_key is None:
      tx_routing_key = "empty"

    if rx_routing_key is None:
      rx_routing_key = tx_routing_key

    if trace_snoop_encryption_key is None:
      trace_snoop_encryption_key = mesh_encryption_key

    if spy_snoop_encryption_key is None:
      spy_snoop_encryption_key = mesh_encryption_key

    self.nets = MirosNets(miros_object = self,
                 rabbit_user=rabbit_user,
                 rabbit_password=rabbit_password,
                 mesh_encryption_key=mesh_encryption_key,
                 trace_snoop_encryption_key=trace_snoop_encryption_key,
                 spy_snoop_encryption_key=spy_snoop_encryption_key,
                 tx_routing_key=tx_routing_key,
                 rx_routing_key=rx_routing_key,
                 on_mesh_rx=on_message_callback,
                 on_trace_rx=on_trace_message_callback,
                 on_spy_rx=on_spy_message_callback)


  def start_at(self, initial_state):
    while not self.nets.mesh.producers:
      time.sleep(0.1)
      self.nets.update_producers()
    super().start_at(initial_state)
    time.sleep(0.1)
    self.nets.start_threads()

class NetworkedFactory(Factory, MirosNetsInterface):
  '''
    **Example**:

    .. code-block:: python

      print(af.lan.other.addresses) => \\
        ['192.168.1.66',
        '192.168.1.69',
        '192.168.1.70',
        '192.168.1.71',
        '192.168.1.254']

      print(af.lan.this.address)  # => '192.168.1.75'

      print(af.lan.get_working_ip_address()) # => \\
        '192.168.1.75'
  '''
  def __init__(self,
                name,
                rabbit_user,
                rabbit_password,
                mesh_encryption_key,
                tx_routing_key=None,
                rx_routing_key=None,
                spy_snoop_encryption_key=None,
                trace_snoop_encryption_key=None):
    super().__init__(name)

    on_message_callback = functools.partial(self.on_network_message)
    on_trace_message_callback = functools.partial(self.on_network_trace_message)
    on_spy_message_callback = functools.partial(self.on_network_spy_message)

    if tx_routing_key is None:
      tx_routing_key = "empty"

    if rx_routing_key is None:
      rx_routing_key = tx_routing_key

    if trace_snoop_encryption_key is None:
      trace_snoop_encryption_key = mesh_encryption_key

    if spy_snoop_encryption_key is None:
      spy_snoop_encryption_key = mesh_encryption_key

    self.nets = MirosNets(miros_object = self,
                 rabbit_user=rabbit_user,
                 rabbit_password=rabbit_password,
                 mesh_encryption_key=mesh_encryption_key,
                 trace_snoop_encryption_key=trace_snoop_encryption_key,
                 spy_snoop_encryption_key=spy_snoop_encryption_key,
                 tx_routing_key=tx_routing_key,
                 rx_routing_key=rx_routing_key,
                 on_mesh_rx=on_message_callback,
                 on_trace_rx=on_trace_message_callback,
                 on_spy_rx=on_spy_message_callback)

  def start_at(self, initial_state):
    super().start_at(initial_state)
    time.sleep(0.1)
    self.nets.start_threads()


if __name__ == '__main__':

  from miros.activeobject import ActiveObject
  lan = LocalAreaNetwork()
  print(lan.this.address)
  print(lan.addresses)
  print(lan.other.addresses)
  name = uuid.uuid4().hex[0:2]
  print("I am {}".format(name))

