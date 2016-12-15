#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/19

# server info
DEBUG = True
USORDER = {
    "TEST": ["192.168.1.35", ],
    "PROD": ["192.168.1.127", ],
}

CNORDER = {
    "TEST": ["172.15.120.9"],
    "PROD": ["172.15.120.12",],
}

JPORDER = {
    "TEST": ["192.168.1.37"],
    "PROD": ["192.168.1.126",],
}

MANUFACTURING = {
    "TEST": ["10.168.3.84"],
    "PROD": ["10.168.2.164", "10.168.2.80"],
}

CNSHIPPING = {
    "TEST": ["10.168.3.85"],
    "PROD": ["10.168.2.163",],
}

USSHIPPING = {
    "TEST": ["10.168.3.85"],
    "PROD": ["10.168.2.163",],
}

MATERIAL = {
    "TEST": ["10.168.3.84"],
    "PROD": ["10.168.2.166",],
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

# 定时任务服务器
QUARTZ_SERVER = ["10.168.2.80", "192.168.1.127", "172.15.120.12", "192.168.1.126", "10.168.2.163", "10.168.2.166",
                 "192.168.1.35", "172.15.120.9", "192.168.1.37", "10.168.3.84", "10.168.3.85"]
