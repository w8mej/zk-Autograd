"""conftest.py

Pytest configuration and fixtures for the ZK-Autograd test suite.
"""
import pytest
import os
import shutil
import tempfile

@pytest.fixture
def temp_run_dir():
    """Creates a temporary directory for a run and cleans it up afterwards.

    Yields:
        The path to the temporary directory.
    """
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)
