#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/28


from flask import Flask
from flaskext.xmlrpc import XMLRPCHandler, Fault
import jenkins
import time
import base64
import commands
import os
import re
import subprocess

app = Flask(__name__)
app.config.from_pyfile("../config.py")
handler = XMLRPCHandler('api')
handler.connect(app, '/api')
j = jenkins.Jenkins("http://127.1:8080", 'rpcuser', '2266bcc74441b07e9c50ba468a620199')

@handler.register
def Hello(name='follow'):
    if not name:
        raise Fault('WTF')
    return "hello %s" % name


@handler.register
def GetInfo():
    data = j.get_info()
    return data


@handler.register
def GetQueueInfo():
    data = j.get_queue_info()
    return data


@handler.register
def GetJobs():
    data = j.get_jobs()
    return data


@handler.register
def GetBuildConsoleOutput(name, number):
    data = j.get_build_console_output(name, number)
    data_encode = base64.b64encode(data.encode("utf-8"))
    return data_encode


@handler.register
def GetJobInfo(n):
    data = j.get_job_info(n)
    return str(data)


@handler.register
def BuildJob(n):
    data = j.build_job(n)
    return data


@handler.register
def DoCmd(operate, node_info, is_quartz):
    print "cmd is  %s" % operate
    (system, ver) = re.split("-", node_info)
    tomcat_port = "28080" if re.match('cnshipping', system) else "8080"
    tomcat_root = get_tomcat_root(system)
    tomcat_user = get_tomcat_user(system)
    package_name = get_package_prefix(system) + ".war"
    if operate == "start":
        if system == "fedexClient":
            command = "su - {} -c startscm".format(tomcat_user)
        else:
            command = "su - {} -c {}/bin/startup.sh".format(tomcat_user, tomcat_root)
        child = subprocess.Popen(command, shell=True)
        status = [child.pid, "nothing"]
        con = False
        while not con:
            pidinfo = commands.getstatusoutput(
                'netstat -nlp | grep :{} | awk \'{{print $7}}\' | cut -d / -f 1'.format(tomcat_port))
            print "pid is:%s" % str(pidinfo[1])
            if not re.match("\d", pidinfo[1]):
                print "sleep"
                time.sleep(1)
            else:
                con = True
    elif operate == "update":
        copy_command = "rm -fr {}/work/*; rm -fr {}/webapps/{}*;" \
                       " cp -ap {}/{}/*.war {}/webapps/{}".format(tomcat_root,
                                                                  tomcat_root,
                                                                  get_package_prefix(system),
                                                                  app.config['RR_PACKAGE_ROOT'],
                                                                  node_info,
                                                                  tomcat_root,
                                                                  package_name)
        copy_release = "cp -ap {}/{}/*.war {}/release-{}/".format(app.config['RR_PACKAGE_ROOT'], node_info, app.config['RR_PACKAGE_ROOT'], node_info)
        unzip_command = "sudo -u {} unzip -qo {}/webapps/{} -d {}/webapps/{}".format(tomcat_user, tomcat_root,
                                                                                     package_name, tomcat_root,
                                                                                     get_package_prefix(system))
        subprocess.call(copy_command, shell=True)
        subprocess.call(copy_release, shell=True)
        status = subprocess.call(unzip_command, shell=True)
        if not is_quartz:
            del_quartz_config = "sed -i '/ref bean/d' {}/webapps/{}/WEB-INF/classes/" \
                                "schedule/applicationContext-quartz.xml".format(tomcat_root, get_package_prefix(system))
            status = subprocess.call(del_quartz_config, shell=True)
        if system == "manufacturing":
            chmod_cmd = "chmod 755 /home/mes/apache-tomcat-8.0.24/webapps/mes.manufacturing/WEB-INF/cgi/*"
            subprocess.call(chmod_cmd, shell=True)
        return [status, "nothing"]
    else:
        pid = \
            commands.getstatusoutput(
                'netstat -nlp | grep :{} | awk \'{{print $7}}\' | cut -d / -f 1'.format(tomcat_port))[1]
        if re.match("\d", pid):
            command = "kill -9 %s" % pid
            status = commands.getstatusoutput(command)
            print "start to kill %s" % pid
            print status
        else:
            status = [0, "java is not running"]
        time.sleep(2)
    return status


@handler.register
def GetProcessInfo(system, ver):
    status = {}
    tomcat_port = "28080" if system == 'cnshipping' else "8080"
    tomcat_root = get_tomcat_root(system)
    package_name = get_package_prefix(system) + ".war"
    pidinfo = commands.getstatusoutput(
        'netstat -nlp | grep :{} | awk \'{{print $7}}\' | cut -d / -f 1'.format(tomcat_port))
    status['qa_mtime'] = commands.getoutput(
        'stat  {}/webapps/{} | grep \'^Modify\' | cut  -d " " -f 2-3 | cut -d . -f1'.format(tomcat_root, package_name))
    status['newest_filename'] = commands.getoutput('ls {}/{}-{}/'.format(app.config['RR_PACKAGE_ROOT'], system, ver)).lstrip()
    status['aria_status'] = commands.getstatusoutput('ps -ef| grep aria| grep -v grep')
    status['newest_mtime'] = commands.getoutput(
        'stat  {}/{}-{}/*.war | grep \'^Modify\' | cut  -d " " -f 2-3 | cut -d . -f1'.format(app.config['RR_PACKAGE_ROOT'], system,
                                                                                             ver))
    status['load_info'] = commands.getoutput(' w |grep \'load\' | cut -d , -f 4,5,6')
    status['release'] = get_release_info(system, ver)
    status['ver'] = app.config['RR_VERSION']
    if pidinfo[1] == "":
        return status
    else:
        status['pid'] = pidinfo[1]
        status['uptime'] = commands.getoutput('ps -p %s -o lstart | sed -n \'2p\'' % pidinfo[1])
        status['mem_info'] = commands.getoutput("cat /proc/{}/status  | grep RSS".format(pidinfo[1]))
        return status


