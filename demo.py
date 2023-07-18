import json
from core import SeerSDK
from common import *
from objects import PlateMap

def log(fn):
    try:
        print(json.dumps(fn, indent = 4))
    except:
        print(fn)

sdk = SeerSDK("gnu403", "Test!234567")

##### Add a plate
# log(sdk.add_plate(ms_filepaths, "testing/AgamSDKPlateMapATest.csv", "finalPlateIdTest", "finalPlateNameTest", f"Generated from SDK at {str(datetime.datetime.now())})"))