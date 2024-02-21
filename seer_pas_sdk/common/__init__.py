from dotenv import load_dotenv
from botocore.config import Config
from botocore.exceptions import ClientError
from re import sub

import pandas as pd
import os
import io
import requests
import boto3
import json

from ..auth import Auth

load_dotenv()


def upload_file(file_name, bucket, object_name=None):
    """
    Upload a file to an S3 bucket.

    Parameters
    ----------
    file_name : str
        The name of the file being uploaded.
    bucket : str
        The name of the bucket to upload to.
    object_name : str
        The name of the object in the bucket. Defaults to `file_name`.

    Returns
    -------
    bool
        True if file was uploaded, else False.

    Examples
    --------
    >>> upload_file("someFileNameHere.raw", "someBucketName")
    >>> True
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        return False
    return True


def dict_to_df(data):
    """
    Returns a Pandas DataFrame from a dictionary.

    Parameters
    ----------
    data : dict
        The dictionary to convert to a Pandas DataFrame.

    Returns
    -------
    pandas.core.frame.DataFrame
        A Pandas DataFrame.

    Examples
    --------
    >>> data = {
            "Sample ID": [1, 2, 3, 4, 5, 6],
            "Sample name": ["SampleName1", "SampleName2", "SampleName3", "SampleName4", "SampleName5", "SampleName6"],
            "Well location": [1, 2, 3, 4, 5, 6],
        }
    >>> df = dict_to_df(data)
    >>> print(df)
    >>>     Sample ID  Sample name  Well location
        0           1  SampleName1              1
        1           2  SampleName2              2
        2           3  SampleName3              3
        ...         ...          ...            ...

    """
    df = pd.DataFrame.from_dict(data)
    return df


def url_to_df(url):
    """
    Returns a Pandas DataFrame from a URL.

    Parameters
    ----------
    url : str
        The URL of the CSV file.

    Returns
    -------
    pandas.core.frame.DataFrame
        A Pandas DataFrame.

    Examples
    --------
    >>> csv = url_to_df("link_to_csv_file")
    >>> print(csv)
    >>>     Sample ID  Sample name  Well location  MS file name
        0           1  SampleName1              1  SDKTest1.raw
        1           2  SampleName2              2  SDKTest2.raw
        2           3  SampleName3              3  SDKTest3.raw
        3           4  SampleName4              4  SDKTest4.raw
        4           5  SampleName5              5  SDKTest5.raw
        5           6  SampleName6              6  SDKTest6.raw
    """

    url_content = io.StringIO(requests.get(url).content.decode("utf-8"))
    csv = pd.read_csv(url_content, sep="\t")
    return csv


def get_sample_info(
    plate_id,
    ms_data_files,
    plate_map_file,
    space,
    sample_description_file=None,
):
    """
    Returns all `sample_id` and `sample_name` values for a plate_map_file and checks if ms_data_files are contained within the plate_map_file.

    Parameters
    ----------
    plate_id : str
        The plate ID.
    ms_data_files : list
        A list of MS data files.
    plate_map_file : str
        The plate map file.
    space : str
        The space.
    sample_description_file : str
        Path to the sample description file.

    Returns
    -------
    list
        A list of dictionaries containing the `plateID`, `sampleID`, `sampleName`, and `sampleUserGroup` values.

    >>> get_sample_info("plate_id", ["AgamSDKTest1.raw", "AgamSDKTest2.raw"], "AgamSDKPlateMapATest.csv", "sdkTestPlateId1", "SDKPlate", "Generated from SDK")
    >>> [
            {
                "plateID": "YOUR_PLATE_ID",
                "sampleID": "YOUR_SAMPLE_ID",
                "sampleName": "YOUR_SAMPLE_NAME",
                "sampleUserGroup": "YOUR_SAMPLE_USER_GROUP"
            }
        ]
    """

    df = pd.read_csv(plate_map_file, on_bad_lines="skip")
    data = df.iloc[:, :]  # all the data in the platemap csv
    files = data["MS file name"]  # all filenames in the platemap csv
    local_file_names = set(
        [os.path.basename(file) for file in ms_data_files]
    )  # all filenames in the local directory
    res = []

    # Step 1: Check if ms_data_files are contained within the plate_map_file.
    if len(files) != len(local_file_names):
        raise ValueError("Plate map file is invalid.")

    for file in files:
        if file not in local_file_names:
            raise ValueError(
                "Plate map file does not contain the attached MS data files."
            )

    # Step 2: Validating and mapping the contents of the sample description file.
    if sample_description_file:
        sdf = pd.read_csv(sample_description_file, on_bad_lines="skip")
        sdf_data = sdf.iloc[:, :]

        sdf.rename(columns={"Sample Name": "Sample name"}, inplace=True)

    # Step 3: CSV manipulation.
    number_of_rows = df.shape[0]  # for platemap csv

    for i in range(number_of_rows):
        row = df.iloc[i]
        sample_id = row["Sample ID"]
        sample_name = row["Sample name"]
        sample_info = {
            "plateID": plate_id,
            "sampleID": sample_id,
            "sampleName": sample_name,
            "sampleUserGroup": space,
        }

        if sample_description_file:
            sdf_row = dict(sdf.iloc[i])
            row_names = list(sdf_row.keys())

            if sdf_row["Sample name"] == sample_name:
                for row_name in row_names:
                    sdf_data = sdf_row[row_name]
                    sample_info[camel_case(row_name)] = (
                        sdf_data if pd.notna(sdf_data) else ""
                    )

        res.append(sample_info)

    return res


def parse_plate_map_file(plate_map_file, samples, raw_file_paths, space=None):
    """
    Parses the plate map CSV file and returns a list of parameters for each sample.

    Parameters
    ----------
    plate_map_file : str
        The plate map file.
    samples : list
        A list of samples.
    raw_file_paths : dict
        A dictionary of raw file paths.
    space : str
        The space or usergroup.

    Returns
    -------
    list
        A list of dictionaries containing all the parameters for each sample.

    Examples
    --------
    >>> raw_file_paths = { "SDKTest1.raw": "FILE_PATH_1", "SDKTest2.raw": "FILE_PATH_2" }
    >>> samples = [
            {
                "id": "SAMPLE_ID_HERE",
                "tenant_id": "TENANT_ID_HERE",
                "plate_id": "PLATE_ID_HERE",
            },
            {
                "id": "SAMPLE_ID_HERE",
                "tenant_id": "TENANT_ID_HERE",
                "plate_id": "PLATE_ID_HERE",
            }
        ]
    >>> parse_plate_map_file("AgamSDKPlateMapATest.csv", samples, raw_file_paths, "SDKPlate")
    >>> [
            {
                "sampleId": "YOUR_SAMPLE_ID",
                "sample_id_tracking": "YOUR_SAMPLE_ID_TRACKING",
                "wellLocation": "YOUR_WELL_LOCATION",
                ...
            },
            {
                "sampleId": "YOUR_SAMPLE_ID",
                "sample_id_tracking": "YOUR_SAMPLE_ID_TRACKING",
                "wellLocation": "YOUR_WELL_LOCATION",
                ...
            }
        ]
    """

    df = pd.read_csv(plate_map_file, on_bad_lines="skip")
    number_of_rows = df.shape[0]
    res = []

    for rowIndex in range(number_of_rows):
        row = df.iloc[rowIndex]
        path = None
        sample_id = None

        if (
            samples[rowIndex]["sample_id"] == row["Sample ID"]
            and samples[rowIndex]["sample_name"] == row["Sample name"]
        ):
            sample_id = samples[rowIndex]["id"]

        for filename in raw_file_paths:
            if filename == row["MS file name"]:
                path = raw_file_paths[filename]

        if not path or not sample_id:
            raise ValueError("Plate map file is invalid.")

        res.append(
            {
                "sampleId": str(sample_id),
                "sample_id_tracking": str(row["Sample ID"]),
                "wellLocation": (
                    str(row["Well location"])
                    if pd.notna(row["Well location"])
                    else ""
                ),
                "nanoparticle": (
                    str(row["Nanoparticle"])
                    if pd.notna(row["Nanoparticle"])
                    else ""
                ),
                "nanoparticleID": (
                    str(row["Nanoparticle ID"])
                    if pd.notna(row["Nanoparticle ID"])
                    else ""
                ),
                "control": (
                    str(row["Control"]) if pd.notna(row["Control"]) else ""
                ),
                "controlID": (
                    str(row["Control ID"])
                    if pd.notna(row["Control ID"])
                    else ""
                ),
                "instrumentName": (
                    str(row["Instrument name"])
                    if pd.notna(row["Instrument name"])
                    else ""
                ),
                "dateSamplePrep": (
                    str(row["Date sample preparation"])
                    if pd.notna(row["Date sample preparation"])
                    else ""
                ),
                "sampleVolume": (
                    str(row["Sample volume"])
                    if pd.notna(row["Sample volume"])
                    else ""
                ),
                "peptideConcentration": (
                    str(row["Peptide concentration"])
                    if pd.notna(row["Peptide concentration"])
                    else ""
                ),
                "peptideMassSample": (
                    str(row["Peptide mass sample"])
                    if pd.notna(row["Peptide mass sample"])
                    else ""
                ),
                "dilutionFactor": (
                    str(row["Dilution factor"])
                    if pd.notna(row["Dilution factor"])
                    else ""
                ),
                "msdataUserGroup": space,
                "rawFilePath": path,
            }
        )

    return res


def valid_ms_data_file(path):
    """
    Checks if an MS data file exists and if its extension is valid for upload.

    Parameters
    ----------
    path : str
        The path to the MS data file.

    Returns
    -------
    bool
        True if the file exists and its extension is valid, False otherwise.
    """

    if not os.path.exists(path):
        return False

    full_filename = path.split("/")[-1].split(".")

    if len(full_filename) >= 3:
        extension = f'.{".".join(full_filename[-2:])}'
    else:
        extension = f".{full_filename[-1]}"

    return extension.lower() in [
        ".d",
        ".d.zip",
        ".mzml",
        ".raw",
        ".mzml",
        ".wiff",
        ".wiff.scan",
    ]


def download_hook(t):
    """
    Wraps tqdm instance.

    Example
    -------
    >>> with tqdm(...) as t:
    ...     reporthook = download_hook(t)
    ...     urllib.urlretrieve(..., reporthook=reporthook)
    """
    last_b = [0]

    def update_to(b=1, bsize=1, tsize=None):
        """
        b : int, optional
            Number of blocks transferred so far [default: 1].
        bsize : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            t.total = tsize
        t.update((b - last_b[0]) * bsize)
        last_b[0] = b

    return update_to


def camel_case(s):
    # Use regular expression substitution to replace underscores and hyphens with spaces,
    # then title case the string (capitalize the first letter of each word), and remove spaces
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")

    # Join the string, ensuring the first letter is lowercase
    return "".join([s[0].lower(), s[1:]])
