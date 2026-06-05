# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Repo-level lint test: black/flake8/bandit on this package."""

import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]  # geoips_yaml_utils/

LINT_COMMANDS = {
    "black": ["black", "--check", "."],
    "flake8": ["flake8", "."],
    "bandit": ["bandit", "-ll", "-r", "geoips_yaml_utils"],
}


@pytest.mark.lint
@pytest.mark.integration
@pytest.mark.parametrize("checker", list(LINT_COMMANDS))
def test_code_check(checker):
    """Fail if <checker> reports a violation against the package."""
    result = subprocess.run(
        LINT_COMMANDS[checker],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{checker} reported issues (ran: {' '.join(LINT_COMMANDS[checker])})\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )
