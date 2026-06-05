# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Exception classes raised by geoips_yaml_utils."""


class DuplicateKeyError(Exception):
    """Raised when a YAML mapping contains duplicate keys."""

    pass


class MissingEnvironmentVariableError(Exception):
    """Raised when an environment variable is referenced without being set."""

    pass
