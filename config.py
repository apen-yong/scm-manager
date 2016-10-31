#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/19

DEBUG = True
US_ORDER = ["192.168.1.35", "192.168.1.36"]

# 文件上传设置
UPLOAD_FOLDER = 'upload_files/'
ALLOWED_EXTENSIONS = set(['zip', ])


# jenkins
RPC_SERVER = '10.1.2.49'
RPC_PORT = '8085'

# deploy
DEPLOY_ENV = ["test", "prod"]
