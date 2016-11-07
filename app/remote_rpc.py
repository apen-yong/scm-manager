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

app = Flask(__name__)
handler = XMLRPCHandler('api')
handler.connect(app, '/api')
j = jenkins.Jenkins("http://127.1:8080", 'rpcuser', '2266bcc74441b07e9c50ba468a620199')
manager_host = '10.1.2.49'
package_root = "/opt/scm-manager/wars"
tomcat_root_7 = "/home/scm/apache-tomcat-7.0.39"
tomcat_root_8 = "/home/mes/apache-tomcat-8.0.24"
tomcat_root_cscm = "/home/cscm/apache-tomcat-7.0.39"


@handler.register
def Hello(name='follow'):
    if not name:
        raise Fault('WTF')
    return "hello %s" % name


@handler.register
def GetInfo():
    data = j.get_info()
    print data
    return data


@handler.register
def GetQueueInfo():
    data = j.get_queue_info()
    print data
    return data


@handler.register
def GetJobs():
    data = j.get_jobs()
    print data
    return data


@handler.register
def GetBuildConsoleOutput(name, number):
    data = j.get_build_console_output(name, number)
    d1 = base64.b64encode(data)
    print d1
    return d1


@handler.register
def GetJobInfo(n):
    data = j.get_job_info(n)
    return str(data)


@handler.register
def BuildJob(n):
    data = j.build_job(n)
    return data


@handler.register
def DoCmd(operate, node_info):
    print "cmd is  %s" % operate
    (system, ver) = re.split("-", node_info)
    tomcat_port = "28080" if re.match('cnshipping', system) else "8080"
    if re.match('manufacturing', system):
        tomcat_root = tomcat_root_8
        package_name = "mes.{}.war".format(system)
    elif re.match('material', system):
        tomcat_root = tomcat_root_8
        package_name = "{}.war".format(system)
    elif re.match('cnshipping', system):
        tomcat_root = tomcat_root_cscm
        package_name = "scm.war"
    else:
        tomcat_root = tomcat_root_7
        package_name = "scm.war"
    if operate == "start":
        command = "su - scm -c {}/bin/startup.sh".format(tomcat_root)
        status = [os.system(command), "nothing"]
        con = False
        while not con:
            pidinfo = commands.getstatusoutput(
                'netstat -nlp | grep {} | awk \'{{print $7}}\' | cut -d / -f 1'.format(tomcat_port))
            print "pid is:%s" % str(pidinfo[1])
            if not re.match("\d", pidinfo[1]):
                print "sleep"
                time.sleep(1)
            else:
                con = True
    elif operate == "update":
        command = "rm -fr {}/work/*; rm -fr {}/webapps/*; cp -a {}/{}/*.war {}/webapps/{}".format(tomcat_root,
                                                                                                      tomcat_root,
                                                                                                      package_root,
                                                                                                      node_info,
                                                                                                      tomcat_root,
                                                                                                      package_name)
        time.sleep(2)
        status = commands.getstatusoutput(command)
    else:
        pid = \
            commands.getstatusoutput(
                'netstat -nlp | grep {} | awk \'{{print $7}}\' | cut -d / -f 1'.format(tomcat_port))[1]
        if re.match("\d", pid):
            command = "kill -9 %s" % pid
            status = commands.getstatusoutput(command)
            print "start to kill %s" % pid
            print status
        time.sleep(2)
    return status


@handler.register
def GetProcessInfo(system, ver):
    status = {}
    tomcat_port = "28080" if system == 'cnshipping' else "8080"
    package_name = "scm.war"
    if system == 'cnshipping':
        tomcat_root = tomcat_root_7
    elif system == "manufacturing" or system == "meterial":
        tomcat_root = tomcat_root_8
        package_name = "{}.war".format(system)
    else:
        tomcat_root = tomcat_root_7
    pidinfo = commands.getstatusoutput(
        'netstat -nlp | grep :{} | awk \'{{print $7}}\' | cut -d / -f 1'.format(tomcat_port))
    status['qa_mtime'] = commands.getoutput(
        'stat  {}/webapps/{} | grep \'^Modify\' | cut  -d " " -f 2-3 | cut -d . -f1'.format(tomcat_root, package_name))
    status['newest_filename'] = commands.getoutput('ls /opt/scm-manager/wars/{}-{}/'.format(system, ver)).lstrip()
    status['newest_mtime'] = commands.getoutput(
        'stat  /opt/scm-manager/wars/{}-{}/*.war | grep \'^Modify\' | cut  -d " " -f 2-3 | cut -d . -f1'.format(system,
                                                                                                                ver))
    status['load_info'] = commands.getoutput(' w |grep \'load\' | cut -d , -f 4,5,6')
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
    file_url = "http://{}:{}/uploaded_file/{}?folder=SCM-{}".format(manager_host, "80", filename, path)
    download_dir = "/opt/scm-manager/wars/{}".format(path)
    download_command = "aria2c -s 2 -x 2 {} -d {} -D".format(file_url, download_dir)
    print "Start to download file {}".format(download_command)
    commands.getoutput("rm -f {}/*.war".format(download_dir))
    output = commands.getoutput(download_command)
    print output
    return output


app.run('0.0.0.0', port=8085, debug=True)
