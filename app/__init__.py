from flask import Flask

from viper import config

from sign_up.views import sign_up_blueprint


app = Flask(__name__)
app.config.from_object(config)
app.register_blueprint(sign_up_blueprint)


if config.VIPER_IN_DEV:
    app.debug = True  # disabled in PRODUCTION, and forces logging to syslog
else:
    app.debug = False

if not app.debug:
    import logging
    from logging.handlers import SysLogHandler
    viper_syslog = SysLogHandler(address = '/dev/log', facility = SysLogHandler.LOG_LOCAL6)
    viper_syslog.setLevel(logging.DEBUG)

    viper_formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
    viper_syslog.setFormatter(viper_formatter)

    app.logger.setLevel(logging.DEBUG)
    app.logger_name = "viper_gui"
    app.logger.addHandler(viper_syslog)

    app.logger.debug("Starting Viper")