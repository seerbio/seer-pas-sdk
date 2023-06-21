import json
from core import SeerSDK
from common import *

def log(fn):
    try:
        print(json.dumps(fn, indent = 4))
    except:
        print(fn)

sdk = SeerSDK("gnu403", "Test!234567")

plate_id = "7ec8cad0-15e0-11ee-bdf1-bbaa73585acf" # random plate_id
project_id = "7e48e150-8a47-11ed-b382-bf440acece26" # random project_id

##### Add a plate
# log(sdk.add_plate(["testing/AgamSDKTest1.raw", "testing/AgamSDKTest2.raw"], "testing/AgamSDKPlateMapATest.csv", "finalPlateIdTest", "finalPlateNameTest", f"Generated from SDK at {str(datetime.datetime.now())})"))