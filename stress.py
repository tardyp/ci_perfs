import os
import time

import argh

import psutil
import requests


@argh.arg('num_builds', type=int)
@argh.arg('num_workers', type=int)
@argh.arg('config_kind', type=str)
def main(num_builds, num_workers, config_kind, numlines, sleep):
    for w in os.listdir(os.curdir):
        if w.startswith('worker'):
            print "cleanup", w
            os.system("buildbot-worker stop {} 2>&1 >/dev/null".format(w))
            os.system("rm -rf {} 2>&1 >/dev/null".format(w))
    for i in xrange(num_workers):
        print "create worker", i
        os.system("buildbot-worker create-worker worker{} localhost worker{} pass 2>&1 >/dev/null".format(i, i))

    print "create builds", num_builds
    for i in xrange(num_builds):
        r = requests.post(
            "http://localhost:8010/api/v2/forceschedulers/force",
            json={"id": 1, "jsonrpc": "2.0", "method": "force", "params": {
                "builderid": "1", "username": "", "reason": "force build",
                "project": "", "repository": "", "branch": "", "revision": "",
                "NUMLINES": str(numlines),
                "SLEEP": str(sleep)}})
        r.raise_for_status()

    print "starting workers"
    for i in xrange(num_workers):
        os.system("cd worker{}; twistd -y buildbot.tac".format(i))
    finished = False
    start = time.time()
    while not finished:
        t1 = time.time()
        r = requests.get("http://localhost:8010/api/v2/buildrequests?complete=0")
        r.raise_for_status()
        brs = r.json()['buildrequests']
        t2 = time.time()
        print psutil.cpu_percent(), len(brs), t2-t1
        finished = not brs
        time.sleep(0.4)
    end = time.time()
    with open("results.csv", 'a') as f:
        f.write("{};{};{};{}\n".format(config_kind, num_builds, num_workers, end-start))
    print "finished in ", end - start
    for i in xrange(num_workers):
        os.system("buildbot-worker stop worker{}".format(i))
        os.system("rm -rf worker{}".format(i))

argh.dispatch_command(main)
