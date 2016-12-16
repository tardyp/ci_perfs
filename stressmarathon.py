import os
import time

import argh
import psutil
import requests

MARATHON_URL = os.environ["MARATHON_URL"]


def getMasterURL():
    r = requests.get(MARATHON_URL + "/v2/apps//master0")
    r.raise_for_status()
    data = r.json()
    for task in data['app']['tasks']:
        return "http://{}:{}/".format(task['host'], task['ports'][1])


@argh.arg('num_builds', type=int)
@argh.arg('num_workers', type=int)
def main(num_builds, num_workers, config_kind, numlines, sleep):
    os.system("python marathon.py worker {}".format(0))
    url = getMasterURL()
    print "create builds", num_builds
    start = time.time()
    for i in xrange(num_builds):
        r = requests.post(
            url + "api/v2/forceschedulers/force",
            json={"id": 1, "jsonrpc": "2.0", "method": "force", "params": {
                "builderid": "1", "username": "", "reason": "force build",
                "project": "", "repository": "", "branch": "", "revision": "",
                "NUMLINES": str(numlines),
                "SLEEP": str(sleep)}})
        r.raise_for_status()
    os.system("python marathon.py worker {}".format(num_workers))

    finished = False
    while not finished:
        t1 = time.time()
        r = requests.get(url + "api/v2/buildrequests?complete=0")
        r.raise_for_status()
        brs = r.json()['buildrequests']
        t2 = time.time()
        print psutil.cpu_percent(), len(brs), t2 - t1
        finished = not brs
        time.sleep(0.4)
    end = time.time()
    print "finished in ", end - start
    with open("marathonresults.csv", 'a') as f:
        f.write("{};{};{};{};{};{}\n".format(
            config_kind, num_builds, num_workers, numlines, sleep, end - start))

argh.dispatch_command(main)
