"""App initialization."""
from flask import Flask
from viper import config as viper_config

from gui.config import config_map
from gui.raxsso import raxsso_blueprint


def create_app(config_name='default'):
    """Application factory."""
    # Construct application and initialize configuration.
    app = Flask(__name__)
    config = config_map[config_name]()  # Instantiate config.
    app.config.from_object(config)
    config.init_app(app)

    # Register blueprints.
    app.register_blueprint(raxsso_blueprint)

    return app


# Some heuristics to determine which configuration to use for the application.
if viper_config.VIPER_IN_QA:
    app = create_app(config_name='qa')
elif viper_config.VIPER_IN_DEV:
    app = create_app(config_name='development')
else:
    app = create_app(config_name='production')

# Load views.
from gui import views  # noqa
