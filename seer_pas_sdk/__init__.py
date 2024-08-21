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
        __version__ = version("pas-python-sdk")
    except PackageNotFoundError:
        pass

except ImportError:
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        __version__ = get_distribution("pas-python-sdk").version
    except DistributionNotFound:
        pass

# Export public functions and classes.
from .core import SeerSDK
from .objects.platemap import PlateMap
