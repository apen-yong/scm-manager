#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/20
import base64

from flask import Blueprint, current_app, send_from_directory, redirect
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
    # return render_template('system_detail.html', current_user=current_user, system=system)
    return redirect(url_for('dashboard.deploy', system=system, wars="wars"))


@dashboard.route('/server_status/<system>/<ver>')
def server_status(system, ver):
    hosts = current_app.config[system.upper()].get(ver.upper())
    status = {}
    for h in hosts:
        rpc_url = "http://{}:{}/api".format(h, current_app.config["RPC_PORT"])
        try:
            jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
            status[h] = jenkins_rpc.GetProcessInfo(system, ver)
        except socket.error, e:
            print "Connect error: {}".format(e)
            status[h] = {}
        except xmlrpclib.Fault, e:
            print "rpc error: {}".format(e)
            status[h] = {}
        if h in current_app.config["QUARTZ_SERVER"]:
            status[h]["is_quartz"] = True
        else:
            status[h]["is_quartz"] = False
    return render_template('system_manager.html', current_user=current_user, system=system, status=status, ver=ver)


@dashboard.route('/logger/<system>/<taillog>')
def taillog(system, taillog):
    return "hello"


@dashboard.route('/deploy/<system>/<wars>')
def deploy(system, wars):
    try:
        rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'], current_app.config["RPC_PORT"])
        jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
        deploy_env = current_app.config['DEPLOY_ENV']
        jobdata = []
        info = jenkins_rpc.GetInfo()

        for job in info['jobs']:
            if not re.match(system, job['name']):
                continue
            color = job['color']
            job_info = eval(jenkins_rpc.GetJobInfo(job['name']))
            try:
                lastSuccessfulBuildNumber = job_info['lastSuccessfulBuild']['number']
                job_info['lastSuccessfulBuildDetail'] = jenkins_rpc.GetBuildInfo(job['name'], lastSuccessfulBuildNumber)
            except TypeError, e:
                return "Please run job manually"

            try:
                lastUnsuccessfulBuildNumber = job_info['lastUnsuccessfulBuild']['number']
                job_info['lastUnsuccessfulBuildNumber'] = jenkins_rpc.GetBuildInfo(job['name'],
                                                                                   lastUnsuccessfulBuildNumber)
                job_info['lastUnsuccessfulBuildDetail'] = jenkins_rpc.GetBuildInfo(job['name'],
                                                                                   lastUnsuccessfulBuildNumber)
            except TypeError, e:
                job_info['lastUnsuccessfulBuildDetail'] = 'null'

            try:
                lastCompletedBuildNumber = job_info['lastCompletedBuild']['number']
                job_info['lastCompletedBuildDetail'] = jenkins_rpc.GetBuildInfo(job['name'], lastCompletedBuildNumber)
            except TypeError, e:
                job_info['lastCompletedBuildNumber'] = None

            if re.search("test", job['name']):
                jobdata.insert(0, {job['name']: job_info})
            else:
                jobdata.insert(1, {job['name']: job_info})

    except socket.error, e:
        return "Can not connect to remote jenkins. {}".format(e)
    return render_template('deploy_show.html', current_user=current_user, system=system, deploy_env=deploy_env,
                           job_info=jobdata)


@dashboard.route('/zipfile/<system>/<zipfile>')
def zipfile(system, zipfile):
    return render_template('file_upload.html', current_user=current_user, system=system)


@dashboard.route('/upload/<system>', methods=['POST', 'GET'])
def upload(system):
    # TODO 上传文件后生成标准的文件名 避免出现文件冲突
    ver = request.form['system_ver']
    zip_file_name = get_package_prefix(system) + "-{}.zip".format(
        time.strftime("%Y%M%d-%S", time.localtime(time.time())))
    if request.method == 'POST':
        file_uploaded = request.files['zipfile']
        if file_uploaded and allowed_file(file_uploaded.filename):
            file_uploaded.save(
                os.path.join(current_app.config['UPLOAD_FOLDER'], "SCM-zipfiles", zip_file_name))
        else:
            return "Error"
    for h in current_app.config[system.upper()][ver.upper()]:
        rpc_url = "http://{}:{}/api".format(h, current_app.config["RPC_PORT"])
        remote_rpc = xmlrpclib.ServerProxy(rpc_url)
        remote_rpc.DownloadPackage("zipfiles", zip_file_name)
        unzip_info = remote_rpc.UpdateZipFile(zip_file_name, system)
        inflating_data = re.split("\n", unzip_info[1])
    return render_template('file_status.html', zip_file_name=zip_file_name, current_user=current_user,
                           filename=file_uploaded.filename,
                           hosts=current_app.config[system.upper()][ver.upper()], info=inflating_data, system=system)


