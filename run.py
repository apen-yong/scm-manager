#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/19

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0')