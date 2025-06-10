from io import StringIO

import pandas as pd
import pytest

from seer_pas_sdk import PlateMap


def test_toofew_items():
    """Test passing too few items to one or more attributes"""
    filenames = ["test_0.msfile", "test_1.msfile"]
    samplenames = ["TEST_sample_name"]
    platemap = PlateMap(
        ms_file_name=filenames.copy(),  # prevent mutating shared state
        sample_name=samplenames.copy(),  # prevent mutating shared state
    )

    assert len(platemap.ms_file_name) == len(filenames)
    assert len(platemap.sample_name) == len(filenames)

    for i in range(len(platemap.sample_name)):
        assert (platemap.sample_name[i] == None) == (i >= len(samplenames))


def test_toomany_items():
    with pytest.raises(ValueError):
        PlateMap(
            ms_file_name=["test.msfile"],
            sample_name=["TEST_sample_name_0", "TEST_sample_name_1"],
        )


def test_platemap_to_dict(platemap):
    res = platemap.to_dict()

    assert isinstance(res, dict)

    for k in res:
        assert len(res[k]) == platemap.length


def test_platemap_to_df(platemap):
    res = platemap.to_df()

    assert isinstance(res, pd.DataFrame)

    assert len(res) == platemap.length

    for k in res.columns:
        assert len(res[k]) == platemap.length


def test_platemap_to_csv_str(platemap):
    res = platemap.to_csv()

    assert isinstance(res, str)
    assert len(StringIO(res).readlines()) == platemap.length + 1

    # Re-parse CSV with Pandas for additional checks
    df = pd.read_csv(StringIO(res))

    assert len(df) == platemap.length
    for k in df.columns:
        assert len(df[k]) == platemap.length


def test_platemap_to_csv_file(platemap, tmpdir):
    outfile = tmpdir / "test.csv"
    res = platemap.to_csv(outfile)

    with open(outfile, "r") as f:
        assert len(f.readlines()) == platemap.length + 1

        # Re-parse CSV with Pandas for additional checks
        f.seek(0)
        df = pd.read_csv(f)

    assert len(df) == platemap.length
    for k in df.columns:
        assert len(df[k]) == platemap.length


def test_mutate_defaults():
    """Test that default values in the construtor aren't shared mutable instances"""

    # Force extension of default (empty) values by creating a platemap with 2 samples
    platemap_0 = PlateMap(["test_0.msfile", "test_1.msfile"])

    # Now create a platemap with fewer samples; this will trigger an error if the default
    # values were mutated by the first call.
    platemap_1 = PlateMap(["test_0.msfile"])
