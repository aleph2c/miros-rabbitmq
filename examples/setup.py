import os
from dotenv import load_dotenv
from pathlib import Path
import json
import time
import functools
from datetime import datetime, timedelta

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=str(env_path))

MESH_ENCRYPTION_KEY = os.getenv("MESH_ENCRYPTION_KEY")
SNOOP_TRACE_ENCRYPTION_KEY = os.getenv("SNOOP_TRACE_ENCRYPTION_KEY")
SNOOP_SPY_ENCRYPTION_KEY = os.getenv("SNOOP_SPY_ENCRYPTION_KEY")
RABBIT_USER = os.getenv("RABBIT_USER")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD")

class ScoutMemory():
  default_structure = """{
  "nodes": {
    "private": {
      "addresses": [],
      "amqp_urls": []
    },
    "public": {
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
      * An address and it's amqp_url can only exist in either the public live or
        public dead node, it can not exist in both at the same time.
      * An address/amqp_url can only be listed once in any of the private, public-live,
        or public-dead collections.  None of these collections will have
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

  def addesses_and_amqp_urls_for(self, private=None, public=None, live=None, dead=None):
    '''Get the addresses and amqp_urls for node

    The contract rules for this method are:
      private and not public or not private and public
      if public then
        live and not dead or not live and dead
    '''

    assert((private and not public) or (not private and public))
    if public:
      assert((live and not dead) or(not live and dead))

    if private:
      addresses = self.dict['nodes']['private']['addresses']
      amqp_urls = self.dict['nodes']['private']['amqp_urls']
    elif public:
      if live:
        addresses = self.dict['nodes']['public']['live']['addresses']
        amqp_urls = self.dict['nodes']['public']['live']['amqp_urls']
      elif dead:
        addresses = self.dict['nodes']['public']['dead']['addresses']
        amqp_urls = self.dict['nodes']['public']['dead']['amqp_urls']
    return (addresses, amqp_urls)

  def append(self, address, amqp_url, private=None, public=None, live=None, dead=None):
    '''Append an address or amqp_url to a node'''

    changed = False
    addresses, amqp_urls = self.addesses_and_amqp_urls_for(private, public, live, dead)

    if address is not None and (address in addresses) is False:
      addresses.append(address)
      changed |= True
    if amqp_url is not None and (amqp_url in amqp_urls) is False:
      amqp_urls.append(amqp_url)
      changed |= True
    if changed:
      self.write()

  def remove(self, address, amqp_url, private=None, public=None, live=None, dead=None):
    '''Remove an address or amqp_url to a node'''
    changed = False
    addresses, amqp_urls = self.addesses_and_amqp_urls_for(private, public, live, dead)

    if address is not None and (address in addresses) is False:
      addresses.remove(address)
      changed |= True
    if amqp_url is not None and (amqp_url in amqp_urls) is False:
      amqp_urls.remove(amqp_url)
      changed |= True
    if changed:
      self.write()

  def append_private(self, address=None, amqp_url=None):
    '''Remove an address or amqp_url to a private node'''
    append = functools.partial(self.append, private=True)
    append(address, amqp_url)

  def append_public_live(self, address=None, amqp_url=None):
    '''Append an address or amqp_url to a public live node

    If this address and or amqp_url exists in the public dead node, it is
    removed'''
    append_to_live = functools.partial(self.append, public=True, live=True)
    remove_from_dead = functools.partial(self.remove, public=True, dead=True)
    append_to_live(address, amqp_url)
    remove_from_dead(address, amqp_url)

  def append_public_dead(self, address=None, amqp_url=None):
    '''Append an address or amqp_url to a public dead node

    If this address and or amqp_url exists in the public live node, it is
    removed'''
    append_to_dead = functools.partial(self.append, public=True, dead=True)
    remove_from_live = functools.partial(self.remove, public=True, live=True)
    append_to_dead(address, amqp_url)
    remove_from_live(address, amqp_url)

  def write(self, addresses=None, ampq_urls=None):
    '''Write the cache file to disk'''
    with open(self.cache_file_name, "w") as f:
      f.write(json.dumps(self.dict, sort_keys=True, indent=2))

  def remove_all_private(self):
    '''Remove all private addresses and amqp_urls from the private node'''
    private_nodes = self.dict['nodes']['private']
    private_nodes['addresses'] = []
    private_nodes['amqp_urls'] = []
    self.write()

  def remove_all_dead(self):
    '''Remove all private addresses and amqp_urls from the public dead node'''
    private_nodes = self.dict['nodes']['public']['dead']
    private_nodes['addresses'] = []
    private_nodes['amqp_urls'] = []
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


if __name__ == '__main__':
  sm = ScoutMemory()
  sm.append_private(address='192.168.1.74')
  sm.append_public_live(address='192.168.1.74')
  sm.append_public_dead(address='192.168.1.74')
  # sm.remove_all_private()
  print("expired? {}".format(sm.cached_expired()))
  print("{}".format(sm.created_at()))

