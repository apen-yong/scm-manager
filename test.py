#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by follow on 2016/12/8
import time


def main():
    while True:
        try:
            new_worker = CustomGearmanWorker(JOBSERVER)
            new_worker.set_client_id(str(os.getpid()))
            new_worker.register_task(WORKER_NAME, get_result)
            new_worker.work()
        except KeyboardInterrupt, e:
            print "exit..."
            exit()
        except Exception:
            msg = traceback.format_exc()
            time.sleep(1)
            print msg
            # ut.print_r('main is error:%s' % str(msg), WORKER_NAME, uid)
