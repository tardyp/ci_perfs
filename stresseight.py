import os
import time

import argh

import psutil
import requests


@argh.arg('num_builds', type=int)
@argh.arg('num_workers', type=int)
@argh.arg('config_kind', type=str)
def main(num_builds, num_workers, config_kind):
    for w in os.listdir(os.curdir):
        if w.startswith('worker'):
            print "cleanup", w
            os.system("buildslave stop {} 2>&1 >/dev/null".format(w))
            os.system("rm -rf {} 2>&1 >/dev/null".format(w))
    for i in xrange(num_workers):
        print "create worker", i
        os.system("buildslave create-slave worker{} localhost worker{} pass 2>&1 >/dev/null".format(i, i))

    print "create builds", num_builds
    for i in xrange(num_builds):
        r = requests.post(
            "http://localhost:8010/builders/runtests/force",
            data={
                "forcescheduler": "force",
                "username": "",
                "reason": "force build",
                "branch": "",
                "revision": "",
                "repository": "",
                "project": "",
                "NUMLINES": 10000,
                "SLEEP": 0,
                "Name": "",
            })
        r.raise_for_status()

    print "starting workers"
    for i in xrange(num_workers):
        os.system("cd worker{}; twistd -y buildbot.tac".format(i))
    finished = False
    start = time.time()
    while not finished:
        t1 = time.time()
        r = requests.get("http://localhost:8010/json/builders/runtests")
        r.raise_for_status()
        j = r.json()
        pendingBuilds = j['pendingBuilds']
        currentBuilds = j['currentBuilds']
        t2 = time.time()
        print psutil.cpu_percent(), t2-t1, len(currentBuilds), pendingBuilds
        finished = pendingBuilds == 0
        time.sleep(0.4)
    end = time.time()
    with open("results.csv", 'a') as f:
        f.write("{};{};{};{}\n".format(config_kind, num_builds, num_workers, end-start))
    print "finished in ", end - start
    for i in xrange(num_workers):
        os.system("buildslave stop worker{}".format(i))
        os.system("rm -rf worker{}".format(i))

argh.dispatch_command(main)
