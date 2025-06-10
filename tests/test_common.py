import pytest

from seer_pas_sdk.common import *


@pytest.fixture
def mock_sample(platemap):
    """A file name in our mock platemap"""
    idx = 0
    return (
        platemap.ms_file_name[idx],
        platemap.sample_name[idx],
        platemap.sample_id[idx],
    )


@pytest.fixture(scope="function")
def platemap_file(platemap, tmpdir):
    """Our mock platemap, as a file"""
    outfile = tmpdir / "test_platemap.csv"

    platemap.to_csv(outfile)

    blank_raw_file = tmpdir / "test.raw"
    blank_raw_file.write("")

    yield outfile

    # Clean up test file
    outfile.remove()
    blank_raw_file.remove()


def test_get_sample_info(platemap_file, mock_sample):
    """Test that get_sample_info correctly parses the platemap file"""
    filename, sample_name, sample_id = mock_sample

    plate_id = "TEST_plate_id"
    space = "TEST_space_id"
    res = get_sample_info(
        plate_id=plate_id,
        plate_map_file=platemap_file,
        space=space,
        sample_description_file=None,  # TODO: test sample description file
    )

    assert len(res) == 1

    for sampleinfo in res:
        assert sampleinfo["plateID"] == plate_id
        assert sampleinfo["sampleName"] == sample_name
        assert sampleinfo["sampleID"] == sample_id
        assert sampleinfo["sampleUserGroup"] == space


def test_valid_pas_folder():
    assert valid_pas_folder_path("foo")
    assert valid_pas_folder_path("foo/bar")
    assert valid_pas_folder_path("foo/bar/baz")
    assert not valid_pas_folder_path("foo/bar/")
    assert not valid_pas_folder_path("/foo/bar")
    assert not valid_pas_folder_path("foo//bar")
    assert not valid_pas_folder_path("foo/bar//")
    assert not valid_pas_folder_path("//foo/bar/")
    assert not valid_pas_folder_path("foo///bar")
    assert not valid_pas_folder_path("foo////////////////////////bar")


def test_camel_case():
    assert camel_case("my favorite") == "myFavorite"
    assert camel_case("my Favorite") == "myFavorite"
    assert camel_case("My favorite") == "myFavorite"
    assert camel_case("My Favorite") == "myFavorite"
    assert camel_case("snake_case") == "snakeCase"
    assert camel_case("snake_Case") == "snakeCase"
    assert camel_case("Snake_case") == "snakeCase"
    assert camel_case("Snake_Case") == "snakeCase"
    assert camel_case("camelcase") == "camelcase"
    assert camel_case("camelCase") == "camelcase"
    assert camel_case("Camelcase") == "camelcase"
    assert camel_case("CamelCase") == "camelcase"
    assert camel_case("kebab-case") == "kebabCase"
    assert camel_case("kebab-Case") == "kebabCase"
    assert camel_case("Kebab-case") == "kebabCase"
    assert camel_case("Kebab-Case") == "kebabCase"

    # Corner cases:
    assert camel_case("two\nlines") == "two\nLines"
    assert camel_case("two\nLines") == "two\nLines"
    assert camel_case("Two\nlines") == "two\nLines"
    assert camel_case("Two\nLines") == "two\nLines"
    assert camel_case("über コンピュータコード") == "überコンピュータコード"
    assert camel_case("über コンピュータコード") == "überコンピュータコード"
    assert camel_case("Über コンピュータコード") == "überコンピュータコード"
    assert camel_case("Über コンピュータコード") == "überコンピュータコード"
    assert camel_case("clap👏back") == "clap👏Back"
    assert camel_case("clap👏Back") == "clap👏Back"
    assert camel_case("Clap👏back") == "clap👏Back"
    assert camel_case("Clap👏Back") == "clap👏Back"
