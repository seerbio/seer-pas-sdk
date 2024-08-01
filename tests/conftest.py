"""
`conftest.py` -- common fixtures and other pytest config
"""

import pytest

from seer_pas_sdk import PlateMap


@pytest.fixture
def platemap():
    """A very basic platemap"""
    return PlateMap(
        ms_file_name=["test.msfile"],
        sample_name=["TEST_sample_name"],
        sample_id=["TEST0"],
    )
