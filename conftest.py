"""Root pytest configuration and module collision resolver."""
import sys


def pytest_pycollect_makemodule(module_path, parent):
    """Clear cached 'tests.*' modules between collections to prevent cross-package collisions."""
    for key in list(sys.modules.keys()):
        if key == "tests" or key.startswith("tests."):
            sys.modules.pop(key, None)
