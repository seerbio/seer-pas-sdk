from core import SeerSDK
from common import *
from objects import PlateMap

import json

def log(fn):
    try:
        print(json.dumps(fn, indent=4))
    except:
        print(fn)

USERNAME = "gnu403" # "Tenant-admin"
PASSWORD = "Test!234567" # "Abcd1234*"

sdk = SeerSDK(USERNAME, PASSWORD)

# TEST CODE GOES HERE

"""
pd.set_option('display.width', 100)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

project_id = "7e48e150-8a47-11ed-b382-bf440acece26"
sample_project = sdk.get_project(project_id=project_id, msdata=True, df=True)
log(sample_project) 
"""