"""
seer_pas_sdk.core -- contains core class for SDK: `SeerSDK`

Examples
--------
>>> from seer_pas_sdk.core import SeerSDK
>>> seer_sdk = SeerSDK(USERNAME, PASSWORD)
"""

# Export the internal class under the expected name
from .internal import InternalSDK as SeerSDK
