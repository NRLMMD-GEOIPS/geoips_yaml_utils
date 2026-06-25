# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Drop-in replacement for `import yaml` with duplicate key detection.

Usage:
    import geoips_yaml_utils as yaml

`safe_load` and `safe_load_all` raise `DuplicateKeyError` on repeated keys.
All other yaml symbols (dump, SafeLoader, SafeDumper, ...) pass through unchanged.
Adds logic from `pyaml-env` to create `parse_config` which performs environment
variable substitution on '!ENV' tags in yaml files.
"""

import os
import re
import logging
import yaml

from geoips_yaml_utils.errors import DuplicateKeyError, MissingEnvironmentVariableError

# Defining the exports
__all__ = [
    # loaders
    "SafeLoaderNoDuplicates",
    "EnvVarLoader",
    "EnvVarLoaderNoDuplicates",
    # callables
    "safe_load",
    "safe_load_all",
    "parse_config",
]


LOG = logging.getLogger(__name__)

# This regex pattern matches all instances in a YAML node which use the syntax:
#   ${MY_ENV:/default/value}
# This pattern names the two groups "name" & "default"
# such that the above example would result in the following assignments:
#   MY_ENV         -> "name"    group
#   /default/value -> "default" group
ENV_VAR_PATTERN = re.compile(r".*?\$\{(?P<name>[^}{:]+)(?P<default>:[^}]+)?\}.*?")

# DEFAULT_SEP separates the env var name from its default.
#   e.g.  !ENV ${MY_ENV:/default/value}
DEFAULT_SEP = ":"

# ---------------
# Constructors
# ---------------


def _construct_mapping_no_duplicates(loader, node):
    """Construct a YAML mapping while checking for duplicate keys.

    Parameters
    ----------
    loader : yaml.Loader
        The YAML loader instance processing the current document.
    node : yaml.MappingNode
        The mapping node being constructed.

    Returns
    -------
    dict
        The constructed mapping.

    Raises
    ------
    DuplicateKeyError
        If a duplicate key is found in the mapping.
    """
    # flatten "<<: *anchor" merge keys before checking
    #   a key that appears both explicitly and via merge will falsely raise
    loader.flatten_mapping(node)

    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise DuplicateKeyError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key ({key})",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node)
    return mapping


def _construct_env_var(loader, node):
    """Resolve a YAML !ENV node by substituting environment variables.

    Adapted from pyaml_env.parse_config.constructor_env_variables.
    Supports `${VAR}` and `${VAR:default}` forms, with multiple variables
    in a single scalar (e.g. `http://${HOST}:${PORT}`).

    Parameters
    ----------
    loader : yaml.Loader
        The YAML loader instance processing the current document.
    node : yaml.ScalarNode
        The scalar node tagged with `!ENV`.

    Returns
    -------
    str
        The scalar value with every `${VAR}` and `${VAR:default}` resolved.

    Raises
    ------
    MissingEnvironmentVariableError
        If a referenced variable is not set and no default was provided.
    """
    value = loader.construct_scalar(node)
    matches = list(ENV_VAR_PATTERN.finditer(value))
    if not matches:
        return value

    full_value = value
    for match in matches:
        # `match` is a lazy iterator with named groups: "name" & "default"
        env_var_name = match.group("name")
        default_segment = match.group("default")
        env_var_name_with_default = env_var_name + (default_segment or "")

        default = None
        if default_segment:
            # Remove the DEFAULT_SEP character from the captured group
            default = default_segment.split(DEFAULT_SEP, 1)[1]

        env_value = os.environ.get(env_var_name)
        if env_value is not None:
            substituted = env_value
        elif default is not None:
            substituted = default
        else:
            raise MissingEnvironmentVariableError(env_var_name)

        full_value = full_value.replace(
            f"${{{env_var_name_with_default}}}",
            substituted,
        )
    return full_value


# ---------------
# YAML Loaders
# ---------------


class SafeLoaderNoDuplicates(yaml.SafeLoader):
    """A YAML SafeLoader that raises an error on duplicate mapping keys.

    Inherits all behaviour from `yaml.SafeLoader` but overrides the default
    mapping constructor to track keys that have already been seen within each
    mapping node.
    """

    pass


SafeLoaderNoDuplicates.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


class EnvVarLoader(yaml.SafeLoader):
    """A YAML SafeLoader that resolves `!ENV` tags into environment variable values.

    Inherits all behaviour from `yaml.SafeLoader` but adds a new constructor so that
    `EnvVarLoader` enforces `!ENV` tag resolution to the corresponding environment
    variable.
    """

    pass


EnvVarLoader.add_constructor("!ENV", _construct_env_var)


class EnvVarLoaderNoDuplicates(yaml.SafeLoader):
    """A YAML SafeLoader that combines both SafeLoaderNoDuplicates and EnvVarLoader.

    Inherits all behaviour from `yaml.SafeLoader` but overrides the default mapping
    constructor to track keys that have already been seen within each mapping node.
    Also adds a new constructor so that `EnvVarLoader` enforces `!ENV` tag resolution
    to the corresponding environment variable.
    """

    pass


EnvVarLoaderNoDuplicates.add_constructor("!ENV", _construct_env_var)
EnvVarLoaderNoDuplicates.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


# -------------------
# Callable Functions
# -------------------


def safe_load(stream, Loader=SafeLoaderNoDuplicates):
    """Load a single YAML document, raising on duplicate keys by default.

    Drop-in replacement for `yaml.safe_load` that uses
    `SafeLoaderNoDuplicates` to reject mappings with repeated keys.

    Parameters
    ----------
    stream : str or file-like
        YAML content to parse.
    Loader : yaml.SafeLoader subclass, optional
        Loader class to use. Defaults to `SafeLoaderNoDuplicates`, which raises
        `DuplicateKeyError` on repeated keys. Pass `yaml.SafeLoader` to restore
        standard behaviour without duplicate detection.

    Returns
    -------
    dict
        The parsed YAML document.

    Raises
    ------
    DuplicateKeyError
        If a duplicate key is detected and the default `Loader` is used.
    """
    return yaml.load(stream, Loader=Loader)  # nosec B506


def safe_load_all(stream, Loader=SafeLoaderNoDuplicates):
    """Load all YAML documents from a stream, raising on duplicate keys by default.

    Drop-in replacement for `yaml.safe_load_all` that uses
    `SafeLoaderNoDuplicates` to reject mappings with repeated keys.

    Parameters
    ----------
    stream : str or file-like
        YAML content to parse.
    Loader : yaml.SafeLoader subclass, optional
        Loader class to use. Defaults to `SafeLoaderNoDuplicates`, which raises
        `DuplicateKeyError` on repeated keys. Pass `yaml.SafeLoader` to restore
        standard behaviour without duplicate detection.

    Yields
    ------
    dict
        Each parsed YAML document.

    Raises
    ------
    DuplicateKeyError
        If a duplicate key is detected and the default `Loader` is used.
    """
    return yaml.load_all(stream, Loader=Loader)  # nosec B506
