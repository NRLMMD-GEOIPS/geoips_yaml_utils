.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _geoips-yaml-utils-functionality:

GeoIPS YAML Utilities
*********************

``geoips_yaml_utils`` is the standard YAML interface for GeoIPS. It is a drop-in
replacement for ``import yaml`` that adds two safeguards on top of PyYAML while leaving
the rest of the library untouched.

First, it detects duplicate mapping keys: ``safe_load`` and ``safe_load_all`` raise
``DuplicateKeyError`` when a YAML document repeats a key, instead of silently keeping
the last value the way plain PyYAML does. Second, it resolves environment variables
in YAML files: ``parse_config`` (adapted from the MIT-licensed pyaml-env) expand
``!ENV ${VAR}`` and ``!ENV ${VAR:default}`` tags, raising
``MissingEnvironmentVariableError`` when a referenced variable is unset and has
no default.

Every other PyYAML symbol (``dump``, ``SafeLoader``, ``YAMLError``, and so on) passes
through unchanged, so ``geoips_yaml_utils`` can serve as the only ``yaml`` import in a
GeoIPS package. No GeoIPS plugins or domain logic live here; this package is a focused,
standalone utility intended to provide consistent YAML handling across GeoIPS and its
plugin packages.

Installation
============

From source:

.. code-block:: bash

    git clone https://github.com/NRLMMD-GEOIPS/geoips_yaml_utils.git
    # cd to geoips_yaml_utils's top level dir
    pip install -e .

Usage
=====

``geoips_yaml_utils`` is a drop-in replacement for ``import yaml``. Import it under the
``yaml`` name and the duplicate-key-checking loaders are used automatically:

.. code-block:: python

    import geoips_yaml_utils as yaml

    cfg = yaml.safe_load(open("plugin.yaml"))  # raises DuplicateKeyError on duplicate keys

Resolving environment variables with parse_config
=================================================

``parse_config`` reads a YAML file from a path and resolves ``!ENV`` tags by
substituting environment variables. This functionality is adapted from the MIT-licensed
`pyaml-env <https://github.com/mkaranasou/pyaml_env>`_ project.

Tag a scalar with ``!ENV``, then reference variables inside it with ``${...}``:

- ``${VAR}`` is replaced with the value of environment variable ``VAR``. If ``VAR`` is
  not set, ``MissingEnvironmentVariableError`` is raised.
- ``${VAR:default}`` falls back to ``default`` when ``VAR`` is not set. The separator is
  a colon (``:``), not bash's ``:-``.
- A single scalar may contain multiple references, e.g. ``${HOST}:${PORT}``.
- Resolved values are always strings, since environment variables are strings.

Given ``config.yaml``:

.. code-block:: yaml

    database:
      host: !ENV ${DB_HOST}
      port: !ENV ${DB_PORT:5432}
      url: !ENV "${DB_HOST}:${DB_PORT:5432}"

with ``DB_HOST=db.example.com`` exported and ``DB_PORT`` unset:

.. code-block:: python

    import geoips_yaml_utils as yaml

    config = yaml.parse_config("config.yaml")
    # {
    #     "database": {
    #         "host": "db.example.com",
    #         "port": "5432",
    #         "url": "db.example.com:5432",
    #     }
    # }

By default ``parse_config`` also rejects duplicate keys (raising ``DuplicateKeyError``).
Pass ``detect_duplicates=False`` to keep the ``!ENV`` resolution but skip that check:

.. code-block:: python

    config = yaml.parse_config("config.yaml", detect_duplicates=False)
