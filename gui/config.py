"""GUI configuration."""
import locale

from flask import abort
from flaskext.kvsession import KVSessionExtension

from gui.canon.http_exceptions import PaymentRequired
from viper import config as viper_config
from viper.mongo_sessions import MongoDBStore


class Config(object):
    """Config base class."""

    def init_app(self, app):
        """Config specific application initialization."""
        # Register viper.config.
        # TODO(Anthony): We shouldn't be using this as config for GUI.
        app.config.from_object(viper_config)

        abort.mapping[402] = PaymentRequired

        # Define crypto keys for cookies.
        app.secret_key = "Super Secret Key"
        app.signing_key = "ba71f41a91e947f680d879c08982d302"

        # TODO: Move this somewhere else and never call it more than once
        locale.setlocale(locale.LC_ALL, '')

        # Session system.
        store = MongoDBStore(viper_config)
        KVSessionExtension(store, app)


class DevelopmentConfig(Config):
    """Configuration for development mode (default)."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    def init_app(self, app):
        """Production specific configuration."""
        super(ProductionConfig, self).init_app(app)

        # Configure application logging.
        import logging
        from logging.handlers import SysLogHandler
        viper_syslog = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL6)
        viper_syslog.setLevel(logging.DEBUG)

        viper_formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
        viper_syslog.setFormatter(viper_formatter)

        app.logger.setLevel(logging.DEBUG)
        app.logger_name = "gui"
        app.logger.addHandler(viper_syslog)

        app.logger.debug("Starting Viper")


class TestingConfig(Config):
    """Configuration for application testing."""
    TESTING = True


# Config mapping for application factory.
config_map = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
