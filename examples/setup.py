import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=str(env_path))

MESH_ENCRYPTION_KEY = os.getenv("MESH_ENCRYPTION_KEY")
SNOOP_TRACE_ENCRYPTION_KEY = os.getenv("SNOOP_TRACE_ENCRYPTION_KEY")
SNOOP_SPY_ENCRYPTION_KEY = os.getenv("SNOOP_SPY_ENCRYPTION_KEY")
