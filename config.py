#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/19

# server info
DEBUG = True
USORDER = {
    "TEST": ["10.1.2.49", "10.1.2.49"],
    "PROD": ["192.168.1.35", "192.168.1.35"],
}

CNORDER = {
    "TEST": ["10.1.2.49"],
    "PROD": ["192.168.1.35", "192.168.1.35"],
}

# 文件上传设置
UPLOAD_FOLDER = 'upload_files/'
PACKAGE_FOLDER = 'wars/'
ALLOWED_EXTENSIONS = set(['zip', 'war'])

# jenkins
RPC_SERVER = '10.1.2.49'
RPC_PORT = '8085'

# deploy
DEPLOY_ENV = ["test", "prod"]
