from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = 0.1.2
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"
