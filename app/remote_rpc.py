#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/10/28


from flask import Flask
from flaskext.xmlrpc import XMLRPCHandler, Fault
import jenkins
import time
import base64
import commands
# from jinja2.nodes import Output
import os
# import MySQLdb
import re

app = Flask(__name__)
handler = XMLRPCHandler('api')
handler.connect(app, '/api')
j = jenkins.Jenkins("http://127.1:8080", 'rpcuser', '2266bcc74441b07e9c50ba468a620199')
manager_host = '10.1.2.49'
tomcat_root = "/home/scm/apache-tomcat-7.0.39"
tomcat_port = "8080"
package_root = "/opt/scm-manager/wars"


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


# @handler.register
# def CleanTheMess():
#     db = MySQLdb.connect("10.168.2.125", "svn", "svnpassword", "svntool")
#     cursor = db.cursor()
#     sql = "update scm_projectstatus set status=0,approve_status=0 where status > 0 and approve_status = 3"
#     sql2 = "delete from scm_proj_with_user where projectid=(select projectid from scm_projectstatus where status > 0 and approve_status = 3)"
#     cursor.execute(sql)
#     cursor.execute(sql2)
#     db.commit()
#     db.close()
#     return


@handler.register
def DoCmd(c):
    print "cmd is  %s" % c
    if c == "start":
        command = "su - scm -c {}/bin/startup.sh".format(tomcat_root)
        status = [os.system(command), "nothing"]
        con = False
        while not con:
            pidinfo = commands.getstatusoutput(
                'netstat -nlp | grep {} | awk \'{print $7}\' | cut -d / -f 1'.format(tomcat_port))
            print "pid is:%s" % str(pidinfo[1])
            if not re.match("\d", pidinfo[1]):
                print "sleep"
                time.sleep(1)
            else:
                con = True
    elif c == "update":
        command = "rm -fr {}/work/*; rm -fr {}/webapps/*; cp -a {}/*.war {}/webapps/scm.war".format(tomcat_root,
                                                                                                    tomcat_root,
                                                                                                    package_root,
                                                                                                    tomcat_root)
        time.sleep(2)
        status = commands.getstatusoutput(command)
    else:
        pid = commands.getstatusoutput('netstat -nlp | grep {} | awk \'{print $7}\' | cut -d / -f 1'.format(tomcat_port))[1]
        if re.match("\d", pid):
            command = "kill -9 %s" % pid
            status = commands.getstatusoutput(command)
            print "start to kill %s" % pid
            print status
        time.sleep(2)
    return status


@handler.register
def GetProcessInfo():
    status = {}
    pidinfo = commands.getstatusoutput('netstat -nlp | grep 8080 | awk \'{print $7}\' | cut -d / -f 1')
    status['qa_mtime'] = commands.getoutput(
        'stat  /home/scm/apache-tomcat-7.0.39/webapps/scm.war | grep \'^Modify\' | cut  -d " " -f 2-3 | cut -d . -f1')
    status['newest_filename'] = commands.getoutput('ls /opt/scm-manager/wars/').lstrip()
    status['newest_mtime'] = commands.getoutput(
        'stat  /opt/scm-manager/wars/*.war | grep \'^Modify\' | cut  -d " " -f 2-3 | cut -d . -f1')
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
    download_dir = "/opt/scm-manager/wars"
    download_command = "aria2c -s 2 -x 2 {} -d {} -D".format(file_url, download_dir)
    commands.getoutput("rm -f {}/*.war".format(download_dir))
    output = commands.getoutput(download_command)
    print output
    return output


app.run('0.0.0.0', port=8085, debug=True)
