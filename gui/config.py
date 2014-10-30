"""GUI configuration."""
import locale
import logging
import os
import sys

from logging.handlers import SysLogHandler

from airbrake.airbrake import AirbrakeErrorHandler
from flask import abort, got_request_exception, request
from flask_kvsession import KVSessionExtension

from simplekv.db.mongo import MongoStore

from gui.http_exceptions import PaymentRequired

from loggly import LogglyHandler

from viper import config as viper_config
from viper.utility import Utility


def configure_sys_log_handler(app):
    """Configure application logging to use a sys log handler."""
    gui_syslog = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL6)
    gui_syslog.setLevel(logging.DEBUG)

    gui_syslog_formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
    gui_syslog.setFormatter(gui_syslog_formatter)

    app.logger.setLevel(logging.DEBUG)
    app.logger_name = "gui"
    app.logger.addHandler(gui_syslog)

    app.logger.debug("Starting GUI.")


def log_exception(app, exception, **kwargs):
    """Log an exception to Airbrake."""
    api_key = app.config.get('AIRBRAKE_API_KEY')
    env_name = app.config.get('GUI_ENV_NAME')
    handler = AirbrakeErrorHandler(api_key=api_key, env_name=env_name, request=request)
    handler.emit(exception, sys.exc_info())


class Config(object):
    """Config base class."""

    AIRBRAKE_API_KEY = os.getenv('AIRBRAKE_API_KEY') or '5b03037d33a7371379fafc35c48af98b'
    GUI_ENV_NAME = os.getenv('GUI_ENV_NAME') or 'Base'
    MAINTENANCE = False

    def init_app(self, app):
        """Config specific application initialization."""
        # TODO(Anthony): We shouldn't be using this as config for GUI.
        # Register viper.config.
        app.config.from_object(viper_config)

        abort.mapping[402] = PaymentRequired

        # Define crypto keys for cookies.
        app.secret_key = "Super Secret Key"
        app.signing_key = "ba71f41a91e947f680d879c08982d302"

        locale.setlocale(locale.LC_ALL, '')

        # Session system.
        if not app.config['MAINTENANCE']:
            session_db = Utility.get_sessions_db_connection(viper_config)
            store = MongoStore(session_db, 'session')
            KVSessionExtension(store, app)

        # Exception logging
        got_request_exception.connect(log_exception, app)

        # General logging
        loggly_rest_handler = LogglyHandler('bb275711-4460-49e0-9b13-a9997da10d2d', tags=['flask', 'gui'])
        formatter = logging.Formatter('%(asctime)s loggly:severity=%(levelname)s, %(message)s')
        loggly_rest_handler.setFormatter(formatter)
        app.logger.addHandler(loggly_rest_handler)
        app.logger.setLevel(logging.ERROR)


class DevelopmentConfig(Config):
    """Configuration for development mode (default)."""
    API_ENDPOINT = viper_config.API_SERVER
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    GUI_ENV_NAME = os.getenv('GUI_ENV_NAME') or 'Development'
    ACTIVE_DATASTORES = ['mongodb', 'redis', 'tokumx']

    def init_app(self, app):
        """Production specific configuration."""
        super(DevelopmentConfig, self).init_app(app)

        # Disconnect Airbrake handler to minimize spam
        got_request_exception.disconnect(log_exception, app)

        # Initialize the development toolbar.
        from flask_debugtoolbar import DebugToolbarExtension  # Only import this in Dev.
        DebugToolbarExtension(app)

        # Configure logging for development mode.
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logging.captureWarnings(True)


class ProductionConfig(Config):
    """Production configuration."""
    API_ENDPOINT = ''  # FIXME: point this to the appropriate LB.
    DEBUG = False
    GUI_ENV_NAME = os.getenv('GUI_ENV_NAME') or 'Production'
    ACTIVE_DATASTORES = ['mongodb', 'redis']

    def init_app(self, app):
        """Production specific configuration."""
        super(ProductionConfig, self).init_app(app)

        # Configure application logging.
        configure_sys_log_handler(app)


class QAConfig(Config):
    """QA configuration."""
    API_ENDPOINT = ''  # FIXME: point this to the appropriate QA LB.
    DEBUG = False
    GUI_ENV_NAME = os.getenv('GUI_ENV_NAME') or 'QA'
    ACTIVE_DATASTORES = ['mongodb', 'redis']

    def init_app(self, app):
        """QA specific configuration."""
        super(QAConfig, self).init_app(app)

        # Configure application logging.
        configure_sys_log_handler(app)


class UnittestingConfig(Config):
    """Configuration for unit testing mode."""
    GUI_ENV_NAME = os.getenv('GUI_ENV_NAME') or 'Unittest'
    TESTING = True
    ACTIVE_DATASTORES = ['mongodb', 'redis', 'tokumx']


# Config mapping for application factory.
config_map = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'qa': QAConfig,
    'unittest': UnittestingConfig,
}
