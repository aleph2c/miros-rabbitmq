import os
from dotenv import load_dotenv
from pathlib import Path
import json
import time
import functools
from datetime import datetime, timedelta

from os import F_OK, W_OK
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR
import uuid
from miros import Factory
from miros import signals, Event, return_status
from miros import pp
import random
from miros_rabbitmq.network import PikaTopicPublisher
from miros_rabbitmq.network import RabbitHelper

env_path = Path('.') / '.env'
load_dotenv()

MESH_ENCRYPTION_KEY = os.getenv("MESH_ENCRYPTION_KEY")
SNOOP_TRACE_ENCRYPTION_KEY = os.getenv("SNOOP_TRACE_ENCRYPTION_KEY")
SNOOP_SPY_ENCRYPTION_KEY = os.getenv("SNOOP_SPY_ENCRYPTION_KEY")
RABBIT_USER = os.getenv("RABBIT_USER")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD")

class ScoutMemory():
  default_structure = """{
  "nodes": {
    "automatic": {
      "addresses": [],
      "amqp_urls": []
    },
    "manual": {
      "live" : {
        "addresses": [],
        "amqp_urls": []
      },
      "dead" : {
        "addresses": [],
        "amqp_urls": []
      }
    }
  },
  "time_out_in_minutes": 30
}
"""

  def __init__(self, cache_file_path=None):
    '''Create a scout memory object using an optional cache_file_path

    The rules which govern this cache file are simple:
      * An address and it's amqp_url can only exist in either the manual live or
        manual dead node, it can not exist in both at the same time.
      * An address/amqp_url can only be listed once in any of the automatic, manual-live,
        or manual-dead collections.  None of these collections will have
        duplicates

    To build the a scout memory object:

      scout_memory = ScoutMemory(<path_to_your_cache_file>)

      If this <path_to_your_cache_file> is None then a default file called
      '.miros_rabbitmq_cache.json' will be made in the directory that you
      building this object from.

    '''
    if cache_file_path is None:
      self.cache_file_name = str(Path('.') / '.miros_rabbitmq_cache.json')
    else:
      self.cache_file_name = cache_file_path

    # check if file exists, if not make it with nothing in it
    if not os.path.isfile(self.cache_file_name):
      open(self.cache_file_name, 'a').close()

    # if the cache is empty write a default structure
    if os.path.getsize(self.cache_file_name) is 0:
      with open(self.cache_file_name, "w") as f:
        f.write(ScoutMemory.default_structure)

    self.dict = json.load(open(self.cache_file_name, 'r'))

  def addesses_and_amqp_urls_for(self, automatic=None, manual=None, live=None, dead=None):
    '''Get the addresses and amqp_urls for node

    The contract rules for this method are:
      automatic and not manual or not automatic and manual
      if manual then
        live and not dead or not live and dead
    '''

    assert((automatic and not manual) or (not automatic and manual))
    if manual:
      assert((live and not dead) or(not live and dead))

    if automatic:
      addresses = self.dict['nodes']['automatic']['addresses']
      amqp_urls = self.dict['nodes']['automatic']['amqp_urls']
    elif manual:
      if live:
        addresses = self.dict['nodes']['manual']['live']['addresses']
        amqp_urls = self.dict['nodes']['manual']['live']['amqp_urls']
      elif dead:
        addresses = self.dict['nodes']['manual']['dead']['addresses']
        amqp_urls = self.dict['nodes']['manual']['dead']['amqp_urls']
    return (addresses, amqp_urls)

  def append(self, address, amqp_url, automatic=None, manual=None, live=None, dead=None):
    '''Append an address or amqp_url to a node'''

    changed = False
    addresses, amqp_urls = self.addesses_and_amqp_urls_for(automatic, manual, live, dead)

    if address is not None and (address in addresses) is False:
      addresses.append(address)
      changed |= True
    if amqp_url is not None and (amqp_url in amqp_urls) is False:
      amqp_urls.append(amqp_url)
      changed |= True
    if changed:
      self.write()

  def in_cache(self, address, amqp_url, automatic=None, manual=None, live=None, dead=None):
    '''Is an address or amqp_url in a given cache?'''
    addresses, amqp_urls = self.addesses_and_amqp_urls_for(automatic, manual, live, dead)
    in_cache = False

    if address in addresses:
      in_cache |= True

    if amqp_url in amqp_urls:
      in_cache |= True

    return in_cache

  def in_automatic_cache(self, address, amqp_url):
    '''Is an address or amqp_url in the automatic cache?'''
    in_cache_fn = functools.partial(self.in_cache, automatic=True)
    result = in_cache_fn(address, amqp_url)
    return result

  def in_manual_live_cache(self, address, amqp_url):
    '''Is an address or amqp_url in the manual live cache?'''
    in_cache_fn = functools.partial(self.in_cache, manual=True, live=True)
    result = in_cache_fn(address, amqp_url)
    return result

  def in_manual_dead_cache(self, address, amqp_url):
    '''Is an address or amqp_url in the manual dead cache?'''
    in_cache_fn = functools.partial(self.in_cache, manual=True, dead=True)
    result = in_cache_fn(address, amqp_url)
    return result

  def remove(self, address, amqp_url, automatic=None, manual=None, live=None, dead=None):
    '''Remove an address or amqp_url to a node'''
    changed = False
    addresses, amqp_urls = self.addesses_and_amqp_urls_for(automatic, manual, live, dead)

    if address is not None and (address in addresses) is False:
      addresses.remove(address)
      changed |= True
    if amqp_url is not None and (amqp_url in amqp_urls) is False:
      amqp_urls.remove(amqp_url)
      changed |= True
    if changed:
      self.write()

  def append_automatic(self, address=None, amqp_url=None):
    '''Append an address or amqp_url to the automatic node'''
    append = functools.partial(self.append, automatic=True)
    append(address, amqp_url)

  def append_manual_live(self, address=None, amqp_url=None):
    '''Append an address or amqp_url to a manual live node

    If this address and or amqp_url exists in the manual dead node, it is
    removed'''
    append_to_live = functools.partial(self.append, manual=True, live=True)
    remove_from_dead = functools.partial(self.remove, manual=True, dead=True)
    append_to_live(address, amqp_url)
    remove_from_dead(address, amqp_url)

  def append_manual_dead(self, address=None, amqp_url=None):
    '''Append an address or amqp_url to a manual dead node

    If this address and or amqp_url exists in the manual live node, it is
    removed'''
    append_to_dead = functools.partial(self.append, manual=True, dead=True)
    remove_from_live = functools.partial(self.remove, manual=True, live=True)
    append_to_dead(address, amqp_url)
    remove_from_live(address, amqp_url)

  def write(self, addresses=None, ampq_urls=None):
    '''Write the cache file to disk'''
    with open(self.cache_file_name, "w") as f:
      f.write(json.dumps(self.dict, sort_keys=True, indent=2))

  def remove_all_automatic(self):
    '''Remove all automatic addresses and amqp_urls from the automatic node'''
    automatic_nodes = self.dict['nodes']['automatic']
    automatic_nodes['addresses'] = []
    automatic_nodes['amqp_urls'] = []
    self.write()

  def remove_all_dead(self):
    '''Remove all automatic addresses and amqp_urls from the manual dead node'''
    automatic_nodes = self.dict['nodes']['manual']['dead']
    automatic_nodes['addresses'] = []
    automatic_nodes['amqp_urls'] = []
    self.write()

  def destroy(self):
    '''Delete the cache file all addresses and amqp_urls will be destroyed'''
    self.dict = {}
    os.remove(self.cache_file_name)

  def last_modified(self):
    '''Return when the cache file was last modified'''
    return time.ctime(os.path.getmtime(self.cache_file_name))

  def created_at(self):
    '''Return when the cache file was created'''
    return time.ctime(os.path.getctime(self.cache_file_name))

  def cached_expired(self):
    '''Using the "time_out_in_minutes" value in the cache file, determine if the
    cache file has expired'''
    last_modified = datetime.fromtimestamp(os.path.getmtime(self.cache_file_name))
    duration = datetime.now() - last_modified
    timeout = timedelta(minutes=self.dict['time_out_in_minutes'])
    is_expired = False
    if duration > timeout:
      is_expired = True
    return is_expired

