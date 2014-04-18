#!/usr/bin/env python
# -*- coding: utf8 -*-
from flask_debugtoolbar import DebugToolbarExtension
from viper import config
from gui import app

app.config['API_SERVER'] = config.API_SERVER

app.secret_key = "Super Secret Key"
app.debug = True
toolbar = DebugToolbarExtension(app)
app.run(host='0.0.0.0', port=5051)
