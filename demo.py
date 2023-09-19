from core import SeerSDK
from common import *
from objects import *

import json
import os
import shutil

# HELPER FUNCTIONS
def log(fn):
    try:
        print(json.dumps(fn, indent=4))
    except:
        print(fn)

def delete_directory(download_path):
    tmpdir = os.path.join(os.path.abspath("."), download_path)
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    
# SDK INSTANCE
INSTANCE = "staging"

credentials = { 
    "staging": ["Tenant-admin", "Abcd1234*"],
    "dev": ["gnu403", "Test!234567"],
    "US": ["css_apps_lab", "QXX!chqN!GswA9M"],
    "EU": ["", ""]
}

if INSTANCE in credentials:
    USERNAME = credentials[INSTANCE][0]
    PASSWORD = credentials[INSTANCE][1]
else:
    raise Exception("Invalid instance")

sdk = SeerSDK(USERNAME, PASSWORD, INSTANCE)