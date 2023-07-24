import json
from core import SeerSDK
from common import *
from objects import PlateMap

def log(fn):
    try:
        print(json.dumps(fn, indent = 4))
    except:
        print(fn)

sdk = SeerSDK("Tenant-admin", "Abcd1234*")