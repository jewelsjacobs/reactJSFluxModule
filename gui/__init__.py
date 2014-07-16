"""App initialization."""
import os
import sys

from airbrake.airbrake import AirbrakeErrorHandler
from flask import Flask, request, got_request_exception

from viper import config as viper_config
from gui.config import config_map


def log_exception(app, exception):
    env_name = os.getenv('ENV_NAME') or app.config.get('ENV_NAME')
    api_key = '5b03037d33a7371379fafc35c48af98b'
    handler = AirbrakeErrorHandler(api_key=api_key,
                                    env_name=env_name,
                                    request=request)
    handler.emit(exception, sys.exc_info())


def create_app(config_name='default'):
    """Application factory."""
    # Construct application and initialize configuration.
    app = Flask(__name__)
    config = config_map[config_name]()  # Instantiate config.
    app.config.from_object(config)
    config.init_app(app)
    got_request_exception.connect(log_exception, app)
    return app


# Expose an instance of app for production gunicorn script.
if viper_config.VIPER_IN_DEV:
    app = create_app('development')
else:
    app = create_app('production')

# Load views.
from gui import views  # noqa