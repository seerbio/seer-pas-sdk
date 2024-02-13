"""
`seer-pas-sdk`

Exports:

- `SeerSDK`
- `PlateMap`
"""

# Initialize the package.
try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("seer-pas-sdk")
    except PackageNotFoundError:
        pass

except ImportError:
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        __version__ = get_distribution("seer-pas-sdk").version
    except DistributionNotFound:
        pass

# Export public functions and classes.
from .core import SeerSDK
from .objects import PlateMap
