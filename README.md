# Seer PAS Python SDK

[![Test](https://github.com/seerbio/pas-python-sdk/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/seerbio/pas-python-sdk/actions/workflows/test.yml)
[![Lint](https://github.com/seerbio/pas-python-sdk/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/seerbio/pas-python-sdk/actions/workflows/lint.yml)

This SDK permits interaction with the Seer Proteograph Analysis Suite using Python.
**It is currently in development and is not ready for production use.**

**IMPORTANT:** This SDK is for **INTERNAL USE**!
The publicly-available version can be found at [https://github.com/seerbio/seer-pas-sdk/]().
Note that changes made to this repository will NOT automatically be made available to users and will have to be **manually ported** for public release.

## Installation

```shell
aws codeartifact login --tool pip --repository seer_ds --domain seer --domain-owner 718843040700 --region us-west-2
pip install pas-python-sdk
```

## Usage

To import and set up the SDK:

```python
from seer_pas_sdk import SeerSDK

# Instantiate an SDK object with your credentials:
sdk = SeerSDK(USERNAME, PASSWORD)
```

You can then use the SDK's functions to create, query, or retrieve projects, plates, samples, and analyses.

For complete documentation of this SDK, visit this repository's GitHub Pages, linked in the sidebar, under "About" ↗️.
