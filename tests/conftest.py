"""Test fixtures for GUI controllers.

Make sure that qatools is imported before app is initialized, otherwise the
app will attempt to make DB connections before a DB is in place.
"""
import sys

import pytest

from viper import config as viper_config
from viper.annunciator import Annunciator
from viper.instance import InstanceManager


def pytest_addoption(parser):
    parser.addoption("--testdb", action="store_true", default=False,
                     help="Use test database")


@pytest.fixture
def testdb(request):
    return request.config.getoption("--testdb")


@pytest.fixture
def app_client(testdb, request):
    "App test client. Add app config overrides here."
    if testdb:
        from viper.tools import qatools
        db = qatools.MongoTestDB()
        db.purge_dbs()
    if 'app' not in sys.modules:
        from gui import app

    ctx = app.test_request_context()
    ctx.push()

    def pop_request():
        ctx.pop()

    request.addfinalizer(pop_request)
    return app.test_client()


def get_instance(login, instance):
    instance_manager = InstanceManager(viper_config)
    instance = instance_manager.get_instance_by_name(login, instance)
    return instance


@pytest.fixture
def annunciator():
    annunciator = Annunciator(viper_config)
    return annunciator


@pytest.fixture
def stripe_token():
    import stripe
    stripe.api_key = viper_config.STRIPE_API_KEY
    stripe_response = stripe.Token.create(card=dict(number='4242424242424242',
                                                    exp_month=12,
                                                    exp_year=2019,
                                                    cvc=123))
    return stripe_response