@dashboard.route('/uploaded_file/<filename>')
def uploaded_file(filename):
    if re.search("zip", filename):
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], request.args.get('folder'))
        return send_from_directory(path, filename)
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
        if j.get('name') == name:
            # print "Get to_c info to render.{0}".format(str(j))
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


@dashboard.route('/cmd/<address>/<cmd>/<node_info>')
def do_cmd(address, cmd, node_info):
    rpc_url = "http://{}:{}/api".format(address, current_app.config["RPC_PORT"])
    jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
    if address in current_app.config["QUARTZ_SERVER"]:
        is_quartz = True
    else:
        is_quartz = False
    data = jenkins_rpc.DoCmd(cmd, node_info, is_quartz)
    json_obj = '{"code":%s, "info":"%s"}' % (data[0], data[1])
    print json_obj
    return str(json_obj)


@dashboard.route('/sync/<system>/<ver>')
def package_sync(system, ver):
    address = current_app.config[system.upper()]
    try:
        for host in address.get(ver.upper()):
            jenkins_rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'],
                                                        current_app.config["RPC_PORT"])
            jenkins_rpc = xmlrpclib.ServerProxy(jenkins_rpc_url)
            job_info = eval(jenkins_rpc.GetJobInfo("{}-{}".format(system, ver).lower()))
            # TODO 解决如果次打包失败，当前打包ID计算错误的问题
            if not job_info['lastUnsuccessfulBuild']:
                lastUnsuccessfulBuildNumber = 0
            else:
                lastUnsuccessfulBuildNumber = job_info['lastUnsuccessfulBuild']['number']
            if not job_info['lastSuccessfulBuild']:
                lastSuccessfulBuildNumber = 0
            else:
                lastSuccessfulBuildNumber = job_info['lastSuccessfulBuild']['number']

            if lastSuccessfulBuildNumber < lastUnsuccessfulBuildNumber:
                package_id = lastUnsuccessfulBuildNumber + 1
            else:
                package_id = lastSuccessfulBuildNumber + 1
            date = time.strftime("%Y%m%d", time.localtime(time.time()))
            package_name = "SCM-{}-{}-{}.war".format(system, date, package_id)
            folder = "{}-{}".format(system, ver)

            remote_rpc_url = "http://{}:{}/api".format(host, current_app.config["RPC_PORT"])
            remote_prc = xmlrpclib.ServerProxy(remote_rpc_url)
            remote_prc.DownloadPackage(folder, package_name)
    except socket.error, e:
        print "connect rpc server error:{}".format(e)
        return "Error: {}".format(e)
    return "Success start download file."


@dashboard.route('/api/get_console')
def get_console():
    name = request.args.get('name')
    deploy_id = request.args.get('id')
    if deploy_id == 'magic':
        return ''
    rpc_url = "http://{}:{}/api".format(current_app.config['RPC_SERVER'], current_app.config["RPC_PORT"])
    jenkins_rpc = xmlrpclib.ServerProxy(rpc_url)
    log = jenkins_rpc.GetBuildConsoleOutput(name, int(deploy_id))
    human_readable_log = re.sub("\n", "</br>", base64.b64decode(log).decode("utf-8"))
    return human_readable_log


@dashboard.route('/api/switch_release')
def switch_release():
    release = request.args.get('release')
    server = request.args.get('server')
    node_info = request.args.get('node_info')
    rpc_url = "http://{}:{}/api".format(server, current_app.config["RPC_PORT"])
    print rpc_url, release, node_info
    try:
        remote_rpc = xmlrpclib.ServerProxy(rpc_url)
        remote_rpc.SwitchRelease(release, node_info)
    except socket.error, e:
        print "connect rpc server error:{}".format(e)
        return "Error: {}".format(e)
    return "success"


def get_package_prefix(system):
    if re.match('manufacturing', system):
        package_prefix = "mes.{}".format(system)
    elif re.match('material', system):
        package_prefix = system
    else:
        package_prefix = "scm"
    return package_prefix
