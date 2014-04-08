#!/usr/bin/env python
# -*- coding: utf8 -*-
from viper import config
from gui import app

app.config['API_SERVER'] = config.API_SERVER

app.secret_key = "Super Secret Key"
app.run(debug=True, host='0.0.0.0', port=5001)
