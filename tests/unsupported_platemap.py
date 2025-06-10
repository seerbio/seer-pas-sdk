# UNSUPPORTED TEST CASE

# import pandas as pd
# import pytest
# from tests.test_common import platemap_file

# from seer_pas_sdk.common import validate_plate_map


# class TestPlateMapValidation:

#     def test_validate_plate_map_valid(self, platemap_file):
#         """Test that validate_plate_map accepts a valid plate map"""

#         ms_data_files = {"test.raw"}
#         plate_map_data = pd.read_csv(platemap_file)
#         res = validate_plate_map(plate_map_data, ms_data_files)

#         assert res.equals(plate_map_data)

#     def test_validate_plate_map_missing_file(self, platemap_file):
#         """Test that validate_plate_map raises an exception if a file doesn't exist"""

#         ms_data_files = {"XXX_file_does_not_exist"}
#         plate_map_data = pd.read_csv(platemap_file)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(plate_map_data, ms_data_files)

#     def test_validate_plate_map_multiple_plate_ids_to_sample(self):
#         """Test that validate_plate_map raises an exception if a individual sample has multiple plate IDs"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw", "test2.raw"],
#                 "Sample name": ["TEST_sample_name", "TEST_sample_name"],
#                 "Sample ID": ["TEST1", "TEST1"],
#                 "Well location": ["A1", "A2"],
#                 "Control": [None, None],
#                 "Plate ID": ["TEST_plate_id", "TEST_plate_id2"],
#                 "Plate Name": ["TEST_plate_name", "TEST_plate_name2"],
#             }
#         )
#         ms_data_files = ["test.raw", "test2.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_validate_plate_map_missing_header(self):
#         """Test that validate_plate_map raises an exception if a required header is missing"""

#         no_plate_name = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_Sample Name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#             }
#         )
#         no_plate_id = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_Sample Name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         no_control = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_Sample Name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         no_well_location = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_Sample Name"],
#                 "Sample ID": ["TEST1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         no_sample_id = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_Sample Name"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         no_sample_name = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         no_file_name = pd.DataFrame(
#             {
#                 "Sample name": ["TEST_Sample Name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         ms_data_files = ["test.raw"]

#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_plate_name, ms_data_files)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_plate_id, ms_data_files)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_control, ms_data_files)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_well_location, ms_data_files)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_sample_id, ms_data_files)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_sample_name, ms_data_files)
#         with pytest.raises(ValueError):
#             res = validate_plate_map(no_file_name, ms_data_files)

#     def test_validate_plate_map_invalid_rawfile_name(self):
#         """Test that validate_plate_map raises an exception if a file name is not in the ms_data_files"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw2"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate name": ["TEST_plate_name"],
#             }
#         )
#         ms_data_files = ["test.raw2"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_plate_id_entity_name(self):
#         """Test that validate_plate_map raises an exception if a plate_id is not a valid entity name"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id&"],
#                 "Plate Name": ["TEST_plate_name"],
#             }
#         )
#         ms_data_files = ["test.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_plate_name_entity_name(self):
#         """Test that validate_plate_map raises an exception if a plate_name is not a valid entity name"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name~"],
#             }
#         )
#         ms_data_files = ["test.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_sample_volume_numeric(self):
#         """Test that validate_plate_map raises an exception if a sample_volume is not numeric"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#                 "Sample volume": ["TEST_sample_volume"],
#             }
#         )
#         ms_data_files = ["test.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_peptide_concentration_numeric(self):
#         """Test that validate_plate_map raises an exception if a peptide_concentration is not numeric"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#                 "Peptide concentration": ["TEST_peptide_concentration"],
#             }
#         )
#         ms_data_files = ["test.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_peptide_mass_sample_numeric(self):
#         """Test that validate_plate_map raises an exception if a peptide_mass_sample is not numeric"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#                 "Peptide mass sample": ["TEST_peptide_mass_sample"],
#             }
#         )
#         ms_data_files = ["test.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)

#     def test_recon_volume_numeric(self):
#         """Test that validate_plate_map raises an exception if a recon_volume is not numeric"""

#         data = pd.DataFrame(
#             {
#                 "MS file name": ["test.raw"],
#                 "Sample name": ["TEST_sample_name"],
#                 "Sample ID": ["TEST1"],
#                 "Well location": ["A1"],
#                 "Control": [None],
#                 "Plate ID": ["TEST_plate_id"],
#                 "Plate Name": ["TEST_plate_name"],
#                 "Recon volume": ["TEST_recon_volume"],
#             }
#         )
#         ms_data_files = ["test.raw"]
#         with pytest.raises(ValueError):
#             res = validate_plate_map(data, ms_data_files)