class CacheFile(Factory):
  def __init__(self, name, file_path, system_read_signal_name=None):
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
      is_expired = False
      if duration > timeout:
        is_expired = True
    except:
      is_expired = False
    return is_expired


class CacheFileChart(CacheFile):
  def __init__(self, file_path=None, live_trace=None, live_spy=None):
    if file_path is None:
      file_path = str(Path('.') / '.miros_rabbitmq_cache.json')

    super().__init__('network_cache', file_path=file_path)

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
      live_trace = True
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy
    self.start_at(self.file_access_waiting)
    time.sleep(0.1)
    self.post_fifo(Event(signal=signals.CACHE_FILE_READ))

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

    # check if file exists, if not make it with nothing in it
    if not os.path.isfile(cache.file_path):
      open(cache.file_path, 'a').close()
    return return_status.HANDLED

  @staticmethod
  def faw_CACHE_FILE_READ(cache, e):
    '''The file_access_waiting state global CACHE_FILE_READ event handler'''
    cache.post_fifo(Event(signal=signals.cache_file_read, payload={'times': 0}))
    return return_status.HANDLED

  @staticmethod
  def faw_CACHE_FILE_WRITE(cache, e):
    '''The file_access_waiting state global CACHE_FILE_WRITE event handler'''
    cache.json = e.payload  # kept for debugging
    cache.dict = json.load(open(cache.file_path, 'r'))
    cache.post_fifo(Event(signal=signals.cache_file_write, payload={'times': 0, 'dict': cache.dict}))
    return return_status.HANDLED

  @staticmethod
  def faw_CACHE_DESTROY(cache, e):
    '''The file_access_waiting state global faw_CACHE_DESTROY event handler'''
    cache.post_fifo(Event(signal=signals.cache_file_write, payload=""))
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
    payload = {
      'dict': cache.dict,
      'last_modified': cache.last_modified,
      'created_at': cache.created_at,
      'expired': cache.expired()
    }
    cache.post_fifo(Event(signal=signals.CACHE, payload=payload))
    cache.post_lifo(Event(signal=signals.read_successful))
    pp(cache.json)
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
    temp_file = cache.temp_file_name()
    status = return_status.HANDLED
    f = open(temp_file, "w")
    cache.json = json.dumps(e.payload, sort_keys=True, indent=2)
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

    self.ip_address = ip_address
    self.routing_key = routing_key
    self.exchange_name = exchange_name
    if os.getenv('RABBIT_PASSWORD') is None:
      load_dotenv()  # climb out of this dir to find dir containing .env file

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

    self.amqp_url = RabbitHelper.make_amqp_url(
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

class RabbitConsumerScout(Factory):
  CONNECTION_ATTEMPTS    = 1

  SCOUT_TEMPO_SEC        = 0.01
  SCOUT_TIMEOUT_SEC      = 0.5

  def __init__(self, ip_address, routing_key, exchange_name):
    super().__init__(ip_address)

    self.ip_address = ip_address
    self.routing_key = routing_key
    self.exchange_name = exchange_name

class RabbitConsumerScoutChart(RabbitConsumerScout):
  def __init__(self, ip_address, routing_key, exchange_name, live_trace=None, live_spy=None):
    super().__init__(ip_address, routing_key, exchange_name)

    self.search = self.create(state='search'). \
      catch(signal=signals.ENTRY_SIGNAL, handler=self.search_entry). \
      catch(signal=signals.REFACTOR_SEARCH, handler=self.search_refactor_search). \
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
      live_trace = True
    else:
      live_trace = live_trace

    if live_spy is None:
      live_spy = False
    else:
      live_spy = live_spy

    self.live_trace = live_trace
    self.live_spy = live_spy
    self.start_at(self.search)
    time.sleep(0.1)

  @staticmethod
  def search_entry(scout, e):
    status = return_status.HANDLED
    scout.producer = PikaTopicPublisherMaker(
        ip_address=scout.ip_address,
        routing_key=scout.routing_key,
        exchange_name=scout.exchange_name,
        connection_attempts=RabbitConsumerScout.CONNECTION_ATTEMPTS,
        callback_tempo=RabbitConsumerScout.SCOUT_TEMPO_SEC).producer
    scout.subscribe(Event(signals.REFACTOR_SEARCH))
    return status

  @staticmethod
  def search_AMPQ_CONSUMER_CHECK(scout, e):
    status = return_status.HANDLED
    if scout.live_trace or scout.live_spy:
      pp(e.payload)
    return status

  @staticmethod
  def search_refactor_search(scout, e):
    status = return_status.HANDLED
    if 'ip_address' in e.payload and scout.name is e.payload['ip_address']:
      for item in ['routing_key', 'exchange_name']:
        if item in e.payload:
          setattr(scout, item, e.payload[item])
    status = scout.trans(scout.search)
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
      period=0.5,
      deferred=True
    )
    return status

  @staticmethod
  def amqp_consumer_server_found_entry(scout, e):
    status = return_status.HANDLED
    scout.post_fifo(Event(signal=signals.AMQP_CONSUMER_CHECK,
      payload=(scout.ip_address, True, scout.routing_key, scout.exchange_name)))
    return status

  @staticmethod
  def no_amqp_consumer_server_found_entry(scout, e):
    status = return_status.HANDLED
    scout.post_fifo(Event(signal=signals.AMQP_CONSUMER_CHECK,
      payload=(scout.ip_address, False, scout.routing_key, scout.exchange_name)))
    return status


