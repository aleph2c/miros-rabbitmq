import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
if env_path.is_file():
  load_dotenv(env_path)
else:
  # recurse outward to find .env file
  load_dotenv()

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

LoadEnvironmentalVariables()

RABBIT_USER = os.getenv('RABBIT_USER')
RABBIT_PORT = os.getenv('RABBIT_PORT')
RABBIT_PASSWORD = os.getenv('RABBIT_PASSWORD')
MESH_ENCRYPTION_KEY = os.getenv('MESH_ENCRYPTION_KEY')
SNOOP_SPY_ENCRYPTION_KEY = os.getenv('SNOOP_SPY_ENCRYPTION_KEY')
SNOOP_TRACE_ENCRYPTION_KEY = os.getenv('SNOOP_TRACE_ENCRYPTION_KEY')

if __name__ == '__main__':
  # cache_chart = CacheFileChart(live_trace=True)
  pass
