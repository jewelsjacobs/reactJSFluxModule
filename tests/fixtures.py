"""Test fixtures for GUI controllers.

Make sure that qatools is imported before app is initialized, otherwise the
app will attempt to make DB connections before a DB is in place.
"""
import pytest

from viper.tools import qatools
testdb = qatools.MongoTestDB()  # Test DB is now live.

from gui import app


def purge_dbs():
    """A generic wrapper to purge the test mongod."""
    testdb.purge_dbs()
    return True


@pytest.fixture
def app_client():
    "App test client. Add app config overrides here."
    purge_dbs()
    return app.test_client()
