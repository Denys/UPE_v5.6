"""Package-level scaffold checks."""

from importlib.metadata import version

import harness


def test_package_imports_from_project_environment() -> None:
    """The installed project and import package expose the same version."""
    assert harness.__version__ == version("upe-harness")
