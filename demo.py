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

""" 
data_file_locations = ["testing/AgamSDKTest1.raw", "testing/AgamSDKTest2.raw"]
sample_plate_id= "unique223id"
sample_plate_name = "some_plate_name" 

generated_plate_map_file = PlateMap(
    ms_file_name =["AgamSDKTest1.raw", "AgamSDKTest2.raw"],
    sample_name = ["A111", "A112"], 
    sample_id = ["A111", "A112"], 
    well_location = ["C11, D11"], 
    nanoparticle = ["NONE"], 
    nanoparticle_id = ["NONE"], 
    control = ["MPE Control"], 
    control_id = ["MPE Control"], 
    sample_volume = [20], 
    peptide_concentration = [59.514], 
    peptide_mass_sample = [8.57], 
    dilution_factor = [1], 
    plate_id = ["A11", "A11"], 
    plate_name = ["A11", "A11"] 
)

log(sdk.add_plate(data_file_locations, generated_plate_map_file, sample_plate_id, sample_plate_name))
"""

##### Add a plate
# log(sdk.add_plate(ms_filepaths, "testing/AgamSDKPlateMapATest.csv", "finalPlateIdTest", "finalPlateNameTest", f"Generated from SDK at {str(datetime.datetime.now())})"))