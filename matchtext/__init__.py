from pkg_resources import DistributionNotFound, get_distribution

try:
    dist_name = "matchtext"
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound
