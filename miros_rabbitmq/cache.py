import os
from pathlib import Path
import json
import time
from datetime import datetime, timedelta

from os import F_OK, W_OK
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR
import uuid
from miros import Factory
from miros import signals, Event, return_status
from miros import pp

import random

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

if __name__ == '__main__':
  cache_chart = CacheFileChart(live_trace=True)
  time.sleep(1)
  cache_chart.post_fifo(Event(signal=signals.CACHE_FILE_READ))
  time.sleep(200)
