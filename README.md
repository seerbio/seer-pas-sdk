# Seer PAS Python SDK

[![Test](https://github.com/seerbio/seer-pas-sdk/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/seerbio/seer-pas-sdk/actions/workflows/test.yml)
[![Lint](https://github.com/seerbio/seer-pas-sdk/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/seerbio/seer-pas-sdk/actions/workflows/lint.yml)

This SDK permits interaction with the Seer Proteograph Analysis Suite using Python.

## Installation

```shell
pip install seer-pas-sdk
```

## Usage

To import and set up the SDK:

```python
from seer_pas_sdk import SeerSDK

# Instantiate an SDK object with your credentials:
sdk = SeerSDK(USERNAME, PASSWORD)
```

You can then use the SDK's methods to create, query, or retrieve projects, plates, samples, and analyses.

For complete documentation of this SDK, visit [https://seerbio.github.io/seer-pas-sdk/](https://seerbio.github.io/seer-pas-sdk/ "Documentation").
