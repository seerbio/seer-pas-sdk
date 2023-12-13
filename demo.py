from core import SeerSDK
from common import *
from objects import *

import json
import os
import shutil

import random
import string
import datetime

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
    
def id_generator(size=4, chars=string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))

def get_timestamp():
    return datetime.datetime.now().strftime("%I%M%p%B%d")
    
# SDK INSTANCE
INSTANCE = "staging"

if __name__ == "__main__":
    credentials = { 
        "staging": { 
            "username": "Tenant-admin",
            "password": "Abcd1234*"
        },
        "dev": {
            "username": "gnu403",
            "password": "Test!234567"
        },
        "US": {
            "username": "css_apps_lab",
            "password": "QXX!chqN!GswA9M"
        },
        "EU": {
            "username": "",
            "password": ""

        }
    }

    if INSTANCE in credentials:
        credential = credentials[INSTANCE]
        USERNAME = credential["username"]
        PASSWORD = credential["password"]
    else:
        raise Exception("Invalid instance")

    sdk = SeerSDK(USERNAME, PASSWORD, INSTANCE)

    # GROUP ANALYSIS TEST ON STAGING
    '''
    analysis_id = "51272fc0-ee5b-11ec-add5-e3b76893df8c"
    another_analysis_id = "b757f170-b505-11eb-892d-4fc7da6e25ac"
    a = sdk.group_analysis(analysis_id)
    '''
    
    # SAMPLE DESCRIPTION FILE TESTING ON STAGING
    '''
    ms_data_files = ["testing/AgamSDKTest1.raw", "testing/AgamSDKTest2.raw"]
    plate_map_file = "testing/AgamSDKPlateMapATest.csv"
    sample_description_file = "testing/AgamSDKSampleDesc.csv"
    plate_id = id_generator()
    plate_name = f"SDK TEST {get_timestamp()}"

    log(sdk.add_plate(ms_data_files=ms_data_files, plate_map_file=plate_map_file, sample_description_file=sample_description_file, plate_id=plate_id, plate_name=plate_name))
    '''

    # LINK PLATE TEST ON STAGING
    '''
    ms_data_files = ["06b8f7a0-7aa2-11ee-818c-cb54538128f7/20231103233801265/AgamSDKTest1.raw", "06b8f7a0-7aa2-11ee-818c-cb54538128f7/20231103233801265/AgamSDKTest2.raw"]

    plate_map_file = "testing/AgamSDKPlateMapATest.csv"
    plate_id = id_generator()
    plate_name = f"SDK TEST {get_timestamp()}"

    log(sdk.link_plate(ms_data_files, plate_map_file, plate_id, plate_name))
    '''

    # START ANALYSIS TEST ON STAGING
    '''
    name = f"SDK-ANALYSIS-TEST {get_timestamp()}"
    project_id = "a25d8730-797f-11ee-89e6-1bcbdb3e06c8"
    analysis_protocol_id = "b07d70f0-5471-11ea-90e8-6743ed53f19f"

    sample_ids = ["45b67430-5624-11ed-89d5-a3468e22373d",
        "45b589d0-5624-11ed-827a-4571ceca6571",
        "45b562c0-5624-11ed-9546-b77bc04130a6",
        "45b589d0-5624-11ed-9f09-c9a8878b12a7",
        "45b7acb0-5624-11ed-892a-47ea6cce1e36"]

    log(sdk.start_analysis(name, project_id,  sample_ids[2:], analysis_protocol_id=analysis_protocol_id))
    '''