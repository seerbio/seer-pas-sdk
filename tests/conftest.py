"""
`conftest.py` -- common fixtures and other pytest config
"""

import pytest

from seer_pas_sdk import PlateMap


@pytest.fixture
def platemap():
    """A very basic platemap"""
    return PlateMap(
        ms_file_name=["test.raw"],
        sample_name=["TEST_sample_name"],
        sample_id=["TEST0"],
        well_location=["A1"],
        control=[None],
        plate_id=["TEST_plate_id"],
        plate_name=["TEST_plate_name"],
    )
