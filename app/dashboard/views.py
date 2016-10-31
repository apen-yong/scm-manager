#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/20
from flask import Blueprint, current_app, send_from_directory
import os
from flask import url_for, render_template, request
import xmlrpclib

dashboard = Blueprint('dashboard', __name__)


current_user = {
    "admin": {
        "username": "admin"
    }
}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']


@dashboard.route("/")
@dashboard.route("/index")
def index():
    return render_template('welcome.html', current_user=current_user)


@dashboard.route('/show/<system>')
def show(system):
    return render_template('system_detail.html', current_user=current_user, system=system)


@dashboard.route('/server_status/<system>/<type>')
def server_status(system, type):
    if type == qa:
        host
    return render_template('system_manager.html', current_user=current_user, system=system)


@dashboard.route('/taillog/<system>')
def taillog(system):
    return request.path


@dashboard.route('/deploy/<system>')
def deploy(system):
    return render_template('deploy_show.html', current_user=current_user, system=system)


@dashboard.route('/zipfile/<system>')
def zipfile(system):
    return render_template('file_upload.html', current_user=current_user, system=system)


@dashboard.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        file = request.files['zipfile']
        if file and allowed_file(file.filename):
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
        else:
            return "Error"
    return render_template('file_status.html', current_user=current_user, filename=file.filename)


@dashboard.route('/uploaded_file/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               filename)


@dashboard.route('/launch/job/<name>')
def jenkins(name):
    jenkins_rpc = xmlrpclib.ServerProxy(
        "http://{}:{}".format(current_app.config['jenkins_rpc_server'], current_app.config["jenkins_rpc_port"]))
    result = jenkins_rpc.BuildJob(name)
    return result
