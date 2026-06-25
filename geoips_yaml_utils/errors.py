# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Exception classes raised by geoips_yaml_utils."""

from yaml.constructor import ConstructorError


class DuplicateKeyError(ConstructorError):
    """Raised when a YAML mapping contains duplicate keys."""

    pass


class MissingEnvironmentVariableError(RuntimeError):
    """Raised when an environment variable is referenced without being set."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"Required environment variable {name!r} is not set "
            f"and no default value was provided in the YAML !ENV tag"
        )
