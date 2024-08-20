"""
seer_pas_sdk.core.internal -- extended SDK with addtional functionality FOR INTERNAL USE ONLY
"""

from .sdk import SeerSDK as _SeerSDK


class InternalSDK(_SeerSDK):
    """
    This class extends the publicly-available SDK class with additional methods meant only
    for use within Seer (for the time being).
    """

    pass
