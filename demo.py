from core import SeerSDK
from common import *
from objects import PlateMap

import json

def log(fn):
    try:
        print(json.dumps(fn, indent=4))
    except:
        print(fn)

USERNAME = "Tenant-admin" # "gnu403"
PASSWORD = "Abcd1234*" # "Test!234567"

sdk = SeerSDK(USERNAME, PASSWORD)

# TEST CODE GOES HERE