if __name__ == '__main__':
  cache_chart = CacheFileChart(live_trace=True)
  time.sleep(1)
  cache_chart.post_fifo(Event(signal=signals.CACHE_FILE_READ))
  #scout1 = RabbitConsumerScoutChart(
  #          '192.168.1.69',
  #          'heya.man',
  #          'miros.mesh.exchange',
  #          live_trace = True)
  scout2 = RabbitConsumerScoutChart(
            '192.168.1.77',
            'heya.man',
            'miros.mesh.exchange',
            live_trace = True)
  #scout3 = RabbitConsumerScoutChart(
  #          '192.168.1.75',
  #          'heya.man',
  #          'miros.mesh.exchange',
  #          live_trace = True)
  time.sleep(1)
  del(scout2)
  time.sleep(3)

  #sm = ScoutMemory()
  #sm.append_automatic(address='192.168.1.74')
  #sm.append_manual_live(address='192.168.1.74')
  #sm.append_manual_dead(address='192.168.1.74')
  # sm.remove_all_automatic()
  #print("expired? {}".format(sm.cached_expired()))
  #print("{}".format(sm.created_at()))

  # network memory
  #   entry:
  #    create cache file chart
  #    request read
  #   Cache:
  #    !expired:
  #      update addresses/calculate AMQP urls
  #    experied:
  #      discover_network
  #   discover_network
  #     entry:
  #       create recon object
  #       wait for NETWORK_RESULTS
  #       created dict object
  #       post CACHE_WRITE
  #       broadcast cache
  #     
