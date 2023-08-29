from core import SeerSDK
from common import *

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
ENVIRONMENT = "staging" # change to `dev` 

if ENVIRONMENT == "staging":
    USERNAME = "Tenant-admin"
    PASSWORD = "Abcd1234*"
    os.environ["URL"] = "https://api.pas.seer-staging.com/"
else:
    USERNAME = "gnu403"
    PASSWORD = "Test!234567"
    os.environ["URL"] = "http://localhost:3006/"

sdk = SeerSDK(USERNAME, PASSWORD)


# TEST CODE BELOW
analysis_id = "271077a0-311c-11ee-a5ea-d92acb8672b3"
download_path = "downloads/"
delete_directory(download_path)