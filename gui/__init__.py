"""App initialization."""
from flask import Flask

from viper import config

# Initialize the app.
app = Flask(__name__)
app.config.from_object(config)

# Load views.
from gui import views  # noqa
