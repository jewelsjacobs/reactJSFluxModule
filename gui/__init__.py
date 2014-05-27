"""App initialization."""
from flask import Flask

from gui.config import config_map
from viper import config as viper_config


# TODO(Anthony): if we use blueprints, then we can simply register the blueprint
# below and then we won't have to check for VIPER_IN_DEV.
def create_app(config_name='default'):
    """Application factory."""
    # Construct application and initialize configuration.
    app = Flask(__name__)
    config = config_map[config_name]()  # Instantiate config.
    app.config.from_object(config)
    config.init_app(app)

    return app

# Expose an instance of app for production gunicorn script.
if viper_config.VIPER_IN_DEV:
    app = create_app('development')
else:
    app = create_app('production')

# Load views.
from gui import views  # noqa
