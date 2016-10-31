#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/19
from flask import Flask
from .dashboard.views import dashboard


def create_app():
    app = Flask('__name__')
    app.config.from_object("config")
    app.register_blueprint(dashboard)
    return app
