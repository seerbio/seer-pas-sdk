from dotenv import load_dotenv
from botocore.config import Config
from botocore.exceptions import ClientError
import re
from re import match, sub, UNICODE

import pandas as pd
import os
import io
import requests
import boto3
import json
import zipfile
import tempfile

from ..auth.auth import Auth

from .groupanalysis import *

from .errors import *

load_dotenv()


def upload_file(file_name, bucket, credentials, object_name=None):
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
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )
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


# Most cases appear to be a .tsv file.
def url_to_df(url, is_tsv=True):
    """
    Fetches a TSV/CSV file from a URL and returns as a Pandas DataFrame.

    Parameters
    ----------
    url : str
        The URL of the TSV/CSV file.

    is_tsv : bool
        True if the file is a TSV file, False if it is a CSV file.

    Returns
    -------
    pandas.core.frame.DataFrame
        The data from the TSV/CSV file as a Pandas DataFrame

    Raises
    ------
    ValueError
        Error response from AWS S3

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

    if not url:
        return pd.DataFrame()
    url_content = io.StringIO(requests.get(url).content.decode("utf-8"))
    if is_tsv:
        csv = pd.read_csv(url_content, sep="\t")
    else:
        csv = pd.read_csv(url_content)
    return csv


def get_sample_info(
    plate_id,
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

    >>> get_sample_info("plate_id", "AgamSDKPlateMapATest.csv", "sdkTestPlateId1", "SDKPlate", "Generated from SDK")
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
    # all filenames in the local directory
    res = []

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

    # Step 4: drop duplicates on sampleID
    df = pd.DataFrame(res).drop_duplicates(subset=["sampleID"])
    res = df.to_dict(orient="records")
    return res


def _validate_rawfile_extensions(rawfile):
    valid_extensions = [".d", ".d.zip", ".mzml", ".raw", ".wiff", ".wiff.scan"]
    if not rawfile.lower().endswith(tuple(valid_extensions)):
        return False
    return True


def entity_name_ruler(entity_name):
    if pd.isna(entity_name):
        return False
    pattern = r"^[\w ._+()!@-]+$"
    if match(pattern, entity_name, UNICODE):
        return True
    else:
        return False


def validate_plate_map(df, local_file_names):
    """
    Validates the plate map contents

    Parameters
    ----------
    plate_map: pd.Dataframe
        The plate map data as a dataframe

    local_file_names: file names that were passed to the top level function.

    Returns
    -------
    pd.DataFrame : the cleaned data as a dataframe

    Examples
    --------
    >>> df = validate_plate_map_file("AgamSDKPlateMapATest.csv")
    """

    required_cols = [
        "MS file name",
        "Sample name",
        "Sample ID",
        "Well location",
        "Plate ID",
        "Plate Name",
    ]

    # We use the presence of the "Method set ID" column as a heuristic to determine if the plate map is Biscayne+
    if "Method set ID" not in df.columns:
        required_cols.append("Control")

    # Catch case variations of Plate Name due to change between XT and Biscayne
    pattern = re.compile(r"(?i)(Plate Name)")
    matches = [s for s in df.columns if pattern.match(s)]
    if matches:
        df.rename(columns={matches[0]: "Plate Name"}, inplace=True)

    if not all(col in df.columns for col in required_cols):
        err_headers = [
            "'" + col + "'" for col in required_cols if col not in df.columns
        ]
        raise ValueError(
            f"The following column headers are required: {', '.join(err_headers)}"
        )

    # Check entity name requirement
    invalid_plate_ids = df[~df["Plate ID"].apply(entity_name_ruler)]

    invalid_plate_names = df[~df["Plate Name"].apply(entity_name_ruler)]

    if not invalid_plate_ids.empty or not invalid_plate_names.empty:
        error_msg = ""
        if not invalid_plate_ids.empty:
            error_msg += f"Invalid plate ID(s): {', '.join(invalid_plate_ids['Plate ID'].tolist())}"
        if not invalid_plate_names.empty:
            error_msg += f"Invalid plate name(s): {', '.join(invalid_plate_names['Plate Name'].tolist())}"
        raise ValueError(error_msg)

    # Check numeric columns
    numeric_cols = [
        "Sample volume",
        "Peptide concentration",
        "Peptide mass sample",
        "Recon volume",
        "Reconstituted peptide concentration",
        "Recovered peptide mass",
        "Reconstitution volume",
    ]

    invalid_cols = []
    for col in numeric_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="raise")
            except Exception as e:
                invalid_cols.append(col)

    if invalid_cols:
        raise ValueError(
            f"The following column(s) must be numeric: {', '.join(invalid_cols)}"
        )

    files = [os.path.basename(x) for x in df["MS file name"].tolist()]

    # Check if ms_data_files are contained within the plate_map_file.
    if len(files) != len(local_file_names):
        raise ValueError(
            f"User provided {len(local_file_names)} MS files, however the plate map lists {len(files)} MS files. \
                         Please check your inputs."
        )
    missing_files = []
    for file in local_file_names:
        if os.path.basename(file) not in files:
            missing_files.append(file)

    # Found file mismatch between function argument and plate map
    if missing_files:
        msg = ""
        try:
            msg = f"The following file names were not found in the plate map: {', '.join(missing_files)}. Please revise the plate map file."
        except:
            raise ValueError(
                "Rawfile names must be type string. Float or None type detected."
            )
        raise ValueError(msg)

    # Check rawfiles end with valid extensions
    invalid_rawfile_extensions = df[
        ~df["MS file name"].apply(_validate_rawfile_extensions)
    ]
    if not invalid_rawfile_extensions.empty:
        raise ValueError(
            f"Invalid raw file extensions: {', '.join(invalid_rawfile_extensions['MS file name'].tolist())}"
        )

    # Check sample IDs are one to one with plate ID, plate name
    sample_ids = df["Sample ID"].unique()
    for sample in sample_ids:
        queryset = df[df["Sample ID"] == sample]
        plate_names = queryset["Plate ID"].unique()
        plate_ids = queryset["Plate ID"].unique()
        if len(plate_names) > 1:
            raise ValueError(
                f"Sample ID {sample} is associated with multiple plates: {', '.join(plate_names)}"
            )
        if len(plate_ids) > 1:
            raise ValueError(
                f"Sample ID {sample} is associated with multiple plates: {', '.join(plate_ids)}"
            )

    return df


def parse_plate_map_file(plate_map_file, samples, raw_file_paths, space=None):
    """
    Parses the plate map CSV file and returns a list of parameters for each sample.

    Parameters
    ----------
    plate_map_file : str
        The plate map file.
    samples : list
        A list of samples.
    raw_file_paths: dict
        A dictionary mapping the plate map MS file paths with the cloud upload path.
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
    >>> parse_plate_map_file("AgamSDKPlateMapATest.csv", samples, "SDKPlate")
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

    # reformat samples to be a dictionary with sample_id as the key
    samples = {sample["sample_id"]: sample for sample in samples}

    # Catch case variations of Plate Name due to change between XT and Biscayne
    pattern = re.compile(r"(?i)(Plate Name)")
    matches = [s for s in df.columns if pattern.match(s)]
    if matches:
        df.rename(columns={matches[0]: "Plate Name"}, inplace=True)

    for rowIndex in range(number_of_rows):
        row = df.iloc[rowIndex]
        sample_id = None
        path = None

        # Validate that the sample ID exists in the samples list
        if samples.get(row["Sample ID"], None):
            sample_id = samples[row["Sample ID"]]["id"]
        else:
            raise ValueError(
                f'Error fetching id for sample ID {row["Sample ID"]}'
            )

        # Map display file path to its underlying file path
        path = raw_file_paths.get(os.path.basename(row["MS file name"]), None)

        if not path:
            raise ValueError(
                f"Row {rowIndex} is missing a value in MS file name."
            )

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
                    if pd.notna(row.get("Nanoparticle", None))
                    else (
                        str(row["Nanoparticle set"])
                        if pd.notna(row.get("Nanoparticle set", None))
                        else ""
                    )
                ),
                "nanoparticleID": (
                    str(row["Nanoparticle ID"])
                    if pd.notna(row.get("Nanoparticle ID", None))
                    else (
                        str(row["Nanoparticle set ID"])
                        if pd.notna(row.get("Nanoparticle set ID", None))
                        else ""
                    )
                ),
                "control": (
                    str(row["Control"])
                    if pd.notna(row.get("Control", None))
                    else ""
                ),
                "controlID": (
                    str(row["Control ID"])
                    if pd.notna(row.get("Control ID", None))
                    else ""
                ),
                "instrumentName": (
                    str(row["Instrument name"])
                    if pd.notna(row.get("Instrument name", None))
                    else (
                        str(row["Instrument ID"])
                        if pd.notna(row.get("Instrument ID", None))
                        else ""
                    )
                ),
                "dateSamplePrep": (
                    str(row["Date sample preparation"])
                    if pd.notna(row.get("Date sample preparation", None))
                    else (
                        str(row["Date assay initiated"])
                        if pd.notna(row.get("Date assay initiated", None))
                        else ""
                    )
                ),
                "sampleVolume": (
                    str(row["Sample volume"])
                    if pd.notna(row.get("Sample volume", None))
                    else ""
                ),
                "peptideConcentration": (
                    str(row["Peptide concentration"])
                    if pd.notna(row.get("Peptide concentration", None))
                    else (
                        str(row["Reconstituted peptide concentration"])
                        if pd.notna(
                            row.get(
                                "Reconstituted peptide concentration", None
                            )
                        )
                        else ""
                    )
                ),
                "peptideMassSample": (
                    str(row["Peptide mass sample"])
                    if pd.notna(row.get("Peptide mass sample", None))
                    else (
                        str(row["Recovered peptide mass"])
                        if pd.notna(row.get("Recovered peptide mass", None))
                        else ""
                    )
                ),
                "reconVolume": (
                    str(row["Recon volume"])
                    if pd.notna(row.get("Recon volume", None))
                    else (
                        str(row["Reconstitution volume"])
                        if pd.notna(row.get("Reconstitution volume", None))
                        else ""
                    )
                ),
                "dilutionFactor": (
                    str(row["Dilution factor"])
                    if pd.notna(row.get("Dilution factor", None))
                    else ""
                ),
                "sampleTubeId": (
                    str(row["Sample tube ID"])
                    if pd.notna(row.get("Sample tube ID", None))
                    else ""
                ),
                "assayProduct": (
                    str(row["Assay"])
                    if pd.notna(row.get("Assay", None))
                    else (
                        str(row["Assay product"])
                        if pd.notna(row.get("Assay product", None))
                        else ""
                    )
                ),
                "methodSetId": (
                    str(row["Method set ID"])
                    if pd.notna(row.get("Method set ID", None))
                    else ""
                ),
                "assayMethodId": (
                    str(row["Assay method ID"])
                    if pd.notna(row.get("Assay method ID", None))
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

    return _validate_rawfile_extensions(path)


def valid_pas_folder_path(path):
    """
    Checks if a PAS folder path is valid.

    Parameters
    ----------
    path : str
        The path to the PAS folder.

    Returns
    -------
    bool
        True if the path is valid, False otherwise.
    """

    #
    # Invalidate the following patterns:
    # 1. Leading forward slash
    # 2. Trailing forward slash
    # 3. Double forward slashes
    #
    if not all(path.split("/")):
        return False
    else:
        return True


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


def rename_d_zip_file(source, destination):
    """
    Renames a .d.zip file. The function extracts the contents of the source zip file, renames the inner .d folder, and rezips the contents into the destination zip file.

    Parameters
    ----------
    file : str
        The name of the zip file.
    new_name : str
        The new name of the zip file.

    Returns
    -------
    None

    Examples
    --------
    >>> rename_zip_file("old_name.zip", "new_name.zip")
    Renamed old_name.zip to new_name.zip

    """
    if not source.lower().endswith(".d.zip"):
        raise ValueError("Invalid zip file extension")

    if not destination.lower().endswith(".d.zip"):
        raise ValueError("Invalid zip file extension")

    # Remove the .zip extension from the destination file
    d_destination = destination[:-4]

    # Create a temporary directory to extract the contents
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the source file
        with zipfile.ZipFile(source, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Rezip the contents into the destination file
        with zipfile.ZipFile(destination, "w") as zip_ref:
            for foldername, subfolders, filenames in os.walk(temp_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = f"{d_destination}/{os.path.relpath(file_path, temp_dir)}"  # substitute the original .d name with the new .d name
                    zip_ref.write(file_path, arcname)

    print(f"Renamed {source} to {destination}")
