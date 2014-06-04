"""GUI configuration."""
import locale

from flask import abort
from flaskext.kvsession import KVSessionExtension

from gui.http_exceptions import PaymentRequired
from viper import config as viper_config
from viper.mongo_sessions import MongoDBStore


class Config(object):
    """Config base class."""

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
        gui_syslog = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL6)
        gui_syslog.setLevel(logging.DEBUG)

        gui_syslog_formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
        gui_syslog.setFormatter(gui_syslog_formatter)

        app.logger.setLevel(logging.DEBUG)
        app.logger_name = "gui"
        app.logger.addHandler(gui_syslog)

        app.logger.debug("Starting GUI.")


class UnittestingConfig(Config):
    """Configuration for unit testing mode."""
    TESTING = True


# Config mapping for application factory.
config_map = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'unittest': UnittestingConfig,
}
