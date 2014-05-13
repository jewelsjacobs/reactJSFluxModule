"""App initialization."""
from flask import Flask, abort

from viper import config

from http_exceptions import PaymentRequired

# Initialize the app.
abort.mapping[402] = PaymentRequired
app = Flask(__name__)
app.config.from_object(config)

# Load views.
from gui import views  # noqa