@handler.register
def GetBuildInfo(name, number):
    data = j.get_build_info(name, number)
    t1 = str(data['timestamp'])
    duration = data['duration'] / 1000
    t2 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(t1[:10])))
    data['timestamp'] = t2
    data['duration'] = duration
    data['changeSet'] = 'changeSet'
    return data  # xml-rpc 不能使用长整数  WTF


@handler.register
def DownloadPackage(path, filename):
    file_url = "http://{}:{}/uploaded_file/{}?folder=SCM-{}".format(app.config['RR_MANAGER_HOST'], "80", filename, path)
    download_dir = "{}/wars/{}".format(app.config['RR_APP_ROOT'], path)
    download_command = "aria2c -s 2 -x 2 {} -d {} -D".format(file_url, download_dir)
    print "Start to download file {}".format(download_command)
    commands.getoutput("rm -f {}/*.war".format(download_dir))
    output = commands.getoutput(download_command)
    print output
    return output


@handler.register
def UpdateZipFile(filename, system):
    # 解压缩到webapps目录 要求zip包解压后是项目名称开头的文件树
    tomcat_root = get_tomcat_root(system)
    tomcat_user = get_tomcat_user(system)
    for i in xrange(10):
        if commands.getstatusoutput('ps -ef| grep aria| grep -v grep')[0] == 0:
            time.sleep(1)
        else:
            unzip_info = commands.getstatusoutput(
                "sudo -u {} unzip -o {}/wars/zipfiles/{} -d {}/webapps/{}".format(tomcat_user, app.config['RR_APP_ROOT'], filename,
                                                                                  tomcat_root,
                                                                                  get_package_prefix(system)))
            break
    print unzip_info
    return unzip_info


@handler.register
def SwitchRelease(release, node_info):
    try:
        select_release = "{}/release-{}/{}".format(app.config['RR_PACKAGE_ROOT'], node_info, release)
        current_release = " {}/{}/*.war".format(app.config['RR_PACKAGE_ROOT'], node_info)
        cmd = "rm -f {}; cp -p {} {}/{}/".format(current_release, select_release, app.config['RR_PACKAGE_ROOT'], node_info)
        status = subprocess.call(cmd, shell=True)
    except Exception, e:
        status = 1
    return status


def get_release_info(system, ver):
    file_path = "{}/release-{}-{}/".format(app.config['RR_PACKAGE_ROOT'], system, ver)
    release = {}
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    for f in subprocess.check_output("ls -t -l --time-style=+%Y%m%d-%H:%M --block-size=M {}".format(file_path), shell=True).split("\n"):
        split_info = re.split("\s+", f)
        if len(split_info) < 7:
            # 如果是目录就跳过去
            continue
        try:
            release["data"].append(split_info)
        except KeyError:
            release["data"] = [split_info]
        if len(release["data"]) >= 10:
            # 如果获取的文件超过10个 就退出循环
            break
    if not release.has_key("data"):
        release['data'] = []
    return release["data"]


def get_tomcat_root(system):
    if re.match('manufacturing', system):
        tomcat_root = app.config['RR_TOMCAT_ROOT_8']
    elif re.match('material', system):
        tomcat_root = app.config['RR_TOMCAT_ROOT_8']
    elif re.match('cnshipping', system):
        tomcat_root = app.config['RR_TOMCAT_ROOT_CSCM']
    elif re.match('usshipping', system):
        tomcat_root = app.config['RR_TOMCAT_ROOT_ISCM']
    elif re.match("jco", system):
        tomcat_root = app.config['RR_TOMCAT_ROOT_JCO']
    elif re.match("fedexClient", system):
        tomcat_root = app.config['RR_TOMCAT_ROOT_FEDEX']
    else:
        tomcat_root = app.config['RR_TOMCAT_ROOT_7']
    return tomcat_root


def get_package_prefix(system):
    if re.match('manufacturing', system):
        package_prefix = "mes.{}".format(system)
    elif re.match('material', system):
        package_prefix = system
    elif re.match('jco', system):
        package_prefix = "SAPJCOLayers"
    elif re.match('fedexClient', system):
        package_prefix = "usshippingclient"
    else:
        package_prefix = "scm"
    return package_prefix


def get_tomcat_user(system):
    if re.match("cnshipping", system):
        user = app.config['RR_CSCM_USER']
    elif re.match("usshipping", system):
        user = app.config['RR_ISCM_USER']
    elif re.match("jco", system):
        user = app.config['RR_JCO_USER']
    elif re.match("manufacturing|material", system):
        user = app.config['RR_MES_USER']
    else:
        user = app.config['RR_SCM_USER']
    return user


app.run('0.0.0.0', port=8085, use_reloader=True, debug=True)
