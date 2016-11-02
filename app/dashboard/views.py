#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/20
from flask import Blueprint, current_app, send_from_directory
import os
from flask import url_for, render_template, request
import xmlrpclib
import re
import socket
import time

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


@dashboard.route('/server_status/<system>/<ver>')
def server_status(system, ver):
    hosts = current_app.config[system.upper()].get(ver.upper())
    status = {}
    for h in hosts:
        rpc_url = "http://{}:{}/api".format(h, current_app.config["RPC_PORT"])
        try:
            jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
            status[h] = jenkins_rpc.GetProcessInfo()
        except socket.error, e:
            print "Connect error: {}".format(e)
            status[h] = {}
    return render_template('system_manager.html', current_user=current_user, system=system, status=status)


@dashboard.route('/taillog/<system>')
def taillog(system):
    return request.path


@dashboard.route('/deploy/<system>')
def deploy(system):
    try:
        rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'], current_app.config["RPC_PORT"])
        jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
        deploy_env = current_app.config['DEPLOY_ENV']
        jobdata = {}
        info = jenkins_rpc.GetInfo()

        for job in info['jobs']:
            if not re.match(system, job['name']):
                continue
            color = job['color']
            job_info = eval(jenkins_rpc.GetJobInfo(job['name']))
            jobdata[job['name']] = job_info
            try:
                lastSuccessfulBuildNumber = job_info['lastSuccessfulBuild']['number']
                job_info['lastSuccessfulBuildDetail'] = jenkins_rpc.GetBuildInfo(job['name'], lastSuccessfulBuildNumber)
            except TypeError, e:
                return "Please run job manually"

            try:
                lastUnsuccessfulBuildNumber = job_info['lastUnsuccessfulBuild']['number']
                job_info['lastUnsuccessfulBuildNumber'] = jenkins_rpc.GetBuildInfo(job['name'], lastUnsuccessfulBuildNumber)
                job_info['lastUnsuccessfulBuildDetail'] = jenkins_rpc.GetBuildInfo(job['name'], lastUnsuccessfulBuildNumber)
            except TypeError, e:
                job_info['lastUnsuccessfulBuildDetail'] = 'null'

            try:
                lastCompletedBuildNumber = job_info['lastCompletedBuild']['number']
                job_info['lastCompletedBuildDetail'] = jenkins_rpc.GetBuildInfo(job['name'], lastCompletedBuildNumber)
            except TypeError, e:
                job_info['lastCompletedBuildNumber'] = None
    except socket.error, e:
        return "Can not connect to remote jenkins. {}".format(e)
    return render_template('deploy_show.html', current_user=current_user, system=system, deploy_env=deploy_env,
                           job_info=jobdata)


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
    if re.search("zip", filename):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                                   filename)
    else:
        path = os.path.join(current_app.config['PACKAGE_FOLDER'], request.args.get('folder'))
        return send_from_directory(path, filename)


@dashboard.route('/api/deploy/<name>')
def jenkins(name):
    rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'], current_app.config["RPC_PORT"])
    jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
    # 同时对测试环境和正式环境开始打包
    try:
        for e in current_app.config['DEPLOY_ENV']:
            jenkins_rpc.BuildJob("{}-{}".format(name, e))
    except Exception, e:
        print "Error, {}".format(e)
    return "true"


@dashboard.route('/api/query/<name>')
def query_status(name):
    rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'], current_app.config["RPC_PORT"])
    jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
    info = jenkins_rpc.GetInfo()
    for j in info['jobs']:
        print j
        if j.get('name') == name:
            print "Get to_c info to render.{0}".format(str(j))
            if j.get('color') == 'blue':
                return '<img src="/static/img/blue.png" tooltip="运行中" ' \
                       'style="width: 18px; height: 18px; " ><img>打包完成'
            elif j.get('color') == 'blue_anime':
                return '<img src="/static/img/blue_anime.gif" tooltip="运行中" ' \
                       'style="width: 18px; height: 18px;" ><img>正在打包'
            elif j.get('color') == 'red':
                return '<img src="/static/img/red.png" tooltip="Failed" ' \
                       'style="width: 18px; height: 18px;" ><img>失败'
            elif j.get('color') == 'red_anime':
                return '<img src="/static/img/red_anime.gif" tooltip="运行中" ' \
                       'style="width: 18px; height: 18px;" ><img>正在打包'
        else:
            continue
    return 'false'


@dashboard.route('/cmd/<address>/<cmd>')
def do_cmd(address, cmd):
    rpc_url = "http://{}:{}/api".format(address, current_app.config["RPC_PORT"])
    jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
    data = jenkins_rpc.DoCmd(cmd)
    return "data"


@dashboard.route('/sync/<system>/<ver>')
def package_sync(system, ver):
    address = current_app.config[system.upper()]
    try:
        for host in address.get(ver.upper()):
            jenkins_rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'],
                                                        current_app.config["RPC_PORT"])
            jenkins_rpc = xmlrpclib.ServerProxy(jenkins_rpc_url)
            job_info = eval(jenkins_rpc.GetJobInfo("{}-{}".format(system, ver).lower()))
            lastSuccessfulBuildNumber = job_info['lastSuccessfulBuild']['number'] + 1
            date = time.strftime("%Y%m%d", time.localtime(time.time()))
            package_name = "SCM-{}-{}-{}.war".format(system, date, lastSuccessfulBuildNumber)
            folder = "{}-{}".format(system, ver)

            remote_rpc_url = "http://{}:{}/api".format(host, current_app.config["RPC_PORT"])
            remote_prc = xmlrpclib.ServerProxy(remote_rpc_url)
            remote_prc.DownloadPackage(folder, package_name)
    except socket.error, e:
        print "connect rpc server error:{}".format(e)
        return "Error: {}".format(e)
    return "Success start download file."
